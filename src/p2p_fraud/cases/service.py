"""Service case management — création, assignation, commentaire, clôture motivée.

Garde-fous explicites :
- Toute mutation passe par le service, qui journalise dans `AuditLog`.
- Un case clos n'est plus modifiable (statut, assignation, commentaire OK
  refusé sauf en mode `reopen` futur). On ajoute uniquement des événements.
- Clôture obligatoirement avec `reason` non vide.

Backend agnostique : SQLite (`:memory:` ou fichier) en démo, PostgreSQL en prod
via `Settings.database_url`. La couche persistance utilise SQLAlchemy 2.0.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import Engine, bindparam, text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.mentions import MentionStore, build_mentions
from p2p_fraud.cases.models import Case, CaseEvent, CaseStatus
from p2p_fraud.cases.sla import DEFAULT_SLA, SLAConfig
from p2p_fraud.persistence import Base, make_engine
from p2p_fraud.schema import Finding


class CaseClosedError(RuntimeError):
    """Une mutation a été tentée sur un case déjà clos."""


class CaseNotFoundError(LookupError):
    """Le case_id demandé n'existe pas."""


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


_CASE_COLUMNS = (
    "case_id, finding_ids, invoice_id, vendor_id, title, severity, "
    "exposure_eur, status, decision, assignee, sla_deadline, created_by, created_at, "
    "closed_at, closure_reason, closure_evidence_path"
)

ALLOWED_CASE_DECISIONS = {
    "pending",
    "monitor",
    "request_documents",
    "block_payment",
    "close_false_positive",
}


