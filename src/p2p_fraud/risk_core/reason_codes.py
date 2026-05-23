"""Registre canonique des reason codes — partagé SEPA + P2P + autres domaines.

Étend la taxonomy historique du module P2P (`scoring/reason_codes.py`) avec
les codes SEPA du spec MandateGuard §06. Cette table est la source de vérité
de l'UI, des Evidence Packs et des exports d'audit — toute nouvelle règle
DOIT y enregistrer son `code`.

Le module `scoring/reason_codes.py` est conservé pour la rétrocompat avec les
détecteurs P2P historiques (rendu FR contextualisé par `Finding`). Le présent
module fournit la *taxonomy plate* (code → titre/description/citation/severity
par défaut) utilisable depuis n'importe quelle règle Risk Core.
"""

from __future__ import annotations

from dataclasses import dataclass

from p2p_fraud.risk_core.types import RiskDomain, Severity

__all__ = [
    "REASON_CODES",
    "ReasonCodeMeta",
    "get_reason_code_meta",
    "list_codes_for_domain",
]


@dataclass(frozen=True)
class ReasonCodeMeta:
    """Métadonnées d'un reason code canonique."""

    code: str
    domain: RiskDomain
    title_fr: str
    description_fr: str
    default_severity: Severity
    citation: str = ""


