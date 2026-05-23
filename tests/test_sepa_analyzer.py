"""Tests `SepaAnalyzer` — Sprint 3 MandateGuard.

End-to-end : ingest → match → assess → audit.
Couvre les scénarios pilote :
- prélèvement valide sur mandat actif → ALLOW
- prélèvement sans mandat → DISPUTE_READY (NO_ACTIVE_MANDATE)
- prélèvement sur mandat révoqué → DISPUTE_READY (MANDATE_REVOKED)
- montant excédant le plafond → score boosté
- audit chain : DEBIT_IMPORTED + DEBIT_ANALYZED présents
"""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import make_engine
from p2p_fraud.risk_core.types import RiskDecision, RiskLevel
from p2p_fraud.sepa import (
    DebitEventInput,
    MandateInput,
    SepaAnalyzer,
)
from p2p_fraud.sepa.types import MandateScheme, SequenceType


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "analyzer-test-secret-32-bytes-x!")


@pytest.fixture
def analyzer():
    engine = make_engine(db_path=":memory:")
    return SepaAnalyzer(engine=engine, audit_log=AuditLog(engine=engine))


def _mandate_payload(**overrides) -> MandateInput:
    defaults = {
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name": "EDF SA",
        "debtor_iban": "FR7630001007941234567890185",
        "rum": "RUM-EDF-001",
        "scheme": MandateScheme.SDD_CORE,
        "sequence_type": SequenceType.RCUR,
        "max_amount_cents": 10000,
    }
    defaults.update(overrides)
    return MandateInput(**defaults)


def _debit_payload(**overrides) -> DebitEventInput:
    defaults = {
        "source": "manual",
        "idempotency_key": "debit-001",
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name_raw": "EDF SA",
        "rum": "RUM-EDF-001",
        "amount_cents": 8900,
        "debtor_iban": "FR7630001007941234567890185",
    }
    defaults.update(overrides)
    return DebitEventInput(**defaults)


# ─── Scénario 1 : mandat actif, montant OK → ALLOW ───────────────────────────


def test_active_mandate_with_normal_amount_allows(analyzer):
    mandate = analyzer.mandates.create(_mandate_payload(), actor="alice")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    result = analyzer.analyze(_debit_payload(), actor="alice")
    assert result.assessment.decision == RiskDecision.ALLOW
    assert result.assessment.score == 0
    assert result.match.matched
    assert result.match.mandate is not None
    assert result.match.mandate.mandate_id == mandate.mandate_id


# ─── Scénario 2 : aucun mandat → DISPUTE_READY ───────────────────────────────


def test_no_mandate_yields_dispute_ready(analyzer):
    result = analyzer.analyze(_debit_payload(), actor="alice")
    assert result.assessment.decision == RiskDecision.DISPUTE_READY
    assert result.assessment.level == RiskLevel.CRITICAL
    assert any(s.code == "NO_ACTIVE_MANDATE" for s in result.assessment.signals)


# ─── Scénario 3 : mandat révoqué → DISPUTE_READY MANDATE_REVOKED ─────────────


def test_revoked_mandate_triggers_block_recommended(analyzer):
    """MANDATE_REVOKED a score 75 (spec §06) → BLOCK_RECOMMENDED (score < 80)."""
    mandate = analyzer.mandates.create(_mandate_payload(), actor="alice")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    analyzer.mandates.revoke(mandate.mandate_id, actor="alice", reason_text="client req")
    result = analyzer.analyze(_debit_payload(), actor="alice")
    codes = {s.code for s in result.assessment.signals}
    assert "MANDATE_REVOKED" in codes
    # NO_ACTIVE_MANDATE doit être silencieux (le revoked l'emporte)
    assert "NO_ACTIVE_MANDATE" not in codes
    assert result.assessment.level == RiskLevel.CRITICAL
    assert result.assessment.decision == RiskDecision.BLOCK_RECOMMENDED


# ─── Scénario 4 : montant supérieur au plafond → score boosté ───────────────


def test_amount_exceeds_limit_boosts_score(analyzer):
    mandate = analyzer.mandates.create(_mandate_payload(max_amount_cents=5000), actor="alice")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    result = analyzer.analyze(_debit_payload(amount_cents=20000), actor="alice")
    codes = {s.code for s in result.assessment.signals}
    assert "MANDATE_AMOUNT_EXCEEDED" in codes
    # 70 points pour AMOUNT_EXCEEDED + critical → REVIEW au moins
    assert result.assessment.score >= 60


