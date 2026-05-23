"""Builder d'Evidence Pack — assemble le payload JSON canonical déterministe.

Le builder ne fait PAS d'I/O : il prend les objets déjà chargés (debit
event + match + assessment + timeline) et produit un dict prêt à être
hashé/persisté. Cela facilite les tests d'idempotence : même input →
même output → même `pack_hash`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from p2p_fraud.evidence.canonical import canonical_hash, canonical_json
from p2p_fraud.risk_core.types import RiskAssessmentResult
from p2p_fraud.sepa.debit_event import DebitEventRecord
from p2p_fraud.sepa.mandate import MandateRecord
from p2p_fraud.sepa.matcher import MatchResult

EVIDENCE_FORMAT_VERSION = "1.0.0"


@dataclass(frozen=True)
class BuiltPack:
    """Résultat du builder : payload + hash + canonical bytes."""

    payload: dict[str, Any]
    canonical_json: str
    pack_hash: str


class EvidenceBuilder:
    """Assemble un Evidence Pack déterministe."""

    def build_for_debit(
        self,
        *,
        event: DebitEventRecord,
        match: MatchResult,
        assessment: RiskAssessmentResult,
        timeline: list[dict[str, Any]] | None = None,
        notes: str | None = None,
    ) -> BuiltPack:
        """Construit un pack pour un prélèvement analysé."""
        payload = {
            "format_version": EVIDENCE_FORMAT_VERSION,
            "subject": {
                "type": "DEBIT_EVENT",
                "id": event.event_id,
            },
            "event": self._serialize_event(event),
            "match": self._serialize_match(match),
            "assessment": self._serialize_assessment(assessment),
            "timeline": timeline or [],
            "notes": notes,
        }
        return self._finalize(payload)

    def _finalize(self, payload: dict[str, Any]) -> BuiltPack:
        canonical, pack_hash = canonical_hash(payload)
        return BuiltPack(payload=payload, canonical_json=canonical, pack_hash=pack_hash)

    # ─── Sérialiseurs déterministes ──────────────────────────────────────────

    @staticmethod
    def _serialize_event(event: DebitEventRecord) -> dict[str, Any]:
        """Représentation safe d'un DebitEvent — IBAN fingerprint uniquement."""
        return {
            "event_id": event.event_id,
            "tenant_id": event.tenant_id,
            "source": event.source,
            "idempotency_key": event.idempotency_key,
            "creditor_ics": event.creditor_ics,
            "creditor_name_raw": event.creditor_name_raw,
            "rum": event.rum,
            "amount_cents": event.amount_cents,
            "currency": event.currency,
            "booking_date": event.booking_date,
            "due_date": event.due_date,
            "debtor_iban_fingerprint": event.debtor_iban_fingerprint,
            "matched_mandate_id": event.matched_mandate_id,
            "created_at": event.created_at,
        }

    @staticmethod
    def _serialize_mandate(mandate: MandateRecord) -> dict[str, Any]:
        return {
            "mandate_id": mandate.mandate_id,
            "tenant_id": mandate.tenant_id,
            "creditor_id": mandate.creditor_id,
            "creditor_ics": mandate.creditor_ics,
            "creditor_name": mandate.creditor_name,
            "debtor_iban_fingerprint": mandate.debtor_iban_fingerprint,
            "rum": mandate.rum,
            "scheme": mandate.scheme.value,
            "sequence_type": mandate.sequence_type.value,
            "status": mandate.status.value,
            "max_amount_cents": mandate.max_amount_cents,
            "currency": mandate.currency,
            "frequency": mandate.frequency,
            "valid_from": mandate.valid_from,
            "valid_to": mandate.valid_to,
            "signed_at": mandate.signed_at,
            "revoked_at": mandate.revoked_at,
            "commitment_hash": mandate.commitment_hash,
            "current_revision_id": mandate.current_revision_id,
            "created_at": mandate.created_at,
            "updated_at": mandate.updated_at,
        }

    def _serialize_match(self, match: MatchResult) -> dict[str, Any]:
        return {
            "matched": match.matched,
            "mandate": self._serialize_mandate(match.mandate) if match.mandate else None,
            "candidates_active": [self._serialize_mandate(m) for m in match.candidates],
            "candidates_inactive": [self._serialize_mandate(m) for m in match.inactive_candidates],
            "warnings": [w.value for w in match.warnings],
        }

    @staticmethod
    def _serialize_assessment(assessment: RiskAssessmentResult) -> dict[str, Any]:
        return {
            "domain": assessment.domain.value,
            "score": assessment.score,
            "level": assessment.level.value,
            "decision": assessment.decision.value,
            "engine_version": assessment.engine_version,
            "assessed_at": assessment.assessed_at.isoformat(),
            "signals": [
                {
                    "code": s.code,
                    "title": s.title,
                    "message": s.message,
                    "severity": s.severity.value,
                    "score": s.score,
                    "evidence": s.evidence,
                    "detected_at": s.detected_at.isoformat(),
                }
                for s in assessment.signals
            ],
        }


def serialize_metadata(record_payload: dict[str, Any]) -> str:
    """Helper exposé : sérialisation canonical d'un payload brut."""
    return canonical_json(record_payload)
