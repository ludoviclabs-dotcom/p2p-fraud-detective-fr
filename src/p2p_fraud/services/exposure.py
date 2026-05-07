"""Calcul d'exposition financière par finding, fournisseur, et cockpit synthèse.

Conventions :
- L'exposition d'un finding est *prioritairement* celle indiquée dans son
  evidence (`evidence.exposure_eur`) — c'est le calcul fait par le détecteur
  qui a le plus de contexte.
- Sinon, l'exposition est dérivée du montant facture si on dispose du
  DataFrame d'invoices.
- L'exposition par fournisseur est la somme des max d'exposition par règle
  (pour éviter la double-comptabilisation quand 3 règles flaguent la même
  facture pour le même fournisseur).
- Le cockpit produit des KPIs *significatifs pour un CFO* : € évités, top 10
  fournisseurs, % SLA respecté, alerte critiques non assignées.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd

from p2p_fraud.cases.models import Case, CaseStatus
from p2p_fraud.schema import Finding


def compute_finding_exposure(
    finding: Finding,
    invoices: pd.DataFrame | None = None,
) -> float:
    """Calcule l'exposition d'un finding (€). Priorité à l'evidence.

    Si l'evidence contient `exposure_eur` non nul, on l'utilise tel quel.
    Sinon, on tente une dérivation depuis le DataFrame d'invoices.
    """
    ev = finding.evidence or {}
    raw = ev.get("exposure_eur")
    if raw is not None:
        try:
            return float(raw)
        except (TypeError, ValueError):
            pass

    if invoices is None or invoices.empty:
        return 0.0

    if finding.invoice_id.startswith("VENDOR::"):
        vendor_id = finding.invoice_id.split("::", 1)[1]
        if "vendor_id" in invoices.columns:
            subset = invoices.loc[invoices["vendor_id"] == vendor_id]
            return float(subset["amount"].sum()) if not subset.empty else 0.0
        return 0.0

    if "invoice_id" in invoices.columns:
        match = invoices.loc[invoices["invoice_id"].astype(str) == str(finding.invoice_id)]
        if not match.empty and "amount" in match.columns:
            return float(match["amount"].iloc[0])
    return 0.0


@dataclass(frozen=True)
class VendorExposure:
    vendor_id: str | None
    vendor_name: str | None
    n_findings: int
    n_critical: int
    exposure_eur: float
    rules: list[str]


def aggregate_exposure_by_vendor(
    findings: Iterable[Finding],
    invoices: pd.DataFrame | None = None,
) -> list[VendorExposure]:
    """Groupe les findings par fournisseur et somme l'exposition (déduplique par règle)."""
    by_vendor: dict[tuple[str | None, str | None], dict] = {}

    for f in findings:
        ev = f.evidence or {}
        vendor_id = ev.get("vendor_id")
        vendor_name = ev.get("vendor_name")
        # Si on n'a pas de vendor_id, on retombe sur l'invoice → vendor_name
        if (
            vendor_id is None
            and invoices is not None
            and not invoices.empty
            and "invoice_id" in invoices.columns
            and not f.invoice_id.startswith("VENDOR::")
        ):
            row = invoices.loc[invoices["invoice_id"].astype(str) == str(f.invoice_id)]
            if not row.empty:
                if "vendor_id" in row.columns:
                    vendor_id = row["vendor_id"].iloc[0]
                if "vendor_name" in row.columns and vendor_name is None:
                    vendor_name = row["vendor_name"].iloc[0]

        key = (vendor_id, vendor_name)
        bucket = by_vendor.setdefault(
            key,
            {
                "n_findings": 0,
                "n_critical": 0,
                "exposure_by_rule": {},
                "rules": set(),
            },
        )
        bucket["n_findings"] += 1
        if f.severity.value == "critical":
            bucket["n_critical"] += 1
        bucket["rules"].add(f.rule_id)
        # Garde le max d'exposition par règle pour ce fournisseur (dédup)
        e = compute_finding_exposure(f, invoices)
        prev = bucket["exposure_by_rule"].get(f.rule_id, 0.0)
        if e > prev:
            bucket["exposure_by_rule"][f.rule_id] = e

    out: list[VendorExposure] = []
    for (vid, vname), b in by_vendor.items():
        out.append(
            VendorExposure(
                vendor_id=vid,
                vendor_name=vname,
                n_findings=b["n_findings"],
                n_critical=b["n_critical"],
                exposure_eur=round(sum(b["exposure_by_rule"].values()), 2),
                rules=sorted(b["rules"]),
            )
        )
    return sorted(out, key=lambda v: v.exposure_eur, reverse=True)


