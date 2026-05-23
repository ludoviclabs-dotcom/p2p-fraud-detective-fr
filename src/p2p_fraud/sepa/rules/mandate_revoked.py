"""Règle MANDATE_REVOKED — prélèvement reçu après révocation du mandat.

C'est l'un des cas les plus graves : le créancier continue à prélever malgré
la révocation. Le débiteur a un droit de contestation immédiat (jusqu'à 13
mois en SDD CORE en cas de mandat invalide).
"""

from __future__ import annotations

from typing import Final

from p2p_fraud.risk_core.types import RiskDomain, RiskSignal, Severity
from p2p_fraud.sepa.rules.context import SepaRiskContext


class MandateRevokedRule:
    """Déclenche si un mandat REVOKED matche le prélèvement."""

    id: Final[str] = "MANDATE_REVOKED"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SEPA_DIRECT_DEBIT

    def evaluate(self, ctx: SepaRiskContext) -> list[RiskSignal]:
        revoked = ctx.revoked_candidates
        if not revoked:
            return []
        first = revoked[0]
        return [
            RiskSignal(
                code=self.id,
                title="Mandat révoqué",
                message=(
                    "Le mandat correspondant a été révoqué avant ce prélèvement. "
                    "Le créancier ne devrait plus émettre de débit."
                ),
                severity=Severity.CRITICAL,
                score=75,
                evidence={
                    "event_id": ctx.event.event_id,
                    "mandate_id": first.mandate_id,
                    "rum": first.rum,
                    "creditor_ics": first.creditor_ics,
                    "revoked_at": first.revoked_at,
                    "n_revoked_candidates": len(revoked),
                },
            )
        ]
