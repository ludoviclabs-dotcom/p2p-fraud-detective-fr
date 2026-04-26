"""Détecteur d'anomalies par Isolation Forest (scikit-learn).

Features comportementales (vectorisées sur le DataFrame) :
- log_amount : log1p du montant (réduit l'écart entre petits/gros montants)
- weekday : 0 = lundi … 6 = dimanche
- ratio_amount_to_vendor_avg : montant / moyenne des montants du même fournisseur
- days_since_last_invoice_same_vendor : écart depuis la facture précédente
- count_invoices_same_user_same_day : nb de factures saisies par le même user le même jour
- has_po : 1 si PO présent, 0 sinon

Pipeline : ColumnTransformer (StandardScaler) → IsolationForest. Score normalisé 0-100.
Modèle persisté pour scoring incrémental.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from p2p_fraud.schema import Finding, Severity

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[3] / "data" / "cache" / "iforest.joblib"

_FEATURE_COLUMNS = (
    "log_amount",
    "weekday",
    "ratio_amount_to_vendor_avg",
    "days_since_last_invoice_same_vendor",
    "count_invoices_same_user_same_day",
    "has_po",
)


@dataclass(frozen=True)
class IsolationForestResult:
    scores: pd.Series  # 0-100, indexé sur invoice_id
    feature_matrix: pd.DataFrame
    contamination: float


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorise les features depuis un DataFrame canonique."""
    feats = pd.DataFrame(index=df.index)
    feats["log_amount"] = np.log1p(df["amount"].astype(float).clip(lower=0))

    dates = pd.to_datetime(df["invoice_date"], errors="coerce")
    feats["weekday"] = dates.dt.weekday.fillna(0).astype(int)

    vendor_avg = df.groupby("vendor_name")["amount"].transform("mean")
    feats["ratio_amount_to_vendor_avg"] = (df["amount"] / vendor_avg.replace(0, np.nan)).fillna(1.0)

    prev_date = (
        df.assign(_d=dates).sort_values(["vendor_name", "_d"]).groupby("vendor_name")["_d"].shift()
    )
    delta = (dates - prev_date).dt.days
    feats["days_since_last_invoice_same_vendor"] = delta.fillna(-1).astype(float)

    if "user_id" in df.columns:
        same_day_user_count = df.groupby([df["user_id"].fillna("__none__"), dates.dt.date])[
            "invoice_id"
        ].transform("count")
        feats["count_invoices_same_user_same_day"] = same_day_user_count.fillna(1).astype(float)
    else:
        feats["count_invoices_same_user_same_day"] = 1.0

    if "po_number" in df.columns:
        feats["has_po"] = df["po_number"].notna().astype(int)
    else:
        feats["has_po"] = 0

    return feats[list(_FEATURE_COLUMNS)]


def fit_isolation_forest(
    df: pd.DataFrame,
    *,
    contamination: float = 0.01,
    n_estimators: int = 200,
    random_state: int = 42,
    save_path: Path | None = DEFAULT_MODEL_PATH,
) -> tuple[Pipeline, pd.DataFrame]:
    """Entraîne le pipeline et le persiste sur disque."""
    feats = _build_features(df)
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "iforest",
                IsolationForest(
                    contamination=contamination,
                    n_estimators=n_estimators,
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(feats.values)
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, save_path)
    return pipeline, feats


def score(pipeline: Pipeline, feats: pd.DataFrame) -> pd.Series:
    """Score 0-100 (100 = anomalie maximale)."""
    raw = pipeline.named_steps["iforest"].score_samples(
        pipeline.named_steps["scaler"].transform(feats.values)
    )
    # raw : plus négatif = plus anormal. Inverse + minmax → 0-100.
    inverted = -raw
    lo, hi = inverted.min(), inverted.max()
    spread = hi - lo if hi > lo else 1.0
    normalized = (inverted - lo) / spread * 100
    return pd.Series(normalized, index=feats.index)


def detect_anomalies(
    df: pd.DataFrame,
    *,
    contamination: float = 0.01,
    pipeline: Pipeline | None = None,
    persist: bool = True,
) -> tuple[list[Finding], IsolationForestResult]:
    """Pipeline complet : entraînement (si pas de pipeline fourni) → scoring → Findings."""
    if df.empty:
        empty = IsolationForestResult(pd.Series(dtype=float), pd.DataFrame(), contamination)
        return [], empty

    feats = _build_features(df)
    if pipeline is None:
        pipeline, _ = fit_isolation_forest(
            df,
            contamination=contamination,
            save_path=DEFAULT_MODEL_PATH if persist else None,
        )
    scores = score(pipeline, feats)

    # Sévérité par quantile
    threshold_high = scores.quantile(1 - contamination * 2)
    threshold_critical = scores.quantile(1 - contamination)

    findings: list[Finding] = []
    flagged = df.loc[scores >= threshold_high].copy()
    flagged["_score"] = scores.loc[flagged.index]
    for idx, row in flagged.iterrows():
        s = float(row["_score"])
        severity = Severity.CRITICAL if s >= threshold_critical else Severity.HIGH
        findings.append(
            Finding(
                invoice_id=str(row["invoice_id"]),
                detector="isolation_forest",
                signal="ml_anomaly",
                severity=severity,
                rule_id="IFOREST",
                evidence={
                    "anomaly_score": round(s, 2),
                    "features": {k: float(feats.at[idx, k]) for k in _FEATURE_COLUMNS},
                },
            )
        )
    return findings, IsolationForestResult(
        scores=scores, feature_matrix=feats, contamination=contamination
    )


def load_pipeline(path: Path | None = None) -> Pipeline | None:
    p = path or DEFAULT_MODEL_PATH
    return joblib.load(p) if p.exists() else None
