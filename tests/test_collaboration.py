"""Tests P3.7 — SLA configurable, @mentions, OIDC."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from p2p_fraud.cases.mentions import (
    MentionStore,
    build_mentions,
    extract_mentions,
)
from p2p_fraud.cases.service import CaseService
from p2p_fraud.cases.sla import DEFAULT_SLA, SLAConfig
from p2p_fraud.schema import Finding, Severity
from p2p_fraud.security.oidc import (
    OIDCConfig,
    build_authorization_url,
    make_pkce_challenge,
    map_groups_to_role,
    parse_userinfo,
)

# ─── SLA configurable ─────────────────────────────────────────────────────────


def test_sla_default_values():
    assert DEFAULT_SLA.critical_hours == 24
    assert DEFAULT_SLA.high_hours == 72
    assert DEFAULT_SLA.medium_hours == 168
    assert DEFAULT_SLA.low_hours == 720


def test_sla_hours_for_unknown_severity_falls_back_low():
    sla = SLAConfig()
    assert sla.hours_for("unknown") == sla.low_hours
    assert sla.hours_for("") == sla.low_hours


def test_sla_deadline_for_critical_is_24h():
    sla = SLAConfig()
    base = datetime(2026, 5, 10, tzinfo=UTC)
    deadline = sla.deadline_for("critical", from_dt=base)
    assert deadline == base + timedelta(hours=24)


def test_sla_is_overdue_skipped_for_closed_case():
    sla = SLAConfig()
    old = datetime(2020, 1, 1, tzinfo=UTC)
    assert sla.is_overdue(severity="critical", created_at=old, status_closed=False) is True
    assert sla.is_overdue(severity="critical", created_at=old, status_closed=True) is False


# ─── @mentions parser ─────────────────────────────────────────────────────────


def test_extract_mentions_basic():
    text = "Bonjour @sbernard, peux-tu valider ? Cc @audit.senior et @jdupont."
    assert extract_mentions(text) == ["sbernard", "audit.senior", "jdupont"]


def test_extract_mentions_deduplicates():
    text = "@alice ping @alice cc @bob"
    assert extract_mentions(text) == ["alice", "bob"]


def test_extract_mentions_handles_empty():
    assert extract_mentions("") == []
    assert extract_mentions("Aucune mention ici.") == []


def test_extract_mentions_strips_trailing_dot():
    assert extract_mentions("Hello @alice.") == ["alice"]


def test_mention_store_record_and_for_user():
    store = MentionStore(":memory:")
    mentions = build_mentions(
        case_id="CASE-001",
        text="Hi @alice, please review",
        mentioned_by="bob",
    )
    n = store.record(mentions)
    assert n == 1

    user_mentions = store.for_user("alice")
    assert len(user_mentions) == 1
    assert user_mentions[0].mentioned_user == "alice"
    assert user_mentions[0].mentioned_by == "bob"
    assert user_mentions[0].case_id == "CASE-001"


def test_mention_store_mark_read():
    store = MentionStore(":memory:")
    store.record(build_mentions(case_id="C1", text="@alice ping", mentioned_by="bob"))
    store.record(build_mentions(case_id="C2", text="@alice second", mentioned_by="bob"))
    assert len(store.for_user("alice", only_unread=True)) == 2

    n = store.mark_read(username="alice", case_id="C1")
    assert n == 1
    assert len(store.for_user("alice", only_unread=True)) == 1
    assert len(store.for_user("alice", only_unread=False)) == 2


# ─── CaseService — SLA + @mentions integration ───────────────────────────────


def test_case_service_uses_severity_specific_sla():
    sla = SLAConfig(critical_hours=24, high_hours=72)
    service = CaseService(sla_config=sla)
    finding_critical = Finding(
        invoice_id="INV-001",
        detector="sanctions",
        signal="test",
        severity=Severity.CRITICAL,
        rule_id="TEST_RULE",
        evidence={},
    )
    case = service.create_case_from_finding(finding_critical, actor="bob")
    expected_max = datetime.now(UTC) + timedelta(hours=24, minutes=1)
    expected_min = datetime.now(UTC) + timedelta(hours=23, minutes=59)
    assert expected_min <= case.sla_deadline <= expected_max


def test_case_service_records_mentions_in_comment():
    service = CaseService()
    finding = Finding(
        invoice_id="INV-1",
        detector="sanctions",
        signal="test",
        severity=Severity.HIGH,
        rule_id="X",
        evidence={},
    )
    case = service.create_case_from_finding(finding, actor="bob")

    service.comment(case.case_id, actor="bob", text="Hi @alice, please look at this.")

    user_mentions = service.mentions.for_user("alice")
    assert len(user_mentions) == 1
    assert user_mentions[0].case_id == case.case_id
    assert user_mentions[0].mentioned_by == "bob"


# ─── OIDC ─────────────────────────────────────────────────────────────────────


def test_oidc_pkce_challenge_is_unique():
    p1 = make_pkce_challenge()
    p2 = make_pkce_challenge()
    assert p1.code_verifier != p2.code_verifier
    assert p1.state != p2.state
    assert len(p1.code_challenge) >= 43  # base64url-encoded SHA-256


def test_oidc_authorization_url_contains_required_params():
    cfg = OIDCConfig(
        issuer="https://login.microsoftonline.com/tenant/v2.0",
        client_id="myapp",
        redirect_uri="https://app.com/callback",
    )
    pkce = make_pkce_challenge()
    url = build_authorization_url(cfg, pkce=pkce)
    assert "client_id=myapp" in url
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert "response_type=code" in url
    assert "scope=openid+email+profile" in url


def test_oidc_map_groups_to_role_picks_highest_rank():
    role_map = {
        "DG-Audit": "admin",
        "Audit-Senior": "manager",
        "Audit-Junior": "analyst",
    }
    assert map_groups_to_role(["Audit-Junior", "DG-Audit"], role_map=role_map) == "admin"
    assert map_groups_to_role(["Audit-Junior"], role_map=role_map) == "analyst"
    assert map_groups_to_role(["UNKNOWN"], role_map=role_map) == "viewer"


def test_oidc_parse_userinfo_extracts_username_from_claims():
    claims = {
        "preferred_username": "jdupont",
        "email": "jdupont@example.com",
        "name": "Jean Dupont",
        "groups": ["Audit-Senior"],
    }
    info = parse_userinfo(claims)
    assert info["username"] == "jdupont"
    assert info["email"] == "jdupont@example.com"
    assert info["groups"] == ["Audit-Senior"]


def test_oidc_parse_userinfo_falls_back_to_email_local():
    claims = {"email": "smith@acme.com", "name": "Smith"}
    info = parse_userinfo(claims)
    assert info["username"] == "smith"
