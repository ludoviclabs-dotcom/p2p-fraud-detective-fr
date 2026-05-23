"""Tests `MandateMatcher` — Sprint 2 MandateGuard.

Couvre :
- match nominal (IBAN+ICS+RUM)
- aucun candidat (mandat absent / révoqué / draft)
- RUM manquante → warning RUM_MISSING
- plusieurs candidats → warning AMBIGUOUS_MANDATE_MATCH
- RUM divergente (un mandat existe mais sans RUM, événement avec RUM différente)
"""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import make_engine
from p2p_fraud.sepa.debit_event import DebitEventInput, DebitEventService
from p2p_fraud.sepa.mandate import MandateInput, MandateService
from p2p_fraud.sepa.matcher import MandateMatcher, MatchWarning
from p2p_fraud.sepa.types import MandateScheme, SequenceType


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "test-secret-32-bytes-do-not-reuse!")


@pytest.fixture
def services():
    engine = make_engine(db_path=":memory:")
    audit = AuditLog(engine=engine)
    mandate_svc = MandateService(engine=engine, audit_log=audit)
    debit_svc = DebitEventService(engine=engine, audit_log=audit)
    return mandate_svc, debit_svc


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


# ─── Match nominal ───────────────────────────────────────────────────────────


def test_match_returns_active_mandate(services):
    mandate_svc, debit_svc = services
    mandate = mandate_svc.create(_mandate_payload(), actor="alice")
    mandate_svc.sign(mandate.mandate_id, actor="alice")
    event = debit_svc.ingest(_debit_payload(), actor="alice")
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    assert result.matched
    assert result.mandate is not None
    assert result.mandate.mandate_id == mandate.mandate_id
    assert not result.warnings


def test_match_no_active_mandate(services):
    mandate_svc, debit_svc = services
    # Mandat existe mais reste en DRAFT
    mandate_svc.create(_mandate_payload(), actor="alice")
    event = debit_svc.ingest(_debit_payload(), actor="alice")
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    assert not result.matched
    assert result.mandate is None


def test_match_revoked_mandate_returns_no_match(services):
    mandate_svc, debit_svc = services
    mandate = mandate_svc.create(_mandate_payload(), actor="alice")
    mandate_svc.sign(mandate.mandate_id, actor="alice")
    mandate_svc.revoke(mandate.mandate_id, actor="alice")
    event = debit_svc.ingest(_debit_payload(), actor="alice")
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    assert not result.matched


# ─── Warnings ────────────────────────────────────────────────────────────────


def test_match_iban_missing_returns_warning(services):
    mandate_svc, debit_svc = services
    event = debit_svc.ingest(
        _debit_payload(debtor_iban=None, idempotency_key="no-iban"),
        actor="alice",
    )
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    assert not result.matched
    assert MatchWarning.IBAN_FP_MISSING in result.warnings


def test_match_ics_missing_returns_warning(services):
    mandate_svc, debit_svc = services
    event = debit_svc.ingest(
        _debit_payload(creditor_ics=None, idempotency_key="no-ics"),
        actor="alice",
    )
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    assert not result.matched
    assert MatchWarning.ICS_MISSING in result.warnings


def test_match_rum_missing_logs_warning(services):
    mandate_svc, debit_svc = services
    mandate = mandate_svc.create(_mandate_payload(), actor="alice")
    mandate_svc.sign(mandate.mandate_id, actor="alice")
    event = debit_svc.ingest(_debit_payload(rum=None), actor="alice")
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    # Le matching peut quand même réussir sans RUM (IBAN+ICS suffisent)
    assert result.matched
    assert MatchWarning.RUM_MISSING in result.warnings


def test_match_ambiguous_when_multiple_candidates(services):
    """Si 2 mandats actifs ont IBAN+ICS identiques (RUM différentes) et que
    l'événement n'a pas de RUM → AMBIGUOUS_MANDATE_MATCH."""
    mandate_svc, debit_svc = services
    m1 = mandate_svc.create(_mandate_payload(rum="RUM-A"), actor="alice")
    m2 = mandate_svc.create(_mandate_payload(rum="RUM-B"), actor="alice")
    mandate_svc.sign(m1.mandate_id, actor="alice")
    mandate_svc.sign(m2.mandate_id, actor="alice")
    event = debit_svc.ingest(_debit_payload(rum=None), actor="alice")
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    assert result.matched  # le premier candidat est retenu
    assert MatchWarning.AMBIGUOUS_MANDATE_MATCH in result.warnings
    assert MatchWarning.RUM_MISSING in result.warnings
    assert len(result.candidates) == 2


def test_match_rum_mismatch_finds_no_strict_match_but_candidates(services):
    """Mandat existe avec RUM-A mais événement a RUM-B → 0 match strict,
    candidats du fallback IBAN+ICS retournés pour permettre signal RUM_MISMATCH."""
    mandate_svc, debit_svc = services
    m = mandate_svc.create(_mandate_payload(rum="RUM-A"), actor="alice")
    mandate_svc.sign(m.mandate_id, actor="alice")
    event = debit_svc.ingest(_debit_payload(rum="RUM-B"), actor="alice")
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event)
    # Pas de match strict (RUM différente)
    assert result.mandate is None
    # Mais le candidat fallback est retourné
    assert len(result.candidates) == 1
    assert result.candidates[0].rum == "RUM-A"


# ─── Tenant isolation ────────────────────────────────────────────────────────


def test_match_isolates_by_tenant(services):
    mandate_svc, debit_svc = services
    m = mandate_svc.create(_mandate_payload(), actor="alice", tenant_id="t-1")
    mandate_svc.sign(m.mandate_id, actor="alice", tenant_id="t-1")
    event = debit_svc.ingest(_debit_payload(), actor="alice", tenant_id="t-2")
    matcher = MandateMatcher(mandate_svc)
    result = matcher.match(event, tenant_id="t-2")
    # Le mandat est dans t-1, l'événement dans t-2 → pas de match
    assert not result.matched
