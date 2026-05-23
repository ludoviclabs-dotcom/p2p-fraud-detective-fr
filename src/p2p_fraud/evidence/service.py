"""Service `EvidenceService` — orchestration création/lecture/vérification.

Responsabilités :
- Charger les objets liés au sujet (DebitEvent + match + assessment + timeline)
- Construire le pack via `EvidenceBuilder`
- Persister `evidence_packs` row
- Auditer `EVIDENCE_PACK_CREATED`
- Exposer get/verify/render

Pour le MVP, le pack est généré uniquement pour `subject_type=DEBIT_EVENT`.
La création nécessite que le `DebitEvent` ait été analysé au moins une fois
(matched_mandate_id renseigné OU à None mais event existant) — le service
relance une analyse pour produire un assessment cohérent.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.evidence.builder import EvidenceBuilder
from p2p_fraud.evidence.renderer import render_html_report
from p2p_fraud.evidence.types import (
    EvidencePackInput,
    EvidencePackRecord,
    EvidenceVerificationResult,
)
from p2p_fraud.evidence.verifier import EvidenceVerifier
from p2p_fraud.persistence import Base, make_engine
from p2p_fraud.sepa.analyzer import SepaAnalyzer
from p2p_fraud.sepa.debit_event import DebitEventInput

log = logging.getLogger(__name__)


class EvidencePackNotFoundError(LookupError):
    """evidence_pack_id inconnu pour ce tenant."""


class EvidenceSubjectNotFoundError(LookupError):
    """Le sujet (debit_event_id) demandé n'existe pas."""


class EvidenceSubjectNotSupported(ValueError):
    """subject_type pas encore implémenté."""


