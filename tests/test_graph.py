"""Tests détecteur graphe NetworkX."""

from __future__ import annotations

from datetime import date

import pandas as pd

from p2p_fraud.detectors.graph import detect_fraud_rings
from p2p_fraud.synthetic.generator import FraudType


def test_no_findings_on_empty():
    df = pd.DataFrame(columns=["invoice_id", "vendor_name", "amount", "invoice_date", "iban"])
    findings, analysis = detect_fraud_rings(df)
    assert findings == []
    assert analysis.n_shared_iban_rings == 0


def test_shared_iban_ring_minimal():
    df = pd.DataFrame(
        {
            "invoice_id": ["A", "B", "C"],
            "vendor_name": ["Vendor X SARL", "Vendor Y SAS", "Vendor X SARL"],
            "amount": [1000.0, 2000.0, 3000.0],
            "invoice_date": [date(2025, 1, 1)] * 3,
            "iban": ["FR111", "FR111", "FR222"],  # X et Y partagent FR111
        }
    )
    findings, analysis = detect_fraud_rings(df, cluster_min_size=2)
    flagged_ids = {f.invoice_id for f in findings if f.signal == "shared_iban_ring"}
    assert flagged_ids == {"A", "B"}
    assert analysis.n_shared_iban_rings == 1


def test_no_false_positive_unique_iban():
    df = pd.DataFrame(
        {
            "invoice_id": ["A", "B"],
            "vendor_name": ["X SARL", "X SARL"],
            "amount": [100.0, 200.0],
            "invoice_date": [date(2025, 1, 1), date(2025, 2, 1)],
            "iban": ["FR111", "FR111"],  # même vendor, normal
        }
    )
    findings, _ = detect_fraud_rings(df)
    iban_ring_findings = [f for f in findings if f.signal == "shared_iban_ring"]
    assert iban_ring_findings == []


def test_recall_on_synthetic_ground_truth(medium_dataset):
    """Le détecteur doit attraper la majorité des anneaux IBAN injectés."""
    invoices, _ = medium_dataset
    findings, analysis = detect_fraud_rings(invoices, cluster_min_size=2)

    truth_ids = set(
        invoices.loc[invoices["fraud_type"] == FraudType.SHARED_IBAN_RING.value, "invoice_id"]
    )
    if not truth_ids:
        return  # skip if not injected

    flagged_ids = {f.invoice_id for f in findings}
    recall = len(flagged_ids & truth_ids) / len(truth_ids)
    print(f"\n[graph] anneaux IBAN recall = {recall:.3f}, n_rings = {analysis.n_shared_iban_rings}")
    assert recall >= 0.85, f"Recall anneaux IBAN trop bas : {recall:.3f}"
