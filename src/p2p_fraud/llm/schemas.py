"""Schémas Pydantic des sorties IA structurées — source de vérité unique (ADR-0007).

Tous les schémas de génération IA du produit vivent ici. Règles communes :

- chaque affirmation factuelle (`GroundedClaim`) cite les `source_ids` du
  source pack fourni au modèle — la validation de provenance est faite en
  code par `llm/provenance.py`, jamais déléguée au modèle ;
- le chemin « preuve insuffisante » est first-class : `missing_evidence` +
  `human_review_required` sont présents sur toute sortie ;
- aucune sortie ne porte de décision automatique — uniquement des
  recommandations de revue humaine.

Le frontend Next.js consomme le JSON typé de ces modèles via `/api/v1` ;
ne pas dupliquer ces schémas en Zod côté TypeScript.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GroundedClaim(BaseModel):
    """Affirmation factuelle sourcée — l'unité de base de toute sortie IA."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="L'affirmation, en français formel.")
    source_ids: list[str] = Field(
        ...,
        description="Identifiants des sources du source pack étayant l'affirmation. "
        "Ne jamais citer un identifiant absent du source pack.",
    )


class AuditChainStatus(StrEnum):
    """Verdict technique de la vérification de chaîne — produit par le code, pas le LLM."""

    INTACT = "intact"
    BROKEN = "broken"
    EMPTY = "empty"


class AuditExplanation(BaseModel):
    """Explication en langage audit du résultat de vérification cryptographique.

    Le statut technique (`chain_status`, séquences invalides, signatures) est
    calculé par `AuditLog.verify_chain()` AVANT l'appel modèle. Le modèle ne
    vérifie rien : il traduit le verdict pour un CAC / DAF / contrôleur interne.
    """

    model_config = ConfigDict(extra="forbid")

    headline: str = Field(
        ...,
        description="Conclusion en une phrase, compréhensible par un non-technicien.",
    )
    explanation: list[GroundedClaim] = Field(
        ...,
        description="Explication pas à pas du verdict, chaque point sourcé.",
    )
    audit_implications: list[GroundedClaim] = Field(
        ...,
        description="Conséquences pour l'audit (valeur probante, diligences).",
    )
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Éléments absents du verdict technique qui limiteraient la conclusion.",
    )
    human_review_required: bool = Field(
        ...,
        description="True si une revue humaine est nécessaire (toujours true en cas de rupture).",
    )
    recommended_next_actions: list[str] = Field(
        default_factory=list,
        description="Actions concrètes recommandées (jamais de décision automatique).",
    )


