"""Rule Studio — draft LLM d'une règle de détection depuis le français (Phase 4).

Séparation stricte des responsabilités (ADR-0007) :

- le LLM **drafte** : il convertit une règle métier en français vers une
  structure RuleDraft (conditions déterministes à un niveau, tests positifs
  et négatifs, limites connues) via la sortie structurée du socle ;
- le **code engage** : la structure est convertie en RuleSpec, sérialisée en
  YAML, re-parsée (aller-retour fail-closed), ses tests sont exécutés par le
  moteur déterministe, et seul le store (`rules/store.py`) peut la promouvoir
  — tests verts + backtest + 4-eyes.

Le draft est journalisé au ledger `ai.generation`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.llm.ai_ledger import log_ai_generation
from p2p_fraud.llm.structured import (
    DEFAULT_STRUCTURED_MODEL,
    StructuredResult,
    generate_structured,
)
from p2p_fraud.rules.dsl import RuleCondition, RuleSpec, parse_rule_yaml, rule_to_yaml
from p2p_fraud.rules.testing import RuleTestCase, RuleTestReport, run_rule_tests

PROMPT_VERSION = "rule-studio/1"
FEATURE_NAME = "rule_studio"

_SYSTEM_PROMPT = """\
Tu es architecte risk-engine Procure-to-Pay (P2P). Tu convertis une règle
métier exprimée en français en une règle de détection DÉTERMINISTE.

Contraintes du moteur de règles :
- une règle = une liste de conditions feuilles combinées en `all` (ET) ou
  `any` (OU) — pas d'imbrication ;
- opérateurs disponibles : eq, ne, gt, gte, lt, lte, in, not_in, contains,
  exists, missing — uniquement des comparaisons de champs explicites ;
- AUCUN calcul statistique implicite (pas de moyenne, percentile, ratio,
  fenêtre temporelle calculée) : si la règle métier en exige un, déclare-le
  dans known_limitations et propose la meilleure approximation par seuils ;
- champs usuels des factures : invoice_id, vendor_id, vendor_name, amount,
  invoice_date, siren, iban, po_number, user_id ; événements master data :
  field, old_value, new_value, validated_by, requested_by ;
- la règle déclare required_fields : les champs sans lesquels elle ne peut
  pas être évaluée.

Tests :
- fournis au moins 2 tests positifs (le record DOIT matcher) et 2 tests
  négatifs (il NE DOIT PAS matcher), dont au moins un cas limite exact
  (valeur à la frontière d'un seuil) ;
- chaque record de test ne contient que des valeurs synthétiques plausibles —
  jamais de données réelles.

Identifiants : rule_id et reason_code en MAJUSCULES_SOUS_TIRETS, parlants
pour un auditeur français."""


class RuleFieldValue(BaseModel):
    """Paire champ/valeur d'un record de test (les dicts libres ne sont pas
    exprimables en structured outputs — additionalProperties interdit)."""

    model_config = ConfigDict(extra="forbid")

    field: str
    value: str | int | float | bool | None


class RuleTestDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Intitulé court du cas de test.")
    record: list[RuleFieldValue] = Field(..., description="Champs du record synthétique testé.")
    expect_match: bool = Field(..., description="True si la règle DOIT matcher ce record.")


class RuleConditionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    op: Literal[
        "eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "exists", "missing"
    ]
    value: str | int | float | bool | None = Field(
        default=None, description="Valeur comparée (null pour exists/missing/in/not_in)."
    )
    values: list[str] | None = Field(
        default=None, description="Liste de valeurs, uniquement pour in / not_in."
    )


class RuleDraft(BaseModel):
    """Sortie structurée du draft LLM — convertie en RuleSpec par le code."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="MAJUSCULES_SOUS_TIRETS, ex. IBAN_CHANGE_NO_4EYES.")
    name: str
    description: str = Field(..., description="Reformulation précise de la règle métier.")
    severity: Literal["low", "medium", "high", "critical"]
    reason_code: str
    required_fields: list[str]
    match_mode: Literal["all", "any"]
    conditions: list[RuleConditionDraft]
    positive_tests: list[RuleTestDraft]
    negative_tests: list[RuleTestDraft]
    known_limitations: list[str] = Field(
        default_factory=list,
        description="Limites connues, dont tout besoin statistique non exprimable.",
    )


@dataclass(frozen=True)
class RuleDraftResult:
    """Draft converti, validé YAML aller-retour et testé par le moteur."""

    spec: RuleSpec
    yaml: str
    test_cases: list[RuleTestCase]
    test_report: RuleTestReport
    model: str
    prompt_version: str


def _to_spec(draft: RuleDraft) -> RuleSpec:
    return RuleSpec(
        rule_id=draft.rule_id,
        name=draft.name,
        description=draft.description,
        severity=draft.severity,
        reason_code=draft.reason_code,
        required_fields=draft.required_fields,
        match_mode=draft.match_mode,
        conditions=[
            RuleCondition(field=c.field, op=c.op, value=c.value, values=c.values)
            for c in draft.conditions
        ],
        known_limitations=draft.known_limitations,
    )


def _to_test_cases(draft: RuleDraft) -> list[RuleTestCase]:
    cases: list[RuleTestCase] = []
    for t in [*draft.positive_tests, *draft.negative_tests]:
        cases.append(
            RuleTestCase(
                name=t.name,
                record={fv.field: fv.value for fv in t.record},
                expect_match=t.expect_match,
            )
        )
    return cases


def draft_rule(
    description_fr: str,
    *,
    audit_log: AuditLog | None = None,
    actor: str = "system",
    model: str = DEFAULT_STRUCTURED_MODEL,
    api_key: str | None = None,
) -> RuleDraftResult:
    """Drafte une règle depuis le français, puis valide et teste en code.

    Raises:
        ValueError: clé API absente, sortie vide, ou draft sans tests
            positifs/négatifs.
        RuleParseError: le YAML produit ne repasse pas la validation (aller-
            retour fail-closed).
    """
    result: StructuredResult[RuleDraft] = generate_structured(
        output_schema=RuleDraft,
        system_prompt=_SYSTEM_PROMPT,
        prompt_version=PROMPT_VERSION,
        user_content=(
            f"Convertis cette règle métier en règle de détection déterministe :\n\n{description_fr}"
        ),
        model=model,
        max_tokens=8192,
        api_key=api_key,
    )
    draft = result.output
    if not draft.positive_tests or not draft.negative_tests:
        raise ValueError("Draft refusé : au moins un test positif ET un test négatif sont requis.")

    spec = _to_spec(draft)
    yaml_text = rule_to_yaml(spec)
    # Aller-retour fail-closed : ce qui est stocké doit re-parser à l'identique.
    reparsed = parse_rule_yaml(yaml_text)
    if reparsed != spec:
        raise ValueError("Draft refusé : l'aller-retour YAML n'est pas stable.")

    test_cases = _to_test_cases(draft)
    report = run_rule_tests(spec, test_cases)

    if audit_log is not None:
        log_ai_generation(
            audit_log,
            actor=actor,
            feature=FEATURE_NAME,
            result=result,
            human_review_required=True,  # une règle draftée n'est jamais active sans 4-eyes
        )
    return RuleDraftResult(
        spec=spec,
        yaml=yaml_text,
        test_cases=test_cases,
        test_report=report,
        model=result.model,
        prompt_version=result.prompt_version,
    )
