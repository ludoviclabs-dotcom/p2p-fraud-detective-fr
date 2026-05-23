"""Risk Core — abstraction commune SEPA + P2P + futurs domaines de risque.

Ce package fournit les primitives partagées qui permettent à n'importe quel
domaine (prélèvement SEPA entrant, paiement fournisseur sortant, transfert
P2P, paiement QR…) de produire un score, des reason codes et une décision
explicables — selon les conventions du dossier MandateGuard.

Trois primitives clés :

- `RiskRule[TContext]` : protocole d'une règle déterministe — `evaluate(ctx)`
  retourne une liste de `RiskSignal`. Une règle = un reason code = un test
  unitaire dédié.
- `RiskEngine[TContext]` : exécute un ensemble de règles sur un contexte,
  combine les signaux en score (0-100), dérive un niveau et une décision.
- `RiskAssessmentResult` : enveloppe immuable du verdict, incluant la
  `engine_version` pour permettre la rejouabilité d'un Evidence Pack.

Les implémentations P2P existantes (`scoring/risk_engine.py`,
`detectors/*`) ne sont pas remplacées — `risk_core` est une couche additive
qui les rend appelables comme des `RiskRule` via les adapters
(`risk_core.adapters.p2p`). C'est ce qui permettra de partager un même
moteur (et un même Evidence Pack) avec le module SEPA à venir.
"""

from p2p_fraud.risk_core.engine import RiskEngine
from p2p_fraud.risk_core.rule import RiskRule
from p2p_fraud.risk_core.scoring import combine_signals, decide, to_level
from p2p_fraud.risk_core.types import (
    RiskAssessmentResult,
    RiskDecision,
    RiskDomain,
    RiskLevel,
    RiskSignal,
    Severity,
)

__all__ = [
    "RiskAssessmentResult",
    "RiskDecision",
    "RiskDomain",
    "RiskEngine",
    "RiskLevel",
    "RiskRule",
    "RiskSignal",
    "Severity",
    "combine_signals",
    "decide",
    "to_level",
]
