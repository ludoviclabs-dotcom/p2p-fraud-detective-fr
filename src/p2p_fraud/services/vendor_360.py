"""Vue 360° fournisseur — agrège profil, paiements, master data, findings, sanctions.

Ce service ne fait pas d'appel réseau. Il consolide les données disponibles en
session (DataFrames d'invoices, vendors, master events, findings) en un objet
unique consommable par la page Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from p2p_fraud.schema import Finding


@dataclass
class VendorSummary:
    vendor_id: str
    vendor_name: str | None = None
    siren: str | None = None
    address: str | None = None
    ape_code: str | None = None
    creation_date: datetime | None = None
    is_active: bool | None = None
    iban_history: list[dict] = field(default_factory=list)
    name_history: list[dict] = field(default_factory=list)
    invoices: pd.DataFrame = field(default_factory=pd.DataFrame)
    total_paid_eur: float = 0.0
    n_invoices: int = 0
    findings: list[Finding] = field(default_factory=list)
    is_sanctioned: bool = False
    is_pep: bool = False

    @property
    def has_alerts(self) -> bool:
        return bool(self.findings) or self.is_sanctioned or self.is_pep


def _filter_invoices(invoices: pd.DataFrame, vendor_id: str) -> pd.DataFrame:
    if invoices is None or invoices.empty:
        return pd.DataFrame()
    if "vendor_id" in invoices.columns:
        return invoices.loc[invoices["vendor_id"] == vendor_id].copy()
    return pd.DataFrame()


def _filter_events(events: pd.DataFrame, vendor_id: str, field: str) -> list[dict]:
    if events is None or events.empty or "vendor_id" not in events.columns:
        return []
    sub = events.loc[
        (events["vendor_id"] == vendor_id) & (events["field"] == field)
    ].copy()
    if sub.empty:
        return []
    return [
        {
            "event_id": row.get("event_id"),
            "old_value": row.get("old_value"),
            "new_value": row.get("new_value"),
            "changed_at": row.get("changed_at"),
            "changed_by": row.get("changed_by"),
            "approved_by": row.get("approved_by"),
            "source": row.get("source"),
        }
        for row in sub.to_dict("records")
    ]


def _filter_findings(findings: list[Finding], vendor_id: str) -> list[Finding]:
    out: list[Finding] = []
    for f in findings or []:
        ev = f.evidence or {}
        if ev.get("vendor_id") == vendor_id or f.invoice_id == f"VENDOR::{vendor_id}":
            out.append(f)
    return out


def get_vendor_summary(
    vendor_id: str,
    *,
    invoices: pd.DataFrame | None = None,
    vendors: pd.DataFrame | None = None,
    master_events: pd.DataFrame | None = None,
    findings: list[Finding] | None = None,
) -> VendorSummary:
    """Construit la vue 360° d'un fournisseur à partir des sources en session."""
    summary = VendorSummary(vendor_id=vendor_id)

    if vendors is not None and not vendors.empty and "vendor_id" in vendors.columns:
        match = vendors.loc[vendors["vendor_id"] == vendor_id]
        if not match.empty:
            row = match.iloc[0].to_dict()
            summary.vendor_name = row.get("vendor_name")
            summary.siren = row.get("siren")
            summary.address = row.get("address")
            summary.ape_code = row.get("ape_code")
            summary.creation_date = row.get("creation_date")
            summary.is_active = row.get("is_active")

    if invoices is not None:
        sub = _filter_invoices(invoices, vendor_id)
        summary.invoices = sub
        summary.n_invoices = len(sub)
        if not sub.empty and "amount" in sub.columns:
            summary.total_paid_eur = float(sub["amount"].sum())
            if summary.vendor_name is None and "vendor_name" in sub.columns:
                summary.vendor_name = sub["vendor_name"].iloc[0]

    if master_events is not None:
        summary.iban_history = _filter_events(master_events, vendor_id, "iban")
        summary.name_history = _filter_events(master_events, vendor_id, "name")

    findings_filtered = _filter_findings(findings or [], vendor_id)
    summary.findings = findings_filtered
    summary.is_sanctioned = any(
        f.rule_id == "SANCTIONS_VENDOR_HIT" for f in findings_filtered
    )
    summary.is_pep = any(f.rule_id == "SANCTIONS_VENDOR_PEP" for f in findings_filtered)

    return summary
