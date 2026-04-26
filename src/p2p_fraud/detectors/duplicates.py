"""Détecteur de doublons : exacts (clé montant + date + IBAN) et fuzzy (RapidFuzz sur le nom).

Stratégie de complexité : on ne compare PAS toutes les paires (O(n²)). On bucket d'abord
par `(amount_arrondi, fenêtre date)` puis on fait du fuzzy *uniquement* dans chaque bucket.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import pandas as pd
from rapidfuzz import fuzz

from p2p_fraud.schema import Finding, Severity


def _normalize_name(name: str | None) -> str:
    if name is None:
        return ""
    return "".join(c.lower() for c in str(name) if c.isalnum())


def _detect_exact(df: pd.DataFrame) -> list[Finding]:
    """Doublons stricts : même `(amount, invoice_date, iban_or_siren, vendor_name)`."""
    if df.empty:
        return []
    findings: list[Finding] = []
    keys = (
        df["amount"].round(2).astype(str)
        + "|"
        + df["invoice_date"].astype(str)
        + "|"
        + df.get("iban", pd.Series([""] * len(df))).fillna("").astype(str)
        + "|"
        + df["vendor_name"].fillna("").astype(str)
    )
    df_with_key = df.assign(_dup_key=keys)
    grouped = df_with_key.groupby("_dup_key")
    for _, group in grouped:
        if len(group) < 2:
            continue
        ids = group["invoice_id"].tolist()
        for inv_id in ids:
            findings.append(
                Finding(
                    invoice_id=str(inv_id),
                    detector="duplicates",
                    signal="duplicate_exact",
                    severity=Severity.CRITICAL,
                    rule_id="DUP_EXACT",
                    evidence={
                        "siblings": [i for i in ids if i != inv_id],
                        "amount": float(group["amount"].iloc[0]),
                        "vendor_name": group["vendor_name"].iloc[0],
                    },
                )
            )
    return findings


def _day_bucket(d: date, date_window: int) -> int:
    julian = (d - date(1970, 1, 1)).days
    return julian // max(1, date_window)


def _amounts_close(a: float, b: float, *, abs_tol: float, rel_tol: float) -> bool:
    diff = abs(a - b)
    return diff <= abs_tol or diff <= rel_tol * max(abs(a), abs(b))


def _detect_fuzzy(
    df: pd.DataFrame,
    *,
    name_threshold: int,
    date_window: int,
    amount_abs_tol: float,
    amount_rel_tol: float,
) -> list[Finding]:
    """Doublons proches : même fenêtre date, montant proche (tolérance abs/rel),
    score fuzzy nom ≥ `name_threshold`, clé non-exacte."""
    findings: list[Finding] = []
    if df.empty:
        return findings

    # Bucket par jour-fenêtre uniquement (le filtrage montant se fait à l'intérieur).
    buckets: dict[int, list[int]] = defaultdict(list)
    bucket_per_row: list[int | None] = []
    for idx, row in df.iterrows():
        d = row["invoice_date"]
        if isinstance(d, str):
            d = pd.to_datetime(d, errors="coerce").date()
        if pd.isna(d) or d is None:
            bucket_per_row.append(None)
            continue
        bk = _day_bucket(d, date_window)
        bucket_per_row.append(bk)
        buckets[bk].append(idx)

    seen_pairs: set[tuple[str, str]] = set()

    for i, src_idx in enumerate(df.index):
        bk = bucket_per_row[i]
        if bk is None:
            continue
        # Voisins ±1 bucket pour gérer les doublons à cheval sur la frontière de fenêtre.
        candidates: list[int] = []
        for delta in (-1, 0, 1):
            candidates.extend(buckets.get(bk + delta, []))

        src = df.loc[src_idx]
        src_amount = float(src["amount"])
        src_name_norm = _normalize_name(src["vendor_name"])
        if not src_name_norm:
            continue

        for tgt_idx in candidates:
            if tgt_idx == src_idx:
                continue
            pair = tuple(sorted([str(src["invoice_id"]), str(df.at[tgt_idx, "invoice_id"])]))
            if pair in seen_pairs:
                continue
            tgt_amount = float(df.at[tgt_idx, "amount"])
            if not _amounts_close(
                src_amount, tgt_amount, abs_tol=amount_abs_tol, rel_tol=amount_rel_tol
            ):
                continue
            tgt_name_norm = _normalize_name(df.at[tgt_idx, "vendor_name"])
            if not tgt_name_norm:
                continue
            score = fuzz.token_set_ratio(src_name_norm, tgt_name_norm)
            if score < name_threshold:
                continue
            # Filtre : doublon EXACT déjà flaggé séparément
            if (
                str(src.get("iban", ""))
                == str(df.at[tgt_idx, "iban"] if "iban" in df.columns else "")
                and src["vendor_name"] == df.at[tgt_idx, "vendor_name"]
                and src["invoice_date"] == df.at[tgt_idx, "invoice_date"]
                and abs(src_amount - tgt_amount) < 0.005
            ):
                continue
            seen_pairs.add(pair)
            for invoice_idx, sibling_id in (
                (src_idx, str(df.at[tgt_idx, "invoice_id"])),
                (tgt_idx, str(src["invoice_id"])),
            ):
                row = df.loc[invoice_idx]
                findings.append(
                    Finding(
                        invoice_id=str(row["invoice_id"]),
                        detector="duplicates",
                        signal="duplicate_fuzzy",
                        severity=Severity.HIGH,
                        rule_id="DUP_FUZZY",
                        evidence={
                            "sibling": sibling_id,
                            "fuzzy_score": int(score),
                            "amount": float(row["amount"]),
                            "vendor_name": row["vendor_name"],
                        },
                    )
                )
    return findings


def detect_duplicates(
    df: pd.DataFrame,
    *,
    name_threshold: int = 90,
    date_window_days: int = 2,
    amount_abs_tol: float = 1.0,
    amount_rel_tol: float = 0.005,
) -> list[Finding]:
    """Pipeline complet : exacts + fuzzy.

    Args:
        name_threshold: seuil RapidFuzz `token_set_ratio` (0-100). 90 = défaut équilibré.
        date_window_days: tolérance sur l'écart de date (jours).
        amount_abs_tol: tolérance absolue sur le montant (€).
        amount_rel_tol: tolérance relative sur le montant.
    """
    findings = _detect_exact(df)
    findings.extend(
        _detect_fuzzy(
            df,
            name_threshold=name_threshold,
            date_window=date_window_days,
            amount_abs_tol=amount_abs_tol,
            amount_rel_tol=amount_rel_tol,
        )
    )
    return findings
