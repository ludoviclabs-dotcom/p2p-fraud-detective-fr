"""add case decision

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-05-19
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("decision", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "decision")
