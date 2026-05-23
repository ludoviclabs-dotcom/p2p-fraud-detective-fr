"""sepa mandate vault — creditors, bank_accounts, mandates, mandate_revisions, debit_events

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2026-05-23

Sprint 2 MandateGuard — tables du coffre-fort de mandats SEPA et de
l'ingestion des prélèvements observés.

Compatible SQLite (démo, tests) et PostgreSQL (production).

Choix de conception :
- IBAN stocké chiffré (Fernet `enc:v1:`) en `iban_ciphertext`, jamais en clair
- recherche par `iban_fingerprint` HMAC-SHA256 (64 chars hex)
- montants en cents (Integer) pour précision exacte sans flottants
- `tenant_id` nullable partout pour migration mono-tenant → multi-tenant
- horodatages en Text ISO 8601 UTC (cohérent avec le reste du schéma)
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── Creditors ───────────────────────────────────────────────────────────
    op.create_table(
        "creditors",
        sa.Column("creditor_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("ics", sa.String(length=35), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("reputation", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("first_seen_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
    )
    op.create_index("idx_creditors_ics", "creditors", ["ics"])
    op.create_index("idx_creditors_tenant", "creditors", ["tenant_id"])
    op.create_index("uq_creditors_tenant_ics", "creditors", ["tenant_id", "ics"], unique=True)

    # ─── Bank accounts ───────────────────────────────────────────────────────
    op.create_table(
        "bank_accounts",
        sa.Column("account_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("iban_ciphertext", sa.Text(), nullable=False),
        sa.Column("iban_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
    )
    op.create_index("idx_bank_accounts_fingerprint", "bank_accounts", ["iban_fingerprint"])
    op.create_index("idx_bank_accounts_tenant", "bank_accounts", ["tenant_id"])
    op.create_index(
        "uq_bank_accounts_tenant_fp",
        "bank_accounts",
        ["tenant_id", "iban_fingerprint"],
        unique=True,
    )

    # ─── Mandates ────────────────────────────────────────────────────────────
    op.create_table(
        "mandates",
        sa.Column("mandate_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("creditor_id", sa.String(length=64), nullable=False),
        sa.Column("debtor_account_id", sa.String(length=64), nullable=False),
        sa.Column("rum", sa.String(length=35), nullable=False),
        sa.Column("scheme", sa.String(length=16), nullable=False, server_default="SDD_CORE"),
        sa.Column(
            "sequence_type",
            sa.String(length=8),
            nullable=False,
            server_default="RCUR",
        ),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="DRAFT"),
        sa.Column("max_amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("frequency", sa.String(length=32), nullable=True),
        sa.Column("valid_from", sa.Text(), nullable=True),
        sa.Column("valid_to", sa.Text(), nullable=True),
        sa.Column("signed_at", sa.Text(), nullable=True),
        sa.Column("revoked_at", sa.Text(), nullable=True),
        sa.Column("document_key", sa.String(length=255), nullable=True),
        sa.Column("commitment_hash", sa.String(length=64), nullable=True),
        sa.Column("current_revision_id", sa.String(length=64), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
    )
    op.create_index("idx_mandates_creditor", "mandates", ["creditor_id"])
    op.create_index("idx_mandates_debtor", "mandates", ["debtor_account_id"])
    op.create_index("idx_mandates_status", "mandates", ["status"])
    op.create_index("idx_mandates_rum", "mandates", ["rum"])
    op.create_index(
        "uq_mandates_creditor_debtor_rum",
        "mandates",
        ["tenant_id", "creditor_id", "debtor_account_id", "rum"],
        unique=True,
    )

    # ─── Mandate revisions ───────────────────────────────────────────────────
    op.create_table(
        "mandate_revisions",
        sa.Column("revision_id", sa.String(length=64), primary_key=True),
        sa.Column("mandate_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("snapshot_ciphertext", sa.Text(), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("signature_provider", sa.String(length=64), nullable=True),
        sa.Column("signature_evidence_key", sa.String(length=255), nullable=True),
        sa.Column("actor", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_index("idx_mandate_revisions_mandate", "mandate_revisions", ["mandate_id"])

    # ─── Debit events ────────────────────────────────────────────────────────
    op.create_table(
        "debit_events",
        sa.Column("event_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("debtor_account_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("creditor_id", sa.String(length=64), nullable=True),
        sa.Column("creditor_ics", sa.String(length=35), nullable=True),
        sa.Column("creditor_name_raw", sa.String(length=255), nullable=True),
        sa.Column("rum", sa.String(length=35), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("booking_date", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Text(), nullable=True),
        sa.Column("debtor_iban_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("raw_key", sa.String(length=255), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("matched_mandate_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_index("idx_debit_events_tenant", "debit_events", ["tenant_id"])
    op.create_index("idx_debit_events_creditor_ics", "debit_events", ["creditor_ics"])
    op.create_index("idx_debit_events_rum", "debit_events", ["rum"])
    op.create_index("idx_debit_events_iban_fp", "debit_events", ["debtor_iban_fingerprint"])
    op.create_index(
        "uq_debit_events_idempotency",
        "debit_events",
        ["tenant_id", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_debit_events_idempotency", table_name="debit_events")
    op.drop_index("idx_debit_events_iban_fp", table_name="debit_events")
    op.drop_index("idx_debit_events_rum", table_name="debit_events")
    op.drop_index("idx_debit_events_creditor_ics", table_name="debit_events")
    op.drop_index("idx_debit_events_tenant", table_name="debit_events")
    op.drop_table("debit_events")

    op.drop_index("idx_mandate_revisions_mandate", table_name="mandate_revisions")
    op.drop_table("mandate_revisions")

    op.drop_index("uq_mandates_creditor_debtor_rum", table_name="mandates")
    op.drop_index("idx_mandates_rum", table_name="mandates")
    op.drop_index("idx_mandates_status", table_name="mandates")
    op.drop_index("idx_mandates_debtor", table_name="mandates")
    op.drop_index("idx_mandates_creditor", table_name="mandates")
    op.drop_table("mandates")

    op.drop_index("uq_bank_accounts_tenant_fp", table_name="bank_accounts")
    op.drop_index("idx_bank_accounts_tenant", table_name="bank_accounts")
    op.drop_index("idx_bank_accounts_fingerprint", table_name="bank_accounts")
    op.drop_table("bank_accounts")

    op.drop_index("uq_creditors_tenant_ics", table_name="creditors")
    op.drop_index("idx_creditors_tenant", table_name="creditors")
    op.drop_index("idx_creditors_ics", table_name="creditors")
    op.drop_table("creditors")
