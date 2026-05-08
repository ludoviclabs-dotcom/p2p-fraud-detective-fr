"""Modèles Pydantic du case management."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CaseStatus(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    CLOSED_CONFIRMED = "closed_confirmed"
    CLOSED_REJECTED = "closed_rejected"
    CLOSED_FALSE_POSITIVE = "closed_false_positive"

    @property
    def is_closed(self) -> bool:
        return self in {
            CaseStatus.CLOSED_CONFIRMED,
            CaseStatus.CLOSED_REJECTED,
            CaseStatus.CLOSED_FALSE_POSITIVE,
        }


class CaseEvent(BaseModel):
    """Événement appliqué à un case (création, assignation, commentaire, clôture)."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    case_id: str
    kind: str  # created | assigned | commented | escalated | status_changed | closed | evidence_attached
    actor: str
    payload: dict = Field(default_factory=dict)
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Case(BaseModel):
    """Représentation d'un cas d'investigation lié à un ou plusieurs findings."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    finding_ids: list[str]
    invoice_id: str | None = None
    vendor_id: str | None = None
    title: str
    severity: str
    exposure_eur: float | None = None
    status: CaseStatus = CaseStatus.NEW
    assignee: str | None = None
    sla_deadline: datetime | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None
    closure_reason: str | None = None
    closure_evidence_path: str | None = None
