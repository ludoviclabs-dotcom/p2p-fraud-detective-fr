"""Énumérations et constantes SEPA — conformes à la spec EPC + MandateGuard §07."""

from __future__ import annotations

from enum import StrEnum


class MandateStatus(StrEnum):
    """Cycle de vie d'un mandat SEPA.

    DRAFT     → créé mais pas encore signé/actif (aucun prélèvement autorisé)
    ACTIVE    → signé et actif, les prélèvements correspondants sont autorisés
    SUSPENDED → en pause (litige en cours, contrôle bancaire) — transient
    REVOKED   → terminal, ne sera jamais réactivé (nouvelle souscription nécessaire)
    EXPIRED   → terminal, validity_to dépassé (13 mois sans usage en SDD CORE)
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class MandateScheme(StrEnum):
    """Schéma SEPA Direct Debit (EPC SDD Rulebooks).

    SDD_CORE : B2C, fenêtre R-transaction 8 semaines (13 mois pour mandat invalide)
    SDD_B2B  : B2B, fenêtre R-transaction 2 jours ouvrés, contestations très limitées
    """

    SDD_CORE = "SDD_CORE"
    SDD_B2B = "SDD_B2B"


class SequenceType(StrEnum):
    """Type de séquence d'un prélèvement (en-tête pacs.003 / mandat).

    FRST : First (premier d'une série récurrente)
    RCUR : Recurrent (récurrent standard)
    OOFF : One-Off (unique ponctuel)
    FNAL : Final (dernier d'une série, clôt le mandat)
    """

    FRST = "FRST"
    RCUR = "RCUR"
    OOFF = "OOFF"
    FNAL = "FNAL"


class RevisionReason(StrEnum):
    """Raison d'une révision (snapshot) du mandat."""

    CREATED = "CREATED"
    SIGNED = "SIGNED"
    REVOKED = "REVOKED"
    SUSPENDED = "SUSPENDED"
    RESUMED = "RESUMED"
    AMENDED = "AMENDED"
    EXPIRED = "EXPIRED"


# Limites SEPA strictes (rulebook EPC v1.5)
MAX_RUM_LENGTH = 35
MAX_ICS_LENGTH = 35
MAX_CREDITOR_NAME_LENGTH = 70


# Transitions d'état autorisées (clé = état actuel, valeur = états cibles permis)
ALLOWED_TRANSITIONS: dict[MandateStatus, frozenset[MandateStatus]] = {
    MandateStatus.DRAFT: frozenset(
        {MandateStatus.ACTIVE, MandateStatus.REVOKED, MandateStatus.EXPIRED}
    ),
    MandateStatus.ACTIVE: frozenset(
        {MandateStatus.SUSPENDED, MandateStatus.REVOKED, MandateStatus.EXPIRED}
    ),
    MandateStatus.SUSPENDED: frozenset(
        {MandateStatus.ACTIVE, MandateStatus.REVOKED, MandateStatus.EXPIRED}
    ),
    MandateStatus.REVOKED: frozenset(),  # terminal
    MandateStatus.EXPIRED: frozenset(),  # terminal
}


def can_transition(current: MandateStatus, target: MandateStatus) -> bool:
    """Indique si le passage de `current` à `target` est autorisé."""
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())
