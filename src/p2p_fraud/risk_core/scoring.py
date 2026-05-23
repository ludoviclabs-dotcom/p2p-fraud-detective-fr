"""Combinaison de signaux → score → niveau → décision.

Le score consolidé du Risk Core suit la spec MandateGuard §06 :
- score = somme bornée à [0, 100] des `signal.score`
- level dérivé soit par seuil sur le score, soit forcé à CRITICAL si au moins
  un signal critical est présent
- decision dérivée du couple (score, présence de critical)

Ce scoring est **différent** de celui de `scoring.risk_engine.aggregate_findings`
qui pondère par détecteur (P2P historique). Le Risk Core utilise le score
déjà calibré par chaque règle — plus simple, plus explicable, et plus
facilement portable entre domaines (SEPA n'a pas la notion de "détecteur").
"""

from __future__ import annotations

from collections.abc import Iterable

from p2p_fraud.risk_core.types import RiskDecision, RiskLevel, RiskSignal, Severity


def combine_signals(signals: Iterable[RiskSignal]) -> int:
    """Somme bornée des `signal.score`.

    Si un signal a score=80 et un autre 30, le total est 100 (cap). Cette
    règle simple est délibérée — la calibration du score se fait au niveau
    de chaque règle, pas du moteur (spec §06).
    """
    raw = sum(s.score for s in signals)
    return max(0, min(100, raw))


def to_level(score: int, signals: Iterable[RiskSignal]) -> RiskLevel:
    """Dérive le niveau qualitatif.

    Un seul signal `critical` suffit à passer en `CRITICAL`, indépendamment
    du score — exigence d'auditabilité : un facteur disqualifiant (ex.
    `MANDATE_REVOKED`) ne doit pas être masqué par une moyenne.
    """
    sigs = list(signals)
    if any(s.severity == Severity.CRITICAL for s in sigs) or score >= 80:
        return RiskLevel.CRITICAL
    if score >= 60:
        return RiskLevel.HIGH
    if score >= 30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def decide(score: int, signals: Iterable[RiskSignal]) -> RiskDecision:
    """Décision recommandée — pas exécutoire, l'humain valide (ADR-0003)."""
    sigs = list(signals)
    has_critical = any(s.severity == Severity.CRITICAL for s in sigs)
    if has_critical and score >= 80:
        return RiskDecision.DISPUTE_READY
    if score >= 75:
        return RiskDecision.BLOCK_RECOMMENDED
    if score >= 60:
        return RiskDecision.REVIEW
    if score >= 30:
        return RiskDecision.ALERT_USER
    if score >= 15:
        return RiskDecision.ALLOW_MONITOR
    return RiskDecision.ALLOW
