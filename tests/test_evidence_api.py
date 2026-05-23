"""Tests endpoints FastAPI Evidence Pack — Sprint 4 MandateGuard.

- POST /api/v1/evidence
- GET  /api/v1/evidence/{id}
- GET  /api/v1/evidence/{id}/report (HTML)
- POST /api/v1/evidence/{id}/verify
"""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient

from p2p_fraud.api.sepa_router import (
    _get_analyzer,
    _get_evidence_service,
    _require_auth_sepa,
    router,
)
from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.evidence.service import EvidenceService
from p2p_fraud.persistence import make_engine
from p2p_fraud.sepa.analyzer import SepaAnalyzer


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "api-evidence-test-secret-32-bxyz")


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    engine = make_engine(db_path=":memory:")
    audit = AuditLog(engine=engine)
    analyzer = SepaAnalyzer(engine=engine, audit_log=audit)
    evidence = EvidenceService(analyzer=analyzer)
    app.dependency_overrides[_require_auth_sepa] = lambda: "test-actor"
    app.dependency_overrides[_get_analyzer] = lambda: analyzer
    app.dependency_overrides[_get_evidence_service] = lambda: evidence
    return TestClient(app), analyzer


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


def _debit_body(**overrides):
    body = {
        "source": "manual",
        "idempotency_key": "evp-api-debit-001",
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name_raw": "EDF SA",
        "rum": "RUM-EDF-001",
        "amount_cents": 8900,
        "debtor_iban": "FR7630001007941234567890185",
    }
    body.update(overrides)
    return body


# ─── Création ────────────────────────────────────────────────────────────────


def test_create_evidence_pack_returns_201(client):
    api, _ = client
    # Setup : mandat actif + débit analysé
    mid = api.post("/api/v1/mandates", json=_mandate_body()).json()["mandate_id"]
    api.post(f"/api/v1/mandates/{mid}/sign", json={"actor": "x"})
    debit = api.post("/api/v1/debits/analyze", json=_debit_body()).json()
    eid = debit["event_id"]

    response = api.post(
        "/api/v1/evidence",
        json={"subject_type": "DEBIT_EVENT", "subject_id": eid},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["evidence_pack_id"].startswith("evp-")
    assert data["pack_hash"]
    assert data["subject_id"] == eid
    assert data["engine_version"] == "sepa-v0.1.0"
    assert data["has_report"] is True


def test_create_evidence_unknown_subject_returns_404(client):
    api, _ = client
    response = api.post(
        "/api/v1/evidence",
        json={"subject_type": "DEBIT_EVENT", "subject_id": "dbt-nope"},
    )
    assert response.status_code == 404


def test_create_evidence_unsupported_subject_returns_400(client):
    api, _ = client
    response = api.post(
        "/api/v1/evidence",
        json={"subject_type": "CASE", "subject_id": "case-1"},
    )
    assert response.status_code == 400


# ─── Get + Report ────────────────────────────────────────────────────────────


def test_get_evidence_pack_returns_payload(client):
    api, _ = client
    debit = api.post("/api/v1/debits/analyze", json=_debit_body()).json()
    record = api.post(
        "/api/v1/evidence",
        json={"subject_type": "DEBIT_EVENT", "subject_id": debit["event_id"]},
    ).json()
    response = api.get(f"/api/v1/evidence/{record['evidence_pack_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["payload"]["format_version"] == "1.0.0"
    assert data["payload"]["subject"]["id"] == debit["event_id"]


def test_get_evidence_report_html(client):
    api, _ = client
    debit = api.post("/api/v1/debits/analyze", json=_debit_body()).json()
    record = api.post(
        "/api/v1/evidence",
        json={"subject_type": "DEBIT_EVENT", "subject_id": debit["event_id"]},
    ).json()
    response = api.get(f"/api/v1/evidence/{record['evidence_pack_id']}/report")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"].lower()
    assert record["pack_hash"] in response.text


def test_get_evidence_not_found(client):
    api, _ = client
    response = api.get("/api/v1/evidence/evp-does-not-exist")
    assert response.status_code == 404


# ─── Verify ──────────────────────────────────────────────────────────────────


def test_verify_returns_valid(client):
    api, _ = client
    debit = api.post("/api/v1/debits/analyze", json=_debit_body()).json()
    record = api.post(
        "/api/v1/evidence",
        json={"subject_type": "DEBIT_EVENT", "subject_id": debit["event_id"]},
    ).json()
    response = api.post(f"/api/v1/evidence/{record['evidence_pack_id']}/verify")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["hash_matches"] is True
    assert data["audit_chain_valid"] is True


# ─── No IBAN leak ────────────────────────────────────────────────────────────


def test_evidence_response_no_iban_leak(client):
    api, _ = client
    iban = "FR7630001007941234567890185"
    mid = api.post("/api/v1/mandates", json=_mandate_body(debtor_iban=iban)).json()["mandate_id"]
    api.post(f"/api/v1/mandates/{mid}/sign", json={"actor": "x"})
    debit = api.post("/api/v1/debits/analyze", json=_debit_body(debtor_iban=iban)).json()
    response = api.post(
        "/api/v1/evidence",
        json={"subject_type": "DEBIT_EVENT", "subject_id": debit["event_id"]},
    )
    assert iban not in response.text


# ─── Tenant isolation ────────────────────────────────────────────────────────


def test_evidence_tenant_isolation(client):
    api, _ = client
    debit = api.post(
        "/api/v1/debits/analyze",
        json=_debit_body(),
        headers={"X-Tenant-Id": "t-1"},
    ).json()
    record = api.post(
        "/api/v1/evidence",
        json={"subject_type": "DEBIT_EVENT", "subject_id": debit["event_id"]},
        headers={"X-Tenant-Id": "t-1"},
    ).json()
    # Lecture depuis tenant-2 → 404
    response = api.get(
        f"/api/v1/evidence/{record['evidence_pack_id']}",
        headers={"X-Tenant-Id": "t-2"},
    )
    assert response.status_code == 404
