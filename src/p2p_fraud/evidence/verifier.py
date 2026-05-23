"""Vérification d'intégrité d'un Evidence Pack persisté.

Trois contrôles :

1. **Hash payload** : on relit `payload_json` stocké, on recalcule
   `SHA-256(canonical_json(payload))`, on compare au `pack_hash`.
2. **Ancrage audit chain** : si `audit_anchor_seq` est renseigné,
   on vérifie que l'entrée d'audit correspondante existe et porte le
   `hash` attendu. Si `audit_anchor_hash` ne match plus → chain corrompue.
3. **Audit chain globale** : on demande à `AuditLog.verify_chain()` de
   confirmer que la chaîne complète est cohérente. Si non, le pack est
   marqué non valide même si son hash est correct.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import Engine, text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.evidence.canonical import canonical_hash
from p2p_fraud.evidence.types import EvidenceVerificationResult

log = logging.getLogger(__name__)


class EvidenceVerifier:
    """Vérifie l'intégrité d'un Evidence Pack persisté."""

    def __init__(self, engine: Engine, audit_log: AuditLog) -> None:
        self._engine = engine
        self._audit = audit_log

    def verify(self, evidence_pack_id: str, *, tenant_id: str | None = None) -> EvidenceVerificationResult:
        errors: list[str] = []
        with self._engine.begin() as conn:
            sql = "SELECT * FROM evidence_packs WHERE evidence_pack_id = :id"
            params: dict = {"id": evidence_pack_id}
            if tenant_id is not None:
                sql += " AND COALESCE(tenant_id,'') = COALESCE(:tid,'')"
                params["tid"] = tenant_id
            row = conn.execute(text(sql), params).mappings().first()
        if row is None:
            return EvidenceVerificationResult(
                evidence_pack_id=evidence_pack_id,
                valid=False,
                hash_matches=False,
                audit_chain_valid=False,
                audit_anchor_present=False,
                checked_at=datetime.now(UTC).isoformat(),
                errors=("evidence_pack introuvable",),
            )

        # 1. Hash payload
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError as exc:
            return EvidenceVerificationResult(
                evidence_pack_id=evidence_pack_id,
                valid=False,
                hash_matches=False,
                audit_chain_valid=False,
                audit_anchor_present=False,
                checked_at=datetime.now(UTC).isoformat(),
                errors=(f"payload_json invalide : {exc}",),
            )
        _, recomputed = canonical_hash(payload)
        hash_matches = recomputed == row["pack_hash"]
        if not hash_matches:
            errors.append(
                f"pack_hash divergent : stocké {row['pack_hash'][:16]}…, "
                f"recalculé {recomputed[:16]}…"
            )

        # 2. Ancrage audit chain
        audit_anchor_present = False
        anchor_seq = row["audit_anchor_seq"]
        anchor_hash = row["audit_anchor_hash"]
        if anchor_seq is not None:
            with self._engine.begin() as conn:
                anchor_row = conn.execute(
                    text(
                        "SELECT seq, hash FROM audit_log WHERE seq = :seq LIMIT 1"
                    ),
                    {"seq": anchor_seq},
                ).mappings().first()
            if anchor_row is None:
                errors.append(f"audit_anchor_seq {anchor_seq} absent")
            elif anchor_row["hash"] != anchor_hash:
                errors.append(
                    f"audit_anchor_hash divergent : stocké {anchor_hash[:16]}…, "
                    f"trouvé {anchor_row['hash'][:16]}…"
                )
            else:
                audit_anchor_present = True

        # 3. Vérification globale de la chaîne audit
        chain_ok, broken = self._audit.verify_chain()
        if not chain_ok:
            errors.append(f"audit chain rompue aux seq : {broken[:10]}")

        valid = hash_matches and chain_ok and (
            anchor_seq is None or audit_anchor_present
        )
        return EvidenceVerificationResult(
            evidence_pack_id=evidence_pack_id,
            valid=valid,
            hash_matches=hash_matches,
            audit_chain_valid=chain_ok,
            audit_anchor_present=audit_anchor_present,
            checked_at=datetime.now(UTC).isoformat(),
            errors=tuple(errors),
        )
