"""Détecteur sanctions / PEP — produit des findings par fournisseur sanctionné.

Règles :
- `SANCTIONS_VENDOR_HIT` : raison sociale fournisseur match une liste OFAC,
  EU consolidée ou Trésor FR. Severity CRITICAL (réglementaire LCB-FT).
- `SANCTIONS_VENDOR_PEP` : raison sociale fournisseur match une liste PEP.
  Severity HIGH (vigilance renforcée Sapin 2 / LCB-FT).

L'`exposure_eur` reportée correspond au total payé au fournisseur dans la
période ingérée. Les findings sont émis par facture pour rester compatibles
avec le risk_engine et le case management.
"""

from __future__ import annotations

import logging

import pandas as pd

from p2p_fraud.enrichment.sanctions_client import SanctionMatch, SanctionsClient
from p2p_fraud.schema import Finding, Severity

log = logging.getLogger(__name__)


def _emit(
    invoice_id: str,
    severity: Severity,
    rule_id: str,
    signal: str,
    evidence: dict,
) -> Finding:
    return Finding(
        invoice_id=invoice_id,
        detector="sanctions",
        signal=signal,
        severity=severity,
        rule_id=rule_id,
        evidence=evidence,
    )


def detect_sanctioned_vendors(
    invoices: pd.DataFrame,
    *,
    client: SanctionsClient | None = None,
) -> list[Finding]:
    """Évalue chaque fournisseur unique du DataFrame contre le snapshot sanctions.

    Hypothèses :
    - `invoices` contient au minimum `invoice_id`, `vendor_name`, `amount`.
    - Un fournisseur match une seule fois ; on émet ensuite un finding par facture.
    """
    if invoices.empty or "vendor_name" not in invoices.columns:
        return []

    client = client or SanctionsClient()
    if client.n_records == 0:
        log.info("Snapshot sanctions vide — détection sautée.")
        return []

    findings: list[Finding] = []
    by_vendor = invoices.groupby("vendor_name", dropna=True)

    for vendor_name, group in by_vendor:
        if not isinstance(vendor_name, str) or not vendor_name.strip():
            continue
        matches = client.search(vendor_name)
        if not matches:
            continue
        # On garde le meilleur match par catégorie (sanction vs PEP)
        best_sanction: SanctionMatch | None = next((m for m in matches if m.is_sanction), None)
        best_pep: SanctionMatch | None = next((m for m in matches if m.is_pep), None)

        exposure = float(group["amount"].sum())
        invoice_ids = group["invoice_id"].astype(str).tolist()

        for match, severity, rule, signal in (
            (best_sanction, Severity.CRITICAL, "SANCTIONS_VENDOR_HIT", "vendor_sanctioned"),
            (best_pep, Severity.HIGH, "SANCTIONS_VENDOR_PEP", "vendor_pep"),
        ):
            if match is None:
                continue
            evidence = {
                "vendor_name": vendor_name,
                "matched_name": match.name,
                "entity_id": match.entity_id,
                "list_source": match.list_source,
                "score": match.score,
                "country": match.country,
                "listed_at": match.listed_at.isoformat() if match.listed_at else None,
                "reason": match.reason,
                "exposure_eur": round(exposure, 2),
                "n_invoices": len(invoice_ids),
            }
            for invoice_id in invoice_ids:
                findings.append(_emit(invoice_id, severity, rule, signal, evidence))

    return findings
