"""Règle ICS_MISMATCH — créancier divergent entre prélèvement et mandat matché.

En théorie le matcher exige déjà ICS égal, donc ce signal ne peut sortir
qu'en cas d'historique : le mandat matché actif a un ICS mais l'event avait
un ICS différent à l'origine (improbable via la pipeline standard, mais
possible si l'analyzer override le contexte). Cette règle existe surtout
pour les imports externes et le mode Risk Lab.
"""

from __future__ import annotations

from typing import Final

from p2p_fraud.risk_core.types import RiskDomain, RiskSignal, Severity
from p2p_fraud.sepa.rules.context import SepaRiskContext


class IcsMismatchRule:
    """Déclenche si event.creditor_ics != mandate.creditor_ics."""

    id: Final[str] = "ICS_MISMATCH"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SEPA_DIRECT_DEBIT

    def evaluate(self, ctx: SepaRiskContext) -> list[RiskSignal]:
        mandate = ctx.matched_mandate
        if mandate is None or not ctx.event.creditor_ics:
            return []
        if mandate.creditor_ics == ctx.event.creditor_ics:
            return []
        return [
            RiskSignal(
                code=self.id,
                title="ICS différent du mandat",
                message=(
                    "L'ICS du créancier diffère de celui enregistré dans le "
                    "mandat — vérifier l'identité du créancier."
                ),
                severity=Severity.CRITICAL,
                score=80,
                evidence={
                    "event_id": ctx.event.event_id,
                    "mandate_id": mandate.mandate_id,
                    "event_ics": ctx.event.creditor_ics,
                    "mandate_ics": mandate.creditor_ics,
                },
            )
        ]
