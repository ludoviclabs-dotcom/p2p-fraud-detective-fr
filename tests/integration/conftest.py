"""Tests d'intégration P4-2 — backend PostgreSQL.

Skippés par défaut. Pour les exécuter en local :

    docker run -d --rm -p 5432:5432 -e POSTGRES_PASSWORD=test \\
      -e POSTGRES_USER=test -e POSTGRES_DB=p2pfd postgres:16
    INTEGRATION_DATABASE_URL=postgresql://test:test@localhost:5432/p2pfd \\
      pytest -m integration

En CI (GitHub Actions) : voir `.github/workflows/ci.yml` job `integration`.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import Engine, create_engine, text

from p2p_fraud.persistence import Base


def _get_integration_url() -> str | None:
    return os.environ.get("INTEGRATION_DATABASE_URL")


@pytest.fixture(scope="session")
def pg_engine() -> Engine:
    """Engine PostgreSQL pour les tests d'intégration.

    Skippe automatiquement si `INTEGRATION_DATABASE_URL` n'est pas défini.
    """
    url = _get_integration_url()
    if not url:
        pytest.skip("INTEGRATION_DATABASE_URL not set — integration tests skipped")
    if not url.startswith(("postgresql://", "postgresql+")):
        pytest.skip(f"Skipping: URL does not target PostgreSQL ({url[:30]}...)")

    engine = create_engine(url, future=True)
    # Repartir d'un schéma propre — drop puis recréer
    Base.metadata.drop_all(engine, checkfirst=True)
    Base.metadata.create_all(engine, checkfirst=True)
    return engine


@pytest.fixture(autouse=True)
def _truncate_tables(pg_engine: Engine) -> None:
    """Vide les tables avant chaque test pour l'isolement."""
    tables_in_order = [
        "alert_history",
        "mentions",
        "case_events",
        "audit_log",
        "cases",
    ]
    with pg_engine.begin() as conn:
        for tbl in tables_in_order:
            conn.execute(text(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE"))
