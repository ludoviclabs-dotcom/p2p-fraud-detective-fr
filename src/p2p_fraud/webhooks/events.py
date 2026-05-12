"""Schémas Pydantic typés des événements webhook sortants.

Chaque event suit le format standard CloudEvents v1.0 simplifié :
    {
        "id": "evt-<uuid12>",
        "type": "case.created" | "case.assigned" | ...,
        "source": "p2p-fraud-detective-fr",
        "time": "2026-05-12T22:30:00+00:00",
        "specversion": "1.0",
        "subject": "CASE-abc123",       # case_id ou autre ressource
        "actor": "audit-team@org.fr",
        "data": {                        # payload spécifique au type
            ...
        }
    }

Le SIEM destinataire peut router via `type` et identifier la ressource
via `subject`. Le `data` reste minimal (pas de PII fournisseur, juste
les identifiants techniques + métadonnées du case).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

SPEC_VERSION = "1.0"
SOURCE = "p2p-fraud-detective-fr"


class WebhookEventKind(StrEnum):
    """Liste fermée des events `case.*` + `webhook.test`."""

    CASE_CREATED = "case.created"
    CASE_ASSIGNED = "case.assigned"
    CASE_COMMENTED = "case.commented"
    CASE_EVIDENCE_ATTACHED = "case.evidence_attached"
    CASE_ESCALATED = "case.escalated"
    CASE_STATUS_CHANGED = "case.status_changed"
    CASE_CLOSED = "case.closed"
    WEBHOOK_TEST = "webhook.test"


# Mapping `kind` interne `_record_event(kind="created"|"assigned"|...)`
# vers le `type` CloudEvent (préfixe `case.`).
_KIND_TO_EVENT_TYPE: dict[str, WebhookEventKind] = {
    "created": WebhookEventKind.CASE_CREATED,
    "assigned": WebhookEventKind.CASE_ASSIGNED,
    "commented": WebhookEventKind.CASE_COMMENTED,
    "evidence_attached": WebhookEventKind.CASE_EVIDENCE_ATTACHED,
    "escalated": WebhookEventKind.CASE_ESCALATED,
    "status_changed": WebhookEventKind.CASE_STATUS_CHANGED,
    "closed": WebhookEventKind.CASE_CLOSED,
}


class WebhookEvent(BaseModel):
    """Structure d'un événement webhook sortant (CloudEvents v1.0 simplifié)."""

    id: str
    type: WebhookEventKind
    source: str = SOURCE
    time: datetime
    specversion: str = SPEC_VERSION
    subject: str
    actor: str
    data: dict[str, Any] = Field(default_factory=dict)

    def to_signed_json(self) -> str:
        """Sérialise pour la signature HMAC + transport HTTP."""
        return self.model_dump_json(by_alias=True)


def _new_event_id() -> str:
    return f"evt-{uuid.uuid4().hex[:12]}"


def build_event(
    *,
    kind: str,
    case_id: str,
    actor: str,
    payload: dict[str, Any] | None = None,
) -> WebhookEvent | None:
    """Construit un `WebhookEvent` depuis les inputs internes `_record_event`.

    Renvoie `None` si le `kind` n'est pas un événement webhook reconnu —
    cela permet au dispatcher de ne rien faire silencieusement pour les
    events internes hors-périmètre (e.g. `rgpd.erasure`).
    """
    event_type = _KIND_TO_EVENT_TYPE.get(kind)
    if event_type is None:
        return None
    return WebhookEvent(
        id=_new_event_id(),
        type=event_type,
        time=datetime.now(UTC),
        subject=case_id,
        actor=actor,
        data=payload or {},
    )


def build_test_event(actor: str = "system") -> WebhookEvent:
    """Construit un event factice pour valider la configuration côté pilote.

    Utilisé par l'endpoint `GET /webhook/test` et le bouton « Tester la
    configuration » de la page Alertes.
    """
    return WebhookEvent(
        id=_new_event_id(),
        type=WebhookEventKind.WEBHOOK_TEST,
        time=datetime.now(UTC),
        subject="webhook-test",
        actor=actor,
        data={
            "message": "Test webhook delivery from P2P Fraud Detective FR.",
            "hint": "Si vous recevez ceci, la configuration est opérationnelle.",
        },
    )
