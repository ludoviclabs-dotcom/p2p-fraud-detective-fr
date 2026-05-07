"""Service case management — création, assignation, commentaire, clôture motivée.

Garde-fous explicites :
- Toute mutation passe par le service, qui journalise dans `AuditLog`.
- Un case clos n'est plus modifiable (statut, assignation, commentaire OK
  refusé sauf en mode `reopen` futur). On ajoute uniquement des événements.
- Clôture obligatoirement avec `reason` non vide.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import Case, CaseEvent, CaseStatus
from p2p_fraud.schema import Finding


class CaseClosedError(RuntimeError):
    """Une mutation a été tentée sur un case déjà clos."""


class CaseNotFoundError(LookupError):
    """Le case_id demandé n'existe pas."""


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class CaseService:
    """Persistence SQLite des cases + journal d'événements + audit log chaîné.

    Le store SQLite et l'audit log peuvent partager la même base de fichier ou
    être séparés (intéressant pour archiver l'audit log en WORM séparément).
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        finding_ids TEXT NOT NULL,
        invoice_id TEXT,
        vendor_id TEXT,
        title TEXT NOT NULL,
        severity TEXT NOT NULL,
        exposure_eur REAL,
        status TEXT NOT NULL,
        assignee TEXT,
        sla_deadline TEXT,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        closed_at TEXT,
        closure_reason TEXT,
        closure_evidence_path TEXT
    );

    CREATE TABLE IF NOT EXISTS case_events (
        event_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        actor TEXT NOT NULL,
        payload TEXT NOT NULL,
        at TEXT NOT NULL
    );
    """

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        audit_log: AuditLog | None = None,
        *,
        sla_hours_default: int = 5 * 24,  # 5 jours ouvrés ≈ approximation simple
    ) -> None:
        self._path = str(db_path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()
        self._audit = audit_log or AuditLog(":memory:")
        self._sla_default = timedelta(hours=sla_hours_default)

    @property
    def audit_log(self) -> AuditLog:
        return self._audit

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
            sla_deadline=datetime.now(UTC) + self._sla_default,
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
            sla_deadline=datetime.now(UTC) + self._sla_default,
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
        self._record_event(
            case_id,
            "commented",
            actor,
            {"text": text, "post_closure": case.status.is_closed},
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

    # --- Lecture ---

    def get(self, case_id: str) -> Case:
        return self._fetch_or_raise(case_id)

    def list_cases(self, *, status: CaseStatus | None = None) -> list[Case]:
        cur = self._conn.cursor()
        if status:
            cur.execute(
                "SELECT * FROM cases WHERE status = ? ORDER BY created_at DESC", (status.value,)
            )
        else:
            cur.execute("SELECT * FROM cases ORDER BY created_at DESC")
        return [self._row_to_case(row) for row in cur.fetchall()]

    def list_events(self, case_id: str) -> list[CaseEvent]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT event_id, case_id, kind, actor, payload, at FROM case_events "
            "WHERE case_id = ? ORDER BY at ASC",
            (case_id,),
        )
        import json

        return [
            CaseEvent(
                event_id=row[0],
                case_id=row[1],
                kind=row[2],
                actor=row[3],
                payload=json.loads(row[4]),
                at=datetime.fromisoformat(row[5]),
            )
            for row in cur.fetchall()
        ]

    # --- Helpers privés ---

    def _persist(self, case: Case) -> None:
        import json

        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO cases (case_id, finding_ids, invoice_id, vendor_id, title, severity,
                               exposure_eur, status, assignee, sla_deadline,
                               created_by, created_at, closed_at, closure_reason,
                               closure_evidence_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                finding_ids=excluded.finding_ids,
                invoice_id=excluded.invoice_id,
                vendor_id=excluded.vendor_id,
                title=excluded.title,
                severity=excluded.severity,
                exposure_eur=excluded.exposure_eur,
                status=excluded.status,
                assignee=excluded.assignee,
                sla_deadline=excluded.sla_deadline,
                closed_at=excluded.closed_at,
                closure_reason=excluded.closure_reason,
                closure_evidence_path=excluded.closure_evidence_path
            """,
            (
                case.case_id,
                json.dumps(case.finding_ids),
                case.invoice_id,
                case.vendor_id,
                case.title,
                case.severity,
                case.exposure_eur,
                case.status.value,
                case.assignee,
                case.sla_deadline.isoformat() if case.sla_deadline else None,
                case.created_by,
                case.created_at.isoformat(),
                case.closed_at.isoformat() if case.closed_at else None,
                case.closure_reason,
                case.closure_evidence_path,
            ),
        )
        self._conn.commit()

    def _fetch_or_raise(self, case_id: str) -> Case:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if not row:
            raise CaseNotFoundError(case_id)
        return self._row_to_case(row)

    @staticmethod
    def _row_to_case(row: tuple) -> Case:
        import json

        (
            case_id,
            finding_ids_json,
            invoice_id,
            vendor_id,
            title,
            severity,
            exposure_eur,
            status,
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
            assignee=assignee,
            sla_deadline=datetime.fromisoformat(sla_deadline) if sla_deadline else None,
            created_by=created_by,
            created_at=datetime.fromisoformat(created_at),
            closed_at=datetime.fromisoformat(closed_at) if closed_at else None,
            closure_reason=closure_reason,
            closure_evidence_path=closure_evidence_path,
        )

    def _record_event(self, case_id: str, kind: str, actor: str, payload: dict) -> CaseEvent:
        import json

        event = CaseEvent(
            event_id=_new_id("EV"),
            case_id=case_id,
            kind=kind,
            actor=actor,
            payload=payload,
            at=datetime.now(UTC),
        )
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO case_events (event_id, case_id, kind, actor, payload, at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                event.event_id,
                case_id,
                kind,
                actor,
                json.dumps(payload, sort_keys=True),
                event.at.isoformat(),
            ),
        )
        self._conn.commit()
        # Audit log immutable
        self._audit.append(
            actor=actor,
            kind=f"case.{kind}",
            payload={"case_id": case_id, **payload},
        )
        return event

    @staticmethod
    def _assert_not_closed(case: Case) -> None:
        if case.status.is_closed:
            raise CaseClosedError(
                f"Case {case.case_id} déjà clos ({case.status.value}); seul `comment` est autorisé."
            )