@dataclass(frozen=True)
class CockpitSummary:
    n_findings: int
    n_critical: int
    n_high: int
    exposure_eur_total: float
    exposure_eur_critical: float
    n_cases_open: int
    n_cases_overdue: int
    n_cases_unassigned_critical: int
    top_vendors: list[VendorExposure]


def cockpit_summary(
    findings: list[Finding],
    cases: list[Case] | None = None,
    invoices: pd.DataFrame | None = None,
    *,
    top_n: int = 10,
) -> CockpitSummary:
    """Construit le synthèse cockpit attendue par un CFO ou un responsable IC."""
    n_critical = sum(1 for f in findings if f.severity.value == "critical")
    n_high = sum(1 for f in findings if f.severity.value == "high")
    by_vendor = aggregate_exposure_by_vendor(findings, invoices)

    exposure_total = sum(v.exposure_eur for v in by_vendor)
    exposure_critical = sum(v.exposure_eur for v in by_vendor if v.n_critical > 0)

    cases = cases or []
    now = datetime.now(UTC)
    n_open = sum(1 for c in cases if not c.status.is_closed)
    n_overdue = sum(
        1 for c in cases if not c.status.is_closed and c.sla_deadline and c.sla_deadline < now
    )
    n_unassigned_critical = sum(
        1
        for c in cases
        if not c.status.is_closed
        and c.severity == "critical"
        and (c.assignee is None or c.assignee.strip() == "")
    )

    return CockpitSummary(
        n_findings=len(findings),
        n_critical=n_critical,
        n_high=n_high,
        exposure_eur_total=round(exposure_total, 2),
        exposure_eur_critical=round(exposure_critical, 2),
        n_cases_open=n_open,
        n_cases_overdue=n_overdue,
        n_cases_unassigned_critical=n_unassigned_critical,
        top_vendors=by_vendor[:top_n],
    )


def cases_to_dataframe(cases: list[Case]) -> pd.DataFrame:
    """Helper UI : projette une liste de Case en DataFrame triable."""
    if not cases:
        return pd.DataFrame()
    rows = [
        {
            "case_id": c.case_id,
            "status": c.status.value,
            "severity": c.severity,
            "vendor_id": c.vendor_id,
            "exposure_eur": c.exposure_eur,
            "assignee": c.assignee,
            "title": c.title,
            "created_at": c.created_at,
            "sla_deadline": c.sla_deadline,
            "closed_at": c.closed_at,
            "closure_reason": c.closure_reason,
            "is_closed": c.status.is_closed,
            "is_overdue": (
                not c.status.is_closed
                and c.sla_deadline is not None
                and c.sla_deadline < datetime.now(UTC)
            ),
        }
        for c in cases
    ]
    df = pd.DataFrame(rows)
    return df.sort_values("exposure_eur", ascending=False, na_position="last")


# Alias pour exposer un seul nom de classe public
__all__ = [
    "CockpitSummary",
    "VendorExposure",
    "aggregate_exposure_by_vendor",
    "cases_to_dataframe",
    "cockpit_summary",
    "compute_finding_exposure",
]


# Garder CaseStatus visible pour les imports (re-export léger)
_ = CaseStatus
