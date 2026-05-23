"""Tests Evidence Pack — Sprint 4 MandateGuard.

Couvre :
- canonical_json : sérialisation stable et déterministe
- builder : 2 builds successifs même input → même pack_hash
- service : création, get, list, verify, rendu HTML
- audit event EVIDENCE_PACK_CREATED
- vérification : hash match, audit chain valid, ancrage seq
- absence d'IBAN clair dans le payload du pack
"""

from __future__ import annotations

import json

import pytest
from cryptography.fernet import Fernet

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.evidence import EvidenceService, canonical_json, sha256_hex
from p2p_fraud.evidence.builder import EvidenceBuilder
from p2p_fraud.evidence.types import EvidencePackInput
from p2p_fraud.persistence import make_engine
from p2p_fraud.sepa import DebitEventInput, MandateInput, SepaAnalyzer
from p2p_fraud.sepa.types import MandateScheme, SequenceType


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("IBAN_HMAC_SECRET", "evidence-test-secret-32-bytes-aa")


@pytest.fixture
def service():
    engine = make_engine(db_path=":memory:")
    audit = AuditLog(engine=engine)
    analyzer = SepaAnalyzer(engine=engine, audit_log=audit)
    return EvidenceService(analyzer=analyzer)


def _mandate_payload(**overrides) -> MandateInput:
    defaults = {
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name": "EDF SA",
        "debtor_iban": "FR7630001007941234567890185",
        "rum": "RUM-EDF-001",
        "scheme": MandateScheme.SDD_CORE,
        "sequence_type": SequenceType.RCUR,
        "max_amount_cents": 10000,
    }
    defaults.update(overrides)
    return MandateInput(**defaults)


def _debit_payload(**overrides) -> DebitEventInput:
    defaults = {
        "source": "manual",
        "idempotency_key": "evp-debit-001",
        "creditor_ics": "FR18ZZZ002305",
        "creditor_name_raw": "EDF SA",
        "rum": "RUM-EDF-001",
        "amount_cents": 8900,
        "debtor_iban": "FR7630001007941234567890185",
    }
    defaults.update(overrides)
    return DebitEventInput(**defaults)


# ─── canonical_json ──────────────────────────────────────────────────────────


def test_canonical_json_sorts_keys():
    a = canonical_json({"b": 1, "a": 2})
    b = canonical_json({"a": 2, "b": 1})
    assert a == b == '{"a":2,"b":1}'


def test_canonical_json_no_whitespace():
    out = canonical_json({"k": [1, 2], "v": {"x": "y"}})
    assert " " not in out


def test_canonical_json_unicode():
    out = canonical_json({"name": "EDF Énergie"})
    assert "Énergie" in out  # ensure_ascii=False


def test_sha256_hex_stable():
    assert sha256_hex("test") == sha256_hex("test")
    assert sha256_hex("a") != sha256_hex("b")


# ─── Builder déterministe ────────────────────────────────────────────────────


def test_builder_idempotent_for_same_inputs(service):
    """2 builds successifs du même DebitEvent (mêmes données) → même pack_hash."""
    mandate = service.analyzer.mandates.create(_mandate_payload(), actor="alice")
    service.analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")

    builder = EvidenceBuilder()
    # NB : on remplace `assessed_at` qui contient un now() → on prend le même
    # assessment des deux côtés pour tester l'idempotence du builder lui-même.
    built_1 = builder.build_for_debit(
        event=analyzed.event, match=analyzed.match, assessment=analyzed.assessment
    )
    built_2 = builder.build_for_debit(
        event=analyzed.event, match=analyzed.match, assessment=analyzed.assessment
    )
    assert built_1.pack_hash == built_2.pack_hash
    assert built_1.canonical_json == built_2.canonical_json


def test_builder_hash_changes_when_score_changes(service):
    mandate = service.analyzer.mandates.create(_mandate_payload(), actor="alice")
    service.analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    a = service.analyzer.analyze(_debit_payload(idempotency_key="A"), actor="alice")
    # Second event avec dépassement → assessment différent
    b = service.analyzer.analyze(
        _debit_payload(idempotency_key="B", amount_cents=50000),
        actor="alice",
    )
    builder = EvidenceBuilder()
    ha = builder.build_for_debit(event=a.event, match=a.match, assessment=a.assessment).pack_hash
    hb = builder.build_for_debit(event=b.event, match=b.match, assessment=b.assessment).pack_hash
    assert ha != hb


# ─── Service : create / get / verify ────────────────────────────────────────


