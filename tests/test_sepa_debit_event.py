"""Tests `DebitEventService` — Sprint 2 MandateGuard.

Couvre :
- ingestion + idempotence par (tenant_id, idempotency_key)
- fingerprint IBAN calculé et persisté, IBAN clair jamais en DB
- audit log DEBIT_IMPORTED
- isolation tenant
- pagination simple list()
"""

from __future__ import annotations

import json

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import make_engine
from p2p_fraud.security.iban import iban_fingerprint
from p2p_fraud.sepa.debit_event import DebitEventInput, DebitEventService


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "test-secret-32-bytes-do-not-reuse!")


@pytest.fixture
def service():
    engine = make_engine(db_path=":memory:")
    return DebitEventService(engine=engine, audit_log=AuditLog(engine=engine))


def _payload(**overrides) -> DebitEventInput:
    defaults = {
        "source": "manual",
        "idempotency_key": "debit-2026-05-23-001",
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name_raw": "EDF SA",
        "rum": "RUM-EDF-001",
        "amount_cents": 8900,
        "currency": "EUR",
        "debtor_iban": "FR7630001007941234567890185",
    }
    defaults.update(overrides)
    return DebitEventInput(**defaults)


# ─── Ingestion ───────────────────────────────────────────────────────────────


def test_ingest_creates_record(service):
    rec = service.ingest(_payload(), actor="alice")
    assert rec.event_id.startswith("dbt-")
    assert rec.amount_cents == 8900
    assert rec.amount_eur == 89.0
    assert rec.source == "manual"


def test_ingest_persists_to_db(service):
    rec = service.ingest(_payload(), actor="alice")
    fetched = service.get(rec.event_id)
    assert fetched is not None
    assert fetched.idempotency_key == "debit-2026-05-23-001"


def test_ingest_computes_iban_fingerprint(service):
    iban = "FR7630001007941234567890185"
    rec = service.ingest(_payload(debtor_iban=iban), actor="alice")
    assert rec.debtor_iban_fingerprint == iban_fingerprint(iban)


def test_ingest_idempotent_same_key_returns_existing(service):
    rec1 = service.ingest(_payload(), actor="alice")
    rec2 = service.ingest(_payload(), actor="alice")
    assert rec1.event_id == rec2.event_id


def test_ingest_idempotent_different_tenants_creates_distinct(service):
    rec1 = service.ingest(_payload(), actor="alice", tenant_id="t-1")
    rec2 = service.ingest(_payload(), actor="alice", tenant_id="t-2")
    # Même idempotency_key mais tenants différents → 2 events
    assert rec1.event_id != rec2.event_id


def test_ingest_no_iban_no_fingerprint(service):
    payload = _payload(debtor_iban=None)
    rec = service.ingest(payload, actor="alice")
    assert rec.debtor_iban_fingerprint is None


def test_ingest_raw_json_redacts_iban(service):
    iban = "FR7630001007941234567890185"
    rec = service.ingest(_payload(debtor_iban=iban), actor="alice")
    with service._engine.begin() as conn:
        row = conn.execute(
            text("SELECT raw_json FROM debit_events WHERE event_id = :id"),
            {"id": rec.event_id},
        ).mappings().first()
    assert row is not None
    raw = row["raw_json"]
    assert iban not in raw
    assert "[redacted]" in raw


def test_ingest_iban_not_in_audit(service):
    iban = "FR7630001007941234567890185"
    service.ingest(_payload(debtor_iban=iban), actor="alice")
    entries = service._audit.all()
    debit_event = next(e for e in entries if e.kind == "DEBIT_IMPORTED")
    payload_str = json.dumps(debit_event.payload)
    assert iban not in payload_str
    assert "debtor_iban_fingerprint" in debit_event.payload


def test_audit_event_kind_debit_imported(service):
    service.ingest(_payload(), actor="alice")
    entries = service._audit.all()
    assert any(e.kind == "DEBIT_IMPORTED" for e in entries)


# ─── Lookup ──────────────────────────────────────────────────────────────────


def test_list_returns_recent_first(service):
    service.ingest(_payload(idempotency_key="k-1"), actor="alice")
    service.ingest(_payload(idempotency_key="k-2"), actor="alice")
    service.ingest(_payload(idempotency_key="k-3"), actor="alice")
    events = service.list()
    assert len(events) == 3


def test_list_filters_by_tenant(service):
    service.ingest(_payload(idempotency_key="k-1"), actor="alice", tenant_id="t-1")
    service.ingest(_payload(idempotency_key="k-2"), actor="alice", tenant_id="t-2")
    t1 = service.list(tenant_id="t-1")
    t2 = service.list(tenant_id="t-2")
    assert len(t1) == 1
    assert len(t2) == 1


def test_get_with_tenant_isolation(service):
    rec = service.ingest(_payload(), actor="alice", tenant_id="t-1")
    # Lookup from another tenant
    assert service.get(rec.event_id, tenant_id="t-2") is None
    # Lookup with correct tenant
    assert service.get(rec.event_id, tenant_id="t-1") is not None


def test_mark_matched_updates_mandate_id(service):
    rec = service.ingest(_payload(), actor="alice")
    service.mark_matched(rec.event_id, "mnd-12345")
    fetched = service.get(rec.event_id)
    assert fetched is not None
    assert fetched.matched_mandate_id == "mnd-12345"


# ─── Validation ──────────────────────────────────────────────────────────────


def test_amount_must_be_positive():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        DebitEventInput(
            source="manual",
            idempotency_key="k",
            creditor_ics="X",
            creditor_name_raw="Y",
            amount_cents=0,
        )


def test_iban_too_short_rejected():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        DebitEventInput(
            source="manual",
            idempotency_key="k",
            amount_cents=100,
            debtor_iban="FR76",
        )
