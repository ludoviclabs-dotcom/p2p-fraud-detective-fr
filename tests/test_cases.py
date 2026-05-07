"""Tests case management v0 — Sprint 3."""

from __future__ import annotations

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import CaseClosedError, CaseNotFoundError, CaseService
from p2p_fraud.schema import Finding, Severity


@pytest.fixture
def service() -> CaseService:
    return CaseService(":memory:", AuditLog(":memory:"))


def _finding(invoice_id: str = "INV1", rule_id: str = "MD_IBAN_NO_4EYES") -> Finding:
    return Finding(
        invoice_id=invoice_id,
        detector="master_data",
        signal="iban_change_without_4eyes",
        severity=Severity.CRITICAL,
        rule_id=rule_id,
        evidence={"vendor_id": "V001", "exposure_eur": 12_345.0},
    )


def test_create_case_from_finding(service: CaseService):
    case = service.create_case_from_finding(_finding(), actor="alice")
    assert case.status == CaseStatus.NEW
    assert case.exposure_eur == 12_345.0
    assert case.vendor_id == "V001"
    assert case.created_by == "alice"
    # Le case_id est unique
    assert case.case_id.startswith("CASE-")


def test_assign_moves_status_from_new_to_triaged(service: CaseService):
    case = service.create_case_from_finding(_finding(), actor="alice")
    case = service.assign(case.case_id, "bob", actor="alice")
    assert case.assignee == "bob"
    assert case.status == CaseStatus.TRIAGED


def test_close_requires_terminal_status_and_reason(service: CaseService):
    case = service.create_case_from_finding(_finding(), actor="alice")
    with pytest.raises(ValueError, match="terminal"):
        service.close(case.case_id, CaseStatus.IN_PROGRESS, actor="alice", reason="x")
    with pytest.raises(ValueError, match="motif"):
        service.close(case.case_id, CaseStatus.CLOSED_CONFIRMED, actor="alice", reason="")


def test_close_then_mutation_is_blocked(service: CaseService):
    case = service.create_case_from_finding(_finding(), actor="alice")
    service.close(
        case.case_id,
        CaseStatus.CLOSED_CONFIRMED,
        actor="alice",
        reason="Fraude confirmée + paiement bloqué",
    )
    with pytest.raises(CaseClosedError):
        service.assign(case.case_id, "bob", actor="alice")
    with pytest.raises(CaseClosedError):
        service.escalate(case.case_id, actor="alice", channel="legal", reason="x")


def test_comment_is_allowed_post_closure_and_flagged(service: CaseService):
    case = service.create_case_from_finding(_finding(), actor="alice")
    service.close(
        case.case_id, CaseStatus.CLOSED_REJECTED, actor="alice", reason="rejet motivé"
    )
    # Pas d'exception
    service.comment(case.case_id, actor="bob", text="post-mortem")
    events = service.list_events(case.case_id)
    last = events[-1]
    assert last.kind == "commented"
    assert last.payload["post_closure"] is True


def test_set_status_rejects_terminal_status(service: CaseService):
    case = service.create_case_from_finding(_finding(), actor="alice")
    with pytest.raises(ValueError, match="close"):
        service.set_status(case.case_id, CaseStatus.CLOSED_CONFIRMED, actor="alice")


def test_get_unknown_case_raises(service: CaseService):
    with pytest.raises(CaseNotFoundError):
        service.get("CASE-unknown")


def test_audit_log_records_full_lifecycle(service: CaseService):
    case = service.create_case_from_finding(_finding(), actor="alice")
    service.assign(case.case_id, "bob", actor="alice")
    service.comment(case.case_id, actor="bob", text="Vu, je traite.")
    service.escalate(case.case_id, actor="bob", channel="legal", reason="préjudice estimé")
    service.close(
        case.case_id,
        CaseStatus.CLOSED_CONFIRMED,
        actor="charlie",
        reason="Plainte déposée",
        evidence_path="/storage/INV1.zip",
    )

    entries = service.audit_log.all()
    kinds = [e.kind for e in entries]
    assert kinds == [
        "case.created",
        "case.assigned",
        "case.commented",
        "case.escalated",
        "case.closed",
    ]
    valid, invalid = service.audit_log.verify_chain()
    assert valid is True
    assert invalid == []


def test_create_from_multiple_findings_aggregates_severity_and_exposure(service: CaseService):
    f1 = _finding("INV1", "RULE1")
    f2 = _finding("INV2", "RULE2")
    f3 = Finding(
        invoice_id="INV3",
        detector="sanctions",
        signal="vendor_sanctioned",
        severity=Severity.HIGH,
        rule_id="SANCTIONS_VENDOR_HIT",
        evidence={"vendor_id": "V001", "exposure_eur": 5_000.0},
    )
    case = service.create_case_from_findings(
        [f1, f2, f3], actor="alice", title="Investigation V001"
    )
    assert case.severity == "critical"  # max
    assert case.exposure_eur == pytest.approx(12_345.0 + 12_345.0 + 5_000.0)
    assert len(case.finding_ids) == 3
