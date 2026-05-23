"""Tests des endpoints FastAPI SEPA — Sprint 3 MandateGuard.

Vérifie le wire-up des routes :
- POST /api/v1/mandates (création)
- POST /api/v1/mandates/{id}/sign
- POST /api/v1/mandates/{id}/revoke
- GET /api/v1/mandates
- GET /api/v1/mandates/{id}
- POST /api/v1/debits/import
- POST /api/v1/debits/analyze
- POST /api/v1/risk/assess
"""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient

from p2p_fraud.api.sepa_router import _get_analyzer, _require_auth_sepa, router
from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import make_engine
from p2p_fraud.sepa.analyzer import SepaAnalyzer


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "api-test-secret-32-bytes-distinct")


@pytest.fixture
def client():
    """App FastAPI minimale avec uniquement le SEPA router pour tests isolés."""
    app = FastAPI()
    app.include_router(router)
    engine = make_engine(db_path=":memory:")
    analyzer = SepaAnalyzer(engine=engine, audit_log=AuditLog(engine=engine))

    app.dependency_overrides[_require_auth_sepa] = lambda: "test-actor"
    app.dependency_overrides[_get_analyzer] = lambda: analyzer

    return TestClient(app), analyzer


# ─── Mandate CRUD ────────────────────────────────────────────────────────────


def _mandate_body(**overrides):
    body = {
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name": "EDF SA",
        "debtor_iban": "FR7630001007941234567890185",
        "rum": "RUM-EDF-001",
        "max_amount_cents": 10000,
    }
    body.update(overrides)
    return body


def test_create_mandate_returns_201(client):
    api, _ = client
    response = api.post("/api/v1/mandates", json=_mandate_body())
    assert response.status_code == 201
    data = response.json()
    assert data["mandate_id"].startswith("mnd-")
    assert data["status"] == "DRAFT"
    assert data["debtor_iban_fingerprint"]
    # Pas d'IBAN clair dans la réponse
    assert "FR7630001007941234567890185" not in response.text


def test_sign_mandate_returns_active(client):
    api, _ = client
    created = api.post("/api/v1/mandates", json=_mandate_body()).json()
    mid = created["mandate_id"]
    response = api.post(f"/api/v1/mandates/{mid}/sign", json={"actor": "alice"})
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"


