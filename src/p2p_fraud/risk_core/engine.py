"""Moteur générique — exécute des `RiskRule` sur un contexte et produit un verdict.

Le moteur est volontairement minimaliste : il orchestre, ne décide pas. Toute
la logique métier est dans les règles. Cela permet de tester chaque règle en
isolation et de partager le moteur entre SEPA, P2P et futurs domaines.

Pas d'I/O dans le moteur : c'est au service applicatif appelant de :
- construire le contexte enrichi (lookup DB, etc.) ;
- persister le `RiskAssessmentResult` ;
- créer les alertes / evidence pack en aval.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from p2p_fraud.risk_core.rule import RiskRule
from p2p_fraud.risk_core.scoring import combine_signals, decide, to_level
from p2p_fraud.risk_core.types import RiskAssessmentResult, RiskDomain, RiskSignal

T = TypeVar("T")


class RiskEngine(Generic[T]):
    """Exécute un ensemble de règles homogènes (même domaine) sur un contexte.

    Toutes les règles doivent avoir le même `domain` que celui passé au
    constructeur. Le moteur garde le `engine_version` pour traçabilité.
    """

    def __init__(
        self,
        rules: Sequence[RiskRule[T]],
        *,
        engine_version: str,
        domain: RiskDomain,
    ) -> None:
        mismatched = [r for r in rules if r.domain != domain]
        if mismatched:
            ids = ", ".join(r.id for r in mismatched)
            raise ValueError(
                f"RiskEngine pour {domain.value} initialisé avec règles d'un autre domaine : {ids}"
            )
        self._rules: tuple[RiskRule[T], ...] = tuple(rules)
        self._engine_version = engine_version
        self._domain = domain

    @property
    def engine_version(self) -> str:
        return self._engine_version

    @property
    def domain(self) -> RiskDomain:
        return self._domain

    @property
    def rules(self) -> tuple[RiskRule[T], ...]:
        return self._rules

    def assess(self, ctx: T) -> RiskAssessmentResult:
        """Évalue toutes les règles séquentiellement et consolide le verdict."""
        signals: list[RiskSignal] = []
        for rule in self._rules:
            signals.extend(rule.evaluate(ctx))
        score = combine_signals(signals)
        level = to_level(score, signals)
        decision = decide(score, signals)
        return RiskAssessmentResult(
            domain=self._domain,
            score=score,
            level=level,
            decision=decision,
            signals=signals,
            engine_version=self._engine_version,
        )
