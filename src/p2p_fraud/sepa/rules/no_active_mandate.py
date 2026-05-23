"""Règle NO_ACTIVE_MANDATE — aucun mandat actif ne correspond au prélèvement.

C'est le signal le plus critique du module SEPA : un débit observé alors
qu'aucun mandat n'autorise ce créancier à prélever ce débiteur. Cas typique :
prélèvement frauduleux ou mandat révoqué non synchronisé.

La règle ne déclenche PAS si un mandat REVOKED est trouvé (la règle dédiée
MANDATE_REVOKED prend le relais avec un message plus précis).
"""

from __future__ import annotations

from typing import Final

from p2p_fraud.risk_core.types import RiskDomain, RiskSignal, Severity
from p2p_fraud.sepa.rules.context import SepaRiskContext


class NoActiveMandateRule:
    """Déclenche si aucun mandat ACTIVE ne match ET aucun mandat REVOKED non plus."""

    id: Final[str] = "NO_ACTIVE_MANDATE"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SEPA_DIRECT_DEBIT

    def evaluate(self, ctx: SepaRiskContext) -> list[RiskSignal]:
        if ctx.has_active_mandate:
            return []
        # Si un mandat révoqué match, on laisse MandateRevokedRule produire
        # son signal dédié — pas de doublon.
        if ctx.revoked_candidates:
            return []
        evidence: dict = {
            "event_id": ctx.event.event_id,
            "creditor_ics": ctx.event.creditor_ics,
            "rum_present": ctx.event.rum is not None,
            "amount_cents": ctx.event.amount_cents,
            "currency": ctx.event.currency,
            "matcher_warnings": [w.value for w in ctx.match.warnings],
        }
        return [
            RiskSignal(
                code=self.id,
                title="Aucun mandat actif",
                message=(
                    "Ce prélèvement ne correspond à aucun mandat SEPA actif "
                    "connu pour ce couple (créancier, débiteur)."
                ),
                severity=Severity.CRITICAL,
                score=80,
                evidence=evidence,
            )
        ]
