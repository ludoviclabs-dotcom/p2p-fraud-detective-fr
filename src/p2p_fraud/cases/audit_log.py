"""Audit log immutable chaîné par hash SHA-256 (style Merkle-light).

Modèle :
- chaque entrée stocke un hash de son contenu canonique + le hash de l'entrée
  précédente, ce qui rend toute altération a posteriori détectable ;
- les entrées sont écrites en mode append dans SQLite (pragma `journal_mode=WAL`,
  table `audit_log` sans clé primaire INTEGER mutable) ;
- un export JSON Lines est disponible pour archivage WORM.

Ce n'est pas une blockchain (pas de consensus, pas de PoW). C'est un Merkle log
local suffisant pour prouver l'intégrité chronologique aux CAC, AFA, ACPR.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class AuditLogEntry:
    seq: int
    at: str  # ISO 8601 UTC
    actor: str
    kind: str
    payload: dict
    prev_hash: str
    hash: str

    @classmethod
    def compute_hash(
        cls, seq: int, at: str, actor: str, kind: str, payload: dict, prev_hash: str
    ) -> str:
        body = {
            "seq": seq,
            "at": at,
            "actor": actor,
            "kind": kind,
            "payload": payload,
            "prev_hash": prev_hash,
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AuditLog:
    """Journal append-only avec vérification d'intégrité.

    Pour les déploiements en mémoire (tests, démo), passer `path=":memory:"`.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS audit_log (
        seq         INTEGER NOT NULL,
        at          TEXT    NOT NULL,
        actor       TEXT    NOT NULL,
        kind        TEXT    NOT NULL,
        payload     TEXT    NOT NULL,
        prev_hash   TEXT    NOT NULL,
        hash        TEXT    NOT NULL,
        PRIMARY KEY (seq)
    );
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        if self._path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(self.SCHEMA)
        self._conn.commit()

    # --- API d'écriture ---

    def append(self, *, actor: str, kind: str, payload: dict | None = None) -> AuditLogEntry:
        payload = payload or {}
        cur = self._conn.cursor()
        cur.execute("SELECT seq, hash FROM audit_log ORDER BY seq DESC LIMIT 1")
        last = cur.fetchone()
        seq = (last[0] + 1) if last else 1
        prev_hash = last[1] if last else GENESIS_HASH
        at = datetime.now(UTC).isoformat()

        h = AuditLogEntry.compute_hash(seq, at, actor, kind, payload, prev_hash)
        cur.execute(
            "INSERT INTO audit_log (seq, at, actor, kind, payload, prev_hash, hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (seq, at, actor, kind, json.dumps(payload, sort_keys=True), prev_hash, h),
        )
        self._conn.commit()
        return AuditLogEntry(
            seq=seq, at=at, actor=actor, kind=kind, payload=payload, prev_hash=prev_hash, hash=h
        )

    # --- API de lecture ---

    def all(self) -> list[AuditLogEntry]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT seq, at, actor, kind, payload, prev_hash, hash FROM audit_log ORDER BY seq ASC"
        )
        return [
            AuditLogEntry(
                seq=row[0],
                at=row[1],
                actor=row[2],
                kind=row[3],
                payload=json.loads(row[4]),
                prev_hash=row[5],
                hash=row[6],
            )
            for row in cur.fetchall()
        ]

    def __len__(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM audit_log")
        return int(cur.fetchone()[0])

    # --- Vérification d'intégrité ---

    def verify_chain(self) -> tuple[bool, list[int]]:
        """Recalcule le hash de chaque entrée et compare au stocké.

        Retourne (chaîne_valide, liste_des_séquences_invalides).
        """
        entries = self.all()
        invalid: list[int] = []
        prev = GENESIS_HASH
        for e in entries:
            if e.prev_hash != prev:
                invalid.append(e.seq)
                prev = e.hash
                continue
            recomputed = AuditLogEntry.compute_hash(
                e.seq, e.at, e.actor, e.kind, e.payload, e.prev_hash
            )
            if recomputed != e.hash:
                invalid.append(e.seq)
            prev = e.hash
        return (not invalid, invalid)

    # --- Export pour archivage ---

    def export_jsonl(self) -> Iterable[str]:
        for entry in self.all():
            yield json.dumps(asdict(entry), sort_keys=True)

    def close(self) -> None:
        self._conn.close()
