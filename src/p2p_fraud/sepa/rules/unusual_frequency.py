"""Règle UNUSUAL_FREQUENCY — cadence anormale de prélèvements.

Heuristique simple en v0 : si on observe >= N prélèvements du même créancier
sur le même IBAN débiteur dans une fenêtre courte (ex. >= 3 sur 7 jours
glissants), signal HIGH. Le seuil est volontairement strict pour limiter les
faux positifs sur les mandats légitimes hebdomadaires.

Affinements futurs (v1) :
- comparer à la `frequency` déclarée du mandat
- détecter `MULTIPLE_SMALL_DEBITS` séparément
- pondérer par `sequence_type` (FRST vs RCUR)
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from p2p_fraud.risk_core.types import RiskDomain, RiskSignal, Severity
from p2p_fraud.sepa.rules.context import SepaRiskContext

DEFAULT_WINDOW_DAYS = 7
DEFAULT_DEBITS_THRESHOLD = 3


class UnusualFrequencyRule:
    """Déclenche si >= `threshold` débits du même créancier dans la fenêtre."""

    id: Final[str] = "UNUSUAL_FREQUENCY"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SEPA_DIRECT_DEBIT

    def __init__(
        self,
        *,
        window_days: int = DEFAULT_WINDOW_DAYS,
        threshold: int = DEFAULT_DEBITS_THRESHOLD,
    ) -> None:
        self._window_days = window_days
        self._threshold = threshold

    def evaluate(self, ctx: SepaRiskContext) -> list[RiskSignal]:
        if not ctx.recent_debits:
            return []
        ics = ctx.event.creditor_ics
        fp = ctx.event.debtor_iban_fingerprint
        window_start = ctx.now - timedelta(days=self._window_days)

        same_axis = [
            d
            for d in ctx.recent_debits
            if d.creditor_ics == ics
            and d.debtor_iban_fingerprint == fp
            and d.event_id != ctx.event.event_id
        ]
        # Filtrage temporel : on accepte les debits sans booking_date (compté)
        # pour rester conservateur — un volume soudain doit toujours sortir.
        recent_count = 0
        for d in same_axis:
            if d.booking_date is None:
                recent_count += 1
                continue
            try:
                bd = d.booking_date
                # accepts ISO date or datetime
                if "T" in bd:
                    from datetime import datetime

                    parsed = datetime.fromisoformat(bd)
                else:
                    from datetime import date as _date

                    parsed_d = _date.fromisoformat(bd)
                    from datetime import UTC, datetime

                    parsed = datetime.combine(parsed_d, datetime.min.time(), UTC)
                if parsed >= window_start:
                    recent_count += 1
            except ValueError:
                recent_count += 1  # conservateur

        if recent_count + 1 < self._threshold:  # +1 = l'événement courant
            return []
        return [
            RiskSignal(
                code=self.id,
                title="Fréquence inhabituelle",
                message=(
                    "Plusieurs prélèvements de ce créancier observés sur cette "
                    "fenêtre — cadence atypique par rapport à la périodicité "
                    "normale d'un mandat SDD."
                ),
                severity=Severity.HIGH,
                score=45,
                evidence={
                    "event_id": ctx.event.event_id,
                    "creditor_ics": ics,
                    "window_days": self._window_days,
                    "threshold": self._threshold,
                    "observed_count": recent_count + 1,
                },
            )
        ]
