"""Service `MandateService` — coffre-fort de mandats SEPA.

Garanties :
- IBAN jamais persisté en clair (chiffrement Fernet + fingerprint HMAC)
- Transitions d'état validées contre `ALLOWED_TRANSITIONS`
- Chaque mutation crée une `MandateRevision` (snapshot chiffré + hash) et un
  événement dans l'audit log Ed25519 existant
- `tenant_id` propagé partout (nullable pour mono-tenant initial)
- ICS/RUM/nom créancier bornés selon EPC SDD rulebook
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Engine, text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import Base, make_engine
from p2p_fraud.security.crypto import CryptoService, encrypt_iban
from p2p_fraud.security.iban import iban_fingerprint, normalize_iban
from p2p_fraud.sepa.types import (
    MAX_CREDITOR_NAME_LENGTH,
    MAX_ICS_LENGTH,
    MAX_RUM_LENGTH,
    MandateScheme,
    MandateStatus,
    RevisionReason,
    SequenceType,
    can_transition,
)

log = logging.getLogger(__name__)


class MandateNotFoundError(LookupError):
    """Mandate_id inconnu pour ce tenant."""


class MandateStateError(RuntimeError):
    """Transition d'état refusée (terminal, invalide)."""


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class MandateInput(BaseModel):
    """Payload de création d'un mandat — l'IBAN est ici en clair (sera chiffré)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    creditor_ics: str = Field(..., max_length=MAX_ICS_LENGTH)
    creditor_name: str = Field(..., max_length=MAX_CREDITOR_NAME_LENGTH)
    creditor_country: str | None = Field(default=None, min_length=2, max_length=2)
    debtor_iban: str
    debtor_label: str | None = None
    rum: str = Field(..., max_length=MAX_RUM_LENGTH)
    scheme: MandateScheme = MandateScheme.SDD_CORE
    sequence_type: SequenceType = SequenceType.RCUR
    max_amount_cents: int | None = Field(default=None, ge=0)
    currency: str = "EUR"
    frequency: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("debtor_iban")
    @classmethod
    def _strip_iban(cls, v: str) -> str:
        s = "".join(v.split()).upper()
        if len(s) < 8:
            raise ValueError("IBAN trop court")
        return s


@dataclass(frozen=True)
class MandateRecord:
    """Vue applicative d'un mandat — IBAN toujours masqué dans cet objet.

    L'IBAN en clair n'est accessible que via `MandateService.decrypt_iban`
    avec une autorisation explicite (à plumber dans la couche API/RBAC).
    """

    mandate_id: str
    tenant_id: str | None
    creditor_id: str
    creditor_ics: str
    creditor_name: str | None
    debtor_account_id: str
    debtor_iban_fingerprint: str
    rum: str
    scheme: MandateScheme
    sequence_type: SequenceType
    status: MandateStatus
    max_amount_cents: int | None
    currency: str
    frequency: str | None
    valid_from: str | None
    valid_to: str | None
    signed_at: str | None
    revoked_at: str | None
    commitment_hash: str | None
    current_revision_id: str | None
    created_at: str
    updated_at: str

    @property
    def is_active(self) -> bool:
        return self.status == MandateStatus.ACTIVE


class MandateService:
    """Coffre-fort de mandats SEPA — CRUD + transitions + audit chain."""

    def __init__(
        self,
        engine: Engine | None = None,
        *,
        audit_log: AuditLog | None = None,
        crypto: CryptoService | None = None,
        hmac_secret: bytes | None = None,
        db_path: str = ":memory:",
    ) -> None:
        self._engine = engine or make_engine(db_path=db_path)
        Base.metadata.create_all(self._engine, checkfirst=True)
        self._audit = audit_log or AuditLog(engine=self._engine)
        self._crypto = crypto or CryptoService()
        self._hmac_secret = hmac_secret  # None → lit env via security.iban

    # ─── Création ────────────────────────────────────────────────────────────

    def create(
        self,
        payload: MandateInput,
        *,
        actor: str,
        tenant_id: str | None = None,
    ) -> MandateRecord:
        """Crée un mandat en DRAFT, upsert Creditor et BankAccount au passage."""
        now = _now_iso()
        normalized = normalize_iban(payload.debtor_iban)
        fp = iban_fingerprint(normalized, secret=self._hmac_secret)
        ciphertext = encrypt_iban(normalized, service=self._crypto)

        with self._engine.begin() as conn:
            creditor_id = self._upsert_creditor(
                conn,
                tenant_id=tenant_id,
                ics=payload.creditor_ics,
                name=payload.creditor_name,
                country=payload.creditor_country,
                now=now,
            )
            account_id = self._upsert_bank_account(
                conn,
                tenant_id=tenant_id,
                fingerprint=fp,
                ciphertext=ciphertext,
                label=payload.debtor_label,
                currency=payload.currency,
                now=now,
            )
            mandate_id = _new_id("mnd")
            self._insert_mandate(
                conn,
                mandate_id=mandate_id,
                tenant_id=tenant_id,
                creditor_id=creditor_id,
                debtor_account_id=account_id,
                payload=payload,
                actor=actor,
                now=now,
            )
            revision = self._append_revision(
                conn,
                mandate_id=mandate_id,
                reason=RevisionReason.CREATED,
                snapshot=self._snapshot(
                    payload, mandate_id, creditor_id, account_id, MandateStatus.DRAFT
                ),
                actor=actor,
                now=now,
            )
            conn.execute(
                text("UPDATE mandates SET current_revision_id = :rid WHERE mandate_id = :mid"),
                {"rid": revision["revision_id"], "mid": mandate_id},
            )

        self._audit.append(
            actor=actor,
            kind="MANDATE_CREATED",
            payload={
                "mandate_id": mandate_id,
                "tenant_id": tenant_id,
                "creditor_ics": payload.creditor_ics,
                "rum": payload.rum,
                "scheme": payload.scheme.value,
                "iban_fingerprint": fp,  # fingerprint, jamais l'IBAN clair
            },
        )
        return self.get(mandate_id, tenant_id=tenant_id)  # type: ignore[return-value]

    # ─── Transitions ─────────────────────────────────────────────────────────

    def sign(
        self,
        mandate_id: str,
        *,
        actor: str,
        tenant_id: str | None = None,
        signature_provider: str | None = None,
        signature_evidence_key: str | None = None,
    ) -> MandateRecord:
        """Passe un mandat DRAFT → ACTIVE."""
        return self._transition(
            mandate_id,
            target=MandateStatus.ACTIVE,
            reason=RevisionReason.SIGNED,
            actor=actor,
            tenant_id=tenant_id,
            signature_provider=signature_provider,
            signature_evidence_key=signature_evidence_key,
            audit_kind="MANDATE_SIGNED",
            timestamp_field="signed_at",
        )

    def revoke(
        self,
        mandate_id: str,
        *,
        actor: str,
        tenant_id: str | None = None,
        reason_text: str | None = None,
    ) -> MandateRecord:
        """Passe un mandat actif/draft/suspendu → REVOKED (terminal)."""
        return self._transition(
            mandate_id,
            target=MandateStatus.REVOKED,
            reason=RevisionReason.REVOKED,
            actor=actor,
            tenant_id=tenant_id,
            audit_kind="MANDATE_REVOKED",
            timestamp_field="revoked_at",
            extra_payload={"reason": reason_text} if reason_text else None,
        )

    def suspend(
        self,
        mandate_id: str,
        *,
        actor: str,
        tenant_id: str | None = None,
    ) -> MandateRecord:
        """Passe un mandat ACTIVE → SUSPENDED (transient)."""
        return self._transition(
            mandate_id,
            target=MandateStatus.SUSPENDED,
            reason=RevisionReason.SUSPENDED,
            actor=actor,
            tenant_id=tenant_id,
            audit_kind="MANDATE_SUSPENDED",
        )

    def resume(
        self,
        mandate_id: str,
        *,
        actor: str,
        tenant_id: str | None = None,
    ) -> MandateRecord:
        """Passe un mandat SUSPENDED → ACTIVE."""
        return self._transition(
            mandate_id,
            target=MandateStatus.ACTIVE,
            reason=RevisionReason.RESUMED,
            actor=actor,
            tenant_id=tenant_id,
            audit_kind="MANDATE_RESUMED",
        )

    # ─── Lecture ─────────────────────────────────────────────────────────────

    def get(self, mandate_id: str, *, tenant_id: str | None = None) -> MandateRecord | None:
        with self._engine.begin() as conn:
            row = self._fetch_mandate(conn, mandate_id=mandate_id, tenant_id=tenant_id)
            return self._row_to_record(conn, row) if row else None

    def list(
        self,
        *,
        tenant_id: str | None = None,
        status: MandateStatus | None = None,
        limit: int = 100,
    ) -> list[MandateRecord]:
        sql = "SELECT * FROM mandates WHERE 1=1"
        params: dict[str, Any] = {"limit": limit}
        if tenant_id is not None:
            sql += " AND tenant_id = :tid"
            params["tid"] = tenant_id
        if status is not None:
            sql += " AND status = :st"
            params["st"] = status.value
        sql += " ORDER BY created_at DESC LIMIT :limit"
        with self._engine.begin() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [self._row_to_record(conn, r) for r in rows]

    def find_active_candidate(
        self,
        *,
        tenant_id: str | None = None,
        debtor_iban_fingerprint: str,
        creditor_ics: str,
        rum: str | None = None,
    ) -> MandateRecord | None:
        """Recherche un mandat ACTIVE candidat pour matcher un prélèvement.

        Stratégie : tenant + ICS créancier + fingerprint IBAN débiteur, plus
        RUM si fournie. Retourne le premier match ou None.
        """
        candidates = self.find_active_candidates(
            tenant_id=tenant_id,
            debtor_iban_fingerprint=debtor_iban_fingerprint,
            creditor_ics=creditor_ics,
            rum=rum,
        )
        return candidates[0] if candidates else None

    def find_active_candidates(
        self,
        *,
        tenant_id: str | None = None,
        debtor_iban_fingerprint: str,
        creditor_ics: str,
        rum: str | None = None,
    ) -> list[MandateRecord]:
        """Variante qui retourne tous les candidats actifs (utile pour détecter
        AMBIGUOUS_MANDATE_MATCH).
        """
        return self._find_candidates(
            tenant_id=tenant_id,
            debtor_iban_fingerprint=debtor_iban_fingerprint,
            creditor_ics=creditor_ics,
            rum=rum,
            statuses=(MandateStatus.ACTIVE.value,),
        )

    def find_candidates_any_status(
        self,
        *,
        tenant_id: str | None = None,
        debtor_iban_fingerprint: str,
        creditor_ics: str,
        rum: str | None = None,
    ) -> list[MandateRecord]:
        """Tous les candidats matchant les axes (toutes statuses).

        Utile pour exposer les mandats révoqués à la règle MANDATE_REVOKED
        sans modifier la liste retournée par `find_active_candidates`.
        """
        return self._find_candidates(
            tenant_id=tenant_id,
            debtor_iban_fingerprint=debtor_iban_fingerprint,
            creditor_ics=creditor_ics,
            rum=rum,
            statuses=None,
        )

    def _find_candidates(
        self,
        *,
        tenant_id: str | None,
        debtor_iban_fingerprint: str,
        creditor_ics: str,
        rum: str | None,
        statuses: tuple[str, ...] | None,
    ) -> list[MandateRecord]:
        sql = (
            "SELECT m.* FROM mandates m "
            "JOIN bank_accounts ba ON ba.account_id = m.debtor_account_id "
            "JOIN creditors c ON c.creditor_id = m.creditor_id "
            "WHERE ba.iban_fingerprint = :fp AND c.ics = :ics"
        )
        params: dict[str, Any] = {
            "fp": debtor_iban_fingerprint,
            "ics": creditor_ics,
        }
        if statuses:
            placeholders = ",".join(f":st{i}" for i in range(len(statuses)))
            sql += f" AND m.status IN ({placeholders})"
            params.update({f"st{i}": s for i, s in enumerate(statuses)})
        if tenant_id is not None:
            sql += " AND m.tenant_id = :tid"
            params["tid"] = tenant_id
        if rum is not None:
            sql += " AND m.rum = :rum"
            params["rum"] = rum
        sql += " ORDER BY m.created_at ASC"
        with self._engine.begin() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [self._row_to_record(conn, r) for r in rows]

    def decrypt_iban(self, mandate_id: str, *, tenant_id: str | None = None) -> str | None:
        """Déchiffre l'IBAN d'un mandat. À n'appeler qu'avec authz explicite."""
        with self._engine.begin() as conn:
            row = self._fetch_mandate(conn, mandate_id=mandate_id, tenant_id=tenant_id)
            if not row:
                return None
            ba = (
                conn.execute(
                    text("SELECT iban_ciphertext FROM bank_accounts WHERE account_id = :id"),
                    {"id": row["debtor_account_id"]},
                )
                .mappings()
                .first()
            )
            if not ba:
                return None
            return self._crypto.decrypt(ba["iban_ciphertext"])

    # ─── Privé ───────────────────────────────────────────────────────────────

    def _transition(
        self,
        mandate_id: str,
        *,
        target: MandateStatus,
        reason: RevisionReason,
        actor: str,
        tenant_id: str | None,
        audit_kind: str,
        timestamp_field: str | None = None,
        signature_provider: str | None = None,
        signature_evidence_key: str | None = None,
        extra_payload: dict | None = None,
    ) -> MandateRecord:
        now = _now_iso()
        with self._engine.begin() as conn:
            row = self._fetch_mandate(conn, mandate_id=mandate_id, tenant_id=tenant_id)
            if not row:
                raise MandateNotFoundError(mandate_id)
            current = MandateStatus(row["status"])
            if not can_transition(current, target):
                raise MandateStateError(f"Transition refusée : {current.value} → {target.value}")

            updates = {
                "status": target.value,
                "updated_at": now,
                "mid": mandate_id,
            }
            sql_set = "status = :status, updated_at = :updated_at"
            if timestamp_field:
                updates[timestamp_field] = now
                sql_set += f", {timestamp_field} = :{timestamp_field}"

            # commitment_hash recalculé sur snapshot signé/révoqué
            snapshot = self._snapshot_from_row(row, target)
            commitment_hash = self._hash_snapshot(snapshot)
            updates["commitment_hash"] = commitment_hash
            sql_set += ", commitment_hash = :commitment_hash"

            conn.execute(
                text(f"UPDATE mandates SET {sql_set} WHERE mandate_id = :mid"),
                updates,
            )

            revision = self._append_revision(
                conn,
                mandate_id=mandate_id,
                reason=reason,
                snapshot=snapshot,
                actor=actor,
                now=now,
                signature_provider=signature_provider,
                signature_evidence_key=signature_evidence_key,
            )
            conn.execute(
                text("UPDATE mandates SET current_revision_id = :rid WHERE mandate_id = :mid"),
                {"rid": revision["revision_id"], "mid": mandate_id},
            )

        payload = {
            "mandate_id": mandate_id,
            "tenant_id": tenant_id,
            "from_status": current.value,
            "to_status": target.value,
            "commitment_hash": commitment_hash,
        }
        if extra_payload:
            payload.update(extra_payload)
        self._audit.append(actor=actor, kind=audit_kind, payload=payload)
        result = self.get(mandate_id, tenant_id=tenant_id)
        assert result is not None
        return result

    def _fetch_mandate(self, conn, *, mandate_id: str, tenant_id: str | None) -> Any:
        sql = "SELECT * FROM mandates WHERE mandate_id = :mid"
        params: dict[str, Any] = {"mid": mandate_id}
        if tenant_id is not None:
            sql += " AND tenant_id = :tid"
            params["tid"] = tenant_id
        return conn.execute(text(sql), params).mappings().first()

    def _row_to_record(self, conn, row: Any) -> MandateRecord:
        creditor = (
            conn.execute(
                text("SELECT ics, normalized_name FROM creditors WHERE creditor_id = :id"),
                {"id": row["creditor_id"]},
            )
            .mappings()
            .first()
        )
        account = (
            conn.execute(
                text("SELECT iban_fingerprint FROM bank_accounts WHERE account_id = :id"),
                {"id": row["debtor_account_id"]},
            )
            .mappings()
            .first()
        )
        return MandateRecord(
            mandate_id=row["mandate_id"],
            tenant_id=row["tenant_id"],
            creditor_id=row["creditor_id"],
            creditor_ics=creditor["ics"] if creditor else "",
            creditor_name=creditor["normalized_name"] if creditor else None,
            debtor_account_id=row["debtor_account_id"],
            debtor_iban_fingerprint=account["iban_fingerprint"] if account else "",
            rum=row["rum"],
            scheme=MandateScheme(row["scheme"]),
            sequence_type=SequenceType(row["sequence_type"]),
            status=MandateStatus(row["status"]),
            max_amount_cents=row["max_amount_cents"],
            currency=row["currency"],
            frequency=row["frequency"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
            signed_at=row["signed_at"],
            revoked_at=row["revoked_at"],
            commitment_hash=row["commitment_hash"],
            current_revision_id=row["current_revision_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _upsert_creditor(
        self,
        conn,
        *,
        tenant_id: str | None,
        ics: str,
        name: str,
        country: str | None,
        now: str,
    ) -> str:
        existing = (
            conn.execute(
                text(
                    "SELECT creditor_id FROM creditors "
                    "WHERE COALESCE(tenant_id,'') = COALESCE(:tid,'') AND ics = :ics"
                ),
                {"tid": tenant_id, "ics": ics},
            )
            .mappings()
            .first()
        )
        if existing:
            conn.execute(
                text(
                    "UPDATE creditors SET normalized_name = :name, country = :country, "
                    "updated_at = :now WHERE creditor_id = :id"
                ),
                {
                    "name": name,
                    "country": country,
                    "now": now,
                    "id": existing["creditor_id"],
                },
            )
            return existing["creditor_id"]
        cid = _new_id("cre")
        conn.execute(
            text(
                "INSERT INTO creditors (creditor_id, tenant_id, ics, normalized_name, "
                "country, reputation, first_seen_at, updated_at) "
                "VALUES (:id, :tid, :ics, :name, :country, 50, :now, :now)"
            ),
            {
                "id": cid,
                "tid": tenant_id,
                "ics": ics,
                "name": name,
                "country": country,
                "now": now,
            },
        )
        return cid

    def _upsert_bank_account(
        self,
        conn,
        *,
        tenant_id: str | None,
        fingerprint: str,
        ciphertext: str,
        label: str | None,
        currency: str,
        now: str,
    ) -> str:
        existing = (
            conn.execute(
                text(
                    "SELECT account_id FROM bank_accounts "
                    "WHERE COALESCE(tenant_id,'') = COALESCE(:tid,'') "
                    "AND iban_fingerprint = :fp"
                ),
                {"tid": tenant_id, "fp": fingerprint},
            )
            .mappings()
            .first()
        )
        if existing:
            conn.execute(
                text(
                    "UPDATE bank_accounts SET label = COALESCE(:label, label), "
                    "updated_at = :now WHERE account_id = :id"
                ),
                {"label": label, "now": now, "id": existing["account_id"]},
            )
            return existing["account_id"]
        aid = _new_id("acc")
        conn.execute(
            text(
                "INSERT INTO bank_accounts (account_id, tenant_id, label, "
                "iban_ciphertext, iban_fingerprint, currency, created_at, updated_at) "
                "VALUES (:id, :tid, :label, :ct, :fp, :cur, :now, :now)"
            ),
            {
                "id": aid,
                "tid": tenant_id,
                "label": label,
                "ct": ciphertext,
                "fp": fingerprint,
                "cur": currency,
                "now": now,
            },
        )
        return aid

    def _insert_mandate(
        self,
        conn,
        *,
        mandate_id: str,
        tenant_id: str | None,
        creditor_id: str,
        debtor_account_id: str,
        payload: MandateInput,
        actor: str,
        now: str,
    ) -> None:
        conn.execute(
            text(
                "INSERT INTO mandates (mandate_id, tenant_id, creditor_id, "
                "debtor_account_id, rum, scheme, sequence_type, status, "
                "max_amount_cents, currency, frequency, valid_from, valid_to, "
                "created_by, created_at, updated_at) "
                "VALUES (:mid, :tid, :cid, :aid, :rum, :scheme, :seq, 'DRAFT', "
                ":max, :cur, :freq, :vf, :vt, :actor, :now, :now)"
            ),
            {
                "mid": mandate_id,
                "tid": tenant_id,
                "cid": creditor_id,
                "aid": debtor_account_id,
                "rum": payload.rum,
                "scheme": payload.scheme.value,
                "seq": payload.sequence_type.value,
                "max": payload.max_amount_cents,
                "cur": payload.currency,
                "freq": payload.frequency,
                "vf": payload.valid_from.isoformat() if payload.valid_from else None,
                "vt": payload.valid_to.isoformat() if payload.valid_to else None,
                "actor": actor,
                "now": now,
            },
        )

    def _append_revision(
        self,
        conn,
        *,
        mandate_id: str,
        reason: RevisionReason,
        snapshot: dict,
        actor: str,
        now: str,
        signature_provider: str | None = None,
        signature_evidence_key: str | None = None,
    ) -> dict[str, str]:
        revision_id = _new_id("rev")
        snap_json = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
        snap_hash = hashlib.sha256(snap_json.encode("utf-8")).hexdigest()
        ciphertext = self._crypto.encrypt(snap_json)
        conn.execute(
            text(
                "INSERT INTO mandate_revisions (revision_id, mandate_id, reason, "
                "snapshot_ciphertext, snapshot_hash, signature_provider, "
                "signature_evidence_key, actor, created_at) "
                "VALUES (:rid, :mid, :reason, :ct, :hash, :sp, :sk, :actor, :now)"
            ),
            {
                "rid": revision_id,
                "mid": mandate_id,
                "reason": reason.value,
                "ct": ciphertext,
                "hash": snap_hash,
                "sp": signature_provider,
                "sk": signature_evidence_key,
                "actor": actor,
                "now": now,
            },
        )
        return {"revision_id": revision_id, "snapshot_hash": snap_hash}

    def _snapshot(
        self,
        payload: MandateInput,
        mandate_id: str,
        creditor_id: str,
        debtor_account_id: str,
        status: MandateStatus,
    ) -> dict:
        return {
            "mandate_id": mandate_id,
            "creditor_id": creditor_id,
            "debtor_account_id": debtor_account_id,
            "rum": payload.rum,
            "scheme": payload.scheme.value,
            "sequence_type": payload.sequence_type.value,
            "status": status.value,
            "max_amount_cents": payload.max_amount_cents,
            "currency": payload.currency,
            "frequency": payload.frequency,
            "valid_from": payload.valid_from.isoformat() if payload.valid_from else None,
            "valid_to": payload.valid_to.isoformat() if payload.valid_to else None,
        }

    def _snapshot_from_row(self, row: Any, new_status: MandateStatus) -> dict:
        return {
            "mandate_id": row["mandate_id"],
            "creditor_id": row["creditor_id"],
            "debtor_account_id": row["debtor_account_id"],
            "rum": row["rum"],
            "scheme": row["scheme"],
            "sequence_type": row["sequence_type"],
            "status": new_status.value,
            "max_amount_cents": row["max_amount_cents"],
            "currency": row["currency"],
            "frequency": row["frequency"],
            "valid_from": row["valid_from"],
            "valid_to": row["valid_to"],
        }

    @staticmethod
    def _hash_snapshot(snapshot: dict) -> str:
        canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
