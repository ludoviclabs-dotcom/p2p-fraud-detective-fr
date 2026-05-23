"""Protocole `RiskRule[TContext]` — interface commune de toute règle déterministe.

Implémenter une règle = créer une classe ou un objet (dataclass/Pydantic/
classe simple) avec :
- `id` : identifiant unique stable (= reason code).
- `version` : version sémantique (incrémentée à tout changement de logique).
- `domain` : RiskDomain auquel s'applique la règle.
- `evaluate(ctx)` : retourne une liste de `RiskSignal` (vide si non déclenchée).

`TContext` reste typé côté implémentation (chaque domaine définit son propre
contexte enrichi : `SepaRiskContext`, `SupplierPaymentContext`, etc.).
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from p2p_fraud.risk_core.types import RiskDomain, RiskSignal

TContext = TypeVar("TContext", contravariant=True)


@runtime_checkable
class RiskRule(Protocol[TContext]):
    """Protocole structurel d'une règle de risque déterministe."""

    id: str
    version: str
    domain: RiskDomain

    def evaluate(self, ctx: TContext) -> list[RiskSignal]:
        """Évalue la règle sur le contexte et retourne 0..N signaux.

        Doit être **pure** : pas d'I/O, pas d'effet de bord. Les enrichissements
        (DB lookup, appels API) sont réalisés en amont par le service applicatif
        qui construit `ctx`. Cela garantit la testabilité et la rejouabilité.
        """
        ...
