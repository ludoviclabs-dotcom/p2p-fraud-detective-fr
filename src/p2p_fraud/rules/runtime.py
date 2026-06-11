"""Exécution runtime des règles actives du Detection Studio (ADR-0007).

Chaînon entre le store versionné (`rules/store.py`) et le pipeline de
détection : les règles au statut `active` — donc passées par tests verts,
backtest et 4-eyes — sont appliquées aux factures entrantes et produisent
des `Finding` standard (detector "rule_studio"), agrégés dans le risk score
comme ceux des détecteurs codés en dur.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from p2p_fraud.rules.dsl import evaluate
from p2p_fraud.rules.store import RuleStore, RuleVersion
from p2p_fraud.schema import Finding, Severity

DETECTOR_NAME = "rule_studio"

_SEVERITY_MAP = {
    "low": Severity.LOW,
    "medium": Severity.MEDIUM,
    "high": Severity.HIGH,
    "critical": Severity.CRITICAL,
}


def active_rules(store: RuleStore) -> list[RuleVersion]:
    """Versions actuellement actives (une au plus par rule_id, par construction)."""
    return [v for v in store.list_versions() if v.status == "active"]


def run_active_rules(
    records: list[Mapping[str, Any]],
    store: RuleStore,
    *,
    id_field: str = "invoice_id",
) -> list[Finding]:
    """Applique toutes les règles actives à un lot de records → Findings."""
    findings: list[Finding] = []
    for version in active_rules(store):
        spec = version.spec
        severity = _SEVERITY_MAP.get(spec.severity, Severity.MEDIUM)
        for i, record in enumerate(records):
            if not evaluate(spec, record):
                continue
            findings.append(
                Finding(
                    invoice_id=str(record.get(id_field, i)),
                    detector=DETECTOR_NAME,
                    rule_id=spec.rule_id,
                    signal=spec.name,
                    severity=severity,
                    evidence={
                        "reason_code": spec.reason_code,
                        "rule_version": version.version,
                        "approved_by": version.approved_by,
                    },
                )
            )
    return findings


def dataframe_to_records(df) -> list[dict[str, Any]]:
    """DataFrame → records avec NaN normalisés en None (évaluation fail-safe)."""
    return [
        {k: (None if (isinstance(v, float) and v != v) else v) for k, v in row.items()}
        for row in df.to_dict("records")
    ]
