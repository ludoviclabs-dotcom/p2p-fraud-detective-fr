"""Tests détecteur master data changes — Sprint 1.

On vise un recall ≥ 0.95 sur les scénarios étiquetés `bec_iban_swap`
et `dormant_reactivation` du générateur synthétique.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from p2p_fraud.detectors import master_data_changes as md
from p2p_fraud.schema import MasterDataField, Severity, VendorMasterEvent
from p2p_fraud.synthetic.generator import (
    GeneratorConfig,
    MasterDataEventsConfig,
    attach_vendor_ids,
    generate_dataset,
    generate_master_data_events,
)


def _make_event(
    vendor_id: str,
    field: MasterDataField,
    when: datetime,
    *,
    new: str = "NEW",
    old: str = "OLD",
    approved_by: str | None = None,
    changed_by: str = "U001",
) -> VendorMasterEvent:
    return VendorMasterEvent(
        event_id=f"EV-{vendor_id}-{field.value}-{when.isoformat()}",
        vendor_id=vendor_id,
        field=field,
        old_value=old,
        new_value=new,
        changed_at=when,
        changed_by=changed_by,
        approved_by=approved_by,
        source="manual",
    )


def _invoice_row(invoice_id: str, vendor_id: str, when: datetime, amount: float) -> dict:
    return {
        "invoice_id": invoice_id,
        "vendor_id": vendor_id,
        "vendor_name": vendor_id,
        "amount": amount,
        "invoice_date": pd.Timestamp(when),
        "currency": "EUR",
    }


# --- Tests unitaires (cas clean isolés) ---


def test_iban_change_with_4eyes_does_not_trigger():
    when = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
    ev = _make_event(
        "V001",
        MasterDataField.IBAN,
        when,
        approved_by="U002",
        changed_by="U001",
    )
    invoices = pd.DataFrame([_invoice_row("INV1", "V001", when + timedelta(days=10), 5_000.0)])
    findings = md.detect_iban_change_without_4eyes([ev], invoices)
    assert findings == []


def test_iban_change_without_4eyes_triggers_critical_per_invoice():
    when = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
    ev = _make_event("V001", MasterDataField.IBAN, when, approved_by=None)
    invoices = pd.DataFrame(
        [
            _invoice_row("INV1", "V001", when + timedelta(days=5), 12_000.0),
            _invoice_row("INV2", "V001", when + timedelta(days=20), 8_000.0),
        ]
    )
    findings = md.detect_iban_change_without_4eyes([ev], invoices)
    assert len(findings) == 2
    assert all(f.severity == Severity.CRITICAL for f in findings)
    assert {f.invoice_id for f in findings} == {"INV1", "INV2"}
    # Exposure cumulée
    assert findings[0].evidence["exposure_eur"] == pytest.approx(20_000.0)


def test_iban_change_same_user_approved_treated_as_no_4eyes():
    when = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
    ev = _make_event(
        "V001",
        MasterDataField.IBAN,
        when,
        changed_by="U001",
        approved_by="U001",  # même user
    )
    invoices = pd.DataFrame([_invoice_row("INV1", "V001", when + timedelta(days=2), 3_000.0)])
    findings = md.detect_iban_change_without_4eyes([ev], invoices)
    assert len(findings) == 1
    assert findings[0].rule_id == "MD_IBAN_NO_4EYES"


def test_iban_change_no_subsequent_invoice_emits_vendor_level_high():
    when = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
    ev = _make_event("V001", MasterDataField.IBAN, when, approved_by=None)
    invoices = pd.DataFrame(
        [_invoice_row("INV1", "V001", when - timedelta(days=10), 1_000.0)]  # avant le changement
    )
    findings = md.detect_iban_change_without_4eyes([ev], invoices)
    assert len(findings) == 1
    assert findings[0].invoice_id.startswith("VENDOR::")
    assert findings[0].severity == Severity.HIGH


def test_dormant_reactivation_detects_long_gap():
    last_old = datetime(2024, 1, 15, tzinfo=UTC)
    swap = datetime(2025, 6, 1, tzinfo=UTC)  # > 180 jours
    new_invoice = swap + timedelta(days=10)
    ev = _make_event("V001", MasterDataField.IBAN, swap, approved_by="U002", changed_by="U001")
    invoices = pd.DataFrame(
        [
            _invoice_row("INV_OLD", "V001", last_old, 4_000.0),
            _invoice_row("INV_NEW", "V001", new_invoice, 25_000.0),
        ]
    )
    findings = md.detect_dormant_reactivation([ev], invoices, dormant_days=180)
    assert len(findings) == 1
    assert findings[0].invoice_id == "INV_NEW"
    assert findings[0].severity == Severity.CRITICAL
    assert findings[0].evidence["dormant_days"] >= 180


def test_dormant_reactivation_short_gap_does_not_trigger():
    last_old = datetime(2025, 5, 15, tzinfo=UTC)
    swap = datetime(2025, 6, 1, tzinfo=UTC)  # 17 jours
    new_invoice = swap + timedelta(days=5)
    ev = _make_event("V001", MasterDataField.IBAN, swap)
    invoices = pd.DataFrame(
        [
            _invoice_row("INV_OLD", "V001", last_old, 4_000.0),
            _invoice_row("INV_NEW", "V001", new_invoice, 25_000.0),
        ]
    )
    findings = md.detect_dormant_reactivation([ev], invoices, dormant_days=180)
    assert findings == []


def test_name_and_iban_same_day():
    base = datetime(2025, 6, 1, 9, 0, tzinfo=UTC)
    iban_ev = _make_event("V001", MasterDataField.IBAN, base)
    name_ev = _make_event("V001", MasterDataField.NAME, base + timedelta(hours=2))
    invoices = pd.DataFrame([_invoice_row("INV1", "V001", base + timedelta(days=3), 7_500.0)])
    findings = md.detect_name_and_iban_same_day([iban_ev, name_ev], invoices)
    assert len(findings) == 1
    assert findings[0].rule_id == "MD_NAME_AND_IBAN_SAME_DAY"
    assert findings[0].severity == Severity.CRITICAL


def test_run_all_dedupes_overlapping_findings():
    base = datetime(2025, 6, 1, 9, 0, tzinfo=UTC)
    # IBAN swap sans 4-eyes ET clone vendor même jour
    iban_ev = _make_event("V001", MasterDataField.IBAN, base, approved_by=None)
    name_ev = _make_event("V001", MasterDataField.NAME, base + timedelta(hours=1))
    invoices = pd.DataFrame([_invoice_row("INV1", "V001", base + timedelta(days=3), 7_500.0)])
    findings = md.run_all([iban_ev, name_ev], invoices)
    rule_ids = {f.rule_id for f in findings}
    assert "MD_IBAN_NO_4EYES" in rule_ids
    assert "MD_NAME_AND_IBAN_SAME_DAY" in rule_ids


def test_empty_inputs_return_empty():
    assert md.run_all([], pd.DataFrame()) == []


# --- Test d'intégration sur dataset synthétique étiqueté ---


def test_recall_on_synthetic_bec_iban_swaps():
    cfg = GeneratorConfig(n_invoices=2_000, n_vendors=200, seed=2026)
    invoices, vendors = generate_dataset(cfg)
    invoices = attach_vendor_ids(invoices, vendors)
    events = generate_master_data_events(
        invoices,
        vendors,
        MasterDataEventsConfig(
            n_bec_swaps=20,
            n_dormant_reactivations=5,
            n_name_iban_same_day=5,
            n_legitimate_changes=50,
            seed=2026,
        ),
    )
    bec_swaps = events[events["fraud_type"] == "bec_iban_swap"]
    assert len(bec_swaps) > 0

    pydantic_events = [
        VendorMasterEvent(
            event_id=row["event_id"],
            vendor_id=row["vendor_id"],
            field=row["field"],
            old_value=row.get("old_value"),
            new_value=row.get("new_value"),
            changed_at=pd.Timestamp(row["changed_at"]).to_pydatetime(),
            changed_by=row.get("changed_by"),
            approved_by=row.get("approved_by") if pd.notna(row.get("approved_by")) else None,
            source=row.get("source", "erp"),
        )
        for _, row in events.iterrows()
    ]
    findings = md.detect_iban_change_without_4eyes(pydantic_events, invoices)
    detected_vendor_ids = {f.evidence["vendor_id"] for f in findings}
    expected_vendor_ids = set(bec_swaps["vendor_id"].tolist())
    recall = len(detected_vendor_ids & expected_vendor_ids) / max(1, len(expected_vendor_ids))
    assert recall >= 0.95, f"Recall BEC swaps insuffisant : {recall:.2f}"
