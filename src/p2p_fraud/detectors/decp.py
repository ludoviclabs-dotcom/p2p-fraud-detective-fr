"""Détecteur DECP / RBE — croisement fournisseurs P2P × marchés publics × bénéficiaires effectifs.

Règles :
- `RBE_BENEFICIAL_OWNER_MATCH` : le bénéficiaire effectif du fournisseur correspond à
  une personne référencée dans les listes PEP ou sanctions. Severity CRITICAL.
- `DECP_VENDOR_IN_PUBLIC_MARKET` : le fournisseur est titulaire d'un marché public
  auprès de l'acheteur audité (risque conflit d'intérêts, Sapin 2 art. 17). Severity HIGH.
- `RBE_OPAQUE_STRUCTURE` : la structure de propriété du fournisseur est opaque
  (bénéficiaire effectif non renseigné ou nationalité haute risque). Severity HIGH.

Conformité : Sapin 2 art. 17, AMLD6 art. 30, Directive Marchés Publics 2014/24/UE.
"""

from __future__ import annotations

import logging

import pandas as pd

from p2p_fraud.enrichment.decp_client import DECPClient
from p2p_fraud.enrichment.rbe_client import RBEClient
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
        detector="decp_rbe",
        signal=signal,
        severity=severity,
        rule_id=rule_id,
        evidence=evidence,
    )


def detect_decp_rbe(
    invoices: pd.DataFrame,
    *,
    decp_client: DECPClient | None = None,
    rbe_client: RBEClient | None = None,
    min_name_score: int = 80,
) -> list[Finding]:
    """Croise les fournisseurs de `invoices` avec DECP et RBE.

    Args:
        invoices: DataFrame avec colonnes vendor_name, siren (optionnel), invoice_id, amount.
        decp_client: client DECP (démo par défaut).
        rbe_client: client RBE (démo par défaut).
        min_name_score: score minimal RapidFuzz pour le matching nom (défaut 80).

    Returns:
        Liste de Findings — un par facture pour les fournisseurs flagués.
    """
    if decp_client is None:
        decp_client = DECPClient(demo_mode=True)
    if rbe_client is None:
        rbe_client = RBEClient(demo_mode=True)

    required = {"vendor_name", "invoice_id"}
    missing = required - set(invoices.columns)
    if missing:
        log.warning("DECP detector: colonnes manquantes %s — pas de findings", missing)
        return []

    findings: list[Finding] = []

    vendor_names = invoices["vendor_name"].dropna().unique().tolist()
    has_siren = "siren" in invoices.columns

    for vendor_name in vendor_names:
        vendor_mask = invoices["vendor_name"] == vendor_name
        vendor_invoices = invoices[vendor_mask]
        vendor_rows = invoices[vendor_mask]
        exposure = float(vendor_rows["amount"].sum()) if "amount" in vendor_rows.columns else 0.0

        siren = None
        if has_siren:
            sirens = vendor_invoices["siren"].dropna().unique()
            if len(sirens) > 0:
                siren = str(sirens[0]).strip()[:9]

        for inv_row in vendor_rows.itertuples(index=False):
            invoice_id = str(getattr(inv_row, "invoice_id", "?"))
            amount = float(getattr(inv_row, "amount", 0) or 0)

            decp_contracts = (
                decp_client.lookup_by_siren(siren)
                if siren
                else decp_client.lookup_by_name(vendor_name, min_score=min_name_score)
            )

            if decp_contracts:
                for contract in decp_contracts[:3]:
                    findings.append(
                        _emit(
                            invoice_id=invoice_id,
                            severity=Severity.HIGH,
                            rule_id="DECP_VENDOR_IN_PUBLIC_MARKET",
                            signal=f"Fournisseur titulaire de marché public : {contract.acheteur}",
                            evidence={
                                "vendor_name": vendor_name,
                                "siren": siren or contract.siren,
                                "acheteur": contract.acheteur,
                                "objet_marche": contract.objet,
                                "montant_marche_eur": contract.montant_eur,
                                "date_notification": contract.date_notification,
                                "exposure_eur": round(exposure, 2),
                                "amount_eur": amount,
                                "reason": (
                                    f"Conflit d'intérêts potentiel (Sapin 2 art. 17) : "
                                    f"{vendor_name} est titulaire d'un marché public "
                                    f"auprès de '{contract.acheteur}'."
                                ),
                            },
                        )
                    )
                break  # une seule alerte DECP par fournisseur pour limiter le bruit

            if siren:
                if rbe_client.is_opaque_structure(siren):
                    findings.append(
                        _emit(
                            invoice_id=invoice_id,
                            severity=Severity.HIGH,
                            rule_id="RBE_OPAQUE_STRUCTURE",
                            signal="Structure de propriété opaque (bénéficiaire effectif non identifié)",
                            evidence={
                                "vendor_name": vendor_name,
                                "siren": siren,
                                "exposure_eur": round(exposure, 2),
                                "amount_eur": amount,
                                "reason": (
                                    f"Bénéficiaire effectif non renseigné ou nationalité haute risque "
                                    f"pour {vendor_name} (SIREN {siren}). "
                                    "Diligence renforcée requise (AMLD6 art. 30 / Sapin 2 art. 17)."
                                ),
                            },
                        )
                    )
                    break

                if rbe_client.has_pep_beneficial_owner(siren):
                    owners = rbe_client.lookup_by_siren(siren)
                    pep_names = [
                        f"{o.owner_first_name} {o.owner_last_name}" for o in owners if o.is_pep
                    ]
                    findings.append(
                        _emit(
                            invoice_id=invoice_id,
                            severity=Severity.CRITICAL,
                            rule_id="RBE_BENEFICIAL_OWNER_MATCH",
                            signal=f"Bénéficiaire effectif PEP : {', '.join(pep_names)}",
                            evidence={
                                "vendor_name": vendor_name,
                                "siren": siren,
                                "pep_owners": pep_names,
                                "exposure_eur": round(exposure, 2),
                                "amount_eur": amount,
                                "reason": (
                                    f"Le fournisseur {vendor_name} a un bénéficiaire effectif "
                                    f"PEP ({', '.join(pep_names)}). "
                                    "Blocage recommandé (LCB-FT / Sapin 2 art. 17)."
                                ),
                            },
                        )
                    )
                    break

    return findings
