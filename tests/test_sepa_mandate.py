"""Tests `MandateService` — Sprint 2 MandateGuard.

Couvre :
- création (états initiaux, upsert Creditor/BankAccount, audit event)
- transitions (sign, revoke, suspend, resume) + validation ALLOWED_TRANSITIONS
- lookup (get, list, find_active_candidate, find_active_candidates)
- IBAN jamais en clair dans la DB ni dans l'audit
- déchiffrement explicite via decrypt_iban
- isolation tenant
"""

from __future__ import annotations

import json

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import make_engine
from p2p_fraud.sepa.mandate import (
    MandateInput,
    MandateNotFoundError,
    MandateService,
    MandateStateError,
)
from p2p_fraud.sepa.types import MandateScheme, MandateStatus, SequenceType


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "test-secret-32-bytes-do-not-reuse!")


@pytest.fixture
def service():
    engine = make_engine(db_path=":memory:")
    return MandateService(engine=engine, audit_log=AuditLog(engine=engine))


def _payload(**overrides) -> MandateInput:
    defaults = {
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name": "EDF SA",
        "creditor_country": "FR",
        "debtor_iban": "FR7630001007941234567890185",
        "rum": "RUM-EDF-001",
        "scheme": MandateScheme.SDD_CORE,
        "sequence_type": SequenceType.RCUR,
        "max_amount_cents": 10000,
        "currency": "EUR",
    }
    defaults.update(overrides)
    return MandateInput(**defaults)


# ─── Création ────────────────────────────────────────────────────────────────


def test_create_mandate_starts_in_draft(service):
    rec = service.create(_payload(), actor="alice")
    assert rec.status == MandateStatus.DRAFT
    assert rec.mandate_id.startswith("mnd-")
    assert rec.signed_at is None
    assert rec.revoked_at is None


def test_create_mandate_persists_to_db(service):
    rec = service.create(_payload(), actor="alice")
    fetched = service.get(rec.mandate_id)
    assert fetched is not None
    assert fetched.mandate_id == rec.mandate_id
    assert fetched.creditor_ics == "FR18ZZZ002305"
    assert fetched.rum == "RUM-EDF-001"


def test_create_mandate_creates_revision(service):
    rec = service.create(_payload(), actor="alice")
    with service._engine.begin() as conn:
        revisions = (
            conn.execute(
                text("SELECT * FROM mandate_revisions WHERE mandate_id = :id"),
                {"id": rec.mandate_id},
            )
            .mappings()
            .all()
        )
    assert len(revisions) == 1
    assert revisions[0]["reason"] == "CREATED"
    assert revisions[0]["actor"] == "alice"
    assert rec.current_revision_id == revisions[0]["revision_id"]


def test_create_mandate_iban_not_in_clear_in_db(service):
    iban = "FR7630001007941234567890185"
    rec = service.create(_payload(debtor_iban=iban), actor="alice")
    with service._engine.begin() as conn:
        ba = (
            conn.execute(
                text(
                    "SELECT iban_ciphertext, iban_fingerprint FROM bank_accounts "
                    "WHERE account_id = :id"
                ),
                {"id": rec.debtor_account_id},
            )
            .mappings()
            .first()
        )
    assert ba is not None
    assert iban not in ba["iban_ciphertext"]
    assert ba["iban_ciphertext"].startswith("enc:v1:")
    # Fingerprint cohérent avec security.iban
    from p2p_fraud.security.iban import iban_fingerprint

    assert ba["iban_fingerprint"] == iban_fingerprint(iban)


def test_create_mandate_iban_not_in_clear_in_audit(service):
    iban = "FR7630001007941234567890185"
    service.create(_payload(debtor_iban=iban), actor="alice")
    # L'event MANDATE_CREATED ne doit jamais contenir l'IBAN clair
    entries = list(service._audit.all())
    md_event = next(e for e in entries if e.kind == "MANDATE_CREATED")
    payload_str = json.dumps(md_event.payload)
    assert iban not in payload_str
    assert iban[:6] not in payload_str
    assert "iban_fingerprint" in md_event.payload


