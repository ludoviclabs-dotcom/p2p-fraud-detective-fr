"""Couche de persistance — modèles ORM + factory d'engine SQLAlchemy.

Phase 4 / PR P4-2 : remplace `sqlite3.connect` direct dans les 4 stores
(`CaseService`, `MentionStore`, `AuditLog`, `AlertStore`) par une couche
SQLAlchemy 2.0 agnostique du backend (SQLite ou PostgreSQL).

Usage :

    from p2p_fraud.persistence import make_engine, Base

    engine = make_engine(database_url=None)  # SQLite :memory: par défaut
    Base.metadata.create_all(engine)
"""

from __future__ import annotations

from .engine import make_engine
from .models import (
    AlertHistoryRow,
    AuditLogRow,
    Base,
    CaseEventRow,
    CaseRow,
    MentionRow,
)

__all__ = [
    "AlertHistoryRow",
    "AuditLogRow",
    "Base",
    "CaseEventRow",
    "CaseRow",
    "MentionRow",
    "make_engine",
]
