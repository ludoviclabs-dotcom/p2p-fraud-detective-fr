"""Webhooks sortants — émission d'événements case.* vers SIEM/ERP/SOC.

Module P5-3. Activé via `Settings.webhook_url` (vide → no-op).

Architecture :
- `events.py` : schémas Pydantic typés des 8 events (`case.created`,
  `case.assigned`, `case.commented`, `case.evidence_attached`,
  `case.escalated`, `case.status_changed`, `case.closed`, `webhook.test`).
- `dispatcher.py` : POST signé HMAC-SHA256, retry tenacity exponentiel,
  log structuré JSON. **Synchrone bloquant** par défaut (cohérence avec
  l'audit log immutable). Bascule async via `dispatch_in_background()`
  pour les contextes où la latence est critique.

Le dispatcher est injecté dans `CaseService` via le constructeur ou
attribut `case_service.webhook_dispatcher = ...` après création.
"""

from __future__ import annotations

from p2p_fraud.webhooks.dispatcher import (
    WebhookDeliveryError,
    WebhookDispatcher,
    sign_payload,
)
from p2p_fraud.webhooks.events import (
    WebhookEvent,
    WebhookEventKind,
    build_event,
)

__all__ = [
    "WebhookDeliveryError",
    "WebhookDispatcher",
    "WebhookEvent",
    "WebhookEventKind",
    "build_event",
    "sign_payload",
]
