"""Tests P4-5 — purge RGPD art. 17 sur CaseService."""

from __future__ import annotations

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import CaseService
from p2p_fraud.schema import Finding, Severity


def _finding(invoice: str, severity: Severity = Severity.HIGH) -> Finding:
    return Finding(
        invoice_id=invoice,
        detector="duplicates",
        signal="dup",
        severity=severity,
        rule_id="DUP",
        evidence={"vendor_id": "V-1", "exposure_eur": 1000.0},
    )


def _make_service() -> CaseService:
    audit = AuditLog(":memory:")
    return CaseService(":memory:", audit_log=audit)


def test_purge_user_data_removes_only_target_user_cases():
    s = _make_service()
    alice_case = s.create_case_from_finding(_finding("INV-A"), actor="alice")
    bob_case = s.create_case_from_finding(_finding("INV-B"), actor="bob")
    alice_case2 = s.create_case_from_finding(_finding("INV-C"), actor="alice")

    n_deleted = s.purge_user_data("alice", actor="admin")
    assert n_deleted == 2

    remaining = s.list_cases()
    remaining_ids = {c.case_id for c in remaining}
    assert bob_case.case_id in remaining_ids
    assert alice_case.case_id not in remaining_ids
    assert alice_case2.case_id not in remaining_ids


def test_purge_user_data_removes_case_events():
    s = _make_service()
    case = s.create_case_from_finding(_finding("INV-X"), actor="charlie")
    s.assign(case.case_id, "delphine", actor="charlie")
    s.comment(case.case_id, actor="charlie", text="à investiguer")
    assert len(s.list_events(case.case_id)) == 3  # created, assigned, commented

    s.purge_user_data("charlie", actor="admin")

    # Le case n'existe plus → list_events renvoie vide
    assert s.list_events(case.case_id) == []


def test_purge_user_data_logs_rgpd_erasure_event():
    s = _make_service()
    s.create_case_from_finding(_finding("INV-1"), actor="eve")
    s.create_case_from_finding(_finding("INV-2"), actor="eve")

    s.purge_user_data("eve", actor="dpo-admin")

    entries = s.audit_log.all()
    rgpd_events = [e for e in entries if e.kind == "rgpd.erasure"]
    assert len(rgpd_events) == 1
    evt = rgpd_events[0]
    assert evt.actor == "dpo-admin"
    assert evt.payload["target_user"] == "eve"
    assert evt.payload["n_cases_deleted"] == 2


def test_purge_user_data_returns_zero_when_no_matching_user():
    s = _make_service()
    s.create_case_from_finding(_finding("INV-Z"), actor="known-user")
    n = s.purge_user_data("unknown-user", actor="admin")
    assert n == 0
    # Mais un événement rgpd.erasure est tout de même journalisé (preuve de tentative)
    entries = [e for e in s.audit_log.all() if e.kind == "rgpd.erasure"]
    assert len(entries) == 1
    assert entries[0].payload["n_cases_deleted"] == 0


def test_purge_does_not_affect_closed_cases_from_other_users():
    """Régression : la purge ne touche que les cases du `created_by` ciblé."""
    s = _make_service()
    closed = s.create_case_from_finding(_finding("INV-C"), actor="alice")
    s.close(
        closed.case_id,
        status=CaseStatus.CLOSED_CONFIRMED,
        actor="alice",
        reason="Confirmé",
    )
    bob_open = s.create_case_from_finding(_finding("INV-B"), actor="bob")

    s.purge_user_data("alice", actor="admin")

    remaining = {c.case_id for c in s.list_cases()}
    assert bob_open.case_id in remaining
    assert closed.case_id not in remaining
