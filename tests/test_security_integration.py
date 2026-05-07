"""Tests d'intégration sécurité — Sprint 8 hardening.

- RBAC × case service (manager peut clore, viewer non, mode strict).
- Tampering avancés sur audit log (suppression de ligne, swap de hash entre
  deux entrées, prev_hash forgé).
"""

from __future__ import annotations

import os
import sqlite3

import pytest

from p2p_fraud.cases.audit_log import GENESIS_HASH, AuditLog
from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import CaseService
from p2p_fraud.schema import Finding, Severity
from p2p_fraud.security.auth import (
    AuthError,
    AuthService,
    Role,
    User,
    hash_password,
    requires_role,
)


def _make_user(name: str, role: Role) -> User:
    salt, h, it = hash_password("p")
    return User(username=name, role=role, salt_hex=salt, hash_hex=h, iterations=it)


def _f() -> Finding:
    return Finding(
        invoice_id="INV1",
        detector="master_data",
        signal="iban_change_without_4eyes",
        severity=Severity.CRITICAL,
        rule_id="MD_IBAN_NO_4EYES",
        evidence={"vendor_id": "V1", "exposure_eur": 10_000.0},
    )


# --- RBAC × Case service ---


def test_close_case_through_rbac_decorator(monkeypatch):
    """En mode strict, un viewer ne doit pas pouvoir clore un case via un wrapper protégé."""
    monkeypatch.setenv("P2P_FRAUD_AUTH_REQUIRED", "1")

    service = CaseService(":memory:", AuditLog(":memory:"))
    case = service.create_case_from_finding(_f(), actor="alice")

    @requires_role(Role.MANAGER)
    def close_case(case_id: str, *, current_user: User | None = None) -> None:
        service.close(
            case_id,
            CaseStatus.CLOSED_CONFIRMED,
            actor=current_user.username if current_user else "anon",
            reason="ok",
        )

    viewer = _make_user("v", Role.VIEWER)
    manager = _make_user("m", Role.MANAGER)

    with pytest.raises(AuthError, match="insuffisant"):
        close_case(case.case_id, current_user=viewer)

    # Mais un manager peut clore
    close_case(case.case_id, current_user=manager)
    final = service.get(case.case_id)
    assert final.status == CaseStatus.CLOSED_CONFIRMED
    os.environ.pop("P2P_FRAUD_AUTH_REQUIRED", None)


def test_audit_service_blocks_anonymous_when_users_present():
    svc = AuthService(users=[_make_user("alice", Role.ANALYST)])
    assert not svc.has_permission(None, Role.VIEWER)


def test_audit_service_grants_when_no_users_demo_mode():
    svc = AuthService(users=[])
    assert svc.has_permission(None, Role.ADMIN)


# --- Audit log tampering avancés ---


def test_chain_detects_deleted_entry(tmp_path):
    db = tmp_path / "audit.sqlite"
    log = AuditLog(db)
    for i in range(5):
        log.append(actor="u", kind="evt", payload={"i": i})
    log.close()

    raw = sqlite3.connect(db)
    raw.execute("DELETE FROM audit_log WHERE seq = 3")
    raw.commit()
    raw.close()

    log2 = AuditLog(db)
    valid, _ = log2.verify_chain()
    # La séquence 4 a un prev_hash qui ne match plus le hash de seq 2
    assert valid is False


def test_chain_detects_swapped_hashes(tmp_path):
    """Si deux entrées voient leurs hashes échangés, la chaîne doit révéler la fraude."""
    db = tmp_path / "audit.sqlite"
    log = AuditLog(db)
    for i in range(4):
        log.append(actor="u", kind="evt", payload={"i": i})
    log.close()

    raw = sqlite3.connect(db)
    cur = raw.cursor()
    cur.execute("SELECT seq, hash FROM audit_log ORDER BY seq ASC")
    rows = cur.fetchall()
    h1 = rows[0][1]
    h2 = rows[1][1]
    cur.execute("UPDATE audit_log SET hash = ? WHERE seq = 1", (h2,))
    cur.execute("UPDATE audit_log SET hash = ? WHERE seq = 2", (h1,))
    raw.commit()
    raw.close()

    log2 = AuditLog(db)
    valid, _ = log2.verify_chain()
    assert valid is False


def test_chain_detects_forged_prev_hash_continuity(tmp_path):
    """Si un attaquant insère une entrée avec un prev_hash forgé pour faire croire
    à la continuité, la vérification de hash unitaire la détecte."""
    db = tmp_path / "audit.sqlite"
    log = AuditLog(db)
    log.append(actor="u", kind="evt", payload={"i": 0})
    log.append(actor="u", kind="evt", payload={"i": 1})
    log.close()

    raw = sqlite3.connect(db)
    # Insère une entrée seq=3 avec prev_hash = hash de seq=2 mais payload modifié
    cur = raw.cursor()
    cur.execute("SELECT hash FROM audit_log WHERE seq = 2")
    h2 = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO audit_log (seq, at, actor, kind, payload, prev_hash, hash) "
        "VALUES (3, '2026-01-01T00:00:00+00:00', 'attacker', 'forged', "
        "'{\"backdoor\": true}', ?, 'fake_hash_value')",
        (h2,),
    )
    raw.commit()
    raw.close()

    log2 = AuditLog(db)
    valid, invalid = log2.verify_chain()
    assert valid is False
    assert 3 in invalid


def test_chain_with_first_entry_genesis(tmp_path):
    """La toute première entrée doit avoir prev_hash = GENESIS_HASH."""
    db = tmp_path / "audit.sqlite"
    log = AuditLog(db)
    e = log.append(actor="u", kind="evt", payload={})
    assert e.prev_hash == GENESIS_HASH


def test_full_lifecycle_audit_with_multiple_users(monkeypatch):
    """Cycle complet : 3 utilisateurs, 1 case, audit log valide."""
    monkeypatch.setenv("P2P_FRAUD_AUTH_REQUIRED", "1")
    service = CaseService(":memory:", AuditLog(":memory:"))

    case = service.create_case_from_finding(_f(), actor="alice")
    service.assign(case.case_id, "bob", actor="alice")
    service.comment(case.case_id, actor="bob", text="Vu")
    service.escalate(case.case_id, actor="bob", channel="legal", reason="High")
    service.close(
        case.case_id,
        CaseStatus.CLOSED_CONFIRMED,
        actor="charlie",
        reason="Confirmé",
    )

    entries = service.audit_log.all()
    assert [e.actor for e in entries] == ["alice", "alice", "bob", "bob", "charlie"]
    valid, _ = service.audit_log.verify_chain()
    assert valid
    os.environ.pop("P2P_FRAUD_AUTH_REQUIRED", None)
