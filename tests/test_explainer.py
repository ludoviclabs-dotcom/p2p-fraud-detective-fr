"""Tests explainer (waterfall + perturbation Isolation Forest) — Sprint 4."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from p2p_fraud.schema import Finding, Severity
from p2p_fraud.scoring.explainer import (
    explain_isolation_forest_row,
    score_waterfall,
    top_contributions_summary,
    waterfall_to_dataframe,
)
from p2p_fraud.scoring.risk_engine import aggregate_findings_with_explanations


def _f(invoice_id: str, detector: str, rule_id: str, severity: Severity, evidence=None) -> Finding:
    return Finding(
        invoice_id=invoice_id,
        detector=detector,
        signal="test",
        severity=severity,
        rule_id=rule_id,
        evidence=evidence or {},
    )


def test_waterfall_with_explanations_orders_by_contribution():
    findings = [
        _f(
            "INV1",
            "master_data",
            "MD_IBAN_NO_4EYES",
            Severity.CRITICAL,
            {
                "changed_at": "2025-06-01",
                "changed_by": "U",
                "exposure_eur": 1000,
                "exposure_window_days": 90,
            },
        ),
        _f("INV1", "duplicates", "DUP_EXACT", Severity.HIGH, {"duplicate_of": "INV2"}),
    ]
    scores = aggregate_findings_with_explanations(findings)
    rs = scores["INV1"]
    assert rs.contributions
    # MD_IBAN_NO_4EYES (poids 1.5 × CRITICAL 1.0) > DUP_EXACT (poids 1.0 × HIGH 0.6)
    assert rs.contributions[0].finding_rule_id == "MD_IBAN_NO_4EYES"
    assert rs.contributions[0].contribution > rs.contributions[1].contribution


def test_score_waterfall_sums_to_score():
    findings = [
        _f("INV1", "master_data", "MD_IBAN_NO_4EYES", Severity.CRITICAL, {}),
        _f("INV1", "sanctions", "SANCTIONS_VENDOR_HIT", Severity.CRITICAL, {}),
    ]
    scores = aggregate_findings_with_explanations(findings)
    rs = scores["INV1"]
    steps = score_waterfall(rs)
    assert len(steps) == 2
    # Le cumulatif doit converger vers le score final (capé à 100)
    assert steps[-1].cumulative <= 100.0


def test_score_waterfall_falls_back_to_breakdown_when_no_contributions():
    from p2p_fraud.schema import RiskScore

    rs = RiskScore(
        invoice_id="INV1",
        score=42.0,
        findings_count=2,
        breakdown={"duplicates": 30.0, "sirene": 12.0},
    )
    steps = score_waterfall(rs)
    assert len(steps) == 2
    assert {s.label for s in steps} == {"duplicates", "sirene"}


def test_waterfall_to_dataframe_columns():
    findings = [_f("INV1", "duplicates", "DUP_EXACT", Severity.HIGH, {})]
    rs = aggregate_findings_with_explanations(findings)["INV1"]
    df = waterfall_to_dataframe(score_waterfall(rs))
    assert {"label", "delta", "cumulative", "reason_fr"}.issubset(df.columns)
    assert len(df) == 1


def test_top_contributions_summary():
    findings = [
        _f("INV1", "master_data", "MD_IBAN_NO_4EYES", Severity.CRITICAL, {}),
        _f("INV1", "sanctions", "SANCTIONS_VENDOR_PEP", Severity.HIGH, {}),
    ]
    rs = aggregate_findings_with_explanations(findings)["INV1"]
    summary = top_contributions_summary(rs, n=2)
    assert "MD_IBAN_NO_4EYES" in summary
    assert "SANCTIONS_VENDOR_PEP" in summary


def test_top_contributions_summary_legacy_fallback():
    from p2p_fraud.schema import RiskScore

    rs = RiskScore(invoice_id="INV1", score=42.0)
    text = top_contributions_summary(rs)
    assert text.startswith("Score 42")


@pytest.fixture(scope="module")
def trained_pipeline_and_features() -> tuple[Pipeline, pd.DataFrame]:
    """Crée un pipeline IF déterministe sur jeu jouet."""
    rng = np.random.default_rng(42)
    n = 200
    n_features = 4
    base = rng.normal(size=(n, n_features))
    # 3 outliers explicites
    base[:3] = base[:3] + 8
    df = pd.DataFrame(base, columns=[f"f{i}" for i in range(n_features)])
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("iforest", IsolationForest(random_state=42, contamination=0.02)),
        ]
    )
    pipeline.fit(df)
    return pipeline, df


def test_explain_isolation_forest_row_returns_sorted_features(
    trained_pipeline_and_features,
):
    pipeline, df = trained_pipeline_and_features
    row = df.iloc[0]
    contribs = explain_isolation_forest_row(pipeline, row, df.columns.tolist())
    assert len(contribs) == len(df.columns)
    # Tri décroissant par delta
    deltas = [c.delta_anomaly_score for c in contribs]
    assert deltas == sorted(deltas, reverse=True)


def test_explain_isolation_forest_row_handles_none_pipeline():
    assert explain_isolation_forest_row(None, pd.Series([0.1, 0.2]), ["a", "b"]) == []


def test_explain_is_deterministic(trained_pipeline_and_features):
    pipeline, df = trained_pipeline_and_features
    row = df.iloc[0]
    a = explain_isolation_forest_row(pipeline, row, df.columns.tolist())
    b = explain_isolation_forest_row(pipeline, row, df.columns.tolist())
    assert [c.delta_anomaly_score for c in a] == [c.delta_anomaly_score for c in b]
