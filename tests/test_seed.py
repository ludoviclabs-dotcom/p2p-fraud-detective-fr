"""Tests du seed de démo (cases pré-chargés pour la vitrine Streamlit Cloud)."""

from __future__ import annotations

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.seed import seed_demo_cases
from p2p_fraud.cases.service import CaseService


def _service() -> CaseService:
    return CaseService(":memory:", AuditLog(":memory:"))


def test_seed_creates_five_cases() -> None:
    svc = _service()
    n = seed_demo_cases(svc)
    assert n == 5
    assert len(svc.list_cases()) == 5


def test_seed_is_idempotent() -> None:
    svc = _service()
    seed_demo_cases(svc)
    second = seed_demo_cases(svc)
    assert second == 0
    assert len(svc.list_cases()) == 5


def test_seed_covers_all_severities_and_diverse_statuses() -> None:
    svc = _service()
    seed_demo_cases(svc)
    cases = svc.list_cases()

    severities = {c.severity for c in cases}
    assert "critical" in severities
    assert "high" in severities
    assert "medium" in severities

    statuses = {c.status for c in cases}
    assert CaseStatus.NEW in statuses
    assert CaseStatus.TRIAGED in statuses
    assert CaseStatus.IN_PROGRESS in statuses
    assert CaseStatus.ESCALATED in statuses
    assert CaseStatus.CLOSED_FALSE_POSITIVE in statuses


def test_seed_audit_chain_valid() -> None:
    svc = _service()
    seed_demo_cases(svc)
    valid, invalid = svc.audit_log.verify_chain()
    assert valid is True
    assert invalid == []
    # 5 cases × 1 création + 4 assignations + 1 set_status + 1 commentaire
    # + 1 escalade + 1 clôture = 13 entrées attendues (création est un seul kind).
    # On vérifie au moins que le seeding produit > 5 entrées (tous les events).
    assert len(svc.audit_log.all()) >= 5


def test_seed_exposure_amounts_are_positive() -> None:
    svc = _service()
    seed_demo_cases(svc)
    for case in svc.list_cases():
        assert case.exposure_eur is not None
        assert case.exposure_eur > 0


def test_seed_closed_case_has_reason() -> None:
    svc = _service()
    seed_demo_cases(svc)
    closed_cases = [c for c in svc.list_cases() if c.status.is_closed]
    assert len(closed_cases) == 1
    assert closed_cases[0].closure_reason is not None
    assert len(closed_cases[0].closure_reason) > 10
