"""Export a sanitized P2P graph demo dataset for the Vercel/Next.js app."""

from __future__ import annotations

import argparse
from pathlib import Path

from p2p_fraud.services.p2p_graph_demo import (
    DEFAULT_INVOICES,
    DEFAULT_OUTPUT,
    DEFAULT_VENDORS,
    build_dataset,
    export_dataset,
    mask_iban,
    normalize_key,
    read_invoices,
    read_vendors,
    sanitize_evidence,
    stable_hash,
)

__all__ = [
    "DEFAULT_INVOICES",
    "DEFAULT_OUTPUT",
    "DEFAULT_VENDORS",
    "build_dataset",
    "export_dataset",
    "mask_iban",
    "normalize_key",
    "read_invoices",
    "read_vendors",
    "sanitize_evidence",
    "stable_hash",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invoices", type=Path, default=DEFAULT_INVOICES)
    parser.add_argument("--vendors", type=Path, default=DEFAULT_VENDORS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cluster-min-size", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = export_dataset(
        invoices_path=args.invoices,
        vendors_path=args.vendors,
        output_path=args.output,
        cluster_min_size=args.cluster_min_size,
    )
    print(
        "[OK] exported "
        f"{len(dataset['nodes'])} nodes / {len(dataset['edges'])} edges / "
        f"{len(dataset['findings'])} findings -> {args.output}"
    )


if __name__ == "__main__":
    main()
