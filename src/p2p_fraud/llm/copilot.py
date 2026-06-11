"""Copilote analyste P2P — questions prédéfinies sur un cas (Phase 5, ADR-0007).

Périmètre volontairement serré pour le MVP :

- **questions prédéfinies uniquement** (pas de chat libre) : chaque question
  du catalogue porte sa consigne d'analyse ;
- **surface d'outils contrôlée par le code** : le modèle ne reçoit que le
  source pack du cas (mêmes sources que le Dossier 360) — c'est l'équivalent
  fail-closed du « tool-use forcé » du brief, sans boucle agentique ;
- **garde-fous** : provenance validée en code, `human_review_required` forcé
  à true, le prompt interdit toute décision automatique de blocage ;
- **modèle** : Sonnet 4.6 (Q&A volume, ADR-0007 décision C) ;
- chaque réponse est journalisée au ledger `ai.generation`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import Case, CaseEvent
from p2p_fraud.llm.ai_ledger import log_ai_generation
from p2p_fraud.llm.case360 import build_case_source_pack
from p2p_fraud.llm.schemas import CopilotAnswer
from p2p_fraud.llm.structured import StructuredResult, generate_structured

PROMPT_VERSION = "copilot/1"
FEATURE_NAME = "copilot"
COPILOT_MODEL = "claude-sonnet-4-6"  # Q&A volume — ADR-0007 décision C

_SYSTEM_PROMPT = """\
Tu es copilote d'enquête fraude Procure-to-Pay (P2P) pour un analyste
d'audit interne français. Tu réponds à UNE question prédéfinie sur un cas
d'investigation, exclusivement à partir des sources fournies.

Règles spécifiques :
- Réponse courte et directe (answer_short), puis preuves sourcées (evidence),
  puis ce que les sources ne permettent PAS d'affirmer (uncertainties).
- Tu ne déclenches JAMAIS d'action : pas de blocage de paiement, pas de
  clôture, pas d'escalade automatique. Ta recommended_next_action est une
  proposition adressée à l'analyste, qui décide.
- Si les sources ne suffisent pas à répondre, dis-le explicitement dans
  answer_short et liste le manque dans uncertainties.
- Style : sobre, audit, sans familiarité."""


@dataclass(frozen=True)
class CopilotQuestion:
    """Question prédéfinie du catalogue (pas de chat libre au MVP)."""

    question_id: str
    label_fr: str
    instruction: str


QUESTIONS: dict[str, CopilotQuestion] = {
    q.question_id: q
    for q in (
        CopilotQuestion(
            question_id="why_severity",
            label_fr="Pourquoi cette alerte a-t-elle cette sévérité ?",
            instruction=(
                "Explique pourquoi ce cas porte sa sévérité actuelle : quels "
                "éléments des sources la justifient, et qu'est-ce qui la ferait "
                "monter ou descendre."
            ),
        ),
        CopilotQuestion(
            question_id="deterministic_signals",
            label_fr="Quels signaux sont déterministes ?",
            instruction=(
                "Liste les signaux de ce cas issus de règles déterministes "
                "(comparaisons explicites : IBAN modifié, seuils, doublons, "
                "sanctions) par opposition aux scores statistiques (ML). "
                "Appuie-toi sur les rule_id présents dans les sources."
            ),
        ),
        CopilotQuestion(
            question_id="missing_to_conclude",
            label_fr="Qu'est-ce qui manque pour conclure ?",
            instruction=(
                "Identifie les pièces et vérifications manquantes pour qu'un "
                "reviewer puisse conclure ce cas (confirmé / faux positif), "
                "et propose l'ordre dans lequel les obtenir."
            ),
        ),
        CopilotQuestion(
            question_id="failed_control",
            label_fr="Quel contrôle interne a échoué ?",
            instruction=(
                "Déduis des sources quel contrôle interne a échoué ou été "
                "contourné (4-eyes, séparation des tâches, rapprochement "
                "PO/facture, gel des données de base) et quelle remédiation "
                "proposer au contrôle interne."
            ),
        ),
    )
}


def ask_copilot(
    question_id: str,
    case: Case,
    *,
    events: list[CaseEvent] | None = None,
    findings: list[dict[str, Any]] | None = None,
    audit_log: AuditLog | None = None,
    actor: str = "system",
    api_key: str | None = None,
) -> StructuredResult[CopilotAnswer]:
    """Répond à une question prédéfinie sur un cas, preuves sourcées.

    Raises:
        KeyError: question_id hors catalogue.
        ValueError: clé API absente ou sortie vide.
        ProvenanceError: la réponse cite des sources hors pack.
    """
    if question_id not in QUESTIONS:
        raise KeyError(f"Question inconnue : {question_id}. Catalogue : {sorted(QUESTIONS)}.")
    question = QUESTIONS[question_id]
    source_pack = build_case_source_pack(case, events, findings)
    result = generate_structured(
        output_schema=CopilotAnswer,
        system_prompt=_SYSTEM_PROMPT,
        prompt_version=PROMPT_VERSION,
        user_content=(
            f"Question de l'analyste sur le cas {case.case_id} : "
            f"« {question.label_fr} »\n\nConsigne d'analyse : {question.instruction}"
        ),
        source_pack=source_pack,
        model=COPILOT_MODEL,
        api_key=api_key,
    )
    # Garde-fou métier : le copilote assiste, il ne décide jamais.
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
