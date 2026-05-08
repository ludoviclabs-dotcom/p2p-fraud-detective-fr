"""Explicabilité du scoring — niveau finding et niveau ML.

Deux capacités exposées :

1. **score_waterfall(score)** : transforme un `RiskScore` enrichi (issu de
   `aggregate_findings(..., with_explanations=True)`) en lignes prêtes à
   l'affichage Plotly waterfall.
2. **explain_isolation_forest_row()** : par perturbation feature-par-feature,
   identifie les variables qui contribuent le plus au score d'anomalie d'une
   facture donnée. C'est une approximation locale qui évite la dépendance
   à `shap` (lourd) tout en restant interprétable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from p2p_fraud.schema import RiskScore


@dataclass(frozen=True)
class WaterfallStep:
    label: str  # ex. "MD_IBAN_NO_4EYES (master_data)"
    delta: float  # points ajoutés au score
    cumulative: float
    reason_fr: str | None = None


def score_waterfall(score: RiskScore) -> list[WaterfallStep]:
    """Construit la liste de steps pour un graphique Plotly waterfall.

    Si le RiskScore n'a pas de `contributions` (mode legacy), retourne une
    seule step agrégée par détecteur depuis le `breakdown`.
    """
    steps: list[WaterfallStep] = []
    cumulative = 0.0

    if score.contributions:
        for c in score.contributions:
            cumulative += c.contribution
            steps.append(
                WaterfallStep(
                    label=f"{c.finding_rule_id} ({c.detector})",
                    delta=round(c.contribution, 2),
                    cumulative=round(min(100.0, cumulative), 2),
                    reason_fr=c.reason_fr,
                )
            )
    else:
        # Fallback breakdown legacy : un step par détecteur
        for detector, value in score.breakdown.items():
            cumulative += value
            steps.append(
                WaterfallStep(
                    label=detector,
                    delta=round(value, 2),
                    cumulative=round(min(100.0, cumulative), 2),
                )
            )
    return steps


@dataclass(frozen=True)
class FeatureContribution:
    feature: str
    delta_anomaly_score: float  # impact sur l'anomaly score si on neutralise la feature


def explain_isolation_forest_row(
    pipeline: Pipeline,
    feature_row: pd.Series,
    feature_columns: list[str] | tuple[str, ...],
) -> list[FeatureContribution]:
    """Explique une décision Isolation Forest par perturbation locale.

    Pour chaque feature, on remplace sa valeur par la médiane (0 après
    StandardScaler) et on mesure la variation de `decision_function`. Une
    variation négative importante signifie que la feature poussait la ligne
    vers l'anomalie.

    Conception : robuste et reproductible, pas de dépendance shap. Coût
    O(n_features) par ligne — adapté au scoring d'une alerte ouverte par un
    auditeur (1 ligne à la fois), pas au batch massif.
    """
    if pipeline is None:
        return []
    feature_columns = list(feature_columns)
    base = feature_row[feature_columns].astype(float).values.reshape(1, -1)
    base_score = float(pipeline.decision_function(base)[0])

    contributions: list[FeatureContribution] = []
    for i, name in enumerate(feature_columns):
        perturbed = base.copy()
        perturbed[0, i] = 0.0  # neutralisation
        score_after = float(pipeline.decision_function(perturbed)[0])
        # delta > 0 : neutraliser la feature *augmente* le score (= la rend
        # moins anormale) ⇒ la feature contribuait à l'anomalie.
        contributions.append(
            FeatureContribution(
                feature=name,
                delta_anomaly_score=round(score_after - base_score, 4),
            )
        )

    return sorted(contributions, key=lambda c: c.delta_anomaly_score, reverse=True)


def waterfall_to_dataframe(steps: list[WaterfallStep]) -> pd.DataFrame:
    """Convertit une liste de WaterfallStep en DataFrame pour Plotly."""
    if not steps:
        return pd.DataFrame(columns=["label", "delta", "cumulative", "reason_fr"])
    return pd.DataFrame(
        [
            {
                "label": s.label,
                "delta": s.delta,
                "cumulative": s.cumulative,
                "reason_fr": s.reason_fr,
            }
            for s in steps
        ]
    )


def top_contributions_summary(score: RiskScore, n: int = 3) -> str:
    """Phrase synthèse FR : `score X/100 (top contributeurs : a, b, c)`."""
    if not score.contributions:
        return f"Score {score.score:.0f}/100"
    top = sorted(score.contributions, key=lambda c: c.contribution, reverse=True)[:n]
    parts = [f"{c.finding_rule_id} ({c.contribution_pct}%)" for c in top]
    return f"Score {score.score:.0f}/100 — top contributeurs : " + ", ".join(parts)


def _safe_to_dict(score: RiskScore) -> dict:
    """Helper pour sérialisation Streamlit."""
    return {
        "invoice_id": score.invoice_id,
        "score": score.score,
        "findings_count": score.findings_count,
        "contributions": [c.model_dump() for c in score.contributions],
        "reason_codes_fr": score.reason_codes_fr,
        "breakdown": score.breakdown,
    }


# Compat shim attendu par certaines pages : exposer numpy pour debugging
# (utilisé par les tests sans imports redondants côté pages)
__all__ = [
    "FeatureContribution",
    "WaterfallStep",
    "explain_isolation_forest_row",
    "np",
    "score_waterfall",
    "top_contributions_summary",
    "waterfall_to_dataframe",
]
np = np  # ré-exposé pour signal explicite (lint-friendly)