# Convention :
# - codes SEPA préfixés par leur famille (MANDATE_, RUM_, ICS_, etc.)
# - codes P2P sans préfixe spécifique (héritage du module historique)
# - codes graph préfixés GRAPH_
# - codes AML préfixés SANCTIONS_/PEP_
REASON_CODES: dict[str, ReasonCodeMeta] = {
    # ─── SEPA — Mandate / Direct Debit (spec §06 + §07) ──────────────────────
    "NO_ACTIVE_MANDATE": ReasonCodeMeta(
        code="NO_ACTIVE_MANDATE",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Aucun mandat actif",
        description_fr=(
            "Ce prélèvement ne correspond à aucun mandat SEPA actif connu pour "
            "ce couple (créancier, débiteur)."
        ),
        default_severity=Severity.CRITICAL,
        citation="EPC SDD Core Rulebook §4.2",
    ),
    "MANDATE_REVOKED": ReasonCodeMeta(
        code="MANDATE_REVOKED",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Mandat révoqué",
        description_fr="Le mandat correspondant a été révoqué avant ce prélèvement.",
        default_severity=Severity.CRITICAL,
        citation="EPC SDD Core Rulebook §4.7",
    ),
    "MANDATE_UNSIGNED": ReasonCodeMeta(
        code="MANDATE_UNSIGNED",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Mandat non signé",
        description_fr="Le mandat existe en DRAFT mais n'a pas été signé/activé.",
        default_severity=Severity.HIGH,
        citation="EPC SDD Core Rulebook §4.3",
    ),
    "MANDATE_AMOUNT_EXCEEDED": ReasonCodeMeta(
        code="MANDATE_AMOUNT_EXCEEDED",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Montant supérieur au plafond du mandat",
        description_fr="Le prélèvement dépasse le plafond `maxAmountCents` du mandat.",
        default_severity=Severity.CRITICAL,
        citation="Mandate constraints",
    ),
    "MANDATE_FREQUENCY_EXCEEDED": ReasonCodeMeta(
        code="MANDATE_FREQUENCY_EXCEEDED",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Fréquence du mandat dépassée",
        description_fr="Nombre de prélèvements supérieur à la périodicité prévue.",
        default_severity=Severity.HIGH,
        citation="Mandate constraints",
    ),
    "RUM_MISMATCH": ReasonCodeMeta(
        code="RUM_MISMATCH",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="RUM inconnue",
        description_fr="La RUM du prélèvement ne correspond à aucun mandat actif.",
        default_severity=Severity.HIGH,
        citation="EPC SDD §4.4",
    ),
    "ICS_MISMATCH": ReasonCodeMeta(
        code="ICS_MISMATCH",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="ICS différent du mandat",
        description_fr="L'ICS du créancier diffère de celui enregistré dans le mandat.",
        default_severity=Severity.CRITICAL,
        citation="Référentiel ICS Banque de France",
    ),
    "CREDITOR_NAME_MISMATCH": ReasonCodeMeta(
        code="CREDITOR_NAME_MISMATCH",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Nom du créancier divergent",
        description_fr="Le nom brut du créancier diffère significativement du mandat.",
        default_severity=Severity.MEDIUM,
    ),
    "UNUSUAL_FREQUENCY": ReasonCodeMeta(
        code="UNUSUAL_FREQUENCY",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Fréquence inhabituelle",
        description_fr="Cadence des prélèvements anormale par rapport à l'historique.",
        default_severity=Severity.HIGH,
    ),
    "FIRST_DEBIT_AFTER_MANDATE_CREATION": ReasonCodeMeta(
        code="FIRST_DEBIT_AFTER_MANDATE_CREATION",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Premier prélèvement immédiatement après création mandat",
        description_fr="Délai très court entre signature du mandat et premier débit.",
        default_severity=Severity.MEDIUM,
    ),
    # ─── IBAN / Beneficiary (cross-domain) ───────────────────────────────────
    "NEW_BENEFICIARY": ReasonCodeMeta(
        code="NEW_BENEFICIARY",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Nouveau bénéficiaire",
        description_fr="Bénéficiaire jamais vu sur ce tenant.",
        default_severity=Severity.MEDIUM,
    ),
    "NEW_IBAN": ReasonCodeMeta(
        code="NEW_IBAN",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Nouvel IBAN",
        description_fr="IBAN jamais vu pour ce bénéficiaire.",
        default_severity=Severity.HIGH,
    ),
    "IBAN_RECENTLY_ADDED": ReasonCodeMeta(
        code="IBAN_RECENTLY_ADDED",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="IBAN ajouté récemment",
        description_fr="L'IBAN a été ajouté dans les dernières 72h.",
        default_severity=Severity.HIGH,
    ),
    "IBAN_NAME_MISMATCH": ReasonCodeMeta(
        code="IBAN_NAME_MISMATCH",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="IBAN ne correspond pas au nom",
        description_fr="Mismatch entre nom du bénéficiaire et titulaire de l'IBAN.",
        default_severity=Severity.HIGH,
    ),
    "SHARED_IBAN": ReasonCodeMeta(
        code="SHARED_IBAN",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="IBAN partagé entre fournisseurs",
        description_fr="Plusieurs bénéficiaires distincts utilisent le même IBAN.",
        default_severity=Severity.HIGH,
    ),
    "IBAN_COUNTRY_CHANGED": ReasonCodeMeta(
        code="IBAN_COUNTRY_CHANGED",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Pays IBAN modifié",
        description_fr="L'IBAN est passé d'un pays à un autre — signal fort BEC.",
        default_severity=Severity.HIGH,
    ),
    # ─── Supplier / 4-eyes / invoices (P2P historique) ───────────────────────
    "SUPPLIER_RIB_RECENT_CHANGE": ReasonCodeMeta(
        code="SUPPLIER_RIB_RECENT_CHANGE",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="RIB fournisseur modifié récemment",
        description_fr="RIB modifié peu avant l'émission du paiement.",
        default_severity=Severity.CRITICAL,
        citation="AFP 2026 §BEC",
    ),
    "SUPPLIER_DORMANT_REACTIVATED": ReasonCodeMeta(
        code="SUPPLIER_DORMANT_REACTIVATED",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Fournisseur dormant réactivé",
        description_fr="Fournisseur inactif depuis longtemps dont l'IBAN change avant un paiement.",
        default_severity=Severity.HIGH,
    ),
    "SIREN_INACTIVE": ReasonCodeMeta(
        code="SIREN_INACTIVE",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="SIREN inactif",
        description_fr="SIREN en cessation administrative (INSEE Sirene v3).",
        default_severity=Severity.HIGH,
        citation="INSEE Sirene v3",
    ),
    "SIREN_NAME_MISMATCH": ReasonCodeMeta(
        code="SIREN_NAME_MISMATCH",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Nom diffère de l'INSEE",
        description_fr="Nom enregistré différent du référentiel INSEE.",
        default_severity=Severity.MEDIUM,
    ),
    "FOUR_EYES_BREACH": ReasonCodeMeta(
        code="FOUR_EYES_BREACH",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Violation du principe 4-eyes",
        description_fr="Même utilisateur a modifié et approuvé le paiement.",
        default_severity=Severity.HIGH,
        citation="ISA 240 §32",
    ),
    "DUPLICATE_INVOICE": ReasonCodeMeta(
        code="DUPLICATE_INVOICE",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Doublon de facture",
        description_fr="Une facture déjà existante avec ce numéro/montant a été détectée.",
        default_severity=Severity.HIGH,
        citation="AICPA Audit Data Standards",
    ),
    # ─── Velocity (cross-domain) ─────────────────────────────────────────────
    "UNUSUAL_AMOUNT": ReasonCodeMeta(
        code="UNUSUAL_AMOUNT",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Montant inhabituel",
        description_fr="Montant atypique par rapport à l'historique du bénéficiaire.",
        default_severity=Severity.MEDIUM,
    ),
    "SPLIT_PAYMENTS": ReasonCodeMeta(
        code="SPLIT_PAYMENTS",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Paiements fractionnés sous seuil",
        description_fr="Plusieurs paiements de petit montant pour contourner un seuil.",
        default_severity=Severity.HIGH,
    ),
    "MULTIPLE_SMALL_DEBITS": ReasonCodeMeta(
        code="MULTIPLE_SMALL_DEBITS",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Multiples petits prélèvements",
        description_fr="Série anormale de petits prélèvements d'un même créancier.",
        default_severity=Severity.HIGH,
    ),
    # ─── Graph / cluster ─────────────────────────────────────────────────────
    "GRAPH_HIGH_RISK_CLUSTER": ReasonCodeMeta(
        code="GRAPH_HIGH_RISK_CLUSTER",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Cluster à haut risque",
        description_fr="Bénéficiaire dans un cluster de fraude identifié.",
        default_severity=Severity.HIGH,
    ),
    "GRAPH_SHARED_IBAN": ReasonCodeMeta(
        code="GRAPH_SHARED_IBAN",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="IBAN partagé dans le graphe",
        description_fr="Anneau de fournisseurs partageant un même IBAN.",
        default_severity=Severity.HIGH,
    ),
    "GRAPH_MULE_LINKED_PAYERS": ReasonCodeMeta(
        code="GRAPH_MULE_LINKED_PAYERS",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Comptes mules liés",
        description_fr="Réseau de payeurs/bénéficiaires typique de blanchiment.",
        default_severity=Severity.CRITICAL,
    ),
    "GRAPH_CREDITOR_DISPUTE_CLUSTER": ReasonCodeMeta(
        code="GRAPH_CREDITOR_DISPUTE_CLUSTER",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        title_fr="Créancier dans cluster contesté",
        description_fr="Créancier lié à plusieurs contestations récentes.",
        default_severity=Severity.HIGH,
    ),
    # ─── AML / sanctions (cross-domain) ──────────────────────────────────────
    "SANCTIONS_POSSIBLE_HIT": ReasonCodeMeta(
        code="SANCTIONS_POSSIBLE_HIT",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Correspondance sanctions possible",
        description_fr="Match probable avec liste de sanctions (à confirmer).",
        default_severity=Severity.CRITICAL,
        citation="LCB-FT ; Règl. UE 2580/2001",
    ),
    "PEP_POSSIBLE_HIT": ReasonCodeMeta(
        code="PEP_POSSIBLE_HIT",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Personne politiquement exposée",
        description_fr="Bénéficiaire correspond probablement à une PEP.",
        default_severity=Severity.HIGH,
        citation="LCB-FT",
    ),
    "HIGH_RISK_COUNTRY": ReasonCodeMeta(
        code="HIGH_RISK_COUNTRY",
        domain=RiskDomain.SUPPLIER_PAYMENT,
        title_fr="Pays à haut risque",
        description_fr="Bénéficiaire localisé dans une juridiction à risque.",
        default_severity=Severity.HIGH,
        citation="GAFI liste grise/noire",
    ),
}


def get_reason_code_meta(code: str) -> ReasonCodeMeta | None:
    """Lookup par code. Retourne None si inconnu (l'appelant fait fallback)."""
    return REASON_CODES.get(code)


def list_codes_for_domain(domain: RiskDomain) -> list[str]:
    """Liste les codes enregistrés pour un domaine donné, triés."""
    return sorted(code for code, meta in REASON_CODES.items() if meta.domain == domain)
