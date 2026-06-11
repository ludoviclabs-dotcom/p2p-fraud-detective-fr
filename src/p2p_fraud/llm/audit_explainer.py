"""Audit Log Explainer — traduction du verdict cryptographique en langage audit.

Feature pilote du socle IA de confiance (ADR-0007). Séparation stricte :

1. **Vérification = code déterministe.** `AuditLog.verify_chain()` recalcule
   la chaîne SHA-256 et valide les signatures Ed25519. Le verdict technique
   (`TechnicalVerdict`) est produit ici, AVANT tout appel modèle.
2. **Le LLM traduit, il ne vérifie pas.** Le prompt système l'interdit
   explicitement ; le source pack ne contient que le verdict déjà calculé,
   donc le modèle ne peut citer que des faits établis par le code.
3. **Provenance validée en code** : chaque affirmation de l'explication cite
   des `source_ids` du verdict, vérifiés par `validate_provenance`.
4. **Journalisé** : l'appel est inscrit au ledger `ai.generation` du même
   audit log (l'explication d'un journal devient elle-même un événement
   du journal — traçabilité complète).
"""

from __future__ import annotations

from dataclasses import dataclass

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.llm.ai_ledger import log_ai_generation
from p2p_fraud.llm.provenance import SourcePack
from p2p_fraud.llm.schemas import AuditChainStatus, AuditExplanation
from p2p_fraud.llm.structured import (
    DEFAULT_STRUCTURED_MODEL,
    StructuredResult,
    generate_structured,
)

PROMPT_VERSION = "audit-explainer/1"
FEATURE_NAME = "audit_explainer"

_SYSTEM_PROMPT = """\
Tu traduis le résultat d'une vérification cryptographique de journal d'audit
en langage compréhensible par un commissaire aux comptes (CAC), un DAF ou un
contrôleur interne français.

Contexte technique (déjà établi par le code, pas par toi) :
- le journal est un log append-only chaîné par hash SHA-256 : chaque entrée
  référence le hash de la précédente, toute altération a posteriori casse la
  chaîne à partir de l'entrée modifiée ;
- les entrées peuvent porter une signature Ed25519 vérifiable avec la clé
  publique exposée par le système (non-répudiation) ;
- la vérification (recalcul des hashes, contrôle des signatures) a déjà été
  exécutée par du code déterministe. Son verdict t'est fourni en sources.

Règles spécifiques :
- Ne dis JAMAIS que tu as vérifié toi-même quoi que ce soit. Le code a produit
  le verdict ; tu l'expliques.
- En cas de rupture de chaîne, `human_review_required` est obligatoirement true
  et tu recommandes des diligences (investigation des séquences touchées,
  rapprochement avec l'archivage WORM, information du reviewer).
- Style : français formel d'audit, sans jargon cryptographique non expliqué.
- Reste factuel : pas de spéculation sur la cause d'une rupture (altération
  malveillante vs incident technique) — c'est précisément l'objet de la revue
  humaine."""


@dataclass(frozen=True)
class TechnicalVerdict:
    """Verdict de vérification produit par le code déterministe."""

    chain_status: AuditChainStatus
    n_total: int
    n_signed: int
    invalid_seqs: list[int]
    signatures_checked: bool  # une clé publique était disponible

    def to_source_pack(self) -> SourcePack:
        pack = SourcePack()
        pack.add("verdict.status", "Statut de la chaîne de hash", self.chain_status.value)
        pack.add("verdict.n_total", "Nombre total d'entrées du journal", self.n_total)
        pack.add("verdict.n_signed", "Nombre d'entrées signées Ed25519", self.n_signed)
        pack.add(
            "verdict.invalid_seqs",
            "Numéros de séquence en rupture (vide si chaîne intacte)",
            self.invalid_seqs,
        )
        pack.add(
            "verdict.signatures_checked",
            "Les signatures ont été contrôlées avec la clé publique configurée",
            self.signatures_checked,
        )
        return pack


def compute_verdict(audit_log: AuditLog, *, public_key_b64: str = "") -> TechnicalVerdict:
    """Exécute la vérification déterministe et fige le verdict technique."""
    valid, invalid = audit_log.verify_chain(public_key_b64=public_key_b64)
    entries = audit_log.all()
    if not entries:
        status = AuditChainStatus.EMPTY
    elif valid:
        status = AuditChainStatus.INTACT
    else:
        status = AuditChainStatus.BROKEN
    return TechnicalVerdict(
        chain_status=status,
        n_total=len(entries),
        n_signed=sum(1 for e in entries if e.signature),
        invalid_seqs=invalid,
        signatures_checked=bool(public_key_b64),
    )


def explain_verdict(
    verdict: TechnicalVerdict,
    *,
    audit_log: AuditLog | None = None,
    actor: str = "system",
    model: str = DEFAULT_STRUCTURED_MODEL,
    api_key: str | None = None,
) -> StructuredResult[AuditExplanation]:
    """Traduit un verdict technique en explication audit structurée et sourcée.

    Si `audit_log` est fourni, l'appel est journalisé au ledger `ai.generation`.

    Raises:
        ValueError: clé API absente ou sortie vide.
        ProvenanceError: l'explication cite des sources hors verdict.
    """
    source_pack = verdict.to_source_pack()
    result = generate_structured(
        output_schema=AuditExplanation,
        system_prompt=_SYSTEM_PROMPT,
        prompt_version=PROMPT_VERSION,
        user_content=(
            "Explique le résultat de vérification ci-dessus (fourni en sources) "
            "pour un public d'audit. Retourne l'explication structurée."
        ),
        source_pack=source_pack,
        model=model,
        api_key=api_key,
    )
    # Garde-fou métier : une rupture impose toujours la revue humaine, quoi
    # qu'ait répondu le modèle.
    if verdict.chain_status is AuditChainStatus.BROKEN:
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
            human_review_required=result.output.human_review_required,
        )
    return result
