"""Store versionné des règles de détection — lifecycle + 4-eyes (Phase 4, ADR-0007).

Lifecycle d'une version de règle :

    draft ──(tests générés passent)──► tested ──(backtest enregistré +
            approbateur ≠ auteur)──► active ──(nouvelle version activée)──► superseded

Invariants appliqués EN CODE (jamais délégués au LLM ni à l'UI) :
- une règle ne peut être activée que si son rapport de tests est intégralement
  vert ET qu'un backtest a été enregistré ;
- l'approbateur doit être différent de l'auteur (4-eyes) — ironique et
  assumé : le produit détecte précisément les changements sans 4-eyes ;
- chaque transition est journalisée dans l'audit log signé du produit
  (kinds `rule.drafted`, `rule.tested`, `rule.backtested`, `rule.activated`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.persistence import make_engine
from p2p_fraud.rules.backtest import BacktestSummary
from p2p_fraud.rules.dsl import RuleSpec, parse_rule_yaml, rule_to_yaml
from p2p_fraud.rules.testing import RuleTestCase, RuleTestReport


class RuleNotFoundError(KeyError):
    pass


class PromotionError(ValueError):
    """La version ne remplit pas les conditions de promotion."""


class FourEyesError(PromotionError):
    """L'approbateur est identique à l'auteur."""


@dataclass(frozen=True)
class RuleVersion:
    rule_id: str
    version: int
    status: str  # draft | tested | active | superseded | rejected
    yaml: str
    author: str
    created_at: str
    name: str
    severity: str
    reason_code: str
    tests_json: str
    test_report_json: str | None
    backtest_json: str | None
    approved_by: str | None
    activated_at: str | None

    @property
    def spec(self) -> RuleSpec:
        return parse_rule_yaml(self.yaml)

    @property
    def test_cases(self) -> list[RuleTestCase]:
        return [RuleTestCase.model_validate(c) for c in json.loads(self.tests_json)]

    @property
    def test_report(self) -> RuleTestReport | None:
        if not self.test_report_json:
            return None
        return RuleTestReport.model_validate_json(self.test_report_json)

    @property
    def backtest(self) -> BacktestSummary | None:
        if not self.backtest_json:
            return None
        return BacktestSummary.model_validate_json(self.backtest_json)


_COLUMNS = (
    "rule_id, version, status, yaml, author, created_at, name, severity, "
    "reason_code, tests_json, test_report_json, backtest_json, approved_by, activated_at"
)


class RuleStore:
    """Versions de règles persistées (SQLite/PostgreSQL, table dédiée)."""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        engine: Engine | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self._engine = engine or make_engine(db_path=db_path)
        self._audit = audit_log
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS rule_versions ("
                    "rule_id TEXT NOT NULL, "
                    "version INTEGER NOT NULL, "
                    "status TEXT NOT NULL, "
                    "yaml TEXT NOT NULL, "
                    "author TEXT NOT NULL, "
                    "created_at TEXT NOT NULL, "
                    "name TEXT NOT NULL, "
                    "severity TEXT NOT NULL, "
                    "reason_code TEXT NOT NULL, "
                    "tests_json TEXT NOT NULL, "
                    "test_report_json TEXT, "
                    "backtest_json TEXT, "
                    "approved_by TEXT, "
                    "activated_at TEXT, "
                    "PRIMARY KEY (rule_id, version))"
                )
            )

    # ─── Écriture ────────────────────────────────────────────────────────────

    def save_draft(
        self,
        spec: RuleSpec,
        *,
        author: str,
        tests: list[RuleTestCase],
    ) -> RuleVersion:
        """Enregistre une nouvelle version (statut draft) d'une règle."""
        yaml_text = rule_to_yaml(spec)
        now = datetime.now(UTC).isoformat()
        with self._engine.begin() as conn:
            last = conn.execute(
                text("SELECT MAX(version) FROM rule_versions WHERE rule_id = :rid"),
                {"rid": spec.rule_id},
            ).scalar()
            version = (last or 0) + 1
            conn.execute(
                text(
                    "INSERT INTO rule_versions (rule_id, version, status, yaml, author, "
                    "created_at, name, severity, reason_code, tests_json) "
                    "VALUES (:rid, :v, 'draft', :yaml, :author, :at, :name, :sev, :rc, :tests)"
                ),
                {
                    "rid": spec.rule_id,
                    "v": version,
                    "yaml": yaml_text,
                    "author": author,
                    "at": now,
                    "name": spec.name,
                    "sev": spec.severity,
                    "rc": spec.reason_code,
                    "tests": json.dumps(
                        [c.model_dump(mode="json") for c in tests], sort_keys=True
                    ),
                },
            )
        self._log("rule.drafted", author, {"rule_id": spec.rule_id, "version": version})
        return self.get(spec.rule_id, version)

    def record_test_report(
        self, rule_id: str, version: int, report: RuleTestReport, *, actor: str
    ) -> RuleVersion:
        """Enregistre le rapport de tests ; statut tested si tout est vert."""
        current = self.get(rule_id, version)
        if current.status in ("active", "superseded"):
            raise PromotionError(f"Version {version} déjà {current.status} — figée.")
        new_status = "tested" if report.all_passed else "draft"
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE rule_versions SET test_report_json = :rep, status = :st "
                    "WHERE rule_id = :rid AND version = :v"
                ),
                {
                    "rep": report.model_dump_json(),
                    "st": new_status,
                    "rid": rule_id,
                    "v": version,
                },
            )
        self._log(
            "rule.tested",
            actor,
            {
                "rule_id": rule_id,
                "version": version,
                "all_passed": report.all_passed,
                "n_passed": report.n_passed,
                "n_total": report.n_total,
            },
        )
        return self.get(rule_id, version)

    def record_backtest(
        self, rule_id: str, version: int, summary: BacktestSummary, *, actor: str
    ) -> RuleVersion:
        """Enregistre le résultat d'un backtest sur dataset labellisé."""
        current = self.get(rule_id, version)
        if current.status in ("active", "superseded"):
            raise PromotionError(f"Version {version} déjà {current.status} — figée.")
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE rule_versions SET backtest_json = :bt "
                    "WHERE rule_id = :rid AND version = :v"
                ),
                {"bt": summary.model_dump_json(), "rid": rule_id, "v": version},
            )
        self._log(
            "rule.backtested",
            actor,
            {
                "rule_id": rule_id,
                "version": version,
                "n_flagged": summary.n_flagged,
                "n_false_positive": summary.n_false_positive,
                "precision": summary.precision,
            },
        )
        return self.get(rule_id, version)

    def activate(self, rule_id: str, version: int, *, approver: str) -> RuleVersion:
        """Promotion 4-eyes : tests verts + backtest présent + approbateur ≠ auteur."""
        current = self.get(rule_id, version)
        if current.status == "active":
            raise PromotionError(f"Version {version} déjà active.")
        report = current.test_report
        if report is None or not report.all_passed:
            raise PromotionError(
                "Activation refusée : le rapport de tests doit être intégralement vert."
            )
        if current.backtest_json is None:
            raise PromotionError(
                "Activation refusée : un backtest sur dataset labellisé est requis."
            )
        if approver.strip().lower() == current.author.strip().lower():
            raise FourEyesError(
                "Activation refusée : l'approbateur doit être différent de l'auteur (4-eyes)."
            )
        now = datetime.now(UTC).isoformat()
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE rule_versions SET status = 'superseded' "
                    "WHERE rule_id = :rid AND status = 'active'"
                ),
                {"rid": rule_id},
            )
            conn.execute(
                text(
                    "UPDATE rule_versions SET status = 'active', approved_by = :by, "
                    "activated_at = :at WHERE rule_id = :rid AND version = :v"
                ),
                {"by": approver, "at": now, "rid": rule_id, "v": version},
            )
        self._log(
            "rule.activated",
            approver,
            {"rule_id": rule_id, "version": version, "author": current.author},
        )
        return self.get(rule_id, version)

    # ─── Lecture ─────────────────────────────────────────────────────────────

    def get(self, rule_id: str, version: int) -> RuleVersion:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    f"SELECT {_COLUMNS} FROM rule_versions "
                    "WHERE rule_id = :rid AND version = :v"
                ),
                {"rid": rule_id, "v": version},
            ).first()
        if row is None:
            raise RuleNotFoundError(f"Règle {rule_id} v{version} introuvable.")
        return self._row_to_version(row)

    def list_versions(self, rule_id: str | None = None) -> list[RuleVersion]:
        sql = f"SELECT {_COLUMNS} FROM rule_versions"
        params: dict = {}
        if rule_id:
            sql += " WHERE rule_id = :rid"
            params["rid"] = rule_id
        sql += " ORDER BY rule_id ASC, version DESC"
        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).all()
        return [self._row_to_version(r) for r in rows]

    # ─── Interne ─────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_version(row) -> RuleVersion:
        return RuleVersion(
            rule_id=row[0],
            version=row[1],
            status=row[2],
            yaml=row[3],
            author=row[4],
            created_at=row[5],
            name=row[6],
            severity=row[7],
            reason_code=row[8],
            tests_json=row[9],
            test_report_json=row[10],
            backtest_json=row[11],
            approved_by=row[12],
            activated_at=row[13],
        )

    def _log(self, kind: str, actor: str, payload: dict) -> None:
        if self._audit is not None:
            self._audit.append(actor=actor, kind=kind, payload=payload)

    def close(self) -> None:
        self._engine.dispose()