def test_create_upserts_creditor_by_ics(service):
    p1 = _payload(rum="RUM-001")
    p2 = _payload(rum="RUM-002", creditor_name="EDF SA (updated)")
    r1 = service.create(p1, actor="alice")
    r2 = service.create(p2, actor="alice")
    # Même ICS → même creditor_id (upsert)
    assert r1.creditor_id == r2.creditor_id


def test_create_upserts_bank_account_by_fingerprint(service):
    p1 = _payload(rum="RUM-001")
    p2 = _payload(rum="RUM-002")  # même IBAN
    r1 = service.create(p1, actor="alice")
    r2 = service.create(p2, actor="alice")
    assert r1.debtor_account_id == r2.debtor_account_id


def test_create_with_tenant_id_isolates(service):
    r1 = service.create(_payload(rum="A"), actor="alice", tenant_id="tenant-1")
    r2 = service.create(_payload(rum="A"), actor="alice", tenant_id="tenant-2")
    # Même RUM mais tenants différents → 2 mandats
    assert r1.mandate_id != r2.mandate_id
    assert r1.tenant_id == "tenant-1"
    assert r2.tenant_id == "tenant-2"


# ─── Transitions ─────────────────────────────────────────────────────────────


def test_sign_transitions_draft_to_active(service):
    rec = service.create(_payload(), actor="alice")
    signed = service.sign(rec.mandate_id, actor="alice")
    assert signed.status == MandateStatus.ACTIVE
    assert signed.signed_at is not None
    assert signed.commitment_hash is not None


