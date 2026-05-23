"""Convertisseur `schema.Finding` → `risk_core.RiskSignal`.

Réutilise le `reason_codes` Risk Core pour récupérer le titre et la sévérité
par défaut. Si le `rule_id` du Finding n'est pas dans le registre canonique,
fallback sur un titre générique sans crasher (exigence UX).
"""

from __future__ import annotations

from p2p_fraud.risk_core.reason_codes import get_reason_code_meta
from p2p_fraud.risk_core.types import RiskSignal, Severity
from p2p_fraud.schema import Finding
from p2p_fraud.scoring.reason_codes import render_reason

# Calibration des scores par sévérité (spec MandateGuard §06, tables SEPA/P2P v0).
# CRITICAL : 80 = à un cheveu du seuil DISPUTE_READY (≥80 + critical).
# HIGH     : 50 = REVIEW (≥60 nécessite cumul de signaux).
# MEDIUM   : 25 = ALERT_USER (≥30 nécessite cumul).
# LOW      : 8  = ALLOW_MONITOR (≥15 nécessite cumul).
DEFAULT_SCORE_BY_SEVERITY: dict[Severity, int] = {
    Severity.CRITICAL: 80,
    Severity.HIGH: 50,
    Severity.MEDIUM: 25,
    Severity.LOW: 8,
}


def finding_to_signal(
    finding: Finding,
    *,
    score_by_severity: dict[Severity, int] | None = None,
    rule_id_to_code: dict[str, str] | None = None,
) -> RiskSignal:
    """Convertit un Finding en RiskSignal.

    - `score_by_severity` permet à un adapter de re-calibrer (ex. un détecteur
      de poids élevé peut booster ses scores).
    - `rule_id_to_code` permet de re-mapper un `rule_id` legacy vers un code
      canonique du registre Risk Core.
    """
    scores = score_by_severity or DEFAULT_SCORE_BY_SEVERITY
    code = (rule_id_to_code or {}).get(finding.rule_id, finding.rule_id)
    meta = get_reason_code_meta(code)
    title = meta.title_fr if meta else f"{finding.detector} — {finding.signal}"
    message = render_reason(finding)
    score = scores.get(finding.severity, DEFAULT_SCORE_BY_SEVERITY[finding.severity])
    return RiskSignal(
        code=code,
        title=title,
        message=message,
        severity=finding.severity,
        score=score,
        evidence=dict(finding.evidence) if finding.evidence else {},
    )
