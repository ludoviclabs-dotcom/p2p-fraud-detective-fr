"""DSL de règles de détection — format YAML déterministe (Phase 4, ADR-0007).

Une règle est un ensemble de conditions de comparaison de champs, combinées
en `all` (ET) ou `any` (OU). Aucun calcul statistique implicite : uniquement
des comparaisons explicites sur les champs du record (facture, événement
master data…). La règle déclare ses `required_fields` : un record auquel il
manque un champ requis ne matche jamais (fail-safe — on n'alerte pas sur des
données incomplètes).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["low", "medium", "high", "critical"]


class ConditionOp(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    EXISTS = "exists"
    MISSING = "missing"


class RuleCondition(BaseModel):
    """Condition feuille : comparaison d'un champ du record à une valeur."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(..., min_length=1, max_length=64)
    op: ConditionOp
    value: str | int | float | bool | None = None
    values: list[str] | None = Field(
        default=None, description="Liste de valeurs pour in / not_in."
    )


class RuleSpec(BaseModel):
    """Spécification complète d'une règle de détection."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    name: str = Field(..., min_length=3, max_length=256)
    description: str = Field(..., min_length=10, max_length=2000)
    severity: Severity
    reason_code: str = Field(..., pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    required_fields: list[str] = Field(..., min_length=1)
    match_mode: Literal["all", "any"] = "all"
    conditions: list[RuleCondition] = Field(..., min_length=1)
    known_limitations: list[str] = Field(default_factory=list)


class RuleParseError(ValueError):
    """YAML invalide ou non conforme au schéma RuleSpec."""


def parse_rule_yaml(text: str) -> RuleSpec:
    """Parse + valide un document YAML de règle (fail-closed)."""
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RuleParseError(f"YAML invalide : {exc}") from exc
    if not isinstance(raw, dict):
        raise RuleParseError("Le document YAML doit être un objet (mapping).")
    try:
        return RuleSpec.model_validate(raw)
    except Exception as exc:
        raise RuleParseError(f"Règle non conforme au schéma : {exc}") from exc


def rule_to_yaml(rule: RuleSpec) -> str:
    """Sérialise une règle en YAML canonique (ordre des champs préservé)."""
    data = rule.model_dump(mode="json", exclude_none=True)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def _eval_condition(cond: RuleCondition, record: Mapping[str, Any]) -> bool:
    present = cond.field in record and record[cond.field] is not None
    if cond.op is ConditionOp.EXISTS:
        return present
    if cond.op is ConditionOp.MISSING:
        return not present
    if not present:
        return False
    actual = record[cond.field]

    if cond.op in (ConditionOp.GT, ConditionOp.GTE, ConditionOp.LT, ConditionOp.LTE):
        left = _as_number(actual)
        right = _as_number(cond.value)
        if left is None or right is None:
            return False
        return {
            ConditionOp.GT: left > right,
            ConditionOp.GTE: left >= right,
            ConditionOp.LT: left < right,
            ConditionOp.LTE: left <= right,
        }[cond.op]

    if cond.op in (ConditionOp.EQ, ConditionOp.NE):
        left_num, right_num = _as_number(actual), _as_number(cond.value)
        if left_num is not None and right_num is not None:
            equal = left_num == right_num
        else:
            equal = str(actual).strip().lower() == str(cond.value).strip().lower()
        return equal if cond.op is ConditionOp.EQ else not equal

    if cond.op in (ConditionOp.IN, ConditionOp.NOT_IN):
        candidates = {str(v).strip().lower() for v in (cond.values or [])}
        member = str(actual).strip().lower() in candidates
        return member if cond.op is ConditionOp.IN else not member

    if cond.op is ConditionOp.CONTAINS:
        return str(cond.value).strip().lower() in str(actual).lower()

    return False  # op inconnu — fail-safe


def evaluate(rule: RuleSpec, record: Mapping[str, Any]) -> bool:
    """Évalue une règle sur un record. Champ requis manquant → False."""
    for field in rule.required_fields:
        if field not in record or record[field] is None:
            return False
    results = (_eval_condition(c, record) for c in rule.conditions)
    return all(results) if rule.match_mode == "all" else any(results)


def run_rule(
    rule: RuleSpec,
    records: list[Mapping[str, Any]],
    *,
    id_field: str = "invoice_id",
) -> list[Any]:
    """Applique la règle à un lot de records ; renvoie les ids (ou index) matchés."""
    matched: list[Any] = []
    for i, record in enumerate(records):
        if evaluate(rule, record):
            matched.append(record.get(id_field, i))
    return matched
