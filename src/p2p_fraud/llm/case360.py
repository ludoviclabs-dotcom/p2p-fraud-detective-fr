"""Fraud Case 360 AI — génération d'un dossier d'enquête sourcé (Phase 3, ADR-0007).

Transforme un cas d'investigation existant (case management) en dossier
structuré : faits vérifiés, signaux, contradictions, données manquantes,
questions ouvertes, diligences. Garanties héritées du socle :

- le modèle ne voit QUE le source pack construit ici depuis le case, ses
  événements et ses findings — il ne peut citer que des faits établis ;
- provenance validée en code (`validate_provenance`, fail-closed) ;
- `human_review_required` est **forcé à true en code** après génération :
  un dossier généré n'autorise jamais de décision automatique ;
- appel journalisé au ledger `ai.generation` de l'audit log signé.
"""

from __future__ import annotations

from typing import Any

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import Case, CaseEvent
from p2p_fraud.llm.ai_ledger import log_ai_generation
from p2p_fraud.llm.provenance import SourcePack
from p2p_fraud.llm.schemas import FraudCase360
from p2p_fraud.llm.structured import (
    DEFAULT_STRUCTURED_MODEL,
    StructuredResult,
    generate_structured,
)

PROMPT_VERSION = "case360/1"
FEATURE_NAME = "fraud_case_360"

_SYSTEM_PROMPT = """\
Tu es analyste senior fraude Procure-to-Pay (P2P). Tu produis des dossiers
d'enquête à destination d'équipes d'audit interne, de commissaires aux comptes
(CAC) et de directions financières françaises.

À partir des sources fournies (cas d'investigation, événements de workflow,
signaux des détecteurs), tu produis un dossier FraudCase360 structuré.

Règles spécifiques :
- Ne crée AUCUN fait absent des sources. Un fait vérifié = un élément
  littéralement présent dans une source citée.
- Sépare strictement : faits vérifiés (sourcés), signaux de risque (sourcés,
  sévérité reprise des sources sans réévaluation), contradictions, données
  manquantes et questions ouvertes.
- N'autorise jamais une décision automatique (blocage de paiement, clôture) :
  formule uniquement des recommandations de revue humaine et des diligences
  (validation IBAN, contrôle Sirene, entretien fournisseur, rapprochement
  PO/réception/facture, escalade).
- Si les sources sont pauvres, dis-le dans missing_evidence plutôt que de
  broder : un dossier court et honnête vaut mieux qu'un dossier rempli.
- Style : français formel d'audit, références réglementaires (ISA 240,
  Sapin 2, LCB-FT) uniquement si pertinentes."""


def build_case_source_pack(
    case: Case,
    events: list[CaseEvent] | None = None,
    findings: list[dict[str, Any]] | None = None,
) -> SourcePack:
    """Construit le source pack d'un cas — les seuls faits citables par le modèle."""
    pack = SourcePack()
    pack.add("case.id", "Identifiant du cas", case.case_id)
    pack.add("case.title", "Titre du cas", case.title)
    pack.add("case.severity", "Sévérité du cas", case.severity)
    pack.add("case.status", "Statut du cas", case.status.value)
    pack.add(
        "case.exposure_eur",
        "Exposition financière (€)",
        case.exposure_eur if case.exposure_eur is not None else "inconnue",
    )
    pack.add("case.vendor_id", "Fournisseur concerné", case.vendor_id or "inconnu")
    pack.add("case.invoice_id", "Facture concernée", case.invoice_id or "inconnue")
    pack.add("case.created_at", "Date de création du cas", case.created_at.isoformat())
    pack.add("case.assignee", "Reviewer assigné", case.assignee or "non assigné")
    pack.add(
        "case.finding_ids",
        "Findings rattachés (format RULE::facture)",
        case.finding_ids,
    )
    for i, event in enumerate(events or []):
        pack.add(
            f"event.{i}",
            f"Événement workflow « {event.kind} » par {event.actor}",
            {"at": event.at.isoformat(), **event.payload},
        )
    for i, finding in enumerate(findings or []):
        pack.add(
            f"finding.{i}",
            f"Signal détecteur {finding.get('rule_id', '?')} "
            f"(sévérité {finding.get('severity', '?')})",
            finding.get("signal", ""),
        )
    return pack


def generate_case360(
    case: Case,
    *,
    events: list[CaseEvent] | None = None,
    findings: list[dict[str, Any]] | None = None,
    audit_log: AuditLog | None = None,
    actor: str = "system",
    model: str = DEFAULT_STRUCTURED_MODEL,
    api_key: str | None = None,
) -> StructuredResult[FraudCase360]:
    """Génère le dossier FraudCase360 d'un cas existant.

    Raises:
        ValueError: clé API absente ou sortie vide.
        ProvenanceError: le dossier cite des sources hors pack.
    """
    source_pack = build_case_source_pack(case, events, findings)
    result = generate_structured(
        output_schema=FraudCase360,
        system_prompt=_SYSTEM_PROMPT,
        prompt_version=PROMPT_VERSION,
        user_content=(
            f"Produis le dossier d'enquête FraudCase360 du cas {case.case_id} "
            "à partir des sources fournies. Sépare faits vérifiés, signaux, "
            "contradictions, données manquantes et questions ouvertes."
        ),
        source_pack=source_pack,
        model=model,
        max_tokens=8192,
        api_key=api_key,
    )
    # Garde-fou métier : un dossier généré exige TOUJOURS une revue humaine,
    # quoi qu'ait répondu le modèle.
    result = StructuredResult(
        output=result.output.model_copy(update={"human_review_required": True}),
        model=result.model,
        prompt_version=result.prompt_version,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cached_tokens=result.cached_tokens,
    )
    if audit_log is not None:
        log_ai_generation(
            audit_log,
            actor=actor,
            feature=FEATURE_NAME,
            result=result,
            source_ids=sorted(source_pack.ids),
            human_review_required=True,
        )
    return result
