"""Configuration SLA par sévérité — délais de clôture configurables.

Permet aux organismes de contrôle (DGFiP, IGF, Cour des comptes) de configurer
des délais de traitement adaptés à leur cadre opérationnel : durée de réponse
imposée par la criticité de l'alerte (ISA 240, AS 2401, AMLD6 art. 24).

Valeurs par défaut alignées sur les bonnes pratiques marché 2026 :
- CRITICAL : 24 h (LCB-FT exige une déclaration de soupçon sans délai)
- HIGH     : 72 h (3 jours ouvrés)
- MEDIUM   : 168 h (7 jours)
- LOW      : 720 h (30 jours)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class SLAConfig:
    """Configuration SLA — heures jusqu'à la deadline par sévérité."""

    critical_hours: int = 24
    high_hours: int = 72
    medium_hours: int = 168
    low_hours: int = 720

    def deadline_for(self, severity: str, *, from_dt: datetime | None = None) -> datetime:
        base = from_dt or datetime.now(UTC)
        hours = self.hours_for(severity)
        return base + timedelta(hours=hours)

    def hours_for(self, severity: str) -> int:
        sev = (severity or "low").lower()
        return {
            "critical": self.critical_hours,
            "high": self.high_hours,
            "medium": self.medium_hours,
            "low": self.low_hours,
        }.get(sev, self.low_hours)

    def is_overdue(self, *, severity: str, created_at: datetime, status_closed: bool) -> bool:
        if status_closed:
            return False
        deadline = self.deadline_for(severity, from_dt=created_at)
        return datetime.now(UTC) > deadline


DEFAULT_SLA = SLAConfig()
