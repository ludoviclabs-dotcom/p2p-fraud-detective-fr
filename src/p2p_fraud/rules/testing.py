"""Exécution déterministe des cas de test d'une règle (Phase 4, ADR-0007).

Les cas de test (positifs : le record DOIT matcher ; négatifs : il NE DOIT
PAS) sont générés par le LLM au draft, mais leur exécution est 100 % code :
c'est ce rapport — pas la parole du modèle — qui conditionne la promotion
d'une règle dans le store.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from p2p_fraud.rules.dsl import RuleSpec, evaluate


class RuleTestCase(BaseModel):
    """Un cas de test : un record synthétique + le verdict attendu."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=256)
    record: dict[str, Any]
    expect_match: bool


class RuleTestResult(BaseModel):
    name: str
    expected: bool
    actual: bool
    passed: bool


class RuleTestReport(BaseModel):
    all_passed: bool
    n_total: int
    n_passed: int
    results: list[RuleTestResult]


def run_rule_tests(rule: RuleSpec, cases: list[RuleTestCase]) -> RuleTestReport:
    """Exécute tous les cas de test sur la règle compilée."""
    results: list[RuleTestResult] = []
    for case in cases:
        actual = evaluate(rule, case.record)
        results.append(
            RuleTestResult(
                name=case.name,
                expected=case.expect_match,
                actual=actual,
                passed=actual == case.expect_match,
            )
        )
    n_passed = sum(1 for r in results if r.passed)
    return RuleTestReport(
        all_passed=n_passed == len(results) and len(results) > 0,
        n_total=len(results),
        n_passed=n_passed,
        results=results,
    )