def _new_id() -> str:
    return f"evp-{uuid.uuid4().hex[:16]}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class EvidenceService:
    """Service Evidence Pack — persistance + audit + rendu HTML."""

    def __init__(
        self,
        *,
        engine: Engine | None = None,
        audit_log: AuditLog | None = None,
        analyzer: SepaAnalyzer | None = None,
        db_path: str = ":memory:",
        include_html_report: bool = True,
    ) -> None:
        if analyzer is not None:
            # Service partagé : on hérite de l'engine et de l'audit du SepaAnalyzer
            self._engine = analyzer._engine  # type: ignore[attr-defined]
            self._audit = analyzer.audit
        else:
            self._engine = engine or make_engine(db_path=db_path)
            self._audit = audit_log or AuditLog(engine=self._engine)
        Base.metadata.create_all(self._engine, checkfirst=True)
        self._analyzer = analyzer or SepaAnalyzer(engine=self._engine, audit_log=self._audit)
        self._builder = EvidenceBuilder()
        self._verifier = EvidenceVerifier(self._engine, self._audit)
        self._include_html = include_html_report

    @property
    def audit(self) -> AuditLog:
        return self._audit

    @property
    def analyzer(self) -> SepaAnalyzer:
        return self._analyzer

    # ─── Création ────────────────────────────────────────────────────────────

    def create(
        self,
        payload: EvidencePackInput,
        *,
        actor: str,
        tenant_id: str | None = None,
    ) -> EvidencePackRecord:
        if payload.subject_type != "DEBIT_EVENT":
            raise EvidenceSubjectNotSupported(
                f"subject_type non supporté en v0 : {payload.subject_type}"
            )

        event = self._analyzer.debits.get(payload.subject_id, tenant_id=tenant_id)
        if event is None:
            raise EvidenceSubjectNotFoundError(payload.subject_id)

        # Recalcul d'un assessment cohérent à partir des données persistées :
        # on relance le pipeline avec l'idempotency_key existant → le DebitEvent
        # est récupéré tel quel (idempotent), le matcher + engine reconstruisent
        # le verdict. Ça garantit que l'assessment dans le pack correspond
        # bien à l'état courant de la base.
        analyzed = self._analyzer.analyze(
            DebitEventInput(
                source=event.source,
                idempotency_key=event.idempotency_key,
                creditor_ics=event.creditor_ics,
                creditor_name_raw=event.creditor_name_raw,
                rum=event.rum,
                amount_cents=event.amount_cents,
                currency=event.currency,
                # date types : on remet None pour ne pas re-sérialiser ; idempotent
                debtor_iban=None,
            ),
            actor=actor,
            tenant_id=tenant_id,
        )
        # NB : analyzer.analyze() utilise idempotency → retourne le même event_id

        timeline = (
            self._collect_timeline_for(event.event_id, tenant_id=tenant_id)
            if payload.include_audit_timeline
            else []
        )

        built = self._builder.build_for_debit(
            event=analyzed.event,
            match=analyzed.match,
            assessment=analyzed.assessment,
            timeline=timeline,
            notes=payload.notes,
        )

        # Ancrage à l'audit chain : on prend le dernier seq AU MOMENT du build
        anchor_seq, anchor_hash = self._latest_audit_anchor()

        evidence_pack_id = _new_id()
        now = _now_iso()
        report_html = (
            render_html_report(built.payload, built.pack_hash)
            if self._include_html
            else None
        )

        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO evidence_packs (evidence_pack_id, tenant_id, "
                    "subject_type, subject_id, domain, engine_version, "
                    "pack_hash, audit_anchor_hash, audit_anchor_seq, "
                    "payload_json, report_html, storage_key, actor, created_at) "
                    "VALUES (:id, :tid, :st, :sid, :dom, :ev, :ph, :ah, :as_, "
                    ":payload, :report, NULL, :actor, :now)"
                ),
                {
                    "id": evidence_pack_id,
                    "tid": tenant_id,
                    "st": payload.subject_type,
                    "sid": payload.subject_id,
                    "dom": analyzed.assessment.domain.value,
                    "ev": analyzed.assessment.engine_version,
                    "ph": built.pack_hash,
                    "ah": anchor_hash,
                    "as_": anchor_seq,
                    "payload": built.canonical_json,
                    "report": report_html,
                    "actor": actor,
                    "now": now,
                },
            )

        self._audit.append(
            actor=actor,
            kind="EVIDENCE_PACK_CREATED",
            payload={
                "evidence_pack_id": evidence_pack_id,
                "tenant_id": tenant_id,
                "subject_type": payload.subject_type,
                "subject_id": payload.subject_id,
                "pack_hash": built.pack_hash,
                "engine_version": analyzed.assessment.engine_version,
                "anchor_seq": anchor_seq,
            },
        )
        record = self.get(evidence_pack_id, tenant_id=tenant_id)
        assert record is not None
        return record

    # ─── Lecture ─────────────────────────────────────────────────────────────

    def get(
        self, evidence_pack_id: str, *, tenant_id: str | None = None
    ) -> EvidencePackRecord | None:
        with self._engine.begin() as conn:
            sql = "SELECT * FROM evidence_packs WHERE evidence_pack_id = :id"
            params: dict = {"id": evidence_pack_id}
            if tenant_id is not None:
                sql += " AND COALESCE(tenant_id,'') = COALESCE(:tid,'')"
                params["tid"] = tenant_id
            row = conn.execute(text(sql), params).mappings().first()
            return self._row_to_record(row) if row else None

    def get_report_html(
        self, evidence_pack_id: str, *, tenant_id: str | None = None
    ) -> str | None:
        with self._engine.begin() as conn:
            sql = "SELECT report_html FROM evidence_packs WHERE evidence_pack_id = :id"
            params: dict = {"id": evidence_pack_id}
            if tenant_id is not None:
                sql += " AND COALESCE(tenant_id,'') = COALESCE(:tid,'')"
                params["tid"] = tenant_id
            row = conn.execute(text(sql), params).mappings().first()
            return row["report_html"] if row else None

    def list_for_subject(
        self,
        *,
        subject_type: str,
        subject_id: str,
        tenant_id: str | None = None,
        limit: int = 50,
    ) -> list[EvidencePackRecord]:
        sql = (
            "SELECT * FROM evidence_packs "
            "WHERE subject_type = :st AND subject_id = :sid"
        )
        params: dict = {"st": subject_type, "sid": subject_id, "limit": limit}
        if tenant_id is not None:
            sql += " AND COALESCE(tenant_id,'') = COALESCE(:tid,'')"
            params["tid"] = tenant_id
        sql += " ORDER BY created_at DESC LIMIT :limit"
        with self._engine.begin() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [self._row_to_record(r) for r in rows]

    def verify(
        self, evidence_pack_id: str, *, tenant_id: str | None = None
    ) -> EvidenceVerificationResult:
        return self._verifier.verify(evidence_pack_id, tenant_id=tenant_id)

    # ─── Privé ───────────────────────────────────────────────────────────────

    def _row_to_record(self, row: Any) -> EvidencePackRecord:
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            payload = {}
        return EvidencePackRecord(
            evidence_pack_id=row["evidence_pack_id"],
            tenant_id=row["tenant_id"],
            subject_type=row["subject_type"],
            subject_id=row["subject_id"],
            domain=row["domain"],
            engine_version=row["engine_version"],
            pack_hash=row["pack_hash"],
            audit_anchor_hash=row["audit_anchor_hash"],
            audit_anchor_seq=row["audit_anchor_seq"],
            payload=payload,
            has_report=bool(row["report_html"]),
            storage_key=row["storage_key"],
            actor=row["actor"],
            created_at=row["created_at"],
        )

    def _latest_audit_anchor(self) -> tuple[int | None, str | None]:
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT seq, hash FROM audit_log ORDER BY seq DESC LIMIT 1"
                )
            ).first()
        if row is None:
            return None, None
        return int(row[0]), row[1]

    def _collect_timeline_for(
        self, debit_event_id: str, *, tenant_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Récupère les events d'audit qui mentionnent ce debit_event_id.

        On lit `payload` (JSON) et on filtre par `event_id == debit_event_id`.
        Pour les volumes plus importants, on ajouterait un index applicatif.
        """
        with self._engine.begin() as conn:
            rows = conn.execute(
                text(
                    "SELECT seq, at, actor, kind, payload, prev_hash, hash "
                    "FROM audit_log ORDER BY seq ASC"
                )
            ).mappings().all()
        out: list[dict[str, Any]] = []
        for r in rows:
            try:
                p = json.loads(r["payload"]) if r["payload"] else {}
            except json.JSONDecodeError:
                continue
            if p.get("event_id") != debit_event_id:
                continue
            if tenant_id is not None and p.get("tenant_id") not in (None, tenant_id):
                continue
            out.append(
                {
                    "seq": int(r["seq"]),
                    "at": r["at"],
                    "actor": r["actor"],
                    "kind": r["kind"],
                    "hash": r["hash"],
                }
            )
        return out
