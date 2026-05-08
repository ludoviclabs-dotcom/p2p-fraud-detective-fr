"""Détecteur master data — changements sensibles sur le référentiel fournisseur.

C'est le P0 absolu du produit (ADR-0001). Les trois scénarios principaux couverts :

1. **IBAN swap sans 4-eyes** — modification d'IBAN par un seul utilisateur, sans
   approbateur distinct. Scénario n°1 BEC (Business Email Compromise) selon
   AFP 2026 Payments Fraud Survey.
2. **Dormant reactivation** — fournisseur inactif depuis > N jours dont l'IBAN
   change puis reçoit un paiement. Vecteur classique de détournement.
3. **Name + IBAN même jour** — clone de fournisseur (typosquatting + nouvel IBAN).

Conception :
- Aucun appel réseau, calcul local pur sur DataFrame d'événements.
- Severity calibrée pour que les trois scénarios sortent en CRITICAL (le score
  consolidé doit les pousser au-dessus de tout autre signal).
- L'`exposure_eur` calculée comme somme des paiements postérieurs dans la
  fenêtre de risque (par défaut 90 jours).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

import pandas as pd

from p2p_fraud.schema import Finding, MasterDataField, Severity, VendorMasterEvent

DEFAULT_DORMANT_DAYS = 180
DEFAULT_EXPOSURE_WINDOW_DAYS = 90
DEFAULT_SAME_DAY_NAME_IBAN_HOURS = 24


def _events_to_df(events: Iterable[VendorMasterEvent]) -> pd.DataFrame:
    rows = [e.model_dump() for e in events]
    if not rows:
        return pd.DataFrame(
            columns=[
                "event_id",
                "vendor_id",
                "field",
                "old_value",
                "new_value",
                "changed_at",
                "changed_by",
                "approved_by",
                "source",
            ]
        )
    df = pd.DataFrame(rows)
    df["changed_at"] = pd.to_datetime(df["changed_at"], utc=True)
    return df.sort_values("changed_at").reset_index(drop=True)


def _exposure_after_event(
    invoices: pd.DataFrame, vendor_id: str, after: datetime, window_days: int
) -> tuple[float, list[str]]:
    """Somme des montants payés au fournisseur dans la fenêtre [after, after+window]."""
    if invoices.empty:
        return 0.0, []
    if "vendor_id" not in invoices.columns:
        # Aligner sur la convention pipeline : si pas de vendor_id, utiliser siren ou vendor_name.
        # Au minimum, on renvoie 0 sans bruit.
        return 0.0, []
    subset = invoices.loc[invoices["vendor_id"] == vendor_id].copy()
    if subset.empty:
        return 0.0, []
    subset["invoice_date"] = pd.to_datetime(subset["invoice_date"], utc=True, errors="coerce")
    after_ts = (
        pd.Timestamp(after).tz_convert("UTC")
        if pd.Timestamp(after).tzinfo
        else pd.Timestamp(after, tz="UTC")
    )
    end_ts = after_ts + pd.Timedelta(days=window_days)
    in_window = subset[(subset["invoice_date"] >= after_ts) & (subset["invoice_date"] <= end_ts)]
    return float(in_window["amount"].sum()), in_window["invoice_id"].astype(str).tolist()


def _new_finding(
    invoice_id: str,
    rule_id: str,
    signal: str,
    severity: Severity,
    evidence: dict,
) -> Finding:
    return Finding(
        invoice_id=invoice_id,
        detector="master_data",
        signal=signal,
        severity=severity,
        rule_id=rule_id,
        evidence=evidence,
    )


def detect_iban_change_without_4eyes(
    events: Iterable[VendorMasterEvent],
    invoices: pd.DataFrame,
    *,
    exposure_window_days: int = DEFAULT_EXPOSURE_WINDOW_DAYS,
) -> list[Finding]:
    """Flag tout changement d'IBAN sans approbateur distinct.

    Si `approved_by` est nul OU égal à `changed_by`, on déclenche un finding
    CRITICAL pour chaque facture payée dans les `exposure_window_days` jours
    suivant le changement.
    """
    df = _events_to_df(events)
    if df.empty:
        return []
    iban_changes = df[df["field"] == MasterDataField.IBAN.value]
    findings: list[Finding] = []

    for _, ev in iban_changes.iterrows():
        no_approver = pd.isna(ev["approved_by"]) or ev["approved_by"] in (None, "")
        same_user = (not no_approver) and ev["approved_by"] == ev["changed_by"]
        if not (no_approver or same_user):
            continue
        exposure, impacted = _exposure_after_event(
            invoices, ev["vendor_id"], ev["changed_at"], exposure_window_days
        )
        evidence_base = {
            "vendor_id": ev["vendor_id"],
            "event_id": ev["event_id"],
            "changed_at": ev["changed_at"].isoformat(),
            "changed_by": ev["changed_by"],
            "approved_by": ev["approved_by"],
            "exposure_eur": round(exposure, 2),
            "exposure_window_days": exposure_window_days,
            "impacted_invoices": impacted[:50],  # cap evidence size
        }
        if not impacted:
            # Pas encore d'impact financier mesurable : on émet un finding
            # technique au niveau "vendor" (invoice_id synthétique).
            findings.append(
                _new_finding(
                    invoice_id=f"VENDOR::{ev['vendor_id']}",
                    rule_id="MD_IBAN_NO_4EYES",
                    signal="iban_change_without_4eyes",
                    severity=Severity.HIGH,
                    evidence=evidence_base,
                )
            )
            continue
        for invoice_id in impacted:
            findings.append(
                _new_finding(
                    invoice_id=invoice_id,
                    rule_id="MD_IBAN_NO_4EYES",
                    signal="iban_change_without_4eyes",
                    severity=Severity.CRITICAL,
                    evidence=evidence_base,
                )
            )
    return findings


def detect_dormant_reactivation(
    events: Iterable[VendorMasterEvent],
    invoices: pd.DataFrame,
    *,
    dormant_days: int = DEFAULT_DORMANT_DAYS,
    exposure_window_days: int = DEFAULT_EXPOSURE_WINDOW_DAYS,
) -> list[Finding]:
    """Détecte un fournisseur dormant > N jours dont l'IBAN change.

    Heuristique : pour chaque IBAN change d'un fournisseur, on regarde la dernière
    facture *avant* le changement ; si l'écart dépasse `dormant_days`, le finding
    est levé sur les paiements postérieurs.
    """
    df = _events_to_df(events)
    if df.empty or invoices.empty or "vendor_id" not in invoices.columns:
        return []
    iban_changes = df[df["field"] == MasterDataField.IBAN.value]
    inv = invoices.copy()
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"], utc=True, errors="coerce")

    findings: list[Finding] = []
    for _, ev in iban_changes.iterrows():
        vendor_id = ev["vendor_id"]
        changed_at = pd.Timestamp(ev["changed_at"])
        if changed_at.tzinfo is None:
            changed_at = changed_at.tz_localize("UTC")
        prior = inv[(inv["vendor_id"] == vendor_id) & (inv["invoice_date"] < changed_at)]
        if prior.empty:
            continue
        gap_days = (changed_at - prior["invoice_date"].max()).days
        if gap_days < dormant_days:
            continue
        exposure, impacted = _exposure_after_event(
            invoices, vendor_id, ev["changed_at"], exposure_window_days
        )
        if not impacted:
            continue
        evidence = {
            "vendor_id": vendor_id,
            "event_id": ev["event_id"],
            "changed_at": ev["changed_at"].isoformat(),
            "dormant_days": int(gap_days),
            "exposure_eur": round(exposure, 2),
            "impacted_invoices": impacted[:50],
        }
        for invoice_id in impacted:
            findings.append(
                _new_finding(
                    invoice_id=invoice_id,
                    rule_id="MD_DORMANT_REACTIVATED",
                    signal="dormant_vendor_reactivated_with_iban_change",
                    severity=Severity.CRITICAL,
                    evidence=evidence,
                )
            )
    return findings


def detect_name_and_iban_same_day(
    events: Iterable[VendorMasterEvent],
    invoices: pd.DataFrame,
    *,
    window_hours: int = DEFAULT_SAME_DAY_NAME_IBAN_HOURS,
    exposure_window_days: int = DEFAULT_EXPOSURE_WINDOW_DAYS,
) -> list[Finding]:
    """Changement de nom et d'IBAN dans la même fenêtre courte = clone vendor."""
    df = _events_to_df(events)
    if df.empty:
        return []
    findings: list[Finding] = []
    by_vendor = df.groupby("vendor_id")
    for vendor_id, group in by_vendor:
        iban_evts = group[group["field"] == MasterDataField.IBAN.value]
        name_evts = group[group["field"] == MasterDataField.NAME.value]
        if iban_evts.empty or name_evts.empty:
            continue
        for _, iban_ev in iban_evts.iterrows():
            iban_ts = pd.Timestamp(iban_ev["changed_at"])
            close_name = name_evts[
                (name_evts["changed_at"] >= iban_ts - pd.Timedelta(hours=window_hours))
                & (name_evts["changed_at"] <= iban_ts + pd.Timedelta(hours=window_hours))
            ]
            if close_name.empty:
                continue
            exposure, impacted = _exposure_after_event(
                invoices, vendor_id, iban_ev["changed_at"], exposure_window_days
            )
            evidence = {
                "vendor_id": vendor_id,
                "iban_event_id": iban_ev["event_id"],
                "name_event_ids": close_name["event_id"].tolist(),
                "iban_changed_at": iban_ev["changed_at"].isoformat(),
                "exposure_eur": round(exposure, 2),
                "impacted_invoices": impacted[:50],
            }
            target_ids = impacted or [f"VENDOR::{vendor_id}"]
            severity = Severity.CRITICAL if impacted else Severity.HIGH
            for invoice_id in target_ids:
                findings.append(
                    _new_finding(
                        invoice_id=invoice_id,
                        rule_id="MD_NAME_AND_IBAN_SAME_DAY",
                        signal="vendor_name_and_iban_changed_same_day",
                        severity=severity,
                        evidence=evidence,
                    )
                )
    return findings


def run_all(
    events: Iterable[VendorMasterEvent],
    invoices: pd.DataFrame,
    *,
    dormant_days: int = DEFAULT_DORMANT_DAYS,
    exposure_window_days: int = DEFAULT_EXPOSURE_WINDOW_DAYS,
) -> list[Finding]:
    """Lance toutes les règles master data et déduplique les findings exacts."""
    events = list(events)
    findings = (
        detect_iban_change_without_4eyes(
            events, invoices, exposure_window_days=exposure_window_days
        )
        + detect_dormant_reactivation(
            events,
            invoices,
            dormant_days=dormant_days,
            exposure_window_days=exposure_window_days,
        )
        + detect_name_and_iban_same_day(events, invoices, exposure_window_days=exposure_window_days)
    )
    # Déduplication (invoice_id, rule_id, vendor_id)
    seen: set[tuple[str, str, str]] = set()
    deduped: list[Finding] = []
    for f in findings:
        key = (f.invoice_id, f.rule_id, str(f.evidence.get("vendor_id", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)
    return deduped