def test_revoke_mandate_returns_revoked(client):
    api, _ = client
    created = api.post("/api/v1/mandates", json=_mandate_body()).json()
    mid = created["mandate_id"]
    api.post(f"/api/v1/mandates/{mid}/sign", json={"actor": "alice"})
    response = api.post(
        f"/api/v1/mandates/{mid}/revoke", json={"actor": "alice", "reason": "client"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REVOKED"


def test_revoke_terminal_blocks_resign(client):
    api, _ = client
    created = api.post("/api/v1/mandates", json=_mandate_body()).json()
    mid = created["mandate_id"]
    api.post(f"/api/v1/mandates/{mid}/sign", json={"actor": "alice"})
    api.post(f"/api/v1/mandates/{mid}/revoke", json={"actor": "alice"})
    response = api.post(f"/api/v1/mandates/{mid}/sign", json={"actor": "alice"})
    assert response.status_code == 409


def test_list_mandates_filters_by_status(client):
    api, _ = client
    a = api.post("/api/v1/mandates", json=_mandate_body(rum="A")).json()
    api.post("/api/v1/mandates", json=_mandate_body(rum="B"))
    api.post(f"/api/v1/mandates/{a['mandate_id']}/sign", json={"actor": "x"})
    actives = api.get("/api/v1/mandates?status=ACTIVE").json()
    drafts = api.get("/api/v1/mandates?status=DRAFT").json()
    assert len(actives) == 1
    assert len(drafts) == 1


def test_get_mandate_not_found(client):
    api, _ = client
    response = api.get("/api/v1/mandates/mnd-does-not-exist")
    assert response.status_code == 404


def test_invalid_status_filter_returns_400(client):
    api, _ = client
    response = api.get("/api/v1/mandates?status=BLABLA")
    assert response.status_code == 400


# ─── Debits ──────────────────────────────────────────────────────────────────


def _debit_body(**overrides):
    body = {
        "source": "manual",
        "idempotency_key": "debit-api-001",
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name_raw": "EDF SA",
        "rum": "RUM-EDF-001",
        "amount_cents": 8900,
        "debtor_iban": "FR7630001007941234567890185",
    }
    body.update(overrides)
    return body


def test_import_debit_returns_event_id(client):
    api, _ = client
    response = api.post("/api/v1/debits/import", json=_debit_body())
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"].startswith("dbt-")
    assert data["debtor_iban_fingerprint"]


def test_analyze_debit_without_mandate_returns_dispute_ready(client):
    api, _ = client
    response = api.post("/api/v1/debits/analyze", json=_debit_body())
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "DISPUTE_READY"
    assert data["domain"] == "SEPA_DIRECT_DEBIT"
    assert data["engine_version"] == "sepa-v0.1.0"
    codes = {s["code"] for s in data["signals"]}
    assert "NO_ACTIVE_MANDATE" in codes


def test_analyze_debit_with_active_mandate_returns_allow(client):
    api, _ = client
    mid = api.post("/api/v1/mandates", json=_mandate_body()).json()["mandate_id"]
    api.post(f"/api/v1/mandates/{mid}/sign", json={"actor": "x"})
    response = api.post("/api/v1/debits/analyze", json=_debit_body())
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["match"]["matched"] is True
    assert data["match"]["mandate_id"] == mid


def test_analyze_response_no_iban_leak(client):
    api, _ = client
    iban = "FR7630001007941234567890185"
    response = api.post("/api/v1/debits/analyze", json=_debit_body(debtor_iban=iban))
    assert iban not in response.text


# ─── Risk Lab generic endpoint ───────────────────────────────────────────────


def test_risk_assess_with_sepa_domain(client):
    api, _ = client
    response = api.post(
        "/api/v1/risk/assess",
        json={"risk_domain": "SEPA_DIRECT_DEBIT", "event": _debit_body()},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "SEPA_DIRECT_DEBIT"


def test_risk_assess_rejects_unsupported_domain(client):
    api, _ = client
    response = api.post(
        "/api/v1/risk/assess",
        json={"risk_domain": "SUPPLIER_PAYMENT", "event": _debit_body()},
    )
    assert response.status_code == 400


# ─── Tenant header isolation ─────────────────────────────────────────────────


def test_tenant_header_isolates_mandates(client):
    api, _ = client
    api.post("/api/v1/mandates", json=_mandate_body(rum="A"), headers={"X-Tenant-Id": "t1"})
    api.post("/api/v1/mandates", json=_mandate_body(rum="B"), headers={"X-Tenant-Id": "t2"})
    t1 = api.get("/api/v1/mandates", headers={"X-Tenant-Id": "t1"}).json()
    t2 = api.get("/api/v1/mandates", headers={"X-Tenant-Id": "t2"}).json()
    assert len(t1) == 1
    assert len(t2) == 1
    assert t1[0]["rum"] == "A"
    assert t2[0]["rum"] == "B"


def test_analyze_in_other_tenant_does_not_match_mandate(client):
    api, _ = client
    mid = api.post(
        "/api/v1/mandates",
        json=_mandate_body(),
        headers={"X-Tenant-Id": "t1"},
    ).json()["mandate_id"]
    api.post(
        f"/api/v1/mandates/{mid}/sign",
        json={"actor": "x"},
        headers={"X-Tenant-Id": "t1"},
    )
    # Analyse en tenant-2 ne doit pas trouver le mandat
    response = api.post(
        "/api/v1/debits/analyze",
        json=_debit_body(),
        headers={"X-Tenant-Id": "t2"},
    )
    data = response.json()
    assert data["match"]["matched"] is False
    assert data["decision"] == "DISPUTE_READY"