class CaseService:
    """Persistence des cases + journal d'événements + audit log chaîné.

    Args:
        db_path: chemin SQLite (`:memory:` par défaut). Ignoré si `engine` ou
            `Settings.database_url` est fourni.
        audit_log: instance partagée (par défaut, instance `:memory:` indépendante).
        sla_hours_default: legacy, conservé pour rétrocompat (utilisez `sla_config`).
        sla_config: configuration SLA par sévérité (par défaut `DEFAULT_SLA`).
        mention_store: instance partagée (par défaut, instance `:memory:` indépendante).
        engine: Engine SQLAlchemy partagé (override total).
    """

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        audit_log: AuditLog | None = None,
        *,
        sla_hours_default: int = 5 * 24,
        sla_config: SLAConfig | None = None,
        mention_store: MentionStore | None = None,
        engine: Engine | None = None,
        webhook_dispatcher: object | None = None,
    ) -> None:
        self._engine = engine or make_engine(db_path=db_path)
        Base.metadata.create_all(self._engine, checkfirst=True)
        self._ensure_decision_column()
        self._audit = audit_log or AuditLog(":memory:")
        self._sla_default = timedelta(hours=sla_hours_default)
        self._sla = sla_config or DEFAULT_SLA
        self._mentions = mention_store or MentionStore(":memory:")
        # P5-3 : webhook sortant optionnel (no-op silencieux si non fourni)
        self.webhook_dispatcher = webhook_dispatcher

    @property
    def sla(self) -> SLAConfig:
        return self._sla

    @property
    def mentions(self) -> MentionStore:
        return self._mentions

    @property
    def audit_log(self) -> AuditLog:
        return self._audit

    def _sla_deadline_for(self, severity: str) -> datetime:
        """Calcule la deadline SLA en utilisant la config par sévérité."""
        return self._sla.deadline_for(severity)

    # --- Création ---

    def create_case_from_finding(
        self,
        finding: Finding,
        *,
        actor: str,
        title: str | None = None,
        vendor_id: str | None = None,
    ) -> Case:
        case_id = _new_id("CASE")
        case = Case(
            case_id=case_id,
            finding_ids=[finding.rule_id + "::" + finding.invoice_id],
            invoice_id=finding.invoice_id
            if not finding.invoice_id.startswith("VENDOR::")
            else None,
            vendor_id=vendor_id or finding.evidence.get("vendor_id"),
            title=title or f"{finding.rule_id} — {finding.invoice_id}",
            severity=finding.severity.value,
            exposure_eur=float(finding.evidence.get("exposure_eur") or 0) or None,
            status=CaseStatus.NEW,
            assignee=None,
            sla_deadline=self._sla_deadline_for(finding.severity.value),
            created_by=actor,
        )
        self._persist(case)
        self._record_event(
            case_id, "created", actor, {"rule_id": finding.rule_id, "signal": finding.signal}
        )
        return case

    def create_case_from_findings(
        self,
        findings: list[Finding],
        *,
        actor: str,
        title: str,
        vendor_id: str | None = None,
    ) -> Case:
        if not findings:
            raise ValueError("Au moins un finding requis pour créer un case.")
        max_severity = max(findings, key=lambda f: f.severity_weight).severity.value
        exposure = sum(float(f.evidence.get("exposure_eur") or 0) for f in findings) or None
        case_id = _new_id("CASE")
        case = Case(
            case_id=case_id,
            finding_ids=[f.rule_id + "::" + f.invoice_id for f in findings],
            invoice_id=findings[0].invoice_id
            if not findings[0].invoice_id.startswith("VENDOR::")
            else None,
            vendor_id=vendor_id or findings[0].evidence.get("vendor_id"),
            title=title,
            severity=max_severity,
            exposure_eur=exposure,
            status=CaseStatus.NEW,
            sla_deadline=self._sla_deadline_for(max_severity),
            created_by=actor,
        )
        self._persist(case)
        self._record_event(
            case_id,
            "created",
            actor,
            {"n_findings": len(findings), "title": title},
        )
        return case

    # --- Mutations ---

    def assign(self, case_id: str, assignee: str, *, actor: str) -> Case:
        case = self._fetch_or_raise(case_id)
        self._assert_not_closed(case)
        case.assignee = assignee
        case.status = CaseStatus.TRIAGED if case.status == CaseStatus.NEW else case.status
        self._persist(case)
        self._record_event(case_id, "assigned", actor, {"assignee": assignee})
        return case

    def comment(self, case_id: str, *, actor: str, text: str) -> Case:
        case = self._fetch_or_raise(case_id)
        # Les commentaires post-clôture sont autorisés mais flaggés.
        mentions = build_mentions(case_id=case_id, text=text, mentioned_by=actor)
        if mentions:
            self._mentions.record(mentions)
        self._record_event(
            case_id,
            "commented",
            actor,
            {
                "text": text,
                "post_closure": case.status.is_closed,
                "mentions": [m.mentioned_user for m in mentions],
            },
        )
        return case

    def attach_evidence(self, case_id: str, *, actor: str, path: str, label: str) -> Case:
        case = self._fetch_or_raise(case_id)
        self._record_event(case_id, "evidence_attached", actor, {"path": path, "label": label})
        return case

    def escalate(self, case_id: str, *, actor: str, channel: str, reason: str) -> Case:
        case = self._fetch_or_raise(case_id)
        self._assert_not_closed(case)
        case.status = CaseStatus.ESCALATED
        self._persist(case)
        self._record_event(case_id, "escalated", actor, {"channel": channel, "reason": reason})
        return case

    def set_status(self, case_id: str, status: CaseStatus, *, actor: str) -> Case:
        case = self._fetch_or_raise(case_id)
        self._assert_not_closed(case)
        if status.is_closed:
            raise ValueError("Pour clore un case, utilisez `close()` (motif obligatoire).")
        case.status = status
        self._persist(case)
        self._record_event(case_id, "status_changed", actor, {"to": status.value})
        return case

    def set_decision(self, case_id: str, decision: str, *, actor: str) -> Case:
        decision = decision.strip()
        if decision not in ALLOWED_CASE_DECISIONS:
            raise ValueError(
                f"Decision invalide : {decision}. Choisir parmi {sorted(ALLOWED_CASE_DECISIONS)}."
            )
        case = self._fetch_or_raise(case_id)
        self._assert_not_closed(case)
        if case.decision == decision:
            return case
        case.decision = decision
        self._persist(case)
        self._record_event(case_id, "decision_changed", actor, {"decision": decision})
        return case

    def close(
        self,
        case_id: str,
        status: CaseStatus,
        *,
        actor: str,
        reason: str,
        evidence_path: str | None = None,
    ) -> Case:
        if not status.is_closed:
            raise ValueError(f"Statut {status} n'est pas terminal.")
        if not reason or not reason.strip():
            raise ValueError("Un motif de clôture non vide est obligatoire.")
        case = self._fetch_or_raise(case_id)
        self._assert_not_closed(case)
        case.status = status
        case.closed_at = datetime.now(UTC)
        case.closure_reason = reason.strip()
        case.closure_evidence_path = evidence_path
        self._persist(case)
        self._record_event(
            case_id,
            "closed",
            actor,
            {
                "status": status.value,
                "reason": reason,
                "evidence_path": evidence_path,
            },
        )
        return case

    # --- RGPD art. 17 — droit à l'effacement ---

    def purge_user_data(self, target_user: str, *, actor: str) -> int:
        """Supprime tous les cases créés par `target_user` + leurs événements.

        Action **destructive et persistante** — destinée à l'admin RGPD,
        protégée côté UI par une double confirmation. L'audit log conserve
        une trace `rgpd.erasure` avec le nombre de cases supprimés.

        Args:
            target_user: valeur exacte de `cases.created_by` à purger.
            actor: utilisateur courant exécutant la purge (pour l'audit log).

        Returns:
            Nombre de cases effectivement supprimés.
        """
        with self._engine.begin() as conn:
            rows = conn.execute(
                text("SELECT case_id FROM cases WHERE created_by = :u"),
                {"u": target_user},
            ).all()
            case_ids = [r[0] for r in rows]
            if case_ids:
                conn.execute(
                    text("DELETE FROM case_events WHERE case_id IN :ids").bindparams(
                        bindparam("ids", expanding=True)
                    ),
                    {"ids": case_ids},
                )
                conn.execute(
                    text("DELETE FROM cases WHERE created_by = :u"),
                    {"u": target_user},
                )
        self._audit.append(
            actor=actor,
            kind="rgpd.erasure",
            payload={"target_user": target_user, "n_cases_deleted": len(case_ids)},
        )
        return len(case_ids)

    # --- Lecture ---

    def get(self, case_id: str) -> Case:
        return self._fetch_or_raise(case_id)

    def list_cases(self, *, status: CaseStatus | None = None) -> list[Case]:
        if status:
            sql = (
                f"SELECT {_CASE_COLUMNS} FROM cases WHERE status = :status ORDER BY created_at DESC"
            )
            params = {"status": status.value}
        else:
            sql = f"SELECT {_CASE_COLUMNS} FROM cases ORDER BY created_at DESC"
            params = {}
        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).all()
        return [self._row_to_case(row) for row in rows]

    def list_events(self, case_id: str) -> list[CaseEvent]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT event_id, case_id, kind, actor, payload, at "
                    "FROM case_events WHERE case_id = :case_id ORDER BY at ASC"
                ),
                {"case_id": case_id},
            ).all()
        return [
            CaseEvent(
                event_id=row[0],
                case_id=row[1],
                kind=row[2],
                actor=row[3],
                payload=json.loads(row[4]),
                at=datetime.fromisoformat(row[5]),
            )
            for row in rows
        ]

    # --- Helpers privés ---

    def _persist(self, case: Case) -> None:
        params = {
            "case_id": case.case_id,
            "finding_ids": json.dumps(case.finding_ids),
            "invoice_id": case.invoice_id,
            "vendor_id": case.vendor_id,
            "title": case.title,
            "severity": case.severity,
            "exposure_eur": case.exposure_eur,
            "status": case.status.value,
            "decision": case.decision,
            "assignee": case.assignee,
            "sla_deadline": case.sla_deadline.isoformat() if case.sla_deadline else None,
            "created_by": case.created_by,
            "created_at": case.created_at.isoformat(),
            "closed_at": case.closed_at.isoformat() if case.closed_at else None,
            "closure_reason": case.closure_reason,
            "closure_evidence_path": case.closure_evidence_path,
        }
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    f"INSERT INTO cases ({_CASE_COLUMNS}) "
                    "VALUES (:case_id, :finding_ids, :invoice_id, :vendor_id, :title, "
                    ":severity, :exposure_eur, :status, :decision, :assignee, :sla_deadline, "
                    ":created_by, :created_at, :closed_at, :closure_reason, "
                    ":closure_evidence_path) "
                    "ON CONFLICT(case_id) DO UPDATE SET "
                    "finding_ids=excluded.finding_ids, "
                    "invoice_id=excluded.invoice_id, "
                    "vendor_id=excluded.vendor_id, "
                    "title=excluded.title, "
                    "severity=excluded.severity, "
                    "exposure_eur=excluded.exposure_eur, "
                    "status=excluded.status, "
                    "decision=excluded.decision, "
                    "assignee=excluded.assignee, "
                    "sla_deadline=excluded.sla_deadline, "
                    "closed_at=excluded.closed_at, "
                    "closure_reason=excluded.closure_reason, "
                    "closure_evidence_path=excluded.closure_evidence_path"
                ),
                params,
            )

    def _fetch_or_raise(self, case_id: str) -> Case:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(f"SELECT {_CASE_COLUMNS} FROM cases WHERE case_id = :case_id"),
                {"case_id": case_id},
            ).first()
        if not row:
            raise CaseNotFoundError(case_id)
        return self._row_to_case(row)

    @staticmethod
    def _row_to_case(row) -> Case:
        (
            case_id,
            finding_ids_json,
            invoice_id,
            vendor_id,
            title,
            severity,
            exposure_eur,
            status,
            decision,
            assignee,
            sla_deadline,
            created_by,
            created_at,
            closed_at,
            closure_reason,
            closure_evidence_path,
        ) = row
        return Case(
            case_id=case_id,
            finding_ids=json.loads(finding_ids_json),
            invoice_id=invoice_id,
            vendor_id=vendor_id,
            title=title,
            severity=severity,
            exposure_eur=exposure_eur,
            status=CaseStatus(status),
            decision=decision,
            assignee=assignee,
            sla_deadline=datetime.fromisoformat(sla_deadline) if sla_deadline else None,
            created_by=created_by,
            created_at=datetime.fromisoformat(created_at),
            closed_at=datetime.fromisoformat(closed_at) if closed_at else None,
            closure_reason=closure_reason,
            closure_evidence_path=closure_evidence_path,
        )

    def _record_event(self, case_id: str, kind: str, actor: str, payload: dict) -> CaseEvent:
        event = CaseEvent(
            event_id=_new_id("EV"),
            case_id=case_id,
            kind=kind,
            actor=actor,
            payload=payload,
            at=datetime.now(UTC),
        )
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO case_events (event_id, case_id, kind, actor, payload, at) "
                    "VALUES (:event_id, :case_id, :kind, :actor, :payload, :at)"
                ),
                {
                    "event_id": event.event_id,
                    "case_id": case_id,
                    "kind": kind,
                    "actor": actor,
                    "payload": json.dumps(payload, sort_keys=True),
                    "at": event.at.isoformat(),
                },
            )
        # Audit log immutable
        self._audit.append(
            actor=actor,
            kind=f"case.{kind}",
            payload={"case_id": case_id, **payload},
        )
        # Webhook sortant P5-3 (no-op si dispatcher absent ou désactivé).
        # Tout échec est silencieusement loggé pour ne PAS casser la chaîne
        # d'audit — l'audit log local fait foi en cas d'incident webhook.
        self._dispatch_webhook(kind=kind, case_id=case_id, actor=actor, payload=payload)
        return event

    def _ensure_decision_column(self) -> None:
        """Ajoute `cases.decision` sur les bases SQLite/legacy non migrées."""
        try:
            with self._engine.begin() as conn:
                conn.execute(text("SELECT decision FROM cases LIMIT 1"))
        except Exception:
            try:
                with self._engine.begin() as conn:
                    conn.execute(text("ALTER TABLE cases ADD COLUMN decision VARCHAR(64)"))
            except Exception:
                pass

    def _dispatch_webhook(self, *, kind: str, case_id: str, actor: str, payload: dict) -> None:
        """Envoie l'event au dispatcher si configuré. Catch-all defensive."""
        dispatcher = self.webhook_dispatcher
        if dispatcher is None or not getattr(dispatcher, "enabled", False):
            return
        try:
            from p2p_fraud.webhooks.events import build_event

            evt = build_event(kind=kind, case_id=case_id, actor=actor, payload=payload)
            if evt is None:
                return
            dispatcher.dispatch(evt)  # type: ignore[attr-defined]
        except Exception:
            import logging as _logging

            _logging.getLogger(__name__).warning(
                "webhook dispatch failed for case=%s kind=%s",
                case_id,
                kind,
                exc_info=True,
            )

    @staticmethod
    def _assert_not_closed(case: Case) -> None:
        if case.status.is_closed:
            raise CaseClosedError(
                f"Case {case.case_id} déjà clos ({case.status.value}); seul `comment` est autorisé."
            )
