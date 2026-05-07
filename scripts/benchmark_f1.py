"""Calcule les métriques F1 par détecteur sur ground truth synthétique.

Sortie : tableau Markdown reproductible et fichier JSON pour CI.

Usage :
    python scripts/benchmark_f1.py --rows 50000 --seed 42 --output docs/benchmark_results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from p2p_fraud.detectors import duplicates as detectors_dup
from p2p_fraud.detectors import master_data_changes as detectors_md
from p2p_fraud.detectors import sanctions as detectors_sanctions
from p2p_fraud.detectors import thresholds as detectors_thresholds
from p2p_fraud.enrichment.sanctions_client import SanctionsClient
from p2p_fraud.schema import VendorMasterEvent
from p2p_fraud.synthetic.generator import (
    FraudType,
    GeneratorConfig,
    MasterDataEventsConfig,
    attach_vendor_ids,
    generate_dataset,
    generate_master_data_events,
)


def _f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    if tp == 0:
        return 0.0, 0.0, 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def evaluate_duplicates(invoices: pd.DataFrame) -> dict:
    findings = detectors_dup.detect_duplicates(invoices, name_threshold=88, date_window_days=2)
    flagged = {f.invoice_id for f in findings}
    truth = set(
        invoices.loc[
            invoices["fraud_type"].isin(
                [FraudType.DUPLICATE_EXACT.value, FraudType.DUPLICATE_FUZZY.value]
            ),
            "invoice_id",
        ].astype(str)
    )
    tp = len(flagged & truth)
    fp = len(flagged - truth)
    fn = len(truth - flagged)
    p, r, f1 = _f1(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def evaluate_thresholds(invoices: pd.DataFrame) -> dict:
    findings = detectors_thresholds.detect_under_threshold(invoices)
    flagged = {f.invoice_id for f in findings}
    truth = set(
        invoices.loc[
            invoices["fraud_type"] == FraudType.UNDER_THRESHOLD.value, "invoice_id"
        ].astype(str)
    )
    tp = len(flagged & truth)
    fp = len(flagged - truth)
    fn = len(truth - flagged)
    p, r, f1 = _f1(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def evaluate_master_data(events: pd.DataFrame, invoices: pd.DataFrame) -> dict:
    pydantic_events = [
        VendorMasterEvent(
            event_id=row["event_id"],
            vendor_id=row["vendor_id"],
            field=row["field"],
            old_value=row.get("old_value"),
            new_value=row.get("new_value"),
            changed_at=pd.Timestamp(row["changed_at"]).to_pydatetime(),
            changed_by=row.get("changed_by"),
            approved_by=row.get("approved_by") if pd.notna(row.get("approved_by")) else None,
            source=row.get("source", "erp"),
        )
        for _, row in events.iterrows()
    ]
    findings = detectors_md.detect_iban_change_without_4eyes(pydantic_events, invoices)
    flagged_vendors = {f.evidence.get("vendor_id") for f in findings}

    bec_truth_vendors = set(
        events.loc[events["fraud_type"] == FraudType.BEC_IBAN_SWAP.value, "vendor_id"]
    )
    tp = len(flagged_vendors & bec_truth_vendors)
    fp = len(flagged_vendors - bec_truth_vendors)
    fn = len(bec_truth_vendors - flagged_vendors)
    p, r, f1 = _f1(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def evaluate_sanctions(invoices: pd.DataFrame) -> dict:
    """Test illustratif : on ajoute un fournisseur sanctionné connu.

    Le snapshot embarqué contient des entités fictives ; pour mesurer F1 réel,
    on injecte 3 factures avec un nom matching et on vérifie la détection.
    """
    fake_invoices = pd.DataFrame(
        [
            {
                "invoice_id": "FAKE-1",
                "vendor_name": "Acme Energy Holdings Ltd",
                "amount": 12_000.0,
                "siren": "999999999",
                "iban": "FR7600000000000000000000000",
                "invoice_date": "2025-06-01",
            },
            {
                "invoice_id": "FAKE-2",
                "vendor_name": "Acme Energy Holdings Ltd",
                "amount": 5_000.0,
                "siren": "999999999",
                "iban": "FR7600000000000000000000000",
                "invoice_date": "2025-06-15",
            },
            {
                "invoice_id": "FAKE-3",
                "vendor_name": "Jean-Pierre Dubois",
                "amount": 1_500.0,
                "siren": "999999998",
                "iban": "FR7600000000000000000000001",
                "invoice_date": "2025-06-20",
            },
        ]
    )
    combined = pd.concat([invoices, fake_invoices], ignore_index=True)
    client = SanctionsClient()
    findings = detectors_sanctions.detect_sanctioned_vendors(combined, client=client)

    flagged = {f.invoice_id for f in findings}
    expected_critical = {"FAKE-1", "FAKE-2"}
    expected_pep = {"FAKE-3"}

    tp = len(flagged & (expected_critical | expected_pep))
    fp = len(flagged - (expected_critical | expected_pep))
    fn = len((expected_critical | expected_pep) - flagged)
    p, r, f1 = _f1(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark F1 par détecteur")
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--vendors", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("docs/benchmark_results.json"))
    args = parser.parse_args()

    cfg = GeneratorConfig(n_invoices=args.rows, n_vendors=args.vendors, seed=args.seed)
    print(f"\n=== Benchmark F1 (seed={args.seed}, rows={args.rows:,}) ===\n")
    invoices, vendors = generate_dataset(cfg)
    invoices = attach_vendor_ids(invoices, vendors)
    events = generate_master_data_events(
        invoices,
        vendors,
        MasterDataEventsConfig(
            n_bec_swaps=int(args.rows * 0.001),
            n_dormant_reactivations=int(args.rows * 0.0005),
            n_name_iban_same_day=int(args.rows * 0.0003),
            n_legitimate_changes=int(args.rows * 0.005),
            seed=args.seed,
        ),
    )

    results = {
        "config": {
            "rows": args.rows,
            "vendors": args.vendors,
            "seed": args.seed,
        },
        "duplicates": evaluate_duplicates(invoices),
        "thresholds": evaluate_thresholds(invoices),
        "master_data_iban_no_4eyes": evaluate_master_data(events, invoices),
        "sanctions": evaluate_sanctions(invoices),
    }

    print("| Détecteur | TP | FP | FN | Précision | Rappel | F1 |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for label, key in (
        ("Doublons (exact + fuzzy)", "duplicates"),
        ("Sous-seuils", "thresholds"),
        ("Master data — IBAN no 4-eyes", "master_data_iban_no_4eyes"),
        ("Sanctions / PEP", "sanctions"),
    ):
        m = results[key]
        print(
            f"| {label} | {m['tp']} | {m['fp']} | {m['fn']} | "
            f"{m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} |"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nRésultats : {args.output}")


if __name__ == "__main__":
    main()
