"""Tests détecteur sous-seuils + F1 sur ground truth."""

from __future__ import annotations

from datetime import date

import pandas as pd

from p2p_fraud.detectors.thresholds import _matching_threshold, detect_under_threshold
from p2p_fraud.synthetic.generator import FraudType


def test_matching_threshold():
    levels = [1000, 5000, 10000]
    eps = 0.02
    assert _matching_threshold(4950.0, levels, eps) == 5000
    assert _matching_threshold(4900.0, levels, eps) == 5000
    assert _matching_threshold(4899.0, levels, eps) is None  # hors fenêtre 2 %
    assert _matching_threshold(5000.0, levels, eps) is None  # ≥ seuil
    assert _matching_threshold(995.0, levels, eps) == 1000


def test_basic_detection():
    df = pd.DataFrame(
        {
            "invoice_id": ["A", "B", "C", "D"],
            "vendor_name": ["X SARL", "X SARL", "X SARL", "Y SAS"],
            "amount": [4950.0, 4900.0, 4980.0, 250.0],
            "invoice_date": [date(2025, 1, 1)] * 4,
        }
    )
    findings = detect_under_threshold(df)
    flagged = {f.invoice_id for f in findings}
    assert flagged == {"A", "B", "C"}
    # Cluster fournisseur ≥ 3 → tous HIGH
    assert all(f.severity.value == "high" for f in findings)


def test_f1_on_ground_truth(medium_dataset):
    invoices, _ = medium_dataset
    findings = detect_under_threshold(invoices)
    flagged_ids = {f.invoice_id for f in findings}

    truth_ids = set(
        invoices.loc[invoices["fraud_type"] == FraudType.UNDER_THRESHOLD.value, "invoice_id"]
    )

    tp = len(flagged_ids & truth_ids)
    fp = len(flagged_ids - truth_ids)
    fn = len(truth_ids - flagged_ids)
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    print(f"\n[thresholds] tp={tp} fp={fp} fn={fn} P={precision:.3f} R={recall:.3f} F1={f1:.3f}")
    assert recall >= 0.85, f"Recall trop bas : {recall:.3f}"
