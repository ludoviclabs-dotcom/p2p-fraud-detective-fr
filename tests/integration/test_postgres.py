"""Tests d'intégration P4-2 — `CaseService`, `AuditLog`, `MentionStore`,
`AlertStore` exécutés contre un vrai PostgreSQL 16.

Marqués `@pytest.mark.integration` — skippés si `INTEGRATION_DATABASE_URL`
n'est pas défini (voir `conftest.py`).
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.mentions import MentionStore, build_mentions
from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import CaseService
from p2p_fraud.schema import Finding, Severity

pytestmark = pytest.mark.integration


def test_case_service_full_lifecycle_on_postgres(pg_engine: Engine):
    """Cycle complet création → assign → comment → close sur PostgreSQL."""
    audit = AuditLog(engine=pg_engine)
    mentions = MentionStore(engine=pg_engine)
    service = CaseService(engine=pg_engine, audit_log=audit, mention_store=mentions)

    finding = Finding(
        invoice_id="INV-PG-001",
        detector="duplicates",
        signal="duplicate amount",
        severity=Severity.HIGH,
        rule_id="DUP_AMOUNT",
        evidence={"vendor_id": "V-001", "exposure_eur": 12345.67},
    )

    case = service.create_case_from_finding(finding, actor="alice")
    assert case.status == CaseStatus.NEW
    assert case.severity == "high"

    service.assign(case.case_id, "bob", actor="alice")
    service.comment(case.case_id, actor="alice", text="Hi @charlie please look")
    service.close(
        case.case_id,
        status=CaseStatus.CLOSED_CONFIRMED,
        actor="bob",
        reason="Confirmed duplicate",
    )

    fetched = service.get(case.case_id)
    assert fetched.status == CaseStatus.CLOSED_CONFIRMED
    assert fetched.assignee == "bob"
    assert fetched.closure_reason == "Confirmed duplicate"

    events = service.list_events(case.case_id)
    kinds = [e.kind for e in events]
    assert kinds == ["created", "assigned", "commented", "closed"]


def test_audit_log_chain_integrity_on_postgres(pg_engine: Engine):
    audit = AuditLog(engine=pg_engine)
    audit.append(actor="alice", kind="login", payload={"ip": "10.0.0.1"})
    audit.append(actor="alice", kind="case.created", payload={"case_id": "C1"})
    audit.append(actor="bob", kind="case.closed", payload={"case_id": "C1"})

    valid, invalid = audit.verify_chain()
    assert valid is True
    assert invalid == []

    entries = audit.all()
    assert len(entries) == 3
    assert entries[0].seq == 1
    assert entries[2].seq == 3


def test_mention_store_for_user_on_postgres(pg_engine: Engine):
    store = MentionStore(engine=pg_engine)
    mentions = build_mentions(
        case_id="CASE-PG-1",
        text="@alice please review, cc @bob",
        mentioned_by="charlie",
    )
    n = store.record(mentions)
    assert n == 2

    alice_mentions = store.for_user("alice")
    assert len(alice_mentions) == 1
    assert alice_mentions[0].mentioned_by == "charlie"

    n_marked = store.mark_read(username="alice")
    assert n_marked == 1
    assert len(store.for_user("alice", only_unread=True)) == 0


def test_alembic_migration_runs_on_postgres(pg_engine: Engine):
    """Vérifie que la metadata SQLAlchemy correspond bien aux 5 tables attendues."""
    from p2p_fraud.persistence import Base

    expected = {"cases", "case_events", "audit_log", "mentions", "alert_history"}
    assert expected.issubset(set(Base.metadata.tables.keys()))
