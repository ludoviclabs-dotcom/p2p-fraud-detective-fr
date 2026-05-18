"""Tests for the public-safe Vercel graph export."""

from __future__ import annotations

import json

import pandas as pd

from scripts.export_p2p_graph_demo import export_dataset, mask_iban


def test_mask_iban_hides_middle_digits() -> None:
    masked = mask_iban("FR7612345678901234567890185")

    assert masked == "FR76********0185"
    assert "12345678901234567890" not in masked


def test_export_dataset_sanitizes_iban_and_writes_balanced_json(tmp_path) -> None:
    invoices = pd.DataFrame(
        [
            {
                "invoice_id": "INV-1",
                "siren": "111111111",
                "vendor_name": "Alpha SARL",
                "iban": "FR7612345678901234567890185",
                "amount": 1200.0,
                "currency": "EUR",
                "invoice_date": "2025-01-02",
            },
            {
                "invoice_id": "INV-2",
                "siren": "222222222",
                "vendor_name": "Beta SAS",
                "iban": "FR7612345678901234567890185",
                "amount": 2400.0,
                "currency": "EUR",
                "invoice_date": "2025-01-03",
            },
            {
                "invoice_id": "INV-3",
                "siren": "333333333",
                "vendor_name": "Gamma SA",
                "iban": "FR7611111111111111111111111",
                "amount": 3333.0,
                "currency": "EUR",
                "invoice_date": "2025-01-04",
            },
            {
                "invoice_id": "INV-4",
                "siren": "333333333",
                "vendor_name": "Gamma SA",
                "iban": "FR7611111111111111111111111",
                "amount": 3333.0,
                "currency": "EUR",
                "invoice_date": "2025-01-04",
            },
            {
                "invoice_id": "INV-5",
                "siren": "444444444",
                "vendor_name": "Delta SAS",
                "iban": "FR7622222222222222222222222",
                "amount": 4900.0,
                "currency": "EUR",
                "invoice_date": "2025-01-05",
            },
        ]
    )
    vendors = pd.DataFrame(
        [
            {"vendor_id": "V001", "vendor_name": "Alpha SARL", "siren": "111111111"},
            {"vendor_id": "V002", "vendor_name": "Beta SAS", "siren": "222222222"},
            {"vendor_id": "V003", "vendor_name": "Gamma SA", "siren": "333333333"},
            {"vendor_id": "V004", "vendor_name": "Delta SAS", "siren": "444444444"},
        ]
    )
    invoices_path = tmp_path / "invoices.csv"
    vendors_path = tmp_path / "vendors.csv"
    output_path = tmp_path / "p2p-demo.json"
    invoices.to_csv(invoices_path, index=False)
    vendors.to_csv(vendors_path, index=False)

    dataset = export_dataset(
        invoices_path=invoices_path,
        vendors_path=vendors_path,
        output_path=output_path,
        cluster_min_size=2,
    )
    payload_text = output_path.read_text(encoding="utf-8")
    payload = json.loads(payload_text)

    assert dataset["metrics"]["findingCount"] >= 2
    assert dataset["metrics"]["criticalFindings"] >= 1
    assert dataset["metrics"]["mediumFindings"] >= 1
    assert dataset["metrics"]["signalCounts"]["shared_iban_ring"] >= 1
    assert dataset["metrics"]["signalCounts"]["duplicate_exact"] >= 1
    assert dataset["metrics"]["signalCounts"]["amount_just_under_threshold"] >= 1
    assert payload["nodes"]
    assert payload["edges"]
    assert any(node["kind"] == "iban" for node in payload["nodes"])
    assert {"shared_iban_ring", "duplicate_exact", "amount_just_under_threshold"} <= {
        finding["signal"] for finding in payload["findings"]
    }
    assert {"critical", "medium"} <= {finding["severity"] for finding in payload["findings"]}
    node_ids = {node["id"] for node in payload["nodes"]}
    finding_ids = {finding["id"] for finding in payload["findings"]}
    for edge in payload["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids
        assert set(edge["findingIds"]) <= finding_ids
    assert "FR7612345678901234567890185" not in payload_text
    assert "FR76********0185" in payload_text
