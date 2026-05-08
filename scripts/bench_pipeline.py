"""Benchmark end-to-end du pipeline de détection sur dataset synthétique.

Usage :
    python scripts/bench_pipeline.py --rows 50000 --vendors 5000 --seed 42

Mesure :
- temps de génération du dataset,
- temps de chaque détecteur (Benford, doublons exact + fuzzy, sous-seuils,
  master data, sanctions, isolation forest, graphe),
- temps d'agrégation risk_engine,
- nombre de findings et score consolidé moyen.

Reproduisable via Makefile : `make bench`.
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pandas as pd

from p2p_fraud.detectors import duplicates as detectors_dup
from p2p_fraud.detectors import isolation_forest as detectors_if
from p2p_fraud.detectors import master_data_changes as detectors_md
from p2p_fraud.detectors import sanctions as detectors_sanctions
from p2p_fraud.detectors import thresholds as detectors_thresholds
from p2p_fraud.enrichment.sanctions_client import SanctionsClient
from p2p_fraud.schema import VendorMasterEvent
from p2p_fraud.scoring.risk_engine import aggregate_findings_with_explanations
from p2p_fraud.synthetic.generator import (
    GeneratorConfig,
    MasterDataEventsConfig,
    attach_vendor_ids,
    generate_dataset,
    generate_master_data_events,
)


@contextmanager
def _timer(label: str, results: dict) -> Iterator[None]:
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    results[label] = round(elapsed, 4)
    print(f"  {label:30s} {elapsed:8.3f} s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark pipeline P2P Fraud Detective")
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--vendors", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-iforest", action="store_true")
    args = parser.parse_args()

    print(f"\n=== Benchmark P2P Fraud Detective FR (rows={args.rows:,} seed={args.seed}) ===\n")
    results: dict[str, float] = {}

    with _timer("generate_dataset", results):
        cfg = GeneratorConfig(n_invoices=args.rows, n_vendors=args.vendors, seed=args.seed)
        invoices, vendors = generate_dataset(cfg)

    with _timer("attach_vendor_ids", results):
        invoices = attach_vendor_ids(invoices, vendors)

    with _timer("master_data_events_gen", results):
        events_df = generate_master_data_events(
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

    findings: list = []

    with _timer("detect_duplicates", results):
        findings.extend(detectors_dup.detect_duplicates(invoices))

    with _timer("detect_thresholds", results):
        findings.extend(detectors_thresholds.detect_under_threshold(invoices))

    with _timer("detect_master_data", results):
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
            for _, row in events_df.iterrows()
        ]
        findings.extend(detectors_md.run_all(pydantic_events, invoices))

    with _timer("detect_sanctions", results):
        client = SanctionsClient()
        findings.extend(detectors_sanctions.detect_sanctioned_vendors(invoices, client=client))

    if not args.skip_iforest:
        with _timer("detect_isolation_forest", results):
            iforest_findings, _ = detectors_if.detect_anomalies(invoices)
            findings.extend(iforest_findings)

    with _timer("aggregate_findings", results):
        scores = aggregate_findings_with_explanations(findings)

    print()
    print(f"  total findings              {len(findings):>10,}")
    print(f"  scored invoices             {len(scores):>10,}")
    if scores:
        avg = sum(s.score for s in scores.values()) / len(scores)
        max_s = max(s.score for s in scores.values())
        print(f"  avg score (scored only)    {avg:>10.2f}")
        print(f"  max score                  {max_s:>10.2f}")

    total = sum(results.values())
    print(f"\n  TOTAL                       {total:>10.3f} s\n")


if __name__ == "__main__":
    main()
