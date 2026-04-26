"""Tests doublons + F1 sur ground truth synthétique."""

from __future__ import annotations

from datetime import date

import pandas as pd

from p2p_fraud.detectors.duplicates import detect_duplicates
from p2p_fraud.synthetic.generator import FraudType


def _f1_score(tp: int, fp: int, fn: int) -> float:
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def test_exact_duplicate_detection_minimal():
    df = pd.DataFrame(
        {
            "invoice_id": ["A", "B", "C"],
            "vendor_name": ["ACME SARL", "ACME SARL", "Other SAS"],
            "amount": [100.00, 100.00, 200.00],
            "invoice_date": [date(2025, 1, 1), date(2025, 1, 1), date(2025, 1, 1)],
            "iban": ["FR123", "FR123", "FR456"],
        }
    )
    findings = detect_duplicates(df)
    flagged = {f.invoice_id for f in findings if f.signal == "duplicate_exact"}
    assert flagged == {"A", "B"}


def test_fuzzy_duplicate_detection_minimal():
    df = pd.DataFrame(
        {
            "invoice_id": ["A", "B", "C"],
            "vendor_name": ["ACME SARL", "A.C.M.E. SARL", "Other"],
            "amount": [100.00, 100.00, 100.00],
            "invoice_date": [date(2025, 1, 1), date(2025, 1, 2), date(2025, 6, 1)],
            "iban": ["FR1", "FR2", "FR3"],
        }
    )
    findings = detect_duplicates(df, name_threshold=85, date_window_days=2)
    fuzzy = {f.invoice_id for f in findings if f.signal == "duplicate_fuzzy"}
    assert "A" in fuzzy and "B" in fuzzy
    assert "C" not in fuzzy


def test_recall_on_ground_truth(medium_dataset):
    """On vise un fort RECALL (ne pas rater les fraudes étiquetées) — la précision se
    règle ensuite via les seuils en production."""
    invoices, _ = medium_dataset
    findings = detect_duplicates(invoices, name_threshold=88, date_window_days=2)
    flagged_ids = {f.invoice_id for f in findings}

    truth_ids = set(
        invoices.loc[
            invoices["fraud_type"].isin(
                [FraudType.DUPLICATE_EXACT.value, FraudType.DUPLICATE_FUZZY.value]
            ),
            "invoice_id",
        ]
    )

    tp = len(flagged_ids & truth_ids)
    fp = len(flagged_ids - truth_ids)
    fn = len(truth_ids - flagged_ids)
    recall = tp / (tp + fn) if (tp + fn) else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    f1 = _f1_score(tp, fp, fn)
    print(f"\n[duplicates] tp={tp} fp={fp} fn={fn} P={precision:.3f} R={recall:.3f} F1={f1:.3f}")
    assert recall >= 0.85, f"Recall doublons trop bas : {recall:.3f}"