# ─── Scénario 5 : RUM divergente sans mandat correspondant → RUM_MISMATCH ───


def test_rum_mismatch_produces_signal(analyzer):
    mandate = analyzer.mandates.create(_mandate_payload(rum="RUM-A"), actor="alice")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    result = analyzer.analyze(_debit_payload(rum="RUM-B"), actor="alice")
    codes = {s.code for s in result.assessment.signals}
    assert "RUM_MISMATCH" in codes


# ─── Scénario 6 : événement sans RUM ─────────────────────────────────────────


def test_missing_rum_yields_medium_signal(analyzer):
    mandate = analyzer.mandates.create(_mandate_payload(), actor="alice")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    result = analyzer.analyze(_debit_payload(rum=None), actor="alice")
    codes = {s.code for s in result.assessment.signals}
    assert "RUM_MISMATCH" in codes  # RUM_MISSING route
    rum_signal = next(s for s in result.assessment.signals if s.code == "RUM_MISMATCH")
    assert rum_signal.score == 20


# ─── Audit chain : événements requis ─────────────────────────────────────────


def test_audit_chain_records_imported_and_analyzed(analyzer):
    analyzer.analyze(_debit_payload(), actor="alice")
    kinds = [e.kind for e in analyzer.audit.all()]
    assert "DEBIT_IMPORTED" in kinds
    assert "DEBIT_ANALYZED" in kinds


def test_audit_analyzed_payload_contains_decision_and_engine_version(analyzer):
    analyzer.analyze(_debit_payload(), actor="alice")
    analyzed = next(e for e in analyzer.audit.all() if e.kind == "DEBIT_ANALYZED")
    assert analyzed.payload["engine_version"] == "sepa-v0.1.0"
    assert "score" in analyzed.payload
    assert "decision" in analyzed.payload
    assert isinstance(analyzed.payload["signal_codes"], list)


def test_audit_does_not_leak_iban(analyzer):
    """Aucun IBAN clair ne doit apparaître dans aucun event de l'audit chain."""
    iban = "FR7630001007941234567890185"
    analyzer.analyze(_debit_payload(debtor_iban=iban), actor="alice")
    import json

    for entry in analyzer.audit.all():
        as_str = json.dumps(entry.payload)
        assert iban not in as_str
        assert iban[:8] not in as_str


# ─── Engine + match output ───────────────────────────────────────────────────


def test_engine_version_is_consistent(analyzer):
    result = analyzer.analyze(_debit_payload(), actor="alice")
    assert result.assessment.engine_version == "sepa-v0.1.0"


def test_mark_matched_persists_to_debit_event(analyzer):
    mandate = analyzer.mandates.create(_mandate_payload(), actor="alice")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    result = analyzer.analyze(_debit_payload(), actor="alice")
    stored = analyzer.debits.get(result.event.event_id)
    assert stored is not None
    assert stored.matched_mandate_id == mandate.mandate_id


def test_unmatched_marks_event_with_no_mandate_id(analyzer):
    result = analyzer.analyze(_debit_payload(), actor="alice")
    stored = analyzer.debits.get(result.event.event_id)
    assert stored is not None
    assert stored.matched_mandate_id is None


# ─── Idempotence du pipeline complet ─────────────────────────────────────────


def test_idempotent_analyze_returns_same_event(analyzer):
    mandate = analyzer.mandates.create(_mandate_payload(), actor="alice")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    r1 = analyzer.analyze(_debit_payload(), actor="alice")
    r2 = analyzer.analyze(_debit_payload(), actor="alice")  # même key
    assert r1.event.event_id == r2.event.event_id
    # Le score doit rester déterministe
    assert r1.assessment.score == r2.assessment.score


# ─── Tenant isolation ────────────────────────────────────────────────────────


def test_tenant_isolation_in_analyze(analyzer):
    """Mandat de tenant-1 ne match pas un événement de tenant-2."""
    mandate = analyzer.mandates.create(_mandate_payload(), actor="alice", tenant_id="tenant-1")
    analyzer.mandates.sign(mandate.mandate_id, actor="alice", tenant_id="tenant-1")
    result = analyzer.analyze(_debit_payload(), actor="alice", tenant_id="tenant-2")
    assert not result.match.matched
    codes = {s.code for s in result.assessment.signals}
    assert "NO_ACTIVE_MANDATE" in codes
