"""Contexte passé aux règles SEPA — construit par l'analyzer.

Toute l'I/O (lookup mandat actif, mandats révoqués, historique de prélèvements
récents) est faite en amont. Les règles ne consomment que ce contexte
immuable, ce qui les rend purement testables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from p2p_fraud.sepa.debit_event import DebitEventRecord
from p2p_fraud.sepa.mandate import MandateRecord
from p2p_fraud.sepa.matcher import MatchResult


@dataclass(frozen=True)
class SepaRiskContext:
    """Contexte d'évaluation des règles SEPA.

    Attributes:
        event: le prélèvement observé à évaluer.
        match: résultat du matcher (mandat actif + warnings + inactifs).
        recent_debits: prélèvements récents du même créancier sur ce
            débiteur (fenêtre temporelle à la discrétion de l'analyzer),
            utilisés par UnusualFrequencyRule. Vide tant qu'on n'a pas
            d'historique.
        now: timestamp d'évaluation (injecté pour testabilité).
    """

    event: DebitEventRecord
    match: MatchResult
    recent_debits: tuple[DebitEventRecord, ...] = field(default_factory=tuple)
    now: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def matched_mandate(self) -> MandateRecord | None:
        return self.match.mandate

    @property
    def has_active_mandate(self) -> bool:
        return self.match.mandate is not None

    @property
    def revoked_candidates(self) -> tuple[MandateRecord, ...]:
        """Sous-ensemble des candidats inactifs avec status REVOKED."""
        return tuple(m for m in self.match.inactive_candidates if m.status.value == "REVOKED")
