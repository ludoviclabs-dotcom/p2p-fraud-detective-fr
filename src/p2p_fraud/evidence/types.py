"""Types Pydantic d'Evidence Pack — input/output service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidencePackInput(BaseModel):
    """Payload de création d'un Evidence Pack.

    Le caller choisit le sujet (debit_event_id, case_id, mandate_id…) — le
    service charge les données associées et construit le pack canonical.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    subject_type: str = Field(..., description="DEBIT_EVENT | MANDATE | CASE")
    subject_id: str = Field(..., min_length=1, max_length=64)
    include_audit_timeline: bool = True
    notes: str | None = Field(default=None, max_length=2000)


@dataclass(frozen=True)
class EvidencePackRecord:
    """Vue applicative d'un Evidence Pack persisté."""

    evidence_pack_id: str
    tenant_id: str | None
    subject_type: str
    subject_id: str
    domain: str
    engine_version: str
    pack_hash: str
    audit_anchor_hash: str | None
    audit_anchor_seq: int | None
    payload: dict[str, Any]
    has_report: bool
    storage_key: str | None
    actor: str | None
    created_at: str


@dataclass(frozen=True)
class EvidenceVerificationResult:
    """Résultat de la vérification d'intégrité d'un pack."""

    evidence_pack_id: str
    valid: bool
    hash_matches: bool
    audit_chain_valid: bool
    audit_anchor_present: bool
    checked_at: str
    errors: tuple[str, ...] = ()
