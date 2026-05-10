"""Persistance des alertes — historique SQLite append-only.

Stocke chaque alerte envoyée (avec status par canal) pour audit.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from p2p_fraud.alerts.rules import Alert


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
    """Historique persistent des alertes — append-only en SQLite."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS alert_history (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        triggered_at TEXT NOT NULL,
        rule_name TEXT NOT NULL,
        severity TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        metadata TEXT NOT NULL,
        finding_invoice_id TEXT,
        finding_rule_id TEXT,
        channel TEXT NOT NULL,
        delivered INTEGER NOT NULL
    );
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        if self._path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(self.SCHEMA)
        self._conn.commit()

    def record(self, alert: Alert, channel: str, delivered: bool) -> None:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO alert_history "
            "(triggered_at, rule_name, severity, title, body, metadata, "
            "finding_invoice_id, finding_rule_id, channel, delivered) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                alert.triggered_at.isoformat(),
                alert.rule_name,
                alert.severity,
                alert.title,
                alert.body,
                json.dumps(alert.metadata, sort_keys=True),
                alert.finding_invoice_id,
                alert.finding_rule_id,
                channel,
                int(delivered),
            ),
        )
        self._conn.commit()

    def all(self, limit: int = 200) -> list[AlertHistoryEntry]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT seq, triggered_at, rule_name, severity, title, body, metadata, "
            "finding_invoice_id, finding_rule_id, channel, delivered "
            "FROM alert_history ORDER BY seq DESC LIMIT ?",
            (limit,),
        )
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
            for row in cur.fetchall()
        ]

    def __len__(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM alert_history")
        return int(cur.fetchone()[0])

    def stats(self) -> dict:
        cur = self._conn.cursor()
        cur.execute("SELECT severity, COUNT(*) FROM alert_history GROUP BY severity")
        by_severity = dict(cur.fetchall())
        cur.execute(
            "SELECT channel, SUM(delivered), SUM(1-delivered) FROM alert_history GROUP BY channel"
        )
        by_channel = {
            row[0]: {"delivered": int(row[1]), "failed": int(row[2])} for row in cur.fetchall()
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
        self._conn.close()
