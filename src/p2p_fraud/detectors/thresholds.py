"""Détecteur de montants juste sous seuil de validation.

Les fraudeurs internes contournent les seuils d'approbation hiérarchique en émettant
des factures juste en dessous (ex. 4 950 € pour un seuil de 5 000 €). Ce détecteur :

1. Flagge chaque facture dans la fenêtre `[seuil − ε·seuil, seuil[`.
2. Aggrave la sévérité quand un fournisseur a *plusieurs* factures dans la fenêtre
   (clustering = signal fort, distinct du faux positif aléatoire).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from p2p_fraud.schema import Finding, Severity

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "scoring" / "weights.yaml"


def _load_threshold_config(path: Path | None = None) -> dict:
    p = path or DEFAULT_WEIGHTS_PATH
    if not p.exists():
        return {
            "validation_levels": [1000, 5000, 10000, 25000, 50000],
            "epsilon_pct": 0.02,
            "min_amount": 100,
        }
    with p.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("thresholds", {})


def _matching_threshold(amount: float, levels: list[int], epsilon_pct: float) -> int | None:
    """Renvoie le seuil dont la fenêtre `[seuil − ε·seuil, seuil[` contient `amount`."""
    for lvl in levels:
        lower = lvl * (1 - epsilon_pct)
        if lower <= amount < lvl:
            return lvl
    return None


def detect_under_threshold(
    df: pd.DataFrame,
    *,
    config_path: Path | None = None,
    cluster_min: int = 3,
) -> list[Finding]:
    """Détecte les factures sous-seuil et aggrave par clustering fournisseur.

    Args:
        cluster_min: nombre minimal de factures sous-seuil par fournisseur pour
            passer la sévérité de MEDIUM à HIGH.
    """
    cfg = _load_threshold_config(config_path)
    levels: list[int] = cfg.get("validation_levels", [1000, 5000, 10000, 25000, 50000])
    epsilon_pct: float = cfg.get("epsilon_pct", 0.02)
    min_amount: float = cfg.get("min_amount", 100)

    if df.empty:
        return []

    findings: list[Finding] = []
    matched_threshold = (
        df["amount"]
        .astype(float)
        .map(lambda a: _matching_threshold(a, levels, epsilon_pct) if a >= min_amount else None)
    )
    flagged = df.loc[matched_threshold.notna()].copy()
    if flagged.empty:
        return findings
    flagged["_threshold"] = matched_threshold[matched_threshold.notna()].astype(int)

    # Clustering par fournisseur × seuil
    cluster_counts = flagged.groupby(["vendor_name", "_threshold"]).size().to_dict()

    for _, row in flagged.iterrows():
        vendor = row["vendor_name"]
        threshold = int(row["_threshold"])
        cluster_size = cluster_counts.get((vendor, threshold), 1)
        severity = Severity.HIGH if cluster_size >= cluster_min else Severity.MEDIUM
        gap_pct = (threshold - float(row["amount"])) / threshold
        findings.append(
            Finding(
                invoice_id=str(row["invoice_id"]),
                detector="thresholds",
                signal="amount_just_under_threshold",
                severity=severity,
                rule_id=f"THRESHOLD_{threshold}",
                evidence={
                    "amount": float(row["amount"]),
                    "threshold": threshold,
                    "gap_pct": round(gap_pct, 4),
                    "cluster_size_for_vendor": cluster_size,
                    "vendor_name": vendor,
                },
            )
        )
    return findings
