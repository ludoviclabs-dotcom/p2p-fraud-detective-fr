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

from dataclasses import dataclass, field

from p2p_fraud.cases.audit_log import AuditLog, AuditLogEntry
from p2p_fraud.llm.structured import StructuredResult

AI_GENERATION_KIND = "ai.generation"

_MTOK = 1_000_000

# Prix publics par MTok (input $, output $) — ADR-0007 décision C.
# Le cache lu est facturé ~0,1 × le prix input. Un modèle hors table donne
# un coût None (jamais d'estimation silencieusement fausse).
MODEL_PRICING_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


def estimate_cost_usd(
    model: str, *, input_tokens: int, output_tokens: int, cached_tokens: int = 0
) -> float | None:
    """Coût estimé d'un appel en USD ; None si le modèle est hors table de prix."""
    pricing = next(
        (p for prefix, p in MODEL_PRICING_PER_MTOK.items() if model.startswith(prefix)),
        None,
    )
    if pricing is None:
        return None
    in_price, out_price = pricing
    return (
        input_tokens * in_price + cached_tokens * in_price * 0.1 + output_tokens * out_price
    ) / _MTOK


@dataclass
class AIUsageBucket:
    """Agrégat d'usage IA (une feature, ou le total)."""

    n_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0
    n_calls_unpriced: int = 0  # appels dont le modèle est hors table de prix
    models: set[str] = field(default_factory=set)

    def add(self, payload: dict) -> None:
        input_tokens = int(payload.get("input_tokens") or 0)
        output_tokens = int(payload.get("output_tokens") or 0)
        cached_tokens = int(payload.get("cached_tokens") or 0)
        model = str(payload.get("model") or "")
        self.n_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cached_tokens += cached_tokens
        if model:
            self.models.add(model)
        cost = estimate_cost_usd(
            model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )
        if cost is None:
            self.n_calls_unpriced += 1
        else:
            self.cost_usd += cost


def aggregate_ai_usage(audit_log: AuditLog) -> tuple[AIUsageBucket, dict[str, AIUsageBucket]]:
    """Agrège toutes les entrées `ai.generation` du journal.

    Retourne (total, par_feature) — la matière première du dashboard de coût
    IA : le ledger trace déjà chaque appel, on ne fait qu'additionner.
    """
    total = AIUsageBucket()
    by_feature: dict[str, AIUsageBucket] = {}
    for entry in audit_log.all():
        if entry.kind != AI_GENERATION_KIND:
            continue
        total.add(entry.payload)
        feature = str(entry.payload.get("feature") or "inconnue")
        by_feature.setdefault(feature, AIUsageBucket()).add(entry.payload)
    return total, by_feature


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
