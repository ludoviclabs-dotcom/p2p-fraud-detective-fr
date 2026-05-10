"""Persistance des alertes — historique append-only via SQLAlchemy.

Stocke chaque alerte envoyée (avec status par canal) pour audit. Backend
agnostique : SQLite (`:memory:` ou fichier) en démo, PostgreSQL en prod
via `Settings.database_url`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text

from p2p_fraud.alerts.rules import Alert
from p2p_fraud.persistence import Base, make_engine


@dataclass(frozen=True)
class AlertHistoryEntry:
    seq: int
    triggered_at: str
    rule_name: str
    severity: str
    title: str
    body: str
    metadata: dict
    finding_invoice_id: str
    finding_rule_id: str
    channel: str
    delivered: bool


class AlertStore:
    """Historique persistent des alertes — append-only.

    Args:
        path: chemin SQLite (`:memory:` par défaut). Ignoré si `engine` ou
            `Settings.database_url` est fourni.
        engine: Engine SQLAlchemy partagé (override total).
    """

    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        engine: Engine | None = None,
    ) -> None:
        self._engine = engine or make_engine(db_path=path)
        Base.metadata.create_all(self._engine, checkfirst=True)

    def record(self, alert: Alert, channel: str, delivered: bool) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO alert_history "
                    "(triggered_at, rule_name, severity, title, body, metadata, "
                    "finding_invoice_id, finding_rule_id, channel, delivered) "
                    "VALUES (:triggered_at, :rule_name, :severity, :title, :body, "
                    ":metadata, :finding_invoice_id, :finding_rule_id, :channel, :delivered)"
                ),
                {
                    "triggered_at": alert.triggered_at.isoformat(),
                    "rule_name": alert.rule_name,
                    "severity": alert.severity,
                    "title": alert.title,
                    "body": alert.body,
                    "metadata": json.dumps(alert.metadata, sort_keys=True),
                    "finding_invoice_id": alert.finding_invoice_id,
                    "finding_rule_id": alert.finding_rule_id,
                    "channel": channel,
                    "delivered": int(delivered),
                },
            )

    def all(self, limit: int = 200) -> list[AlertHistoryEntry]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT seq, triggered_at, rule_name, severity, title, body, metadata, "
                    "finding_invoice_id, finding_rule_id, channel, delivered "
                    "FROM alert_history ORDER BY seq DESC LIMIT :lim"
                ),
                {"lim": limit},
            ).all()
        return [
            AlertHistoryEntry(
                seq=row[0],
                triggered_at=row[1],
                rule_name=row[2],
                severity=row[3],
                title=row[4],
                body=row[5],
                metadata=json.loads(row[6]),
                finding_invoice_id=row[7],
                finding_rule_id=row[8],
                channel=row[9],
                delivered=bool(row[10]),
            )
            for row in rows
        ]

    def __len__(self) -> int:
        with self._engine.connect() as conn:
            return int(conn.execute(text("SELECT COUNT(*) FROM alert_history")).scalar() or 0)

    def stats(self) -> dict:
        with self._engine.connect() as conn:
            by_severity = dict(
                conn.execute(
                    text("SELECT severity, COUNT(*) FROM alert_history GROUP BY severity")
                ).all()
            )
            by_channel_rows = conn.execute(
                text(
                    "SELECT channel, SUM(delivered) AS delivered_n, "
                    "SUM(1 - delivered) AS failed_n "
                    "FROM alert_history GROUP BY channel"
                )
            ).all()
        by_channel = {
            row[0]: {"delivered": int(row[1] or 0), "failed": int(row[2] or 0)}
            for row in by_channel_rows
        }
        return {
            "total": len(self),
            "by_severity": by_severity,
            "by_channel": by_channel,
            "as_of": datetime.now(UTC).isoformat(),
        }

    def export_jsonl(self, limit: int = 1000) -> list[str]:
        return [json.dumps(asdict(e), sort_keys=True) for e in self.all(limit)]

    def close(self) -> None:
        self._engine.dispose()