def test_create_evidence_pack_for_debit_event(service):
    mandate = service.analyzer.mandates.create(_mandate_payload(), actor="alice")
    service.analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")

    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    assert record.evidence_pack_id.startswith("evp-")
    assert record.pack_hash
    assert record.subject_id == analyzed.event.event_id
    assert record.engine_version == "sepa-v0.1.0"
    assert record.audit_anchor_seq is not None
    assert record.has_report


def test_create_unknown_subject_raises(service):
    from p2p_fraud.evidence.service import EvidenceSubjectNotFoundError

    with pytest.raises(EvidenceSubjectNotFoundError):
        service.create(
            EvidencePackInput(subject_type="DEBIT_EVENT", subject_id="dbt-nope"),
            actor="alice",
        )


def test_create_unsupported_subject_raises(service):
    from p2p_fraud.evidence.service import EvidenceSubjectNotSupported

    with pytest.raises(EvidenceSubjectNotSupported):
        service.create(
            EvidencePackInput(subject_type="UNKNOWN", subject_id="x"),
            actor="alice",
        )


def test_get_returns_record(service):
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")
    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    fetched = service.get(record.evidence_pack_id)
    assert fetched is not None
    assert fetched.pack_hash == record.pack_hash
    # Payload retrieved is the parsed canonical dict
    assert fetched.payload.get("format_version") == "1.0.0"


def test_list_for_subject_returns_packs(service):
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")
    service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    packs = service.list_for_subject(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id)
    assert len(packs) == 1


def test_get_report_html_returns_html(service):
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")
    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    html = service.get_report_html(record.evidence_pack_id)
    assert html is not None
    assert "<html" in html.lower()
    assert record.pack_hash in html  # footer
    assert "NO_ACTIVE_MANDATE" in html or "Décision" in html


# ─── Audit chain ─────────────────────────────────────────────────────────────


def test_audit_records_evidence_pack_created(service):
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")
    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    kinds = [e.kind for e in service.audit.all()]
    assert "EVIDENCE_PACK_CREATED" in kinds
    evp_event = next(e for e in service.audit.all() if e.kind == "EVIDENCE_PACK_CREATED")
    assert evp_event.payload["evidence_pack_id"] == record.evidence_pack_id
    assert evp_event.payload["pack_hash"] == record.pack_hash


def test_payload_does_not_leak_iban_clear(service):
    """Le payload canonical ne doit jamais contenir l'IBAN clair."""
    iban = "FR7630001007941234567890185"
    mandate = service.analyzer.mandates.create(_mandate_payload(debtor_iban=iban), actor="alice")
    service.analyzer.mandates.sign(mandate.mandate_id, actor="alice")
    analyzed = service.analyzer.analyze(_debit_payload(debtor_iban=iban), actor="alice")
    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    canonical = json.dumps(record.payload)
    assert iban not in canonical
    assert iban[:10] not in canonical


# ─── Verification ────────────────────────────────────────────────────────────


def test_verify_passes_on_unmodified_pack(service):
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")
    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    result = service.verify(record.evidence_pack_id)
    assert result.valid is True
    assert result.hash_matches is True
    assert result.audit_chain_valid is True
    assert result.audit_anchor_present is True
    assert result.errors == ()


def test_verify_fails_when_payload_tampered(service):
    """Si on modifie payload_json en base, la verif doit échouer."""
    from sqlalchemy import text

    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice")
    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
    )
    # Tamper : on change un champ après coup
    with service._engine.begin() as conn:
        original = conn.execute(
            text("SELECT payload_json FROM evidence_packs WHERE evidence_pack_id = :id"),
            {"id": record.evidence_pack_id},
        ).scalar()
        tampered = original.replace('"amount_cents":8900', '"amount_cents":99999')
        conn.execute(
            text("UPDATE evidence_packs SET payload_json = :p WHERE evidence_pack_id = :id"),
            {"p": tampered, "id": record.evidence_pack_id},
        )
    result = service.verify(record.evidence_pack_id)
    assert result.valid is False
    assert result.hash_matches is False
    assert any("pack_hash divergent" in e for e in result.errors)


def test_verify_unknown_pack_returns_invalid(service):
    result = service.verify("evp-does-not-exist")
    assert result.valid is False
    assert "introuvable" in " ".join(result.errors)


# ─── Tenant isolation ────────────────────────────────────────────────────────


def test_evidence_isolated_by_tenant(service):
    analyzed = service.analyzer.analyze(_debit_payload(), actor="alice", tenant_id="t-1")
    record = service.create(
        EvidencePackInput(subject_type="DEBIT_EVENT", subject_id=analyzed.event.event_id),
        actor="alice",
        tenant_id="t-1",
    )
    # Recherche depuis tenant-2 ne doit rien retourner
    assert service.get(record.evidence_pack_id, tenant_id="t-2") is None
    assert service.get(record.evidence_pack_id, tenant_id="t-1") is not None