def test_sign_creates_revision(service):
    rec = service.create(_payload(), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    with service._engine.begin() as conn:
        revisions = (
            conn.execute(
                text(
                    "SELECT reason FROM mandate_revisions WHERE mandate_id = :id ORDER BY created_at"
                ),
                {"id": rec.mandate_id},
            )
            .mappings()
            .all()
        )
    reasons = [r["reason"] for r in revisions]
    assert reasons == ["CREATED", "SIGNED"]


def test_revoke_transitions_to_revoked(service):
    rec = service.create(_payload(), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    revoked = service.revoke(rec.mandate_id, actor="alice", reason_text="client demande")
    assert revoked.status == MandateStatus.REVOKED
    assert revoked.revoked_at is not None


def test_revoke_terminal_state_blocks_further_transitions(service):
    rec = service.create(_payload(), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    service.revoke(rec.mandate_id, actor="alice")
    with pytest.raises(MandateStateError):
        service.sign(rec.mandate_id, actor="alice")


def test_revoke_from_draft_is_allowed(service):
    rec = service.create(_payload(), actor="alice")
    revoked = service.revoke(rec.mandate_id, actor="alice")
    assert revoked.status == MandateStatus.REVOKED


def test_suspend_resume_cycle(service):
    rec = service.create(_payload(), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    suspended = service.suspend(rec.mandate_id, actor="alice")
    assert suspended.status == MandateStatus.SUSPENDED
    resumed = service.resume(rec.mandate_id, actor="alice")
    assert resumed.status == MandateStatus.ACTIVE


def test_sign_already_active_rejected(service):
    rec = service.create(_payload(), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    with pytest.raises(MandateStateError):
        service.sign(rec.mandate_id, actor="alice")


def test_get_nonexistent_returns_none(service):
    assert service.get("mnd-does-not-exist") is None


def test_transition_nonexistent_raises(service):
    with pytest.raises(MandateNotFoundError):
        service.sign("mnd-does-not-exist", actor="alice")


# ─── Lookup ──────────────────────────────────────────────────────────────────


def test_list_filters_by_status(service):
    a = service.create(_payload(rum="A"), actor="alice")
    b = service.create(_payload(rum="B"), actor="alice")
    service.sign(a.mandate_id, actor="alice")
    drafts = service.list(status=MandateStatus.DRAFT)
    actives = service.list(status=MandateStatus.ACTIVE)
    assert {m.mandate_id for m in drafts} == {b.mandate_id}
    assert {m.mandate_id for m in actives} == {a.mandate_id}


def test_list_filters_by_tenant(service):
    service.create(_payload(rum="A"), actor="alice", tenant_id="tenant-1")
    service.create(_payload(rum="B"), actor="alice", tenant_id="tenant-2")
    t1 = service.list(tenant_id="tenant-1")
    t2 = service.list(tenant_id="tenant-2")
    assert len(t1) == 1
    assert len(t2) == 1
    assert t1[0].tenant_id == "tenant-1"


def test_find_active_candidate_returns_match(service):
    from p2p_fraud.security.iban import iban_fingerprint

    iban = "FR7630001007941234567890185"
    rec = service.create(_payload(debtor_iban=iban), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    candidate = service.find_active_candidate(
        debtor_iban_fingerprint=iban_fingerprint(iban),
        creditor_ics="FR18ZZZ002305",
        rum="RUM-EDF-001",
    )
    assert candidate is not None
    assert candidate.mandate_id == rec.mandate_id


def test_find_active_candidate_excludes_draft(service):
    from p2p_fraud.security.iban import iban_fingerprint

    iban = "FR7630001007941234567890185"
    service.create(_payload(debtor_iban=iban), actor="alice")
    # pas signé : reste en DRAFT
    candidate = service.find_active_candidate(
        debtor_iban_fingerprint=iban_fingerprint(iban),
        creditor_ics="FR18ZZZ002305",
        rum="RUM-EDF-001",
    )
    assert candidate is None


def test_find_active_candidate_excludes_revoked(service):
    from p2p_fraud.security.iban import iban_fingerprint

    iban = "FR7630001007941234567890185"
    rec = service.create(_payload(debtor_iban=iban), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    service.revoke(rec.mandate_id, actor="alice")
    candidate = service.find_active_candidate(
        debtor_iban_fingerprint=iban_fingerprint(iban),
        creditor_ics="FR18ZZZ002305",
        rum="RUM-EDF-001",
    )
    assert candidate is None


def test_find_active_candidates_returns_all_matching(service):
    """Plusieurs mandats avec même IBAN+ICS mais RUM différentes → tous retournés."""
    from p2p_fraud.security.iban import iban_fingerprint

    iban = "FR7630001007941234567890185"
    r1 = service.create(_payload(debtor_iban=iban, rum="RUM-1"), actor="alice")
    r2 = service.create(_payload(debtor_iban=iban, rum="RUM-2"), actor="alice")
    service.sign(r1.mandate_id, actor="alice")
    service.sign(r2.mandate_id, actor="alice")
    candidates = service.find_active_candidates(
        debtor_iban_fingerprint=iban_fingerprint(iban),
        creditor_ics="FR18ZZZ002305",
        rum=None,  # pas de RUM → tous les candidats actifs
    )
    assert len(candidates) == 2


# ─── Déchiffrement explicite ─────────────────────────────────────────────────


def test_decrypt_iban_returns_clear_value(service):
    iban = "FR7630001007941234567890185"
    rec = service.create(_payload(debtor_iban=iban), actor="alice")
    decrypted = service.decrypt_iban(rec.mandate_id)
    assert decrypted == iban


def test_decrypt_iban_unknown_mandate_returns_none(service):
    assert service.decrypt_iban("mnd-nope") is None


# ─── Audit log ───────────────────────────────────────────────────────────────


def test_audit_event_for_each_mutation(service):
    rec = service.create(_payload(), actor="alice")
    service.sign(rec.mandate_id, actor="alice")
    service.revoke(rec.mandate_id, actor="alice")
    entries = list(service._audit.all())
    kinds = [e.kind for e in entries]
    assert kinds == ["MANDATE_CREATED", "MANDATE_SIGNED", "MANDATE_REVOKED"]
