"""@mentions dans les commentaires de cases — parsing + dispatch notification.

Convention : un commentaire peut contenir `@username` (alphanumérique + underscore + tiret).
Lors de l'enregistrement, le parser extrait les mentions et émet des notifications
via les canaux configurés (alertes Slack/Teams/SMTP de P3.4).

Backend agnostique : SQLite (`:memory:` ou fichier) en démo, PostgreSQL en prod
via `Settings.database_url`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text

from p2p_fraud.persistence import Base, make_engine

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
    """Persistance des mentions et de leur statut de notification."""

    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        engine: Engine | None = None,
    ) -> None:
        self._engine = engine or make_engine(db_path=path)
        Base.metadata.create_all(self._engine, checkfirst=True)

    def record(self, mentions: Iterable[Mention]) -> int:
        n = 0
        with self._engine.begin() as conn:
            for m in mentions:
                conn.execute(
                    text(
                        "INSERT INTO mentions "
                        "(case_id, mentioned_user, mentioned_by, text, created_at) "
                        "VALUES (:case_id, :user, :by, :text, :created_at)"
                    ),
                    {
                        "case_id": m.case_id,
                        "user": m.mentioned_user,
                        "by": m.mentioned_by,
                        "text": m.text,
                        "created_at": m.created_at,
                    },
                )
                n += 1
        return n

    def for_user(self, username: str, *, only_unread: bool = False) -> list[Mention]:
        sql = (
            "SELECT case_id, mentioned_user, mentioned_by, text, created_at "
            "FROM mentions WHERE mentioned_user = :user "
        )
        if only_unread:
            sql += "AND read_at IS NULL "
        sql += "ORDER BY seq DESC"

        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), {"user": username.lower()}).all()
        return [
            Mention(
                case_id=row[0],
                mentioned_user=row[1],
                mentioned_by=row[2],
                text=row[3],
                created_at=row[4],
            )
            for row in rows
        ]

    def mark_read(self, *, username: str, case_id: str | None = None) -> int:
        now = datetime.now(UTC).isoformat()
        if case_id:
            sql = (
                "UPDATE mentions SET read_at = :now "
                "WHERE mentioned_user = :user AND case_id = :case_id AND read_at IS NULL"
            )
            params = {"now": now, "user": username.lower(), "case_id": case_id}
        else:
            sql = (
                "UPDATE mentions SET read_at = :now "
                "WHERE mentioned_user = :user AND read_at IS NULL"
            )
            params = {"now": now, "user": username.lower()}

        with self._engine.begin() as conn:
            result = conn.execute(text(sql), params)
            return int(result.rowcount)

    def all_users_mentioned(self) -> list[str]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT mentioned_user FROM mentions ORDER BY mentioned_user")
            ).all()
        return [row[0] for row in rows]

    def __len__(self) -> int:
        with self._engine.connect() as conn:
            return int(conn.execute(text("SELECT COUNT(*) FROM mentions")).scalar() or 0)

    def close(self) -> None:
        self._engine.dispose()


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
