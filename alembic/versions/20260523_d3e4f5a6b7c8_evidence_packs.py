"""evidence_packs — dossier de preuve exportable Sprint 4 MandateGuard

Revision ID: d3e4f5a6b7c8
Revises: c1d2e3f4a5b6
Create Date: 2026-05-23

Table `evidence_packs` : stocke pour chaque dossier de preuve le payload
JSON canonical, le hash SHA-256 du payload, l'ancrage à l'audit chain
(seq + hash) et optionnellement un rapport HTML rendu.

Compatible SQLite (démo, tests) et PostgreSQL (production).
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_packs",
        sa.Column("evidence_pack_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.String(length=64), nullable=False),
        sa.Column("domain", sa.String(length=32), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("pack_hash", sa.String(length=64), nullable=False),
        sa.Column("audit_anchor_hash", sa.String(length=64), nullable=True),
        sa.Column("audit_anchor_seq", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("report_html", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("actor", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_index("idx_evidence_packs_tenant", "evidence_packs", ["tenant_id"])
    op.create_index(
        "idx_evidence_packs_subject",
        "evidence_packs",
        ["subject_type", "subject_id"],
    )
    op.create_index("idx_evidence_packs_hash", "evidence_packs", ["pack_hash"])


def downgrade() -> None:
    op.drop_index("idx_evidence_packs_hash", table_name="evidence_packs")
    op.drop_index("idx_evidence_packs_subject", table_name="evidence_packs")
    op.drop_index("idx_evidence_packs_tenant", table_name="evidence_packs")
    op.drop_table("evidence_packs")
