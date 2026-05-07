"""Moteur de risk score consolidé.

Combine tous les `Finding` produits par les détecteurs en un score 0-100 par facture
(et optionnellement par fournisseur). Les pondérations sont chargées depuis
`weights.yaml` et peuvent être surchargées à l'appel.

Formule :
    raw_score(invoice) = Σ_finding ( detector_weight × severity_multiplier )
    score = min(100, raw_score × normalisation)

La normalisation est calibrée pour qu'un finding CRITICAL d'un détecteur poids 1.0
contribue 60 points (le worst case `score=100` est atteint avec une combinaison de
plusieurs Findings critiques croisés).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

from p2p_fraud.schema import Contribution, Finding, RiskScore, Severity
from p2p_fraud.scoring.reason_codes import render_reason

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent / "weights.yaml"

_DEFAULT_DETECTOR_WEIGHTS: dict[str, float] = {
    "duplicates": 1.0,
    "thresholds": 0.7,
    "benford": 0.0,  # rétrogradé en outil de scoping (ADR-0002)
    "sirene": 1.2,
    "isolation_forest": 0.8,
    "graph": 1.5,
    "master_data": 1.5,
    "sanctions": 1.6,
}

_DEFAULT_SEVERITY_MULT: dict[Severity, float] = {
    Severity.LOW: 0.1,
    Severity.MEDIUM: 0.3,
    Severity.HIGH: 0.6,
    Severity.CRITICAL: 1.0,
}

_NORMALIZATION = 60.0  # 1 finding CRITICAL × détecteur poids 1.0 → 60 pts


def _load_weights(path: Path | None = None) -> tuple[dict[str, float], dict[Severity, float]]:
    p = path or DEFAULT_WEIGHTS_PATH
    if not p.exists():
        return _DEFAULT_DETECTOR_WEIGHTS, _DEFAULT_SEVERITY_MULT
    with p.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    detector_weights = {**_DEFAULT_DETECTOR_WEIGHTS, **(cfg.get("detector_weights") or {})}
    sev_raw = cfg.get("severity_multiplier") or {}
    severity_mult = {
        Severity.LOW: float(sev_raw.get("low", _DEFAULT_SEVERITY_MULT[Severity.LOW])),
        Severity.MEDIUM: float(sev_raw.get("medium", _DEFAULT_SEVERITY_MULT[Severity.MEDIUM])),
        Severity.HIGH: float(sev_raw.get("high", _DEFAULT_SEVERITY_MULT[Severity.HIGH])),
        Severity.CRITICAL: float(
            sev_raw.get("critical", _DEFAULT_SEVERITY_MULT[Severity.CRITICAL])
        ),
    }
    return detector_weights, severity_mult


def aggregate_findings(
    findings: list[Finding],
    *,
    weights_path: Path | None = None,
    detector_weights: dict[str, float] | None = None,
    severity_multiplier: dict[Severity, float] | None = None,
    with_explanations: bool = False,
    ml_enabled: bool = True,
) -> dict[str, RiskScore]:
    """Agrège une liste de Findings en RiskScore par invoice_id.

    Si `with_explanations=True`, alimente `RiskScore.contributions` (waterfall
    Sprint 4) et `RiskScore.reason_codes_fr` (phrases FR par finding).
    """
    detector_w, severity_m = _load_weights(weights_path)
    if detector_weights:
        detector_w = {**detector_w, **detector_weights}
    if severity_multiplier:
        severity_m = {**severity_m, **severity_multiplier}

    # Bascule ML (page Gouvernance / AI Act art. 50) : retire l'apport
    # Isolation Forest du score consolidé. Les autres détecteurs sont conservés.
    if not ml_enabled:
        detector_w = {**detector_w, "isolation_forest": 0.0}

    raw_score: dict[str, float] = defaultdict(float)
    breakdown: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts: dict[str, int] = defaultdict(int)
    contribs: dict[str, list[Contribution]] = defaultdict(list)
    reasons: dict[str, list[str]] = defaultdict(list)

    for f in findings:
        weight = detector_w.get(f.detector, 0.5)
        # Détecteurs avec poids 0 (ex. Benford depuis ADR-0002) : skip.
        # Évite que des centaines de findings de scoping polluent le score.
        if weight <= 0:
            continue
        sev_mult = severity_m.get(f.severity, 0.3)
        contribution = weight * sev_mult * _NORMALIZATION
        raw_score[f.invoice_id] += contribution
        breakdown[f.invoice_id][f.detector] += contribution
        counts[f.invoice_id] += 1
        if with_explanations:
            reason_fr = render_reason(f)
            contribs[f.invoice_id].append(
                Contribution(
                    detector=f.detector,
                    finding_rule_id=f.rule_id,
                    signal=f.signal,
                    severity=f.severity.value,
                    weight=weight,
                    severity_multiplier=sev_mult,
                    contribution=round(contribution, 2),
                    reason_fr=reason_fr,
                )
            )
            reasons[f.invoice_id].append(reason_fr)

    out: dict[str, RiskScore] = {}
    for invoice_id, total in raw_score.items():
        capped = min(100.0, total)
        invoice_contribs = contribs.get(invoice_id, [])
        if invoice_contribs and total > 0:
            for c in invoice_contribs:
                c.contribution_pct = round(c.contribution / total * 100, 1)
        out[invoice_id] = RiskScore(
            invoice_id=invoice_id,
            score=capped,
            findings_count=counts[invoice_id],
            breakdown={k: round(v, 2) for k, v in breakdown[invoice_id].items()},
            contributions=sorted(
                invoice_contribs, key=lambda c: c.contribution, reverse=True
            ),
            reason_codes_fr=reasons.get(invoice_id, []),
        )
    return out


def aggregate_findings_with_explanations(
    findings: list[Finding],
    *,
    weights_path: Path | None = None,
    detector_weights: dict[str, float] | None = None,
    severity_multiplier: dict[Severity, float] | None = None,
) -> dict[str, RiskScore]:
    """Wrapper conventionnel : `aggregate_findings(..., with_explanations=True)`."""
    return aggregate_findings(
        findings,
        weights_path=weights_path,
        detector_weights=detector_weights,
        severity_multiplier=severity_multiplier,
        with_explanations=True,
    )


def to_dataframe(scores: dict[str, RiskScore]) -> pd.DataFrame:
    """Convertit les scores en DataFrame triable, prêt pour export."""
    rows = [
        {
            "invoice_id": rs.invoice_id,
            "risk_score": rs.score,
            "findings_count": rs.findings_count,
            **{f"score_{k}": v for k, v in rs.breakdown.items()},
        }
        for rs in scores.values()
    ]
    df = pd.DataFrame(rows).fillna(0)
    return df.sort_values("risk_score", ascending=False).reset_index(drop=True)


def severity_band(score: float) -> str:
    """Étiquette qualitative pour la communication aux auditeurs."""
    if score >= 80:
        return "CRITIQUE"
    if score >= 50:
        return "ÉLEVÉ"
    if score >= 25:
        return "MOYEN"
    if score > 0:
        return "FAIBLE"
    return "AUCUN"
