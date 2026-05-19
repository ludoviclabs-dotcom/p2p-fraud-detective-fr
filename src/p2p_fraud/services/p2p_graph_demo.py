"""Public-safe P2P graph dataset builder.

The Next.js graph demo and the FastAPI `/api/v1/graph` endpoint share this
module so the static Vercel payload and the future API payload keep the same
contract.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from p2p_fraud.detectors.duplicates import detect_duplicates
from p2p_fraud.detectors.graph import _normalize_iban, detect_fraud_rings
from p2p_fraud.detectors.thresholds import detect_under_threshold
from p2p_fraud.schema import Finding, Severity

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INVOICES = REPO_ROOT / "data" / "samples" / "sample_5k.csv"
DEFAULT_VENDORS = REPO_ROOT / "data" / "samples" / "vendors_sample_5k.csv"
DEFAULT_OUTPUT = REPO_ROOT / "apps" / "web" / "data" / "p2p-demo.json"

SEVERITY_RISK_SCORE = {
    Severity.LOW: 20,
    Severity.MEDIUM: 45,
    Severity.HIGH: 70,
    Severity.CRITICAL: 95,
}

SEVERITY_RANK = {
    Severity.LOW.value: 1,
    Severity.MEDIUM.value: 2,
    Severity.HIGH.value: 3,
    Severity.CRITICAL.value: 4,
}

DEMO_SIGNAL_CAPS = {
    "shared_iban_ring": 140,
    "vendor_cluster": 50,
    "duplicate_exact": 40,
    "duplicate_fuzzy": 120,
    "amount_just_under_threshold": 110,
}

DEMO_SIGNAL_ORDER = tuple(DEMO_SIGNAL_CAPS)


def stable_hash(value: str, *, length: int = 12) -> str:
    """Return a short stable SHA-256 hash for public identifiers."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def normalize_key(value: str | None) -> str:
    """Small slug helper used only for display-safe IDs."""
    if not value:
        return "unknown"
    raw = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return raw[:48] or "unknown"


def mask_iban(value: str | None) -> str | None:
    """Mask an IBAN while preserving enough shape for investigation UX."""
    normalized = _normalize_iban(value)
    if not normalized:
        return None
    if len(normalized) <= 10:
        return f"{normalized[:2]}****{normalized[-2:]}"
    return f"{normalized[:4]}********{normalized[-4:]}"


