"""Règle MANDATE_AMOUNT_EXCEEDED — débit supérieur au plafond du mandat.

Quand un mandat porte `max_amount_cents`, tout prélèvement dont le montant
dépasse cette valeur déclenche un signal critique. Le mandat reste actif
(la rule ne le révoque pas) mais une décision humaine est requise.
"""

from __future__ import annotations

from typing import Final

from p2p_fraud.risk_core.types import RiskDomain, RiskSignal, Severity
from p2p_fraud.sepa.rules.context import SepaRiskContext


class AmountExceedsLimitRule:
    """Déclenche si event.amount_cents > mandate.max_amount_cents."""

    id: Final[str] = "MANDATE_AMOUNT_EXCEEDED"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SEPA_DIRECT_DEBIT

    def evaluate(self, ctx: SepaRiskContext) -> list[RiskSignal]:
        mandate = ctx.matched_mandate
        if mandate is None or mandate.max_amount_cents is None:
            return []
        if ctx.event.amount_cents <= mandate.max_amount_cents:
            return []
        delta = ctx.event.amount_cents - mandate.max_amount_cents
        return [
            RiskSignal(
                code=self.id,
                title="Montant supérieur au plafond du mandat",
                message=(
                    "Le prélèvement dépasse le plafond enregistré sur le "
                    "mandat. Vérifier l'autorisation."
                ),
                severity=Severity.CRITICAL,
                score=70,
                evidence={
                    "event_id": ctx.event.event_id,
                    "mandate_id": mandate.mandate_id,
                    "amount_cents": ctx.event.amount_cents,
                    "max_amount_cents": mandate.max_amount_cents,
                    "currency": ctx.event.currency,
                    "delta_cents": delta,
                },
            )
        ]
