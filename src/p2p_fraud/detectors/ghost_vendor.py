"""Détecteur 09 — Ghost vendor (fournisseur fantôme).

Un « ghost vendor » est une fiche fournisseur créée dans le seul but de
recevoir des paiements : création récente suivie d'une première facture
rapide, absence de bon de commande, fiche créée et approuvée par le même
utilisateur, identifiant SIREN absent ou invalide. Chaque signal isolé est
faible — c'est le *faisceau* qui fait le fantôme (ACFE Fraud Tree,
Billing schemes → Shell company ; ISA 240 ; Sapin 2 art. 17).

Signaux (rule_ids) :
- ``GV_FAST_FIRST_INVOICE`` — 1re facture < N jours après création de la fiche (HIGH)
- ``GV_SELF_APPROVED``      — fiche créée sans approbateur distinct (HIGH)
- ``GV_NO_PO``              — factures sans bon de commande au-dessus d'un seuil (MEDIUM)
- ``GV_NO_SIREN``           — SIREN absent ou invalide sur toutes les factures (MEDIUM)
- ``GV_COMBO``              — ≥ `combo_min_signals` signaux distincts sur le même
  fournisseur → synthèse CRITICAL (c'est le finding « ghost vendor » à proprement parler).

Conception :
- calcul local pur (pandas), aucun appel réseau — même doctrine que
  ``master_data_changes`` ;
- la clé fournisseur est ``vendor_id`` si la colonne existe, sinon ``siren``,
  sinon ``vendor_name`` — le détecteur reste utilisable sur un export AP minimal.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from p2p_fraud.schema import Finding, Severity, Vendor, VendorMasterEvent

DEFAULT_FAST_INVOICE_DAYS = 30
DEFAULT_NO_PO_MIN_AMOUNT = 10_000.0
DEFAULT_COMBO_MIN_SIGNALS = 3

_DETECTOR = "ghost_vendor"


def _new_finding(
    invoice_id: str,
    rule_id: str,
    signal: str,
    severity: Severity,
    evidence: dict,
) -> Finding:
    return Finding(
        invoice_id=invoice_id,
        detector=_DETECTOR,
        signal=signal,
        severity=severity,
        rule_id=rule_id,
        evidence=evidence,
    )


def _valid_siren(value: object) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    digits = "".join(c for c in str(value) if c.isdigit())
    return len(digits) == 9


def _vendor_key_series(invoices: pd.DataFrame) -> pd.Series:
    """Clé fournisseur canonique : vendor_id > siren > vendor_name."""
    if "vendor_id" in invoices.columns:
        key = invoices["vendor_id"].astype("string")
    else:
        key = pd.Series(pd.NA, index=invoices.index, dtype="string")
    if "siren" in invoices.columns:
        key = key.fillna(invoices["siren"].astype("string"))
    key = key.fillna(invoices["vendor_name"].astype("string"))
    return key


def _earliest_events(events: Iterable[VendorMasterEvent]) -> dict[str, VendorMasterEvent]:
    """Premier événement master data par vendor_id — considéré comme la création de fiche."""
    first: dict[str, VendorMasterEvent] = {}
    for ev in events:
        cur = first.get(ev.vendor_id)
        if cur is None or ev.changed_at < cur.changed_at:
            first[ev.vendor_id] = ev
    return first


def detect_ghost_vendors(
    invoices: pd.DataFrame,
    vendors: Iterable[Vendor] | None = None,
    events: Iterable[VendorMasterEvent] | None = None,
    *,
    fast_invoice_days: int = DEFAULT_FAST_INVOICE_DAYS,
    no_po_min_amount: float = DEFAULT_NO_PO_MIN_AMOUNT,
    combo_min_signals: int = DEFAULT_COMBO_MIN_SIGNALS,
) -> list[Finding]:
    """Détecte les fournisseurs fantômes par faisceau de signaux.

    Args:
        invoices: table AP canonique (invoice_id, vendor_name, amount,
            invoice_date ; colonnes optionnelles vendor_id, siren, po_number).
        vendors: référentiel fournisseurs (``creation_date`` alimente le signal
            « première facture rapide », joint par SIREN).
        events: événements master data — le premier événement d'un vendor_id
            vaut création de fiche (signal « self-approved »).
    """
    if invoices.empty:
        return []

    df = invoices.copy()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], utc=True, errors="coerce")
    df["_vendor_key"] = _vendor_key_series(df)

    creation_by_siren: dict[str, pd.Timestamp] = {}
    for v in vendors or []:
        if v.creation_date is not None:
            creation_by_siren[v.siren] = pd.Timestamp(v.creation_date, tz="UTC")

    first_event = _earliest_events(events or [])

    findings: list[Finding] = []
    signals_by_vendor: dict[str, set[str]] = {}
    exposure_by_vendor: dict[str, float] = {}
    meta_by_vendor: dict[str, dict] = {}

    for key, group in df.groupby("_vendor_key"):
        group = group.sort_values("invoice_date")
        first_row = group.iloc[0]
        vendor_name = str(first_row.get("vendor_name", key))
        siren_raw = first_row.get("siren")
        siren = str(siren_raw) if _valid_siren(siren_raw) else None
        exposure = float(group["amount"].sum())
        first_invoice_id = str(first_row["invoice_id"])
        vendor_signals = signals_by_vendor.setdefault(str(key), set())
        exposure_by_vendor[str(key)] = exposure
        meta_by_vendor[str(key)] = {
            "vendor_name": vendor_name,
            "siren": siren,
            "first_invoice_id": first_invoice_id,
        }

        # ── GV_NO_SIREN — aucun SIREN valide sur l'ensemble des factures ──
        if "siren" not in group.columns or not group["siren"].map(_valid_siren).any():
            vendor_signals.add("GV_NO_SIREN")
            findings.append(
                _new_finding(
                    first_invoice_id,
                    "GV_NO_SIREN",
                    "Fournisseur sans SIREN vérifiable",
                    Severity.MEDIUM,
                    {
                        "vendor_name": vendor_name,
                        "siren": None,
                        "n_invoices": len(group),
                        "exposure_eur": exposure,
                        "reason": "Aucun identifiant SIREN valide — cross-check Sirene impossible.",
                    },
                )
            )

        # ── GV_NO_PO — factures sans bon de commande au-dessus du seuil ──
        if "po_number" in group.columns:
            no_po = group[
                group["po_number"].isna() | (group["po_number"].astype("string").str.strip() == "")
            ]
            no_po = no_po[no_po["amount"] >= no_po_min_amount]
        else:
            no_po = group[group["amount"] >= no_po_min_amount]
        if not no_po.empty:
            no_po_exposure = float(no_po["amount"].sum())
            vendor_signals.add("GV_NO_PO")
            findings.append(
                _new_finding(
                    str(no_po.iloc[0]["invoice_id"]),
                    "GV_NO_PO",
                    "Factures sans bon de commande",
                    Severity.MEDIUM,
                    {
                        "vendor_name": vendor_name,
                        "siren": siren,
                        "n_invoices": len(no_po),
                        "exposure_eur": no_po_exposure,
                        "reason": (
                            f"{len(no_po)} facture(s) ≥ {no_po_min_amount:,.0f} € sans PO rattaché."
                        ),
                    },
                )
            )

        # ── GV_FAST_FIRST_INVOICE — fiche jeune facturant immédiatement ──
        created_at = creation_by_siren.get(siren or "")
        if created_at is None and str(key) in first_event:
            created_at = pd.Timestamp(first_event[str(key)].changed_at)
        first_invoice_date = first_row["invoice_date"]
        if created_at is not None and pd.notna(first_invoice_date):
            age_days = (first_invoice_date - created_at).days
            if 0 <= age_days <= fast_invoice_days:
                vendor_signals.add("GV_FAST_FIRST_INVOICE")
                findings.append(
                    _new_finding(
                        first_invoice_id,
                        "GV_FAST_FIRST_INVOICE",
                        "Première facture immédiate après création",
                        Severity.HIGH,
                        {
                            "vendor_name": vendor_name,
                            "siren": siren,
                            "age_days": int(age_days),
                            "exposure_eur": exposure,
                            "reason": (
                                f"Première facture {age_days} j après la création de la fiche "
                                f"(seuil {fast_invoice_days} j)."
                            ),
                        },
                    )
                )

        # ── GV_SELF_APPROVED — fiche créée sans approbateur distinct ──
        ev = first_event.get(str(key))
        if ev is not None:
            no_approver = ev.approved_by in (None, "")
            same_user = (not no_approver) and ev.approved_by == ev.changed_by
            if no_approver or same_user:
                vendor_signals.add("GV_SELF_APPROVED")
                findings.append(
                    _new_finding(
                        first_invoice_id,
                        "GV_SELF_APPROVED",
                        "Fiche créée sans validation 4-eyes",
                        Severity.HIGH,
                        {
                            "vendor_name": vendor_name,
                            "siren": siren,
                            "changed_by": ev.changed_by,
                            "approved_by": ev.approved_by,
                            "exposure_eur": exposure,
                            "reason": (
                                "Créateur et approbateur identiques"
                                if same_user
                                else "Aucun approbateur sur la création de fiche"
                            ),
                        },
                    )
                )

    # ── GV_COMBO — synthèse : faisceau ghost vendor ──
    for key, signals in signals_by_vendor.items():
        if len(signals) < combo_min_signals:
            continue
        meta = meta_by_vendor[key]
        findings.append(
            _new_finding(
                meta["first_invoice_id"],
                "GV_COMBO",
                "Faisceau ghost vendor",
                Severity.CRITICAL,
                {
                    "vendor_name": meta["vendor_name"],
                    "siren": meta["siren"],
                    "signals": sorted(signals),
                    "n_signals": len(signals),
                    "exposure_eur": exposure_by_vendor[key],
                    "reason": (
                        f"{len(signals)} signaux ghost vendor cumulés : "
                        + ", ".join(sorted(signals))
                    ),
                },
            )
        )

    return findings
