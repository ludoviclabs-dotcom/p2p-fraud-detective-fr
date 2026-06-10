"""Ledger des appels IA — journalisation dans l'audit log signé (ADR-0007).

Chaque génération IA produit une entrée `ai.generation` dans le même audit
log hash-chaîné / signé Ed25519 que le reste du produit. L'entrée porte tout
ce qu'il faut pour la reproductibilité et le registre AI Act :

- feature et version de prompt (ex. "audit_explainer" / "audit-explainer/1") ;
- modèle exact retourné par l'API ;
- tokens input / output / servis depuis le cache (base du suivi de coût) ;
- source_ids du source pack fourni au modèle ;
- indicateur `human_review_required` de la sortie.

Le contenu généré lui-même n'est PAS journalisé ici (il vit dans la feature
qui l'a demandé) — le ledger trace l'acte de génération, pas le texte.
"""

from __future__ import annotations

from p2p_fraud.cases.audit_log import AuditLog, AuditLogEntry
from p2p_fraud.llm.structured import StructuredResult

AI_GENERATION_KIND = "ai.generation"


def log_ai_generation(
    audit_log: AuditLog,
    *,
    actor: str,
    feature: str,
    result: StructuredResult,
    source_ids: list[str] | None = None,
    human_review_required: bool | None = None,
) -> AuditLogEntry:
    """Journalise un appel IA structuré dans l'audit log signé.

    Args:
        audit_log: journal append-only du produit (signé si signer configuré).
        actor: utilisateur ou service à l'origine de la génération.
        feature: identifiant stable de la feature (ex. "audit_explainer").
        result: sortie de `generate_structured` (modèle, tokens, prompt_version).
        source_ids: identifiants du source pack fourni au modèle.
        human_review_required: indicateur porté par la sortie, si applicable.
    """
    payload: dict = {
        "feature": feature,
        "prompt_version": result.prompt_version,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "cached_tokens": result.cached_tokens,
        "source_ids": sorted(source_ids or []),
    }
    if human_review_required is not None:
        payload["human_review_required"] = human_review_required
    return audit_log.append(actor=actor, kind=AI_GENERATION_KIND, payload=payload)
