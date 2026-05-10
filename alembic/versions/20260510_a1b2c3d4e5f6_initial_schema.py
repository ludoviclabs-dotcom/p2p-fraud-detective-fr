"""initial schema — cases, case_events, audit_log, mentions, alert_history

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-10

Schéma initial pour P2P Fraud Detective FR multi-user.
Compatible SQLite et PostgreSQL.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("case_id", sa.String(length=64), primary_key=True),
        sa.Column("finding_ids", sa.Text(), nullable=False),
        sa.Column("invoice_id", sa.String(length=128)),
        sa.Column("vendor_id", sa.String(length=128)),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("exposure_eur", sa.Numeric(18, 2)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assignee", sa.String(length=128)),
        sa.Column("sla_deadline", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("closure_reason", sa.Text()),
        sa.Column("closure_evidence_path", sa.String(length=512)),
    )
    op.create_index("idx_cases_status", "cases", ["status"])
    op.create_index("idx_cases_assignee", "cases", ["assignee"])
    op.create_index("idx_cases_severity", "cases", ["severity"])

    op.create_table(
        "case_events",
        sa.Column("event_id", sa.String(length=64), primary_key=True),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_case_events_case", "case_events", ["case_id"])

    op.create_table(
        "audit_log",
        sa.Column("seq", sa.Integer(), primary_key=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
    )

    op.create_table(
        "mentions",
        sa.Column("seq", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("mentioned_user", sa.String(length=128), nullable=False),
        sa.Column("mentioned_by", sa.String(length=128), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("read_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_mentions_user", "mentions", ["mentioned_user"])
    op.create_index("idx_mentions_case", "mentions", ["case_id"])

    op.create_table(
        "alert_history",
        sa.Column("seq", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("metadata", sa.Text(), nullable=False),
        sa.Column("finding_invoice_id", sa.String(length=128)),
        sa.Column("finding_rule_id", sa.String(length=128)),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("delivered", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alert_history")
    op.drop_index("idx_mentions_case", table_name="mentions")
    op.drop_index("idx_mentions_user", table_name="mentions")
    op.drop_table("mentions")
    op.drop_table("audit_log")
    op.drop_index("idx_case_events_case", table_name="case_events")
    op.drop_table("case_events")
    op.drop_index("idx_cases_severity", table_name="cases")
    op.drop_index("idx_cases_assignee", table_name="cases")
    op.drop_index("idx_cases_status", table_name="cases")
    op.drop_table("cases")
