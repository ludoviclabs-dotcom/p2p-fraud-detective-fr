"""Service `DebitEventService` — ingestion idempotente des prélèvements observés.

Garanties :
- Idempotence par (`tenant_id`, `idempotency_key`) : un second appel avec la
  même clé retourne l'enregistrement existant (pas de duplication, pas d'erreur)
- IBAN débiteur jamais persisté en clair — seul le fingerprint HMAC est stocké
  (la source de l'IBAN reste dans `raw_json` chiffré côté API)
- Audit log événement `DEBIT_IMPORTED` à chaque ingestion
- `creditor_ics`, `rum`, `debtor_iban_fingerprint` sont les axes de matching
  consommés par `MandateMatcher`
"""

from __future__ import annotations

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
from p2p_fraud.security.iban import iban_fingerprint
from p2p_fraud.sepa.types import (
    MAX_CREDITOR_NAME_LENGTH,
    MAX_ICS_LENGTH,
    MAX_RUM_LENGTH,
)

log = logging.getLogger(__name__)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class DebitEventInput(BaseModel):
    """Payload d'ingestion d'un prélèvement observé."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source: str = Field(..., description="csv | manual | api | sandbox")
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    creditor_ics: str | None = Field(default=None, max_length=MAX_ICS_LENGTH)
    creditor_name_raw: str | None = Field(default=None, max_length=MAX_CREDITOR_NAME_LENGTH)
    rum: str | None = Field(default=None, max_length=MAX_RUM_LENGTH)
    amount_cents: int = Field(..., gt=0)
    currency: str = "EUR"
    booking_date: date | None = None
    due_date: date | None = None
    debtor_iban: str | None = None  # clair, sera fingerprinté + redacté
    raw_key: str | None = None

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("debtor_iban")
    @classmethod
    def _strip_iban(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = "".join(v.split()).upper()
        if len(s) < 8:
            raise ValueError("IBAN trop court")
        return s


@dataclass(frozen=True)
class DebitEventRecord:
    """Vue applicative d'un prélèvement observé — pas d'IBAN clair."""

    event_id: str
    tenant_id: str | None
    source: str
    idempotency_key: str
    creditor_ics: str | None
    creditor_name_raw: str | None
    rum: str | None
    amount_cents: int
    currency: str
    booking_date: str | None
    due_date: str | None
    debtor_iban_fingerprint: str | None
    matched_mandate_id: str | None
    created_at: str

    @property
    def amount_eur(self) -> float:
        return self.amount_cents / 100.0


class DebitEventService:
    """Ingestion idempotente + lookup des prélèvements observés."""

    def __init__(
        self,
        engine: Engine | None = None,
        *,
        audit_log: AuditLog | None = None,
        hmac_secret: bytes | None = None,
        db_path: str = ":memory:",
    ) -> None:
        self._engine = engine or make_engine(db_path=db_path)
        Base.metadata.create_all(self._engine, checkfirst=True)
        self._audit = audit_log or AuditLog(engine=self._engine)
        self._hmac_secret = hmac_secret

    # ─── Ingestion ───────────────────────────────────────────────────────────

    def ingest(
        self,
        payload: DebitEventInput,
        *,
        actor: str,
        tenant_id: str | None = None,
    ) -> DebitEventRecord:
        """Insère un prélèvement (idempotent). Retourne l'enregistrement existant
        si la clé d'idempotence est déjà connue pour ce tenant.
        """
        with self._engine.begin() as conn:
            existing = (
                conn.execute(
                    text(
                        "SELECT * FROM debit_events "
                        "WHERE COALESCE(tenant_id,'') = COALESCE(:tid,'') "
                        "AND idempotency_key = :key"
                    ),
                    {"tid": tenant_id, "key": payload.idempotency_key},
                )
                .mappings()
                .first()
            )
            if existing:
                log.debug(
                    "debit_event idempotent hit",
                    extra={"idempotency_key": payload.idempotency_key},
                )
                return self._row_to_record(existing)

            event_id = _new_id("dbt")
            now = _now_iso()
            fp = (
                iban_fingerprint(payload.debtor_iban, secret=self._hmac_secret)
                if payload.debtor_iban
                else None
            )
            # raw_json conserve le payload reçu MAIS sans IBAN clair
            redacted = payload.model_dump(mode="json")
            if redacted.get("debtor_iban"):
                redacted["debtor_iban"] = "[redacted]"
            raw_json = json.dumps(redacted, sort_keys=True, separators=(",", ":"))

            conn.execute(
                text(
                    "INSERT INTO debit_events (event_id, tenant_id, source, "
                    "idempotency_key, creditor_ics, creditor_name_raw, rum, "
                    "amount_cents, currency, booking_date, due_date, "
                    "debtor_iban_fingerprint, raw_key, raw_json, created_at) "
                    "VALUES (:eid, :tid, :src, :key, :ics, :name, :rum, "
                    ":amt, :cur, :bd, :dd, :fp, :rk, :rj, :now)"
                ),
                {
                    "eid": event_id,
                    "tid": tenant_id,
                    "src": payload.source,
                    "key": payload.idempotency_key,
                    "ics": payload.creditor_ics,
                    "name": payload.creditor_name_raw,
                    "rum": payload.rum,
                    "amt": payload.amount_cents,
                    "cur": payload.currency,
                    "bd": payload.booking_date.isoformat() if payload.booking_date else None,
                    "dd": payload.due_date.isoformat() if payload.due_date else None,
                    "fp": fp,
                    "rk": payload.raw_key,
                    "rj": raw_json,
                    "now": now,
                },
            )

        self._audit.append(
            actor=actor,
            kind="DEBIT_IMPORTED",
            payload={
                "event_id": event_id,
                "tenant_id": tenant_id,
                "creditor_ics": payload.creditor_ics,
                "rum": payload.rum,
                "amount_cents": payload.amount_cents,
                "currency": payload.currency,
                "source": payload.source,
                # fingerprint, jamais l'IBAN clair
                "debtor_iban_fingerprint": fp,
            },
        )
        result = self.get(event_id, tenant_id=tenant_id)
        assert result is not None
        return result

    # ─── Lecture ─────────────────────────────────────────────────────────────

    def get(self, event_id: str, *, tenant_id: str | None = None) -> DebitEventRecord | None:
        sql = "SELECT * FROM debit_events WHERE event_id = :eid"
        params: dict[str, Any] = {"eid": event_id}
        if tenant_id is not None:
            sql += " AND tenant_id = :tid"
            params["tid"] = tenant_id
        with self._engine.begin() as conn:
            row = conn.execute(text(sql), params).mappings().first()
            return self._row_to_record(row) if row else None

    def list(
        self,
        *,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[DebitEventRecord]:
        sql = "SELECT * FROM debit_events WHERE 1=1"
        params: dict[str, Any] = {"limit": limit}
        if tenant_id is not None:
            sql += " AND tenant_id = :tid"
            params["tid"] = tenant_id
        sql += " ORDER BY created_at DESC LIMIT :limit"
        with self._engine.begin() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [self._row_to_record(r) for r in rows]

    def mark_matched(
        self, event_id: str, mandate_id: str | None, *, tenant_id: str | None = None
    ) -> None:
        """Mémorise le mandat matché (ou démarche le si `mandate_id` est None)."""
        with self._engine.begin() as conn:
            sql = "UPDATE debit_events SET matched_mandate_id = :mid WHERE event_id = :eid"
            params: dict[str, Any] = {"mid": mandate_id, "eid": event_id}
            if tenant_id is not None:
                sql += " AND COALESCE(tenant_id,'') = COALESCE(:tid,'')"
                params["tid"] = tenant_id
            conn.execute(text(sql), params)

    # ─── Privé ───────────────────────────────────────────────────────────────

    def _row_to_record(self, row: Any) -> DebitEventRecord:
        return DebitEventRecord(
            event_id=row["event_id"],
            tenant_id=row["tenant_id"],
            source=row["source"],
            idempotency_key=row["idempotency_key"],
            creditor_ics=row["creditor_ics"],
            creditor_name_raw=row["creditor_name_raw"],
            rum=row["rum"],
            amount_cents=row["amount_cents"],
            currency=row["currency"],
            booking_date=row["booking_date"],
            due_date=row["due_date"],
            debtor_iban_fingerprint=row["debtor_iban_fingerprint"],
            matched_mandate_id=row["matched_mandate_id"],
            created_at=row["created_at"],
        )
