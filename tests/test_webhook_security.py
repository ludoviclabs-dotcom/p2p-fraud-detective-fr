"""Tests sécurité webhooks entrants — Sprint 5 MandateGuard.

Couvre :
- compute_signature : déterministe + préfixe sha256=
- verify_signature : OK / KO timestamp / KO sig / replay window
- IdempotencyStore : already_seen + remember + purge
- end-to-end : FastAPI Depends + endpoint debit signé
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from p2p_fraud.api.webhook_security import (
    HEADER_IDEMPOTENCY,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    WebhookIdempotencyStore,
    WebhookVerificationError,
    compute_signature,
    parse_timestamp,
    verify_inbound_webhook,
    verify_signature,
)
from p2p_fraud.persistence import make_engine

SECRET = b"shared-secret-with-psp-for-tests"


# ─── compute_signature ──────────────────────────────────────────────────────


def test_compute_signature_deterministic():
    body = b'{"a":1}'
    a = compute_signature(body, SECRET)
    b = compute_signature(body, SECRET)
    assert a == b
    assert a.startswith("sha256=")
    assert len(a) == len("sha256=") + 64


def test_compute_signature_different_for_different_body():
    a = compute_signature(b'{"a":1}', SECRET)
    b = compute_signature(b'{"a":2}', SECRET)
    assert a != b


def test_compute_signature_different_for_different_secret():
    a = compute_signature(b'{"a":1}', SECRET)
    b = compute_signature(b'{"a":1}', b"other-secret")
    assert a != b


# ─── verify_signature ───────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def test_verify_signature_ok():
    body = b'{"x":42}'
    ts = _now_iso()
    sig = compute_signature(body, SECRET)
    result = verify_signature(
        body, timestamp_header=ts, signature_header=sig, secret=SECRET
    )
    assert isinstance(result, datetime)


def test_verify_signature_rejects_missing_timestamp():
    with pytest.raises(WebhookVerificationError) as exc:
        verify_signature(b"x", timestamp_header=None, signature_header="sha256=ab", secret=SECRET)
    assert "timestamp" in str(exc.value.detail).lower() or "Timestamp" in str(exc.value.detail)


def test_verify_signature_rejects_old_timestamp():
    """Anti-replay : timestamp > tolerance_seconds dans le passé → reject."""
    body = b'{"x":1}'
    old = (datetime.now(UTC) - timedelta(seconds=600)).isoformat()
    sig = compute_signature(body, SECRET)
    with pytest.raises(WebhookVerificationError):
        verify_signature(
            body, timestamp_header=old, signature_header=sig,
            secret=SECRET, tolerance_seconds=300,
        )


def test_verify_signature_rejects_future_timestamp():
    body = b'{"x":1}'
    future = (datetime.now(UTC) + timedelta(seconds=600)).isoformat()
    sig = compute_signature(body, SECRET)
    with pytest.raises(WebhookVerificationError):
        verify_signature(
            body, timestamp_header=future, signature_header=sig,
            secret=SECRET, tolerance_seconds=300,
        )


def test_verify_signature_rejects_missing_signature():
    body = b'{"x":1}'
    with pytest.raises(WebhookVerificationError):
        verify_signature(
            body, timestamp_header=_now_iso(), signature_header=None, secret=SECRET
        )


def test_verify_signature_rejects_malformed_signature():
    body = b'{"x":1}'
    with pytest.raises(WebhookVerificationError):
        verify_signature(
            body, timestamp_header=_now_iso(),
            signature_header="abcdef-no-prefix", secret=SECRET,
        )


def test_verify_signature_rejects_invalid_signature():
    body = b'{"x":1}'
    with pytest.raises(WebhookVerificationError):
        verify_signature(
            body, timestamp_header=_now_iso(),
            signature_header="sha256=" + "0" * 64, secret=SECRET,
        )


def test_verify_signature_rejects_wrong_secret():
    body = b'{"x":1}'
    sig = compute_signature(body, b"other-secret")
    with pytest.raises(WebhookVerificationError):
        verify_signature(
            body, timestamp_header=_now_iso(),
            signature_header=sig, secret=SECRET,
        )


def test_parse_timestamp_accepts_z_suffix():
    ts = parse_timestamp("2026-01-15T10:00:00Z")
    assert ts.tzinfo is not None


# ─── IdempotencyStore ────────────────────────────────────────────────────────


@pytest.fixture
def store():
    engine = make_engine(db_path=":memory:")
    return WebhookIdempotencyStore(engine=engine)


def test_store_unknown_key_returns_false(store):
    assert store.already_seen("key-x") is False


def test_store_remember_then_seen(store):
    store.remember("key-x", source="psp", signature="sha256=abc")
    assert store.already_seen("key-x") is True


def test_store_remember_idempotent(store):
    """INSERT OR IGNORE → un 2nd remember ne crash pas."""
    store.remember("key-x", source="psp", signature="sha256=abc")
    store.remember("key-x", source="psp", signature="sha256=abc")
    assert store.already_seen("key-x") is True


def test_store_purge_removes_old(store):
    """Insère puis purge — l'entrée disparaît si plus vieille que le seuil."""
    from sqlalchemy import text

    store.remember("key-old", source="psp", signature="sha256=abc")
    # On force une date ancienne pour cette entrée
    old = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    with store._engine.begin() as conn:
        conn.execute(
            text("UPDATE webhook_events SET received_at = :d WHERE idempotency_key = :k"),
            {"d": old, "k": "key-old"},
        )
    removed = store.purge_older_than(days=2)
    assert removed == 1
    assert store.already_seen("key-old") is False


