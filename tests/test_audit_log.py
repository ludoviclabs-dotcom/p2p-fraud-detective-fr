"""Tests audit log immutable chaîné par hash — Sprint 3."""

from __future__ import annotations

import sqlite3

from p2p_fraud.cases.audit_log import GENESIS_HASH, AuditLog, AuditLogEntry


def test_empty_log_is_valid():
    log = AuditLog(":memory:")
    valid, invalid = log.verify_chain()
    assert valid is True
    assert invalid == []
    assert len(log) == 0


def test_append_increments_seq_and_chains():
    log = AuditLog(":memory:")
    e1 = log.append(actor="alice", kind="test", payload={"a": 1})
    e2 = log.append(actor="bob", kind="test", payload={"b": 2})
    assert e1.seq == 1
    assert e2.seq == 2
    assert e1.prev_hash == GENESIS_HASH
    assert e2.prev_hash == e1.hash


def test_verify_chain_after_normal_inserts():
    log = AuditLog(":memory:")
    for i in range(20):
        log.append(actor=f"u{i}", kind="evt", payload={"i": i})
    valid, invalid = log.verify_chain()
    assert valid is True
    assert invalid == []
    assert len(log) == 20


def test_verify_chain_detects_payload_tampering(tmp_path):
    db = tmp_path / "audit.sqlite"
    log = AuditLog(db)
    log.append(actor="u", kind="evt", payload={"v": 1})
    log.append(actor="u", kind="evt", payload={"v": 2})
    log.append(actor="u", kind="evt", payload={"v": 3})
    log.close()

    # Altération directe de la base : on modifie le payload de l'entrée 2 sans
    # mettre à jour son hash. La vérification doit détecter au moins seq=2 ou
    # toutes les entrées suivantes (la chaîne est rompue à partir de là).
    raw = sqlite3.connect(db)
    raw.execute("UPDATE audit_log SET payload = ? WHERE seq = 2", ('{"v": 999}',))
    raw.commit()
    raw.close()

    log2 = AuditLog(db)
    valid, invalid = log2.verify_chain()
    assert valid is False
    assert 2 in invalid


def test_verify_chain_detects_prev_hash_tampering(tmp_path):
    db = tmp_path / "audit.sqlite"
    log = AuditLog(db)
    for i in range(5):
        log.append(actor="u", kind="evt", payload={"i": i})
    log.close()

    raw = sqlite3.connect(db)
    raw.execute("UPDATE audit_log SET prev_hash = ? WHERE seq = 3", (GENESIS_HASH,))
    raw.commit()
    raw.close()

    log2 = AuditLog(db)
    valid, _invalid = log2.verify_chain()
    assert valid is False


def test_export_jsonl_round_trips():
    import json

    log = AuditLog(":memory:")
    log.append(actor="alice", kind="test", payload={"x": 1})
    log.append(actor="bob", kind="test", payload={"x": 2})
    lines = list(log.export_jsonl())
    assert len(lines) == 2
    payloads = [json.loads(line)["payload"] for line in lines]
    assert payloads == [{"x": 1}, {"x": 2}]


def test_compute_hash_is_deterministic():
    h1 = AuditLogEntry.compute_hash(
        1, "2026-05-07T10:00:00+00:00", "u", "k", {"a": 1}, GENESIS_HASH
    )
    h2 = AuditLogEntry.compute_hash(
        1, "2026-05-07T10:00:00+00:00", "u", "k", {"a": 1}, GENESIS_HASH
    )
    assert h1 == h2


def test_compute_hash_changes_when_payload_changes():
    h1 = AuditLogEntry.compute_hash(
        1, "2026-05-07T10:00:00+00:00", "u", "k", {"a": 1}, GENESIS_HASH
    )
    h2 = AuditLogEntry.compute_hash(
        1, "2026-05-07T10:00:00+00:00", "u", "k", {"a": 2}, GENESIS_HASH
    )
    assert h1 != h2
