"""Règles SEPA v0 — déterministes, explicables, testables en isolation.

Chacune implémente le protocole `risk_core.RiskRule` et produit zéro ou
plusieurs `RiskSignal` pour un `SepaRiskContext`.

Convention :
- ID = reason code canonique (mapping 1:1 vers `risk_core.reason_codes`)
- Version sémantique versionnée à chaque changement de logique
- Aucune I/O dans `evaluate` (lookup DB faits en amont par l'analyzer)
"""

from p2p_fraud.sepa.rules.amount_exceeds_limit import AmountExceedsLimitRule
from p2p_fraud.sepa.rules.context import SepaRiskContext
from p2p_fraud.sepa.rules.ics_mismatch import IcsMismatchRule
from p2p_fraud.sepa.rules.mandate_revoked import MandateRevokedRule
from p2p_fraud.sepa.rules.no_active_mandate import NoActiveMandateRule
from p2p_fraud.sepa.rules.rum_mismatch import RumMismatchRule
from p2p_fraud.sepa.rules.unusual_frequency import UnusualFrequencyRule

__all__ = [
    "AmountExceedsLimitRule",
    "IcsMismatchRule",
    "MandateRevokedRule",
    "NoActiveMandateRule",
    "RumMismatchRule",
    "SepaRiskContext",
    "UnusualFrequencyRule",
    "build_sepa_rules",
]


def build_sepa_rules() -> list:
    """Factory de l'ensemble des règles SEPA v0 dans l'ordre d'évaluation."""
    return [
        MandateRevokedRule(),
        NoActiveMandateRule(),
        AmountExceedsLimitRule(),
        RumMismatchRule(),
        IcsMismatchRule(),
        UnusualFrequencyRule(),
    ]
