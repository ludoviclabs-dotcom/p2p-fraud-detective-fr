"""Tests des règles SEPA v0 — Sprint 3 MandateGuard.

Couvre chaque règle en isolation via des contextes synthétiques :
- NO_ACTIVE_MANDATE
- MANDATE_REVOKED
- MANDATE_AMOUNT_EXCEEDED
- RUM_MISMATCH (3 cas)
- ICS_MISMATCH
- UNUSUAL_FREQUENCY
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from p2p_fraud.risk_core.types import Severity
from p2p_fraud.sepa.debit_event import DebitEventRecord
from p2p_fraud.sepa.mandate import MandateRecord
from p2p_fraud.sepa.matcher import MatchResult, MatchWarning
from p2p_fraud.sepa.rules import (
    AmountExceedsLimitRule,
    IcsMismatchRule,
    MandateRevokedRule,
    NoActiveMandateRule,
    RumMismatchRule,
    SepaRiskContext,
    UnusualFrequencyRule,
    build_sepa_rules,
)
from p2p_fraud.sepa.types import MandateScheme, MandateStatus, SequenceType

# ─── Factories ───────────────────────────────────────────────────────────────


def _event(
    *,
    event_id: str = "dbt-evt-1",
    creditor_ics: str | None = "FR18ZZZ002305",
    rum: str | None = "RUM-001",
    amount_cents: int = 8900,
    fingerprint: str | None = "fp-iban-1",
    booking_date: str | None = None,
) -> DebitEventRecord:
    return DebitEventRecord(
        event_id=event_id,
        tenant_id=None,
        source="manual",
        idempotency_key=event_id,
        creditor_ics=creditor_ics,
        creditor_name_raw="EDF",
        rum=rum,
        amount_cents=amount_cents,
        currency="EUR",
        booking_date=booking_date,
        due_date=None,
        debtor_iban_fingerprint=fingerprint,
        matched_mandate_id=None,
        created_at=datetime.now(UTC).isoformat(),
    )


def _mandate(
    *,
    mandate_id: str = "mnd-1",
    status: MandateStatus = MandateStatus.ACTIVE,
    rum: str = "RUM-001",
    creditor_ics: str = "FR18ZZZ002305",
    max_amount_cents: int | None = 10000,
    revoked_at: str | None = None,
) -> MandateRecord:
    return MandateRecord(
        mandate_id=mandate_id,
        tenant_id=None,
        creditor_id="cre-1",
        creditor_ics=creditor_ics,
        creditor_name="EDF",
        debtor_account_id="acc-1",
        debtor_iban_fingerprint="fp-iban-1",
        rum=rum,
        scheme=MandateScheme.SDD_CORE,
        sequence_type=SequenceType.RCUR,
        status=status,
        max_amount_cents=max_amount_cents,
        currency="EUR",
        frequency=None,
        valid_from=None,
        valid_to=None,
        signed_at=None,
        revoked_at=revoked_at,
        commitment_hash=None,
        current_revision_id=None,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )


def _ctx(
    *,
    event: DebitEventRecord | None = None,
    match: MatchResult | None = None,
    recent: tuple[DebitEventRecord, ...] = (),
    now: datetime | None = None,
) -> SepaRiskContext:
    return SepaRiskContext(
        event=event or _event(),
        match=match or MatchResult(mandate=None),
        recent_debits=recent,
        now=now or datetime.now(UTC),
    )


# ─── NO_ACTIVE_MANDATE ───────────────────────────────────────────────────────


def test_no_active_mandate_fires_when_no_match():
    rule = NoActiveMandateRule()
    signals = rule.evaluate(_ctx())
    assert len(signals) == 1
    assert signals[0].code == "NO_ACTIVE_MANDATE"
    assert signals[0].severity == Severity.CRITICAL
    assert signals[0].score == 80


def test_no_active_mandate_silent_when_active_match():
    rule = NoActiveMandateRule()
    match = MatchResult(mandate=_mandate())
    signals = rule.evaluate(_ctx(match=match))
    assert signals == []


def test_no_active_mandate_silent_when_revoked_match():
    """Si un mandat REVOKED matche, MANDATE_REVOKED prend le relais."""
    rule = NoActiveMandateRule()
    match = MatchResult(
        mandate=None,
        inactive_candidates=(_mandate(status=MandateStatus.REVOKED),),
    )
    signals = rule.evaluate(_ctx(match=match))
    assert signals == []


# ─── MANDATE_REVOKED ─────────────────────────────────────────────────────────


def test_mandate_revoked_fires_when_revoked_candidate():
    rule = MandateRevokedRule()
    revoked_at = "2026-01-15T10:00:00+00:00"
    match = MatchResult(
        mandate=None,
        inactive_candidates=(_mandate(status=MandateStatus.REVOKED, revoked_at=revoked_at),),
    )
    signals = rule.evaluate(_ctx(match=match))
    assert len(signals) == 1
    assert signals[0].code == "MANDATE_REVOKED"
    assert signals[0].severity == Severity.CRITICAL
    assert signals[0].score == 75
    assert signals[0].evidence["revoked_at"] == revoked_at


def test_mandate_revoked_silent_when_only_active_match():
    rule = MandateRevokedRule()
    match = MatchResult(mandate=_mandate())
    assert rule.evaluate(_ctx(match=match)) == []


def test_mandate_revoked_silent_when_no_candidates():
    rule = MandateRevokedRule()
    assert rule.evaluate(_ctx()) == []


# ─── MANDATE_AMOUNT_EXCEEDED ─────────────────────────────────────────────────


def test_amount_exceeds_limit_fires():
    rule = AmountExceedsLimitRule()
    mandate = _mandate(max_amount_cents=5000)
    event = _event(amount_cents=8000)
    match = MatchResult(mandate=mandate)
    signals = rule.evaluate(_ctx(event=event, match=match))
    assert len(signals) == 1
    assert signals[0].code == "MANDATE_AMOUNT_EXCEEDED"
    assert signals[0].evidence["delta_cents"] == 3000


def test_amount_below_limit_silent():
    rule = AmountExceedsLimitRule()
    mandate = _mandate(max_amount_cents=10000)
    event = _event(amount_cents=8000)
    match = MatchResult(mandate=mandate)
    assert rule.evaluate(_ctx(event=event, match=match)) == []


def test_amount_no_limit_silent():
    rule = AmountExceedsLimitRule()
    mandate = _mandate(max_amount_cents=None)
    match = MatchResult(mandate=mandate)
    assert rule.evaluate(_ctx(match=match)) == []


def test_amount_no_active_mandate_silent():
    """Sans mandat actif, cette règle ne se prononce pas."""
    rule = AmountExceedsLimitRule()
    assert rule.evaluate(_ctx()) == []


# ─── RUM_MISMATCH ────────────────────────────────────────────────────────────


def test_rum_mismatch_when_event_has_rum_but_only_other_active_rums():
    rule = RumMismatchRule()
    # Pas de match (mandat=None), mais d'autres mandats actifs avec autres RUM
    candidates = (_mandate(rum="RUM-OTHER"),)
    match = MatchResult(mandate=None, candidates=candidates)
    event = _event(rum="RUM-WRONG")
    signals = rule.evaluate(_ctx(event=event, match=match))
    assert len(signals) == 1
    assert signals[0].code == "RUM_MISMATCH"
    assert signals[0].severity == Severity.HIGH
    assert "RUM-OTHER" in signals[0].evidence["known_active_rums"]


def test_rum_mismatch_when_rum_missing_with_match():
    rule = RumMismatchRule()
    mandate = _mandate()
    match = MatchResult(mandate=mandate, warnings=(MatchWarning.RUM_MISSING,))
    event = _event(rum=None)
    signals = rule.evaluate(_ctx(event=event, match=match))
    assert len(signals) == 1
    assert signals[0].severity == Severity.MEDIUM
    assert signals[0].score == 20


def test_rum_mismatch_silent_when_match_and_rum_present():
    rule = RumMismatchRule()
    mandate = _mandate(rum="RUM-001")
    match = MatchResult(mandate=mandate)
    event = _event(rum="RUM-001")
    assert rule.evaluate(_ctx(event=event, match=match)) == []


# ─── ICS_MISMATCH ────────────────────────────────────────────────────────────


def test_ics_mismatch_fires_when_ics_differs():
    rule = IcsMismatchRule()
    mandate = _mandate(creditor_ics="FR18ZZZ002305")
    match = MatchResult(mandate=mandate)
    event = _event(creditor_ics="DE89ZZZ999999")  # différent
    signals = rule.evaluate(_ctx(event=event, match=match))
    assert len(signals) == 1
    assert signals[0].code == "ICS_MISMATCH"
    assert signals[0].severity == Severity.CRITICAL


def test_ics_mismatch_silent_when_equal():
    rule = IcsMismatchRule()
    mandate = _mandate(creditor_ics="FR18ZZZ002305")
    match = MatchResult(mandate=mandate)
    event = _event(creditor_ics="FR18ZZZ002305")
    assert rule.evaluate(_ctx(event=event, match=match)) == []


def test_ics_mismatch_silent_when_no_mandate():
    rule = IcsMismatchRule()
    assert rule.evaluate(_ctx()) == []


# ─── UNUSUAL_FREQUENCY ───────────────────────────────────────────────────────


def test_unusual_frequency_fires_above_threshold():
    rule = UnusualFrequencyRule(window_days=7, threshold=3)
    now = datetime.now(UTC)
    recent = tuple(
        _event(
            event_id=f"dbt-evt-{i}",
            booking_date=(now - timedelta(days=i)).date().isoformat(),
        )
        for i in range(1, 4)
    )
    signals = rule.evaluate(_ctx(recent=recent, now=now))
    assert len(signals) == 1
    assert signals[0].code == "UNUSUAL_FREQUENCY"
    assert signals[0].evidence["observed_count"] >= 3


def test_unusual_frequency_silent_below_threshold():
    rule = UnusualFrequencyRule(window_days=7, threshold=3)
    now = datetime.now(UTC)
    recent = (
        _event(
            event_id="dbt-evt-2",
            booking_date=(now - timedelta(days=1)).date().isoformat(),
        ),
    )
    assert rule.evaluate(_ctx(recent=recent, now=now)) == []


def test_unusual_frequency_ignores_old_events():
    rule = UnusualFrequencyRule(window_days=7, threshold=3)
    now = datetime.now(UTC)
    recent = tuple(
        _event(
            event_id=f"dbt-evt-{i}",
            booking_date=(now - timedelta(days=30)).date().isoformat(),
        )
        for i in range(3)
    )
    assert rule.evaluate(_ctx(recent=recent, now=now)) == []


def test_unusual_frequency_ignores_different_creditor():
    rule = UnusualFrequencyRule(window_days=7, threshold=3)
    now = datetime.now(UTC)
    recent = tuple(
        _event(
            event_id=f"dbt-evt-{i}",
            creditor_ics="OTHER",
            booking_date=(now - timedelta(days=i)).date().isoformat(),
        )
        for i in range(3)
    )
    assert rule.evaluate(_ctx(recent=recent, now=now)) == []


# ─── Factory build_sepa_rules ────────────────────────────────────────────────


def test_build_sepa_rules_contains_all_six():
    rules = build_sepa_rules()
    codes = {r.id for r in rules}
    assert codes == {
        "NO_ACTIVE_MANDATE",
        "MANDATE_REVOKED",
        "MANDATE_AMOUNT_EXCEEDED",
        "RUM_MISMATCH",
        "ICS_MISMATCH",
        "UNUSUAL_FREQUENCY",
    }


def test_all_rules_target_sepa_domain():
    from p2p_fraud.risk_core.types import RiskDomain

    for rule in build_sepa_rules():
        assert rule.domain == RiskDomain.SEPA_DIRECT_DEBIT