def sanitize_evidence(value: Any) -> Any:
    """Remove raw bank details recursively from detector evidence."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_lower = str(key).lower()
            if "iban" in key_lower:
                if item is None:
                    out[key] = None
                elif isinstance(item, list):
                    out[key] = [mask_iban(str(v)) for v in item]
                else:
                    out[key] = mask_iban(str(item))
            else:
                out[key] = sanitize_evidence(item)
        return out
    if isinstance(value, list):
        return [sanitize_evidence(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_evidence(item) for item in value]
    return value


def strongest_severity(current: str | None, candidate: str | None) -> str | None:
    if current is None:
        return candidate
    if candidate is None:
        return current
    if SEVERITY_RANK.get(candidate, 0) > SEVERITY_RANK.get(current, 0):
        return candidate
    return current


def read_invoices(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in ("invoice_date", "posting_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def read_vendors(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def vendor_lookup(vendors: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if vendors.empty or "vendor_name" not in vendors.columns:
        return {}
    return {
        str(row["vendor_name"]): {
            "vendorId": str(row.get("vendor_id") or normalize_key(str(row["vendor_name"]))),
            "siren": str(row.get("siren") or ""),
            "apeCode": str(row.get("ape_code") or ""),
            "address": str(row.get("address") or ""),
        }
        for _, row in vendors.iterrows()
    }


def finding_id(finding: Finding, index: int) -> str:
    raw = f"{finding.invoice_id}|{finding.rule_id}|{finding.signal}|{index}"
    return f"finding:{stable_hash(raw, length=16)}"


def invoice_amount(invoice_rows: dict[str, pd.Series], invoice_id: str) -> float:
    row = invoice_rows.get(str(invoice_id))
    if row is None:
        return 0.0
    return float(row.get("amount") or 0)


def select_demo_findings(
    findings: list[Finding],
    invoice_rows: dict[str, pd.Series],
    *,
    max_findings: int,
) -> list[Finding]:
    """Keep the public demo balanced across real detector signals."""
    selected: list[Finding] = []
    selected_keys: set[str] = set()

    def selection_key(finding: Finding) -> str:
        evidence_hash = stable_hash(
            json.dumps(finding.evidence, sort_keys=True, default=str),
            length=12,
        )
        return f"{finding.invoice_id}|{finding.rule_id}|{finding.signal}|{evidence_hash}"

    def sort_key(finding: Finding) -> tuple[int, float, str]:
        return (
            SEVERITY_RISK_SCORE.get(finding.severity, 0),
            invoice_amount(invoice_rows, finding.invoice_id),
            str(finding.invoice_id),
        )

    def append_unique(bucket: list[Finding], cap: int) -> None:
        for finding in sorted(bucket, key=sort_key, reverse=True)[:cap]:
            key = selection_key(finding)
            if key in selected_keys:
                continue
            selected.append(finding)
            selected_keys.add(key)

    for signal in DEMO_SIGNAL_ORDER:
        signal_findings = [finding for finding in findings if finding.signal == signal]
        append_unique(signal_findings, DEMO_SIGNAL_CAPS[signal])

    remaining = [
        finding
        for finding in findings
        if finding.signal not in DEMO_SIGNAL_CAPS and selection_key(finding) not in selected_keys
    ]
    append_unique(remaining, max(0, max_findings - len(selected)))

    return selected[:max_findings]


def build_dataset(
    invoices: pd.DataFrame,
    vendors: pd.DataFrame,
    *,
    cluster_min_size: int = 3,
    max_findings: int = 420,
) -> dict[str, Any]:
    vendor_meta = vendor_lookup(vendors)
    invoice_rows = {
        str(row["invoice_id"]): row
        for _, row in invoices.iterrows()
        if "invoice_id" in row and not pd.isna(row["invoice_id"])
    }
    graph_findings, analysis = detect_fraud_rings(invoices, cluster_min_size=cluster_min_size)
    raw_findings = [
        *graph_findings,
        *detect_duplicates(invoices),
        *detect_under_threshold(invoices),
    ]
    findings = select_demo_findings(
        raw_findings,
        invoice_rows,
        max_findings=max_findings,
    )

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    finding_summaries: list[dict[str, Any]] = []
    vendor_summaries: dict[str, dict[str, Any]] = {}

    def add_node(node: dict[str, Any]) -> None:
        existing = nodes.get(node["id"])
        if existing is None:
            nodes[node["id"]] = node
            return
        existing["riskScore"] = max(existing.get("riskScore") or 0, node.get("riskScore") or 0)
        existing["exposureEur"] = round(
            float(existing.get("exposureEur") or 0) + float(node.get("exposureEur") or 0),
            2,
        )
        existing["severity"] = strongest_severity(existing.get("severity"), node.get("severity"))

    def add_edge(edge: dict[str, Any]) -> None:
        key = f"{edge['source']}->{edge['target']}:{edge['kind']}"
        if key not in edges:
            edges[key] = edge
            return
        edges[key]["weight"] = float(edges[key].get("weight") or 1) + float(edge.get("weight") or 1)
        merged = {*(edges[key].get("findingIds") or []), *(edge.get("findingIds") or [])}
        edges[key]["findingIds"] = sorted(merged)

    for index, finding in enumerate(findings):
        row = invoice_rows.get(str(finding.invoice_id))
        vendor_name = str(row.get("vendor_name")) if row is not None else "Fournisseur inconnu"
        amount = float(row.get("amount") or 0) if row is not None else 0.0
        normalized_iban = _normalize_iban(row.get("iban") if row is not None else None)
        vendor_info = vendor_meta.get(vendor_name, {})
        vendor_id = str(vendor_info.get("vendorId") or f"vendor-{normalize_key(vendor_name)}")
        vendor_node_id = f"vendor:{stable_hash(vendor_name, length=14)}"
        iban_node_id = (
            f"iban:{stable_hash(normalized_iban, length=16)}" if normalized_iban else "iban:unknown"
        )
        fid = finding_id(finding, index)
        risk_score = SEVERITY_RISK_SCORE.get(finding.severity, 45)
        severity = finding.severity.value

        add_node(
            {
                "id": vendor_node_id,
                "kind": "vendor",
                "label": vendor_name,
                "severity": severity,
                "riskScore": risk_score,
                "exposureEur": amount,
                "maskedValue": vendor_info.get("siren") or None,
            }
        )
        add_node(
            {
                "id": iban_node_id,
                "kind": "iban",
                "label": mask_iban(normalized_iban) or "IBAN inconnu",
                "severity": severity,
                "riskScore": risk_score,
                "exposureEur": amount,
                "maskedValue": mask_iban(normalized_iban),
            }
        )
        add_node(
            {
                "id": fid,
                "kind": "finding",
                "label": finding.rule_id,
                "severity": severity,
                "riskScore": risk_score,
                "exposureEur": amount,
                "maskedValue": finding.invoice_id,
            }
        )

        add_edge(
            {
                "source": vendor_node_id,
                "target": iban_node_id,
                "kind": "uses_iban",
                "weight": 1,
                "findingIds": [fid],
            }
        )
        add_edge(
            {
                "source": vendor_node_id,
                "target": fid,
                "kind": "has_finding",
                "weight": 1,
                "findingIds": [fid],
            }
        )
        add_edge(
            {
                "source": iban_node_id,
                "target": fid,
                "kind": "evidences",
                "weight": 1,
                "findingIds": [fid],
            }
        )

        finding_summaries.append(
            {
                "id": fid,
                "invoiceId": finding.invoice_id,
                "vendorName": vendor_name,
                "vendorId": vendor_id,
                "ruleId": finding.rule_id,
                "severity": severity,
                "signal": finding.signal,
                "exposureEur": round(amount, 2),
                "riskScore": risk_score,
                "evidence": sanitize_evidence(finding.evidence),
            }
        )

        vendor_bucket = vendor_summaries.setdefault(
            vendor_node_id,
            {
                "id": vendor_node_id,
                "vendorId": vendor_id,
                "name": vendor_name,
                "siren": vendor_info.get("siren") or None,
                "apeCode": vendor_info.get("apeCode") or None,
                "severity": severity,
                "riskScore": risk_score,
                "exposureEur": 0.0,
                "findingIds": [],
            },
        )
        vendor_bucket["exposureEur"] = round(float(vendor_bucket["exposureEur"]) + amount, 2)
        vendor_bucket["riskScore"] = max(int(vendor_bucket["riskScore"]), int(risk_score))
        vendor_bucket["severity"] = strongest_severity(vendor_bucket["severity"], severity)
        vendor_bucket["findingIds"].append(fid)

    severities = pd.Series([f["severity"] for f in finding_summaries], dtype="object")
    signals = pd.Series([f["signal"] for f in finding_summaries], dtype="object")
    metrics = {
        "invoiceCount": len(invoices),
        "findingCount": len(finding_summaries),
        "vendorCount": int(sum(1 for n in nodes.values() if n["kind"] == "vendor")),
        "ibanNodeCount": int(sum(1 for n in nodes.values() if n["kind"] == "iban")),
        "edgeCount": len(edges),
        "sharedIbanRings": int(analysis.n_shared_iban_rings),
        "vendorClusters": int(analysis.n_vendor_clusters),
        "largestClusterSize": int(analysis.largest_cluster_size),
        "criticalFindings": int((severities == "critical").sum()) if not severities.empty else 0,
        "highFindings": int((severities == "high").sum()) if not severities.empty else 0,
        "mediumFindings": int((severities == "medium").sum()) if not severities.empty else 0,
        "signalCounts": signals.value_counts().sort_index().to_dict() if not signals.empty else {},
        "exposureEur": round(sum(float(f["exposureEur"]) for f in finding_summaries), 2),
    }

    return {
        "generatedAt": datetime.now(UTC).isoformat(),
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "findings": finding_summaries,
        "vendors": sorted(
            vendor_summaries.values(),
            key=lambda vendor: (vendor["riskScore"], vendor["exposureEur"]),
            reverse=True,
        ),
        "metrics": metrics,
    }


@lru_cache(maxsize=8)
def load_default_dataset(
    *,
    cluster_min_size: int = 3,
    max_findings: int = 420,
) -> dict[str, Any]:
    invoices = read_invoices(DEFAULT_INVOICES)
    vendors = read_vendors(DEFAULT_VENDORS)
    return build_dataset(
        invoices,
        vendors,
        cluster_min_size=cluster_min_size,
        max_findings=max_findings,
    )


def export_dataset(
    *,
    invoices_path: Path = DEFAULT_INVOICES,
    vendors_path: Path | None = DEFAULT_VENDORS,
    output_path: Path = DEFAULT_OUTPUT,
    cluster_min_size: int = 3,
) -> dict[str, Any]:
    invoices = read_invoices(invoices_path)
    vendors = read_vendors(vendors_path)
    dataset = build_dataset(invoices, vendors, cluster_min_size=cluster_min_size)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    return dataset
