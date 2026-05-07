"""Tests service exposure (€ par finding, par fournisseur, cockpit) — Sprint 5."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.schema import Finding, Severity
from p2p_fraud.services.exposure import (
    aggregate_exposure_by_vendor,
    cases_to_dataframe,
    cockpit_summary,
    compute_finding_exposure,
)


def _f(invoice_id: str, rule_id: str, vendor_id: str, exposure: float | None,
       severity: Severity = Severity.CRITICAL,
       vendor_name: str | None = None,
       detector: str = "master_data") -> Finding:
    ev = {"vendor_id": vendor_id}
    if exposure is not None:
        ev["exposure_eur"] = exposure
    if vendor_name:
        ev["vendor_name"] = vendor_name
    return Finding(
        invoice_id=invoice_id,
        detector=detector,
        signal="t",
        severity=severity,
        rule_id=rule_id,
        evidence=ev,
    )


def test_compute_exposure_uses_evidence_first():
    f = _f("INV1", "MD_IBAN_NO_4EYES", "V1", 12_345.0)
    assert compute_finding_exposure(f) == 12_345.0


def test_compute_exposure_falls_back_to_invoice_amount():
    f = _f("INV1", "DUP_EXACT", "V1", None)
    invoices = pd.DataFrame([{"invoice_id": "INV1", "amount": 999.0, "vendor_id": "V1"}])
    assert compute_finding_exposure(f, invoices) == 999.0


def test_compute_exposure_handles_vendor_level_invoice_id():
    f = Finding(
        invoice_id="VENDOR::V1",
        detector="master_data",
        signal="t",
        severity=Severity.HIGH,
        rule_id="MD_IBAN_NO_4EYES",
        evidence={"vendor_id": "V1"},
    )
    invoices = pd.DataFrame(
        [
            {"invoice_id": "INV1", "amount": 100.0, "vendor_id": "V1"},
            {"invoice_id": "INV2", "amount": 200.0, "vendor_id": "V1"},
            {"invoice_id": "INV3", "amount": 50.0, "vendor_id": "V2"},
        ]
    )
    assert compute_finding_exposure(f, invoices) == 300.0


def test_aggregate_exposure_by_vendor_dedupes_by_rule():
    findings = [
        _f("INV1", "MD_IBAN_NO_4EYES", "V1", 10_000.0),
        _f("INV2", "MD_IBAN_NO_4EYES", "V1", 5_000.0),  # même règle, on garde le max
        _f("INV3", "SANCTIONS_VENDOR_HIT", "V1", 3_000.0),
    ]
    out = aggregate_exposure_by_vendor(findings)
    assert len(out) == 1
    v1 = out[0]
    assert v1.vendor_id == "V1"
    assert v1.exposure_eur == 13_000.0  # 10 000 (max IBAN) + 3 000 (sanctions)
    assert v1.n_findings == 3
    assert v1.n_critical == 3
    assert {"MD_IBAN_NO_4EYES", "SANCTIONS_VENDOR_HIT"} == set(v1.rules)


def test_aggregate_exposure_sorts_descending():
    findings = [
        _f("INV1", "DUP_EXACT", "V_LOW", 100.0),
        _f("INV2", "DUP_EXACT", "V_HIGH", 50_000.0),
        _f("INV3", "DUP_EXACT", "V_MID", 5_000.0),
    ]
    out = aggregate_exposure_by_vendor(findings)
    assert [v.vendor_id for v in out] == ["V_HIGH", "V_MID", "V_LOW"]


def test_cockpit_summary_aggregates_kpis():
    service = CaseService(":memory:", AuditLog(":memory:"))
    f1 = _f("INV1", "MD_IBAN_NO_4EYES", "V1", 50_000.0)
    f2 = _f("INV2", "DUP_EXACT", "V2", 1_500.0, severity=Severity.HIGH, detector="duplicates")
    case1 = service.create_case_from_finding(f1, actor="alice")
    # Marque le case comme ayant un SLA dépassé
    case1.sla_deadline = datetime.now(UTC) - timedelta(days=1)
    service._persist(case1)
    cases = service.list_cases()

    summary = cockpit_summary([f1, f2], cases=cases)
    assert summary.n_findings == 2
    assert summary.n_critical == 1
    assert summary.n_high == 1
    assert summary.exposure_eur_total == 51_500.0
    assert summary.exposure_eur_critical == 50_000.0
    assert summary.n_cases_open == 1
    assert summary.n_cases_overdue == 1
    assert summary.n_cases_unassigned_critical == 1
    assert summary.top_vendors[0].vendor_id == "V1"


def test_cockpit_summary_no_cases():
    summary = cockpit_summary([], cases=None)
    assert summary.n_findings == 0
    assert summary.n_cases_open == 0
    assert summary.top_vendors == []


def test_cases_to_dataframe_includes_overdue_flag():
    service = CaseService(":memory:", AuditLog(":memory:"))
    f = _f("INV1", "MD_IBAN_NO_4EYES", "V1", 10_000.0)
    case = service.create_case_from_finding(f, actor="alice")
    case.sla_deadline = datetime.now(UTC) - timedelta(hours=1)
    service._persist(case)

    df = cases_to_dataframe(service.list_cases())
    assert "is_overdue" in df.columns
    assert df.iloc[0]["is_overdue"]
    assert not df.iloc[0]["is_closed"]
