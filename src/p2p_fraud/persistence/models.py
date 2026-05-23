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
    decision: Mapped[str | None] = mapped_column(String(64))
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
    # P5-5 : signature Ed25519 hex 128 chars. Nullable pour rétrocompat avec
    # les entrées antérieures à v0.5.0 (verify_chain les accepte sans signature).
    signature: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)


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


# ─── SEPA Mandate Guard — Sprint 2 ───────────────────────────────────────────
# Tables introduites par le module MandateGuard SEPA. Toutes portent une
# colonne `tenant_id` nullable pour permettre la transition vers du multi-
# tenant sans nouvelle migration (le filtrage applicatif est ajouté
# lorsque l'isolation devient nécessaire).
#
# Convention SEPA :
# - ICS : Identifiant Créancier SEPA (≤35 chars)
# - RUM : Référence Unique de Mandat (≤35 chars)
# - IBAN : chiffré (Fernet) + fingerprint HMAC pour recherche, jamais en clair
# - amount stocké en cents (Integer) pour précision exacte


class CreditorRow(Base):
    """Créancier SEPA — identifié par son ICS dans le tenant."""

    __tablename__ = "creditors"

    creditor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64))
    ics: Mapped[str] = mapped_column(String(35), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(2))
    reputation: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    first_seen_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_creditors_ics", "ics"),
        Index("idx_creditors_tenant", "tenant_id"),
        Index("uq_creditors_tenant_ics", "tenant_id", "ics", unique=True),
    )


class BankAccountRow(Base):
    """Compte bancaire (débiteur ou émetteur) — IBAN chiffré + fingerprint."""

    __tablename__ = "bank_accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64))
    label: Mapped[str | None] = mapped_column(String(255))
    iban_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    iban_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="EUR")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_bank_accounts_fingerprint", "iban_fingerprint"),
        Index("idx_bank_accounts_tenant", "tenant_id"),
        Index("uq_bank_accounts_tenant_fp", "tenant_id", "iban_fingerprint", unique=True),
    )


class MandateRow(Base):
    """Mandat SEPA — autorisation de prélèvement d'un créancier vers un débiteur.

    Cycle de vie : DRAFT → ACTIVE → REVOKED (terminal) ou EXPIRED (terminal).
    Le scheme distingue SDD_CORE (B2C) de SDD_B2B. Le sequence_type indique
    si le mandat couvre un premier (FRST), un récurrent (RCUR), un unique
    (OOFF) ou un final (FNAL).
    """

    __tablename__ = "mandates"

    mandate_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64))
    creditor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    debtor_account_id: Mapped[str] = mapped_column(String(64), nullable=False)

    rum: Mapped[str] = mapped_column(String(35), nullable=False)
    scheme: Mapped[str] = mapped_column(String(16), nullable=False, server_default="SDD_CORE")
    sequence_type: Mapped[str] = mapped_column(String(8), nullable=False, server_default="RCUR")
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="DRAFT")

    max_amount_cents: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="EUR")
    frequency: Mapped[str | None] = mapped_column(String(32))
    valid_from: Mapped[str | None] = mapped_column(Text)
    valid_to: Mapped[str | None] = mapped_column(Text)

    signed_at: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[str | None] = mapped_column(Text)

    document_key: Mapped[str | None] = mapped_column(String(255))
    commitment_hash: Mapped[str | None] = mapped_column(String(64))
    current_revision_id: Mapped[str | None] = mapped_column(String(64))

    created_by: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_mandates_creditor", "creditor_id"),
        Index("idx_mandates_debtor", "debtor_account_id"),
        Index("idx_mandates_status", "status"),
        Index("idx_mandates_rum", "rum"),
        Index(
            "uq_mandates_creditor_debtor_rum",
            "tenant_id",
            "creditor_id",
            "debtor_account_id",
            "rum",
            unique=True,
        ),
    )


class MandateRevisionRow(Base):
    """Snapshot historique d'un mandat (création, signature, révocation, amendement)."""

    __tablename__ = "mandate_revisions"

    revision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mandate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_provider: Mapped[str | None] = mapped_column(String(64))
    signature_evidence_key: Mapped[str | None] = mapped_column(String(255))
    actor: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("idx_mandate_revisions_mandate", "mandate_id"),)


class DebitEventRow(Base):
    """Prélèvement SEPA observé — entrée d'analyse, idempotente par tenant+key."""

    __tablename__ = "debit_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64))
    debtor_account_id: Mapped[str | None] = mapped_column(String(64))

    source: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    creditor_id: Mapped[str | None] = mapped_column(String(64))
    creditor_ics: Mapped[str | None] = mapped_column(String(35))
    creditor_name_raw: Mapped[str | None] = mapped_column(String(255))
    rum: Mapped[str | None] = mapped_column(String(35))

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="EUR")
    booking_date: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[str | None] = mapped_column(Text)
    debtor_iban_fingerprint: Mapped[str | None] = mapped_column(String(64))
    raw_key: Mapped[str | None] = mapped_column(String(255))
    raw_json: Mapped[str | None] = mapped_column(Text)

    matched_mandate_id: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_debit_events_tenant", "tenant_id"),
        Index("idx_debit_events_creditor_ics", "creditor_ics"),
        Index("idx_debit_events_rum", "rum"),
        Index("idx_debit_events_iban_fp", "debtor_iban_fingerprint"),
        Index(
            "uq_debit_events_idempotency",
            "tenant_id",
            "idempotency_key",
            unique=True,
        ),
    )


class EvidencePackRow(Base):
    """Dossier de preuve exportable — métadonnées + ancrage hash chain.

    Le contenu sérialisé (JSON canonical + HTML) est stocké dans `payload_json`
    et `report_html` directement (suffisant pour un MVP single-node). Pour la
    production, prévoir un blob storage externe et stocker uniquement la
    `storage_key` (ex. S3 path).

    `pack_hash` = SHA-256 du payload_json canonical. C'est l'empreinte
    vérifiable réplicable depuis le bundle exporté. `audit_anchor_hash`
    pointe sur le `hash` du dernier événement de la chain au moment de la
    création — permet de prouver l'antériorité.
    """

    __tablename__ = "evidence_packs"

    evidence_pack_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64))
    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)

    pack_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    audit_anchor_hash: Mapped[str | None] = mapped_column(String(64))
    audit_anchor_seq: Mapped[int | None] = mapped_column(Integer)

    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    report_html: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(String(255))

    actor: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_evidence_packs_tenant", "tenant_id"),
        Index("idx_evidence_packs_subject", "subject_type", "subject_id"),
        Index("idx_evidence_packs_hash", "pack_hash"),
    )
