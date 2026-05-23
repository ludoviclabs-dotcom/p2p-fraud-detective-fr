"""Règle RUM_MISMATCH — RUM du prélèvement absente ou inconnue.

Cas couverts :
1. Le prélèvement porte une RUM mais aucun mandat actif ne la connaît (un
   mandat existe pour IBAN+ICS mais avec une autre RUM) — typique d'un
   créancier qui réutilise un IBAN pour un client différent (BEC).
2. Le prélèvement n'a pas de RUM du tout (warning RUM_MISSING) — situation
   moins grave mais qui mérite vigilance.
"""

from __future__ import annotations

from typing import Final

from p2p_fraud.risk_core.types import RiskDomain, RiskSignal, Severity
from p2p_fraud.sepa.matcher import MatchWarning
from p2p_fraud.sepa.rules.context import SepaRiskContext


class RumMismatchRule:
    """Déclenche en cas de RUM divergente ou manquante."""

    id: Final[str] = "RUM_MISMATCH"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SEPA_DIRECT_DEBIT

    def evaluate(self, ctx: SepaRiskContext) -> list[RiskSignal]:
        # Cas 1 : event a une RUM, candidats sans RUM existent (= mismatch)
        if (
            ctx.event.rum
            and ctx.match.mandate is None
            and ctx.match.candidates
        ):
            other_rums = sorted({c.rum for c in ctx.match.candidates if c.rum})
            return [
                RiskSignal(
                    code=self.id,
                    title="RUM divergente",
                    message=(
                        "La RUM portée par le prélèvement diffère de celle des "
                        "mandats actifs connus pour ce couple IBAN/ICS."
                    ),
                    severity=Severity.HIGH,
                    score=55,
                    evidence={
                        "event_id": ctx.event.event_id,
                        "event_rum": ctx.event.rum,
                        "known_active_rums": other_rums[:5],
                    },
                )
            ]
        # Cas 2 : event sans RUM (warning du matcher)
        if MatchWarning.RUM_MISSING in ctx.match.warnings:
            return [
                RiskSignal(
                    code=self.id,
                    title="RUM manquante",
                    message=(
                        "Aucune RUM n'a été fournie avec le prélèvement — "
                        "appariement au mandat moins fiable."
                    ),
                    severity=Severity.MEDIUM,
                    score=20,
                    evidence={
                        "event_id": ctx.event.event_id,
                        "matched_active": ctx.has_active_mandate,
                    },
                )
            ]
        return []
