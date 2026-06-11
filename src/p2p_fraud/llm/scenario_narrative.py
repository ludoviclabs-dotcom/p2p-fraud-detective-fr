"""Narratif de scénario synthétique — habillage pédagogique (Phase 6, ADR-0007).

Division stricte des rôles :
- le générateur déterministe (`synthetic/scenarios.py`) reste SEUL
  responsable des données et des labels ground-truth (`is_fraud`,
  `fraud_type`) — sinon on empoisonnerait les golden sets d'éval ;
- le LLM ne produit que le récit (pitch, mode opératoire, pièges
  faux-positifs), sourcé sur les métadonnées du scénario.

Modèle : Sonnet 4.6 (narratif, ADR-0007 décision C).
"""

from __future__ import annotations

from typing import Any

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.llm.ai_ledger import log_ai_generation
from p2p_fraud.llm.provenance import SourcePack
from p2p_fraud.llm.schemas import ScenarioNarrative
from p2p_fraud.llm.structured import StructuredResult, generate_structured

PROMPT_VERSION = "scenario-narrative/1"
FEATURE_NAME = "scenario_narrative"
NARRATIVE_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """\
Tu rédiges l'habillage pédagogique d'un scénario de fraude Procure-to-Pay
SYNTHÉTIQUE, utilisé pour la démonstration et la formation.

Règles spécifiques :
- Le scénario, ses données et ses labels sont générés par du code
  déterministe : tu n'inventes ni montants, ni fournisseurs, ni détecteurs —
  tu racontes ce que décrivent les sources.
- expected_detectors reprend EXACTEMENT les détecteurs listés en sources.
- false_positive_traps décrit des situations LÉGITIMES qui ressemblent au
  schéma de fraude (le piège classique de la démo) — formulées de façon
  générique, sans inventer de données chiffrées.
- Ton sobre, pédagogique, audience DAF / audit interne. Aucune donnée
  personnelle réelle."""


def build_scenario_source_pack(meta: Any) -> SourcePack:
    """Source pack depuis un ScenarioMeta (synthetic/scenarios.py)."""
    pack = SourcePack()
    pack.add("scenario.name", "Identifiant du scénario", meta.name)
    pack.add("scenario.title", "Titre", meta.title)
    pack.add("scenario.pillar", "Pilier de fraude", meta.pillar)
    pack.add("scenario.severity", "Sévérité attendue", meta.severity)
    pack.add("scenario.short", "Résumé court", meta.short)
    pack.add("scenario.detectors", "Détecteurs attendus", list(meta.detectors))
    pack.add(
        "scenario.target_vendor",
        "Fournisseur cible (synthétique)",
        meta.target_vendor or "aucun",
    )
    pack.add("scenario.storyline", "Storyline de référence", meta.storyline)
    return pack


def generate_scenario_narrative(
    meta: Any,
    *,
    audit_log: AuditLog | None = None,
    actor: str = "system",
    api_key: str | None = None,
) -> StructuredResult[ScenarioNarrative]:
    """Génère l'habillage narratif d'un scénario synthétique existant.

    Raises:
        ValueError: clé API absente ou sortie vide.
        ProvenanceError: le récit cite des sources hors pack.
    """
    source_pack = build_scenario_source_pack(meta)
    result = generate_structured(
        output_schema=ScenarioNarrative,
        system_prompt=_SYSTEM_PROMPT,
        prompt_version=PROMPT_VERSION,
        user_content=(
            f"Rédige l'habillage narratif du scénario synthétique "
            f"« {meta.title} » à partir des sources fournies."
        ),
        source_pack=source_pack,
        model=NARRATIVE_MODEL,
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
