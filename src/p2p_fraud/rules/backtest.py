"""Backtest d'une règle sur dataset labellisé (Phase 4, ADR-0007).

Mesure l'impact d'une règle AVANT son activation : volume d'alertes généré
et — quand le dataset porte un label `is_fraud` (synthétique avec ground
truth, ou verdicts de clôture de la boucle de feedback) — précision et taux
de faux positifs. C'est la condition (b) de la promotion d'une règle.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from p2p_fraud.rules.dsl import RuleSpec, evaluate


class BacktestSummary(BaseModel):
    n_records: int
    n_flagged: int
    alert_rate: float  # part du dataset qui déclencherait une alerte
    n_labeled: int  # records portant un label is_fraud
    n_true_positive: int
    n_false_positive: int
    precision: float | None  # None si aucun record flaggé labellisé
    sample_flagged_ids: list[str]  # extrait pour inspection humaine


def backtest_rule(
    rule: RuleSpec,
    records: list[Mapping[str, Any]],
    *,
    label_field: str = "is_fraud",
    id_field: str = "invoice_id",
    sample_size: int = 10,
) -> BacktestSummary:
    """Applique la règle au dataset et agrège l'impact."""
    n_flagged = 0
    n_labeled = 0
    n_tp = 0
    n_fp = 0
    sample: list[str] = []
    for record in records:
        labeled = label_field in record and record[label_field] is not None
        if labeled:
            n_labeled += 1
        if not evaluate(rule, record):
            continue
        n_flagged += 1
        if len(sample) < sample_size:
            sample.append(str(record.get(id_field, "?")))
        if labeled:
            if bool(record[label_field]):
                n_tp += 1
            else:
                n_fp += 1
    flagged_labeled = n_tp + n_fp
    return BacktestSummary(
        n_records=len(records),
        n_flagged=n_flagged,
        alert_rate=(n_flagged / len(records)) if records else 0.0,
        n_labeled=n_labeled,
        n_true_positive=n_tp,
        n_false_positive=n_fp,
        precision=(n_tp / flagged_labeled) if flagged_labeled else None,
        sample_flagged_ids=sample,
    )
