"""Génération IA structurée et groundée — wrapper commun du socle (ADR-0007).

Garanties apportées par ce module (et non par le prompt) :

- **Schéma** : la sortie est contrainte par les structured outputs natifs de
  l'API Anthropic (`client.messages.parse` + schéma Pydantic). Un JSON
  malformé ou non conforme ne peut pas se propager.
- **PII fail-closed** : le contenu utilisateur est passé au filtre
  `ai/redact.py` ; s'il subsiste une fuite (IBAN clair…), l'appel est bloqué
  par `LeakingFieldError` avant tout envoi réseau.
- **Provenance** : si un `source_pack` est fourni, chaque `GroundedClaim` de
  la sortie est validé en code contre le pack (`validate_provenance`).
- **Traçabilité** : le résultat porte modèle, version de prompt et tokens —
  à journaliser via `llm/ai_ledger.py`.

Modèle par défaut : `claude-opus-4-8` (génération structurée critique,
cf. ADR-0007 décision C). Surchargeable par appel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

from p2p_fraud.ai.redact import is_safe_for_llm, redact_text
from p2p_fraud.config import get_settings
from p2p_fraud.llm.provenance import SourcePack, validate_provenance
from p2p_fraud.llm.schemas import GroundedClaim

DEFAULT_STRUCTURED_MODEL = "claude-opus-4-8"

T = TypeVar("T", bound=BaseModel)

# Règles de grounding communes, ajoutées à tout prompt système structuré.
GROUNDING_RULES = """\
Règles de grounding (non négociables) :
- Fonde chaque affirmation exclusivement sur les sources fournies, identifiées
  par leur source_id entre crochets (ex. [verdict.status]).
- Cite dans `source_ids` uniquement des identifiants présents dans les sources.
  Ne jamais inventer un identifiant.
- Si une information manque pour conclure, déclare-le dans `missing_evidence`
  au lieu de combler le vide.
- Ne prends aucune décision automatique : formule des recommandations de revue
  humaine uniquement."""


@dataclass(frozen=True)
class StructuredResult(Generic[T]):
    """Sortie validée + métadonnées d'appel pour le ledger."""

    output: T
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int


def generate_structured(
    *,
    output_schema: type[T],
    system_prompt: str,
    prompt_version: str,
    user_content: str,
    source_pack: SourcePack | None = None,
    model: str = DEFAULT_STRUCTURED_MODEL,
    max_tokens: int = 4096,
    api_key: str | None = None,
) -> StructuredResult[T]:
    """Appel structuré unique : redaction → API (schéma forcé) → provenance.

    Args:
        output_schema: modèle Pydantic de la sortie (cf. `llm/schemas.py`).
        system_prompt: prompt système métier ; les règles de grounding et le
            source pack y sont ajoutés automatiquement.
        prompt_version: identifiant de version du prompt (ex. "audit-explainer/1"),
            journalisé dans le ledger pour reproductibilité.
        user_content: contenu de la requête (déjà factuel ; sera redacté).
        source_pack: faits citables ; si fourni, la provenance de tous les
            `GroundedClaim` de la sortie est validée en code (fail-closed).
        model: modèle Claude (défaut Opus 4.8 pour génération critique).
        max_tokens: plafond de sortie.
        api_key: clé API (fallback ANTHROPIC_API_KEY).

    Raises:
        ImportError: package anthropic absent.
        ValueError: clé API absente.
        LeakingFieldError: PII résiduelle dans le contenu après redaction.
        ProvenanceError: la sortie cite des sources inexistantes ou omet de sourcer.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise ImportError(
            "Le package 'anthropic' est requis pour la génération structurée. "
            "Installez-le avec : pip install anthropic>=0.25"
        ) from exc

    key = api_key or get_settings().anthropic_api_key
    if not key:
        raise ValueError(
            "Variable d'environnement ANTHROPIC_API_KEY manquante. "
            "Configurez-la dans .env ou dans les secrets du déploiement."
        )

    # Redaction PII fail-closed : on redacte, puis on vérifie qu'il ne reste rien.
    safe_user_content = redact_text(user_content)
    is_safe_for_llm(safe_user_content, raise_on_leak=True)

    system_blocks = [system_prompt, GROUNDING_RULES]
    if source_pack is not None:
        sources_text = redact_text(source_pack.render())
        is_safe_for_llm(sources_text, raise_on_leak=True)
        system_blocks.append(f"Sources citables :\n{sources_text}")
    full_system = "\n\n".join(system_blocks)

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": full_system,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": safe_user_content}],
        output_format=output_schema,
    )

    output = response.parsed_output
    if output is None:
        raise ValueError(
            f"Sortie structurée vide (stop_reason={response.stop_reason}) — "
            "augmenter max_tokens ou inspecter la requête."
        )

    if source_pack is not None:
        validate_provenance(_collect_claims(output), source_pack).raise_if_invalid()

    usage = response.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    return StructuredResult(
        output=output,
        model=response.model,
        prompt_version=prompt_version,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cached_tokens=cached,
    )


def _collect_claims(output: BaseModel) -> list[GroundedClaim]:
    """Extrait récursivement tous les GroundedClaim d'une sortie structurée."""
    claims: list[GroundedClaim] = []

    def _walk(value: object) -> None:
        if isinstance(value, GroundedClaim):
            claims.append(value)
        elif isinstance(value, BaseModel):
            for name in type(value).model_fields:
                _walk(getattr(value, name))
        elif isinstance(value, list | tuple):
            for v in value:
                _walk(v)
        elif isinstance(value, dict):
            for v in value.values():
                _walk(v)

    _walk(output)
    return claims
