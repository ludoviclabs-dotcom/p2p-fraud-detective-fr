"""Tests end-to-end de l'endpoint webhook entrant POST /api/v1/webhooks/debit.

Vérifie que :
- une requête signée correctement déclenche l'analyzer et retourne le verdict
- une requête sans signature est rejetée (400/401)
- une signature invalide est rejetée
- un timestamp hors fenêtre est rejeté
- un idempotency_key déjà reçu est rejeté (anti-replay applicatif)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient

from p2p_fraud.api.sepa_router import (
    _get_analyzer,
    _get_evidence_service,
    _get_webhook_idempotency_store,
    _require_auth_sepa,
    router,
)
from p2p_fraud.api.webhook_security import (
    HEADER_IDEMPOTENCY,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    WebhookIdempotencyStore,
    compute_signature,
)
from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.evidence.service import EvidenceService
from p2p_fraud.persistence import make_engine
from p2p_fraud.sepa.analyzer import SepaAnalyzer

SECRET = b"webhook-inbound-test-secret-32b!"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "webhook-iban-test-secret-32-byte")
    monkeypatch.setenv("WEBHOOK_INBOUND_SECRET", SECRET.decode())


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    engine = make_engine(db_path=":memory:")
    audit = AuditLog(engine=engine)
    analyzer = SepaAnalyzer(engine=engine, audit_log=audit)
    evidence = EvidenceService(analyzer=analyzer)
    store = WebhookIdempotencyStore(engine=engine)

    app.dependency_overrides[_require_auth_sepa] = lambda: "test-actor"
    app.dependency_overrides[_get_analyzer] = lambda: analyzer
    app.dependency_overrides[_get_evidence_service] = lambda: evidence
    app.dependency_overrides[_get_webhook_idempotency_store] = lambda: store
    return TestClient(app), analyzer


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _payload(idempotency_key: str = "psp-evt-001") -> bytes:
    import json

    return json.dumps(
        {
            "source": "psp",
            "idempotency_key": idempotency_key,
            "creditor_ics": "FR18ZZZ002305",
            "creditor_name_raw": "EDF SA",
            "rum": "RUM-EDF-001",
            "amount_cents": 8900,
            "currency": "EUR",
            "debtor_iban": "FR7630001007941234567890185",
        }
    ).encode("utf-8")


def _signed_headers(body: bytes, idempotency_key: str = "evt-001") -> dict[str, str]:
    return {
        HEADER_TIMESTAMP: _now_iso(),
        HEADER_SIGNATURE: compute_signature(body, SECRET),
        HEADER_IDEMPOTENCY: idempotency_key,
        "content-type": "application/json",
    }


# ─── Cas nominal ─────────────────────────────────────────────────────────────


def test_signed_request_analyzes_debit(client):
    api, _ = client
    body = _payload()
    resp = api.post("/api/v1/webhooks/debit", content=body, headers=_signed_headers(body))
    assert resp.status_code == 202
    data = resp.json()
    assert data["idempotency_key"]
    assert "analysis" in data
    assert data["analysis"]["domain"] == "SEPA_DIRECT_DEBIT"
    assert data["analysis"]["decision"] == "DISPUTE_READY"
    assert data["analysis"]["score"] == 80
    assert data["analysis"]["engine_version"] == "sepa-v0.1.0"


# ─── Refus ───────────────────────────────────────────────────────────────────


def test_unsigned_request_rejected(client):
    api, _ = client
    resp = api.post(
        "/api/v1/webhooks/debit",
        content=_payload(),
        headers={"content-type": "application/json"},
    )
    assert resp.status_code in (400, 401)


def test_wrong_signature_rejected(client):
    api, _ = client
    body = _payload()
    headers = {
        HEADER_TIMESTAMP: _now_iso(),
        HEADER_SIGNATURE: "sha256=" + "0" * 64,
        "content-type": "application/json",
    }
    resp = api.post("/api/v1/webhooks/debit", content=body, headers=headers)
    assert resp.status_code == 401


def test_old_timestamp_rejected(client):
    api, _ = client
    body = _payload()
    sig = compute_signature(body, SECRET)
    headers = {
        HEADER_TIMESTAMP: (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        HEADER_SIGNATURE: sig,
        "content-type": "application/json",
    }
    resp = api.post("/api/v1/webhooks/debit", content=body, headers=headers)
    assert resp.status_code == 400


def test_replay_rejected(client):
    api, _ = client
    body = _payload()
    headers = _signed_headers(body, idempotency_key="dup-key")
    r1 = api.post("/api/v1/webhooks/debit", content=body, headers=headers)
    assert r1.status_code == 202
    # 2e appel avec même idempotency_key
    headers2 = _signed_headers(body, idempotency_key="dup-key")
    r2 = api.post("/api/v1/webhooks/debit", content=body, headers=headers2)
    assert r2.status_code == 400


def test_invalid_json_returns_400(client):
    api, _ = client
    body = b"{not valid json"
    headers = _signed_headers(body)
    resp = api.post("/api/v1/webhooks/debit", content=body, headers=headers)
    assert resp.status_code == 400


def test_response_no_iban_leak(client):
    api, _ = client
    iban = "FR7630001007941234567890185"
    body = _payload()
    resp = api.post("/api/v1/webhooks/debit", content=body, headers=_signed_headers(body))
    assert iban not in resp.text


# ─── Audit chain ─────────────────────────────────────────────────────────────


def test_webhook_creates_audit_events(client):
    api, analyzer = client
    body = _payload()
    api.post("/api/v1/webhooks/debit", content=body, headers=_signed_headers(body))
    kinds = [e.kind for e in analyzer.audit.all()]
    # L'analyzer crée DEBIT_IMPORTED + DEBIT_ANALYZED
    assert "DEBIT_IMPORTED" in kinds
    assert "DEBIT_ANALYZED" in kinds
