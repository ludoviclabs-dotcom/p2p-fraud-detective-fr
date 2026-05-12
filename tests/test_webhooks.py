"""Tests P5-3 — webhook sortant.

Couvre :
- Construction d'events `case.*` + `webhook.test` (Pydantic).
- Signature HMAC-SHA256 + vérification round-trip.
- Dispatcher : succès, retry tenacity sur 5xx, non-retry sur 4xx.
- Intégration `CaseService` → dispatcher (event émis sur `_record_event`).
- `webhook_url` vide → no-op silencieux.

Pas d'appel réseau réel : `responses` mocke tous les POST.
"""

from __future__ import annotations

import json

import pytest
import requests
import responses

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.schema import Finding, Severity
from p2p_fraud.webhooks.dispatcher import (
    SIGNATURE_HEADER,
    WebhookDeliveryError,
    WebhookDispatcher,
    sign_payload,
    verify_signature,
)
from p2p_fraud.webhooks.events import (
    SOURCE,
    SPEC_VERSION,
    WebhookEventKind,
    build_event,
    build_test_event,
)

# ───────────────────────── Signature HMAC ────────────────────────────────────


def test_sign_payload_round_trip() -> None:
    secret = "shared-secret-123"
    payload = b'{"id":"evt-x","type":"case.created"}'
    sig = sign_payload(payload, secret)
    assert sig.startswith("sha256=")
    assert verify_signature(payload=payload, signature_header=sig, secret=secret)


def test_verify_signature_rejects_tampered_payload() -> None:
    secret = "shared-secret-123"
    sig = sign_payload(b'{"a":1}', secret)
    assert not verify_signature(payload=b'{"a":2}', signature_header=sig, secret=secret)


def test_verify_signature_rejects_bad_format() -> None:
    assert not verify_signature(payload=b"x", signature_header="", secret="s")
    assert not verify_signature(payload=b"x", signature_header="md5=xx", secret="s")


# ───────────────────────── Build events ──────────────────────────────────────


def test_build_event_known_kind() -> None:
    evt = build_event(
        kind="created",
        case_id="CASE-abc123",
        actor="auditeur@org.fr",
        payload={"rule_id": "DECP_VENDOR_IN_PUBLIC_MARKET"},
    )
    assert evt is not None
    assert evt.type == WebhookEventKind.CASE_CREATED
    assert evt.subject == "CASE-abc123"
    assert evt.actor == "auditeur@org.fr"
    assert evt.source == SOURCE
    assert evt.specversion == SPEC_VERSION
    assert evt.data == {"rule_id": "DECP_VENDOR_IN_PUBLIC_MARKET"}
    body = evt.to_signed_json()
    parsed = json.loads(body)
    assert parsed["type"] == "case.created"


def test_build_event_unknown_kind_returns_none() -> None:
    assert build_event(kind="rgpd.erasure", case_id="x", actor="x", payload={}) is None


def test_build_test_event_has_test_type() -> None:
    evt = build_test_event(actor="system")
    assert evt.type == WebhookEventKind.WEBHOOK_TEST


# ───────────────────────── Dispatcher : OK ───────────────────────────────────


@responses.activate
def test_dispatcher_posts_signed_event() -> None:
    responses.add(responses.POST, "https://siem.test/p2pfd", status=200, json={"ok": True})
    dispatcher = WebhookDispatcher(
        url="https://siem.test/p2pfd",
        secret="shared",
        session=requests.Session(),
    )
    result = dispatcher.dispatch(build_test_event())
    assert result["ok"] is True
    assert result["status"] == 200
    # Vérifie que la signature a été envoyée
    call = responses.calls[0]
    assert SIGNATURE_HEADER in call.request.headers
    assert call.request.headers[SIGNATURE_HEADER].startswith("sha256=")
    # Et qu'elle correspond au body envoyé
    assert verify_signature(
        payload=call.request.body or b"",
        signature_header=call.request.headers[SIGNATURE_HEADER],
        secret="shared",
    )


@responses.activate
def test_dispatcher_records_history() -> None:
    responses.add(responses.POST, "https://siem.test/p2pfd", status=200)
    dispatcher = WebhookDispatcher(url="https://siem.test/p2pfd", session=requests.Session())
    dispatcher.dispatch(build_test_event())
    dispatcher.dispatch(build_test_event())
    assert len(dispatcher.sent_history) == 2


