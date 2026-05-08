"""Tests vendor 360° — Sprint 5."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from p2p_fraud.schema import Finding, Severity
from p2p_fraud.services.vendor_360 import get_vendor_summary


def _make_invoices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "invoice_id": "INV1",
                "vendor_id": "V001",
                "vendor_name": "Acme SARL",
                "amount": 5_000.0,
                "invoice_date": "2025-06-01",
            },
            {
                "invoice_id": "INV2",
                "vendor_id": "V001",
                "vendor_name": "Acme SARL",
                "amount": 7_500.0,
                "invoice_date": "2025-06-15",
            },
            {
                "invoice_id": "INV3",
                "vendor_id": "V002",
                "vendor_name": "Other SAS",
                "amount": 1_000.0,
                "invoice_date": "2025-06-10",
            },
        ]
    )


def _make_vendors() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "vendor_id": "V001",
                "vendor_name": "Acme SARL",
                "siren": "123456789",
                "address": "1 rue de la Paix, Paris",
                "ape_code": "6201Z",
                "creation_date": "2010-01-15",
                "is_active": True,
            },
            {
                "vendor_id": "V002",
                "vendor_name": "Other SAS",
                "siren": "987654321",
                "address": "5 avenue Foch, Lyon",
                "ape_code": "4669A",
                "creation_date": "2018-09-01",
                "is_active": True,
            },
        ]
    )


def _make_master_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "E1",
                "vendor_id": "V001",
                "field": "iban",
                "old_value": "FR76OLD",
                "new_value": "FR76NEW",
                "changed_at": datetime(2025, 5, 30, tzinfo=UTC),
                "changed_by": "U001",
                "approved_by": None,
                "source": "manual",
            },
            {
                "event_id": "E2",
                "vendor_id": "V001",
                "field": "name",
                "old_value": "Acme SARL",
                "new_value": "Acme Holdings SARL",
                "changed_at": datetime(2025, 5, 30, 1, tzinfo=UTC),
                "changed_by": "U001",
                "approved_by": "U002",
                "source": "manual",
            },
            {
                "event_id": "E3",
                "vendor_id": "V002",
                "field": "iban",
                "old_value": "FR76A",
                "new_value": "FR76B",
                "changed_at": datetime(2025, 1, 1, tzinfo=UTC),
                "changed_by": "U003",
                "approved_by": "U004",
                "source": "erp",
            },
        ]
    )


def _make_findings() -> list[Finding]:
    return [
        Finding(
            invoice_id="INV1",
            detector="master_data",
            signal="iban_change_without_4eyes",
            severity=Severity.CRITICAL,
            rule_id="MD_IBAN_NO_4EYES",
            evidence={"vendor_id": "V001", "exposure_eur": 12_500.0},
        ),
        Finding(
            invoice_id="INV1",
            detector="sanctions",
            signal="vendor_pep",
            severity=Severity.HIGH,
            rule_id="SANCTIONS_VENDOR_PEP",
            evidence={"vendor_id": "V001", "matched_name": "Some PEP"},
        ),
        Finding(
            invoice_id="INV3",
            detector="duplicates",
            signal="duplicate_exact",
            severity=Severity.HIGH,
            rule_id="DUP_EXACT",
            evidence={"vendor_id": "V002"},
        ),
    ]


def test_summary_aggregates_invoices_and_payments():
    summary = get_vendor_summary(
        "V001",
        invoices=_make_invoices(),
        vendors=_make_vendors(),
    )
    assert summary.vendor_name == "Acme SARL"
    assert summary.siren == "123456789"
    assert summary.n_invoices == 2
    assert summary.total_paid_eur == 12_500.0


def test_summary_filters_master_events_per_vendor():
    summary = get_vendor_summary(
        "V001",
        invoices=_make_invoices(),
        vendors=_make_vendors(),
        master_events=_make_master_events(),
    )
    assert len(summary.iban_history) == 1
    assert len(summary.name_history) == 1
    assert summary.iban_history[0]["new_value"] == "FR76NEW"


def test_summary_picks_only_v001_findings():
    summary = get_vendor_summary(
        "V001",
        invoices=_make_invoices(),
        vendors=_make_vendors(),
        findings=_make_findings(),
    )
    assert len(summary.findings) == 2
    assert all(f.evidence["vendor_id"] == "V001" for f in summary.findings)
    assert summary.is_pep is True
    assert summary.is_sanctioned is False


def test_summary_unknown_vendor_returns_empty_summary():
    summary = get_vendor_summary(
        "V_UNKNOWN",
        invoices=_make_invoices(),
        vendors=_make_vendors(),
    )
    assert summary.vendor_id == "V_UNKNOWN"
    assert summary.n_invoices == 0
    assert summary.findings == []
    assert summary.has_alerts is False


def test_has_alerts_is_true_when_findings_present():
    summary = get_vendor_summary(
        "V002",
        invoices=_make_invoices(),
        vendors=_make_vendors(),
        findings=_make_findings(),
    )
    assert summary.has_alerts is True
    assert len(summary.findings) == 1