# ─── End-to-end : FastAPI endpoint with verify_inbound_webhook ───────────────


@pytest.fixture
def app_with_signed_endpoint(monkeypatch):
    """App minimale avec un endpoint qui exige une signature valide."""
    monkeypatch.setenv("WEBHOOK_INBOUND_SECRET", SECRET.decode("utf-8"))

    app = FastAPI()
    engine = make_engine(db_path=":memory:")
    test_store = WebhookIdempotencyStore(engine=engine)

    @app.post("/secured")
    async def secured_handler(request: Request):
        verified = await verify_inbound_webhook(request, store=test_store, source="test")
        return {
            "ok": True,
            "ts": verified.timestamp.isoformat(),
            "idempotency": verified.idempotency_key,
            "body_len": len(verified.body),
        }

    return TestClient(app)


def test_endpoint_accepts_signed_request(app_with_signed_endpoint):
    body = b'{"hello":"world"}'
    sig = compute_signature(body, SECRET)
    resp = app_with_signed_endpoint.post(
        "/secured",
        content=body,
        headers={
            HEADER_TIMESTAMP: _now_iso(),
            HEADER_SIGNATURE: sig,
            HEADER_IDEMPOTENCY: "evt-001",
            "content-type": "application/json",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["idempotency"] == "evt-001"


def test_endpoint_rejects_replay(app_with_signed_endpoint):
    body = b'{"hello":"world"}'
    sig = compute_signature(body, SECRET)
    headers = {
        HEADER_TIMESTAMP: _now_iso(),
        HEADER_SIGNATURE: sig,
        HEADER_IDEMPOTENCY: "evt-replay",
        "content-type": "application/json",
    }
    r1 = app_with_signed_endpoint.post("/secured", content=body, headers=headers)
    assert r1.status_code == 200
    # Second appel avec même idempotency_key → rejet
    r2 = app_with_signed_endpoint.post("/secured", content=body, headers=headers)
    assert r2.status_code == 400


def test_endpoint_rejects_unsigned(app_with_signed_endpoint):
    resp = app_with_signed_endpoint.post(
        "/secured",
        content=b'{"x":1}',
        headers={"content-type": "application/json"},
    )
    assert resp.status_code in (400, 401)


def test_endpoint_rejects_wrong_signature(app_with_signed_endpoint):
    resp = app_with_signed_endpoint.post(
        "/secured",
        content=b'{"x":1}',
        headers={
            HEADER_TIMESTAMP: _now_iso(),
            HEADER_SIGNATURE: "sha256=" + "0" * 64,
            "content-type": "application/json",
        },
    )
    assert resp.status_code == 401
