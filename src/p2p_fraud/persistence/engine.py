"""Factory d'Engine SQLAlchemy — bascule SQLite (démo) / PostgreSQL (prod).

L'URL est résolue selon la priorité :
1. argument explicite `database_url`
2. champ `Settings.database_url` (variable `DATABASE_URL`)
3. fallback `db_path` SQLite (chemin local ou `:memory:`)

Le SQLite `:memory:` reste le défaut en tests pour ne pas dépendre du
disque ; un fichier SQLite est utilisé en démo Streamlit Cloud.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool

from ..config import get_settings


def make_engine(
    database_url: str | None = None,
    *,
    db_path: str | Path | None = None,
    echo: bool = False,
) -> Engine:
    """Construit un `Engine` SQLAlchemy.

    Args:
        database_url: URL SQLAlchemy explicite (override). Vide → fallback Settings ou db_path.
        db_path: chemin SQLite (`:memory:` par défaut). Ignoré si `database_url` ou
            `Settings.database_url` est fourni.
        echo: log les SQL exécutés (debug).

    Returns:
        Engine SQLAlchemy 2.0.
    """
    url = database_url or get_settings().database_url or _sqlite_url(db_path or ":memory:")
    kwargs: dict[str, Any] = {"echo": echo, "future": True}

    if url.startswith("sqlite") and ":memory:" in url:
        # SQLite in-memory : un seul thread, partagé via StaticPool
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    elif url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}

    return create_engine(url, **kwargs)


def _sqlite_url(db_path: str | Path) -> str:
    p = str(db_path)
    if p == ":memory:":
        return "sqlite:///:memory:"
    return f"sqlite:///{p}"