def test_dispatcher_disabled_when_url_empty() -> None:
    dispatcher = WebhookDispatcher(url="", session=requests.Session())
    assert dispatcher.enabled is False
    result = dispatcher.dispatch(build_test_event())
    assert result["skipped"] is True


# ───────────────────────── Dispatcher : retry & errors ───────────────────────


@responses.activate
def test_dispatcher_retries_on_5xx_then_succeeds() -> None:
    """Deux 503 puis 200 — tenacity doit retenter."""
    responses.add(responses.POST, "https://siem.test/p2pfd", status=503)
    responses.add(responses.POST, "https://siem.test/p2pfd", status=503)
    responses.add(responses.POST, "https://siem.test/p2pfd", status=200, json={"ok": True})
    dispatcher = WebhookDispatcher(
        url="https://siem.test/p2pfd",
        timeout=2.0,
        session=requests.Session(),
    )
    result = dispatcher.dispatch(build_test_event())
    assert result["ok"] is True
    assert len(responses.calls) == 3  # 2 retries + 1 succès


@responses.activate
def test_dispatcher_5xx_persistent_raises() -> None:
    for _ in range(3):
        responses.add(responses.POST, "https://siem.test/p2pfd", status=502)
    dispatcher = WebhookDispatcher(
        url="https://siem.test/p2pfd",
        timeout=2.0,
        session=requests.Session(),
    )
    with pytest.raises(WebhookDeliveryError):
        dispatcher.dispatch(build_test_event())


@responses.activate
def test_dispatcher_4xx_no_retry() -> None:
    """Une seule 401 doit faire échouer immédiatement (config error, no retry)."""
    responses.add(responses.POST, "https://siem.test/p2pfd", status=401)
    dispatcher = WebhookDispatcher(
        url="https://siem.test/p2pfd",
        timeout=2.0,
        session=requests.Session(),
    )
    with pytest.raises(WebhookDeliveryError):
        dispatcher.dispatch(build_test_event())
    assert len(responses.calls) == 1  # pas de retry


# ───────────────────────── Intégration CaseService ───────────────────────────


def _make_finding() -> Finding:
    return Finding(
        invoice_id="INV-001",
        rule_id="DUPLICATE_FUZZY",
        signal="Doublons fuzzy détectés",
        severity=Severity.HIGH,
        evidence={"vendor_id": "V001", "exposure_eur": 1500.0},
        detector="duplicates",
    )


@responses.activate
def test_case_service_dispatches_on_create() -> None:
    responses.add(responses.POST, "https://siem.test/p2pfd", status=200)
    dispatcher = WebhookDispatcher(
        url="https://siem.test/p2pfd",
        secret="s",
        session=requests.Session(),
    )
    svc = CaseService(audit_log=AuditLog(":memory:"), webhook_dispatcher=dispatcher)
    svc.create_case_from_finding(_make_finding(), actor="alice")
    assert len(responses.calls) == 1
    body = json.loads(responses.calls[0].request.body or b"")
    assert body["type"] == "case.created"
    assert body["actor"] == "alice"


@responses.activate
def test_case_service_dispatch_failure_does_not_break_audit() -> None:
    """Si le webhook tombe, l'audit log et la création du case doivent réussir."""
    responses.add(responses.POST, "https://siem.test/p2pfd", status=500)
    responses.add(responses.POST, "https://siem.test/p2pfd", status=500)
    responses.add(responses.POST, "https://siem.test/p2pfd", status=500)
    dispatcher = WebhookDispatcher(
        url="https://siem.test/p2pfd",
        timeout=1.0,
        session=requests.Session(),
    )
    svc = CaseService(audit_log=AuditLog(":memory:"), webhook_dispatcher=dispatcher)
    case = svc.create_case_from_finding(_make_finding(), actor="bob")
    # Le case existe, l'audit log a été appendé, malgré l'échec webhook
    assert case.case_id.startswith("CASE-")
    audit_entries = svc.audit_log.all()
    assert any(e.kind == "case.created" for e in audit_entries)


def test_case_service_without_dispatcher_is_silent() -> None:
    """Sans dispatcher, aucune tentative réseau (test sans `responses.activate`)."""
    svc = CaseService(audit_log=AuditLog(":memory:"), webhook_dispatcher=None)
    case = svc.create_case_from_finding(_make_finding(), actor="charlie")
    assert case.case_id.startswith("CASE-")
