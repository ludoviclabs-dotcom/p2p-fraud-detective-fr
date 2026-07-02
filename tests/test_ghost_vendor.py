"""Tests détecteur 09 — ghost vendor (fournisseur fantôme)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd

from p2p_fraud.detectors.ghost_vendor import detect_ghost_vendors
from p2p_fraud.schema import MasterDataField, Severity, Vendor, VendorMasterEvent


def _invoice(
    invoice_id: str,
    vendor_id: str,
    when: str,
    amount: float,
    *,
    siren: str | None = None,
    po: str | None = None,
    name: str = "Fournisseur Test",
) -> dict:
    return {
        "invoice_id": invoice_id,
        "vendor_id": vendor_id,
        "vendor_name": name,
        "siren": siren,
        "amount": amount,
        "invoice_date": when,
        "po_number": po,
    }


def _creation_event(
    vendor_id: str,
    when: datetime,
    *,
    changed_by: str = "U100",
    approved_by: str | None = None,
) -> VendorMasterEvent:
    return VendorMasterEvent(
        event_id=f"EV-{vendor_id}-CREATE",
        vendor_id=vendor_id,
        field=MasterDataField.STATUS,
        old_value=None,
        new_value="active",
        changed_at=when,
        changed_by=changed_by,
        approved_by=approved_by,
        source="manual",
    )


def test_ghost_vendor_combo_critical() -> None:
    """Fiche jeune + self-approved + sans PO + sans SIREN → GV_COMBO CRITICAL."""
    created = datetime(2026, 3, 1, tzinfo=UTC)
    invoices = pd.DataFrame(
        [
            _invoice("INV-1", "V-GHOST", "2026-03-08", 63_400.0, siren=None, po=None),
            _invoice("INV-2", "V-GHOST", "2026-03-15", 21_000.0, siren=None, po=None),
        ]
    )
    events = [_creation_event("V-GHOST", created, changed_by="U100", approved_by="U100")]

    findings = detect_ghost_vendors(invoices, events=events)
    rule_ids = {f.rule_id for f in findings}

    assert {"GV_NO_SIREN", "GV_NO_PO", "GV_FAST_FIRST_INVOICE", "GV_SELF_APPROVED"} <= rule_ids
    combo = [f for f in findings if f.rule_id == "GV_COMBO"]
    assert len(combo) == 1
    assert combo[0].severity == Severity.CRITICAL
    assert combo[0].evidence["n_signals"] == 4
    assert combo[0].evidence["exposure_eur"] == 84_400.0


def test_clean_vendor_no_findings() -> None:
    """Fournisseur ancien, SIREN valide, PO présents, montants sous seuil → rien."""
    vendors = [
        Vendor(siren="812446901", name="Aciers Nord-Est SAS", creation_date=date(2020, 1, 15))
    ]
    invoices = pd.DataFrame(
        [
            _invoice(
                "INV-10",
                "V-OK",
                "2026-03-08",
                4_500.0,
                siren="812446901",
                po="PO-1",
                name="Aciers Nord-Est SAS",
            ),
        ]
    )
    findings = detect_ghost_vendors(invoices, vendors=vendors)
    assert findings == []


def test_fast_first_invoice_via_vendor_referential() -> None:
    """La date de création peut venir du référentiel Vendor (jointure SIREN)."""
    vendors = [Vendor(siren="443109887", name="Jeune Société", creation_date=date(2026, 3, 1))]
    invoices = pd.DataFrame(
        [
            _invoice(
                "INV-20",
                "V-NEW",
                "2026-03-10",
                5_000.0,
                siren="443109887",
                po="PO-9",
                name="Jeune Société",
            ),
        ]
    )
    findings = detect_ghost_vendors(invoices, vendors=vendors)
    assert [f.rule_id for f in findings] == ["GV_FAST_FIRST_INVOICE"]
    assert findings[0].severity == Severity.HIGH
    assert findings[0].evidence["age_days"] == 9


def test_no_combo_below_threshold() -> None:
    """Deux signaux seulement → pas de synthèse GV_COMBO."""
    invoices = pd.DataFrame(
        [_invoice("INV-30", "V-2SIG", "2026-03-08", 15_000.0, siren=None, po=None)]
    )
    findings = detect_ghost_vendors(invoices)
    rule_ids = sorted(f.rule_id for f in findings)
    assert rule_ids == ["GV_NO_PO", "GV_NO_SIREN"]


def test_empty_invoices() -> None:
    assert detect_ghost_vendors(pd.DataFrame()) == []
