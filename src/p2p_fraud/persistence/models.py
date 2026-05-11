"""Modèles ORM SQLAlchemy 2.0 — schéma partagé avec Alembic.

Une `Base.metadata` unique est utilisée par les migrations Alembic
(`alembic/env.py` → `target_metadata = Base.metadata`) et par les stores
applicatifs (`CaseService`, `MentionStore`, `AuditLog`, `AlertStore`).

Les types choisis privilégient la rétrocompat avec l'existant SQLite :
- horodatages stockés en `Text` (ISO 8601 UTC) — pas en `DateTime` —
  car les services calculent eux-mêmes le format ISO et les comparaisons
  par chaîne lexicographique restent correctes en UTC.
- payloads JSON stockés en `Text` (sérialisation déterministe pour
  préserver le hachage chaîné de l'audit log).
"""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base ORM partagée par toutes les tables P2P Fraud Detective FR."""


class CaseRow(Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    finding_ids: Mapped[str] = mapped_column(Text, nullable=False)
    invoice_id: Mapped[str | None] = mapped_column(String(128))
    vendor_id: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    exposure_eur: Mapped[float | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    assignee: Mapped[str | None] = mapped_column(String(128))
    sla_deadline: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    closed_at: Mapped[str | None] = mapped_column(Text)
    closure_reason: Mapped[str | None] = mapped_column(Text)
    closure_evidence_path: Mapped[str | None] = mapped_column(String(512))

    __table_args__ = (
        Index("idx_cases_status", "status"),
        Index("idx_cases_assignee", "assignee"),
        Index("idx_cases_severity", "severity"),
    )


class CaseEventRow(Base):
    __tablename__ = "case_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("idx_case_events_case", "case_id"),)


class AuditLogRow(Base):
    __tablename__ = "audit_log"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)


class MentionRow(Base):
    __tablename__ = "mentions"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False)
    mentioned_user: Mapped[str] = mapped_column(String(128), nullable=False)
    mentioned_by: Mapped[str] = mapped_column(String(128), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    notified: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    read_at: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("idx_mentions_user", "mentioned_user"),
        Index("idx_mentions_case", "case_id"),
    )


class AlertHistoryRow(Base):
    __tablename__ = "alert_history"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    triggered_at: Mapped[str] = mapped_column(Text, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    extras: Mapped[str] = mapped_column("metadata", Text, nullable=False)
    finding_invoice_id: Mapped[str | None] = mapped_column(String(128))
    finding_rule_id: Mapped[str | None] = mapped_column(String(128))
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    delivered: Mapped[int] = mapped_column(Integer, nullable=False)