class ReplayStep(BaseModel):
    """Une étape de la séquence narrative Risk Replay (Phase 6, ADR-0007)."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Titre court de l'étape (5-8 mots).")
    business_explanation: str = Field(
        ..., description="Explication métier de l'étape, 1-3 phrases."
    )
    evidence: list[GroundedClaim] = Field(
        ..., description="Preuves de l'étape, chacune sourcée."
    )
    risk_level: Literal["info", "low", "medium", "high", "critical"] = Field(
        ..., description="Niveau de risque de l'étape (info pour les étapes système)."
    )
    reviewer_question: str = Field(
        ..., description="Question à poser au reviewer à cette étape."
    )


class RiskReplay(BaseModel):
    """Séquence narrative rejouant un cas comme une enquête (Phase 6).

    Re-skin narratif de données déjà établies (cas + workflow) — aucune
    nouvelle conclusion : chaque étape est sourcée et la revue humaine reste
    requise (forcée en code).
    """

    model_config = ConfigDict(extra="forbid")

    case_summary: str = Field(..., description="Résumé du cas en une phrase.")
    steps: list[ReplayStep] = Field(
        ..., description="3 à 10 étapes, ordonnées chronologiquement."
    )
    human_review_required: bool = Field(
        ..., description="Toujours true : le replay illustre, il ne conclut pas."
    )


class ScenarioNarrative(BaseModel):
    """Habillage narratif d'un scénario synthétique (Phase 6, ADR-0007).

    Le générateur déterministe (`synthetic/`) reste seul responsable des
    données et des labels ground-truth — le LLM ne produit que le récit
    pédagogique et les pièges faux-positifs, sourcés sur les métadonnées.
    """

    model_config = ConfigDict(extra="forbid")

    pitch: str = Field(..., description="Accroche du scénario en 1-2 phrases.")
    fraud_story: list[GroundedClaim] = Field(
        ..., description="Récit du mode opératoire, chaque point sourcé."
    )
    expected_detectors: list[str] = Field(
        ..., description="Détecteurs attendus, repris des sources uniquement."
    )
    false_positive_traps: list[str] = Field(
        ...,
        description="Pièges faux-positifs à montrer en démo (cas légitimes ressemblants).",
    )
    human_review_required: bool = Field(
        ..., description="Toujours true (contenu pédagogique à relire)."
    )


class CopilotAnswer(BaseModel):
    """Réponse du copilote analyste à une question prédéfinie (Phase 5, ADR-0007).

    Le copilote ne voit que le source pack du cas construit par le code (la
    « surface d'outils » est donc contrôlée en code, pas par le modèle) et ne
    déclenche jamais d'action : `human_review_required` est forcé à true.
    """

    model_config = ConfigDict(extra="forbid")

    answer_short: str = Field(
        ...,
        description="Réponse directe en 2-4 phrases, français formel d'audit.",
    )
    evidence: list[GroundedClaim] = Field(
        ...,
        description="Preuves étayant la réponse, chacune sourcée.",
    )
    uncertainties: list[str] = Field(
        default_factory=list,
        description="Ce que les sources ne permettent PAS d'affirmer.",
    )
    recommended_next_action: str = Field(
        ...,
        description="Prochaine action concrète pour l'analyste (jamais un blocage automatique).",
    )
    human_review_required: bool = Field(
        ...,
        description="Toujours true : le copilote assiste, il ne décide pas.",
    )


class RiskSignal(GroundedClaim):
    """Signal de risque sourcé — un claim enrichi d'un rule_id et d'une sévérité.

    Hérite de GroundedClaim pour que la validation de provenance s'applique
    automatiquement (`_collect_claims` collecte par isinstance).
    """

    rule_id: str = Field(
        ...,
        description="Identifiant de la règle/du détecteur à l'origine du signal "
        "(tel que présent dans les sources, ex. IBAN_CHANGE_NO_4EYES).",
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Sévérité du signal, reprise des sources — jamais réévaluée à la hausse.",
    )


class FraudCase360(BaseModel):
    """Dossier d'enquête généré pour un cas de fraude P2P (Phase 3, ADR-0007).

    Toutes les données factuelles proviennent du source pack (case, événements,
    findings) construit par le code. Le dossier sépare strictement faits
    vérifiés, signaux, contradictions et données manquantes — et n'autorise
    jamais une décision automatique : `human_review_required` est de toute
    façon forcé à true en code après génération.
    """

    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(
        ...,
        description="Synthèse exécutive du dossier en 3-5 phrases, français formel.",
    )
    severity_assessment: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Sévérité globale du dossier, cohérente avec celle du cas en source.",
    )
    verified_facts: list[GroundedClaim] = Field(
        ...,
        description="Faits vérifiés, chacun sourcé. Ne créer AUCUN fait absent des sources.",
    )
    risk_signals: list[RiskSignal] = Field(
        ...,
        description="Signaux de risque issus des détecteurs présents dans les sources.",
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description="Incohérences entre éléments du dossier (vide si aucune).",
    )
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Données manquantes pour conclure (à demander au reviewer).",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Questions ouvertes à instruire lors de la revue humaine.",
    )
    human_review_required: bool = Field(
        ...,
        description="Toujours true : un dossier généré exige une revue humaine.",
    )
    recommended_next_actions: list[str] = Field(
        default_factory=list,
        description="Diligences recommandées (jamais de blocage automatique).",
    )
