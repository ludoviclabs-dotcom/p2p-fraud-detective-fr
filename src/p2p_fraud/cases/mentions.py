"""@mentions dans les commentaires de cases — parsing + dispatch notification.

Convention : un commentaire peut contenir `@username` (alphanumérique + underscore + tiret).
Lors de l'enregistrement, le parser extrait les mentions et émet des notifications
via les canaux configurés (alertes Slack/Teams/SMTP de P3.4).
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_MENTION_RE = re.compile(r"@([A-Za-z0-9_\-\.]{2,40})\b")


@dataclass(frozen=True)
class Mention:
    """Mention d'un utilisateur dans un commentaire."""

    case_id: str
    mentioned_user: str
    mentioned_by: str
    text: str
    created_at: str


def extract_mentions(text: str) -> list[str]:
    """Extrait les usernames mentionnés dans un texte (sans le @)."""
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for match in _MENTION_RE.finditer(text):
        username = match.group(1).lower().rstrip(".")
        if username not in seen:
            seen.add(username)
            out.append(username)
    return out


class MentionStore:
    """Persistance SQLite des mentions et de leur statut de notification."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS mentions (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL,
        mentioned_user TEXT NOT NULL,
        mentioned_by TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        notified INTEGER NOT NULL DEFAULT 0,
        read_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_mentions_user ON mentions(mentioned_user);
    CREATE INDEX IF NOT EXISTS idx_mentions_case ON mentions(case_id);
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        if self._path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    def record(self, mentions: Iterable[Mention]) -> int:
        cur = self._conn.cursor()
        n = 0
        for m in mentions:
            cur.execute(
                "INSERT INTO mentions (case_id, mentioned_user, mentioned_by, text, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (m.case_id, m.mentioned_user, m.mentioned_by, m.text, m.created_at),
            )
            n += 1
        self._conn.commit()
        return n

    def for_user(self, username: str, *, only_unread: bool = False) -> list[Mention]:
        cur = self._conn.cursor()
        if only_unread:
            cur.execute(
                "SELECT case_id, mentioned_user, mentioned_by, text, created_at "
                "FROM mentions WHERE mentioned_user = ? AND read_at IS NULL "
                "ORDER BY seq DESC",
                (username.lower(),),
            )
        else:
            cur.execute(
                "SELECT case_id, mentioned_user, mentioned_by, text, created_at "
                "FROM mentions WHERE mentioned_user = ? ORDER BY seq DESC",
                (username.lower(),),
            )
        return [
            Mention(
                case_id=row[0],
                mentioned_user=row[1],
                mentioned_by=row[2],
                text=row[3],
                created_at=row[4],
            )
            for row in cur.fetchall()
        ]

    def mark_read(self, *, username: str, case_id: str | None = None) -> int:
        cur = self._conn.cursor()
        now = datetime.now(UTC).isoformat()
        if case_id:
            cur.execute(
                "UPDATE mentions SET read_at = ? "
                "WHERE mentioned_user = ? AND case_id = ? AND read_at IS NULL",
                (now, username.lower(), case_id),
            )
        else:
            cur.execute(
                "UPDATE mentions SET read_at = ? WHERE mentioned_user = ? AND read_at IS NULL",
                (now, username.lower()),
            )
        self._conn.commit()
        return cur.rowcount

    def all_users_mentioned(self) -> list[str]:
        cur = self._conn.cursor()
        cur.execute("SELECT DISTINCT mentioned_user FROM mentions ORDER BY mentioned_user")
        return [row[0] for row in cur.fetchall()]

    def __len__(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM mentions")
        return int(cur.fetchone()[0])

    def close(self) -> None:
        self._conn.close()


def build_mentions(*, case_id: str, text: str, mentioned_by: str) -> list[Mention]:
    """Construit la liste des Mention objects à partir d'un texte de commentaire."""
    now = datetime.now(UTC).isoformat()
    return [
        Mention(
            case_id=case_id,
            mentioned_user=username,
            mentioned_by=mentioned_by,
            text=text,
            created_at=now,
        )
        for username in extract_mentions(text)
    ]
