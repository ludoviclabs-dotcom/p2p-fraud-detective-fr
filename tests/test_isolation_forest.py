"""Tests Isolation Forest + précision sur ground truth des outliers étiquetés."""

from __future__ import annotations

from p2p_fraud.detectors.isolation_forest import (
    _build_features,
    detect_anomalies,
    fit_isolation_forest,
)
from p2p_fraud.synthetic.generator import FraudType


def test_build_features_columns(small_dataset):
    invoices, _ = small_dataset
    feats = _build_features(invoices)
    assert set(feats.columns) == {
        "log_amount",
        "weekday",
        "ratio_amount_to_vendor_avg",
        "days_since_last_invoice_same_vendor",
        "count_invoices_same_user_same_day",
        "has_po",
    }
    assert len(feats) == len(invoices)
    assert feats.notna().all().all()


def test_fit_and_score(small_dataset, tmp_path):
    invoices, _ = small_dataset
    pipeline, _feats = fit_isolation_forest(
        invoices, contamination=0.02, save_path=tmp_path / "iforest.joblib"
    )
    assert (tmp_path / "iforest.joblib").exists()
    assert pipeline is not None


def test_detect_anomalies_flags_outliers(medium_dataset):
    """L'Isolation Forest doit attraper la majorité des outliers étiquetés (montant 50× moyenne vendor)."""
    invoices, _ = medium_dataset
    findings, result = detect_anomalies(invoices, contamination=0.02, persist=False)

    assert len(findings) > 0
    assert result.scores.max() > result.scores.median()

    flagged_ids = {f.invoice_id for f in findings}
    truth_ids = set(
        invoices.loc[invoices["fraud_type"] == FraudType.AMOUNT_OUTLIER.value, "invoice_id"]
    )
    if not truth_ids:
        return  # skip si pas d'outliers injectés
    recall = len(flagged_ids & truth_ids) / len(truth_ids)
    print(f"\n[isolation_forest] recall amount_outlier = {recall:.3f}")
    assert recall >= 0.5, f"IForest rate trop d'outliers étiquetés : recall={recall:.3f}"
