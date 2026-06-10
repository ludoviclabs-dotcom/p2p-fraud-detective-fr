"""Risk Replay — rejouer un cas comme une séquence d'enquête (Phase 6, ADR-0007).

Valeur démo/onboarding : transforme la timeline technique d'un cas (création,
signaux, commentaires, escalades) en séquence narrative courte. Aucune
nouvelle conclusion n'est produite — chaque étape est sourcée sur le même
source pack que le Dossier 360, la provenance est validée en code et la
revue humaine reste requise.

Modèle : Sonnet 4.6 (narratif, ADR-0007 décision C).
"""

from __future__ import annotations

from typing import Any

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import Case, CaseEvent
from p2p_fraud.llm.ai_ledger import log_ai_generation
from p2p_fraud.llm.case360 import build_case_source_pack
from p2p_fraud.llm.schemas import RiskReplay
from p2p_fraud.llm.structured import StructuredResult, generate_structured

PROMPT_VERSION = "risk-replay/1"
FEATURE_NAME = "risk_replay"
REPLAY_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """\
Tu transformes la timeline technique d'un cas de fraude Procure-to-Pay en
une séquence narrative courte (3 à 10 étapes), destinée à rejouer l'enquête
devant un reviewer, un DAF ou un prospect.

Règles spécifiques :
- Chaque étape suit l'ordre chronologique des sources (événements du cas).
- Chaque étape porte : un titre court, une explication métier accessible,
  ses preuves sourcées, un niveau de risque (info pour les étapes purement
  système) et une question à poser au reviewer.
- Tu ne produis AUCUNE conclusion nouvelle : si la timeline ne montre pas
  un fait, il n'apparaît pas dans le replay.
- Pas de dramatisation : ton sobre d'audit, pas de storytelling sensationnel."""


def generate_replay(
    case: Case,
    *,
    events: list[CaseEvent] | None = None,
    findings: list[dict[str, Any]] | None = None,
    audit_log: AuditLog | None = None,
    actor: str = "system",
    api_key: str | None = None,
) -> StructuredResult[RiskReplay]:
    """Génère la séquence Risk Replay d'un cas existant.

    Raises:
        ValueError: clé API absente ou sortie vide.
        ProvenanceError: une étape cite des sources hors pack.
    """
    source_pack = build_case_source_pack(case, events, findings)
    result = generate_structured(
        output_schema=RiskReplay,
        system_prompt=_SYSTEM_PROMPT,
        prompt_version=PROMPT_VERSION,
        user_content=(
            f"Rejoue le cas {case.case_id} en séquence narrative d'enquête "
            "à partir des sources fournies (ordre chronologique)."
        ),
        source_pack=source_pack,
        model=REPLAY_MODEL,
        max_tokens=8192,
        api_key=api_key,
    )
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
