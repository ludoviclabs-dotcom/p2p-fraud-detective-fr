"""Audit log immutable chaîné par hash SHA-256 (style Merkle-light).

Modèle :
- chaque entrée stocke un hash de son contenu canonique + le hash de l'entrée
  précédente, ce qui rend toute altération a posteriori détectable ;
- les entrées sont écrites en mode append via SQLAlchemy (backend SQLite ou
  PostgreSQL) avec une clé primaire `seq` séquentielle ;
- un export JSON Lines est disponible pour archivage WORM.

Ce n'est pas une blockchain (pas de consensus, pas de PoW). C'est un Merkle log
local suffisant pour prouver l'intégrité chronologique aux CAC, AFA, ACPR.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text

from p2p_fraud.persistence import Base, make_engine

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
    # P5-5 : signature Ed25519 hex (128 chars). Vide pour les entrées
    # historiques antérieures à v0.5.0 ou en mode démo (pas de clé privée).
    signature: str = ""

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

    Quand un `signer` Ed25519 est fourni (P5-5), chaque entrée est
    cryptographiquement signée sur son `hash`. La signature est stockée
    dans la colonne `signature` et vérifiable via `verify_chain()` ou
    `verify_signature()` du module `security/signing.py` à partir de
    la clé publique exposée par `GET /security/public-key`.
    """

    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        engine: Engine | None = None,
        signer: object | None = None,
    ) -> None:
        self._engine = engine or make_engine(db_path=path)
        Base.metadata.create_all(self._engine, checkfirst=True)
        self._signer = signer
        # Migration SQLite legacy : ajouter colonne `signature` si absente
        # (les bases :memory: créées avec checkfirst=True ont déjà la colonne
        # grâce à `Base.metadata.create_all`, mais on défensif les fichiers
        # SQLite préexistants d'une instance v0.4 réutilisée en v0.5).
        self._ensure_signature_column()

    def _ensure_signature_column(self) -> None:
        """Ajoute la colonne `signature` si elle manque (migration legacy)."""
        try:
            with self._engine.begin() as conn:
                conn.execute(text("SELECT signature FROM audit_log LIMIT 1"))
        except Exception:
            try:
                with self._engine.begin() as conn:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN signature TEXT"))
            except Exception:
                pass  # déjà présente (cas race) ou backend qui le supporte mal

    # --- API d'écriture ---

    def append(self, *, actor: str, kind: str, payload: dict | None = None) -> AuditLogEntry:
        payload = payload or {}
        with self._engine.begin() as conn:
            last = conn.execute(
                text("SELECT seq, hash FROM audit_log ORDER BY seq DESC LIMIT 1")
            ).first()
            seq = (last[0] + 1) if last else 1
            prev_hash = last[1] if last else GENESIS_HASH
            at = datetime.now(UTC).isoformat()
            h = AuditLogEntry.compute_hash(seq, at, actor, kind, payload, prev_hash)
            # P5-5 : signe le hash si signer Ed25519 est configuré
            sig = ""
            if self._signer is not None and getattr(self._signer, "enabled", False):
                try:
                    sig = self._signer.sign(h)
                except Exception:
                    sig = ""
            conn.execute(
                text(
                    "INSERT INTO audit_log "
                    "(seq, at, actor, kind, payload, prev_hash, hash, signature) "
                    "VALUES (:seq, :at, :actor, :kind, :payload, :prev_hash, :hash, :signature)"
                ),
                {
                    "seq": seq,
                    "at": at,
                    "actor": actor,
                    "kind": kind,
                    "payload": json.dumps(payload, sort_keys=True),
                    "prev_hash": prev_hash,
                    "hash": h,
                    "signature": sig or None,
                },
            )
        return AuditLogEntry(
            seq=seq,
            at=at,
            actor=actor,
            kind=kind,
            payload=payload,
            prev_hash=prev_hash,
            hash=h,
            signature=sig,
        )

    def append_file_import(
        self,
        *,
        actor: str,
        filename: str,
        content_hash_sha256: str,
        n_rows: int,
    ) -> AuditLogEntry:
        """Journalise l'import d'un fichier avec son hash SHA-256 pour traçabilité WORM."""
        return self.append(
            actor=actor,
            kind="file.imported",
            payload={
                "filename": filename,
                "sha256": content_hash_sha256,
                "n_rows": n_rows,
            },
        )

    # --- API de lecture ---

    def all(self) -> list[AuditLogEntry]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT seq, at, actor, kind, payload, prev_hash, hash, signature "
                    "FROM audit_log ORDER BY seq ASC"
                )
            ).all()
        return [
            AuditLogEntry(
                seq=row[0],
                at=row[1],
                actor=row[2],
                kind=row[3],
                payload=json.loads(row[4]),
                prev_hash=row[5],
                hash=row[6],
                signature=row[7] or "",
            )
            for row in rows
        ]

    def __len__(self) -> int:
        with self._engine.connect() as conn:
            return int(conn.execute(text("SELECT COUNT(*) FROM audit_log")).scalar() or 0)

    # --- Vérification d'intégrité ---

    def verify_chain(self, *, public_key_b64: str = "") -> tuple[bool, list[int]]:
        """Recalcule le hash de chaque entrée et compare au stocké.

        Si `public_key_b64` est fourni, vérifie aussi les signatures Ed25519
        présentes (les entrées sans signature restent valides — backward
        compatible avec les versions antérieures à v0.5.0).

        Retourne (chaîne_valide, liste_des_séquences_invalides).
        """
        from p2p_fraud.security.signing import verify_signature as _vsig

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
                continue
            # P5-5 : vérification signature Ed25519 (uniquement si clé publique
            # fournie ET signature présente — entrées historiques v0.4 OK).
            if (
                public_key_b64
                and e.signature
                and not _vsig(
                    message=e.hash,
                    signature_hex=e.signature,
                    public_key_b64=public_key_b64,
                )
            ):
                invalid.append(e.seq)
            prev = e.hash
        return (not invalid, invalid)

    # --- Export pour archivage ---

    def export_jsonl(self) -> Iterable[str]:
        for entry in self.all():
            yield json.dumps(asdict(entry), sort_keys=True)

    def close(self) -> None:
        self._engine.dispose()
