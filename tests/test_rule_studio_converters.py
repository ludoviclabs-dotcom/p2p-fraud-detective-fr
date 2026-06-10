"""Tests déterministes des convertisseurs du Rule Studio (sans appel API)."""

from __future__ import annotations

from p2p_fraud.llm.rule_studio import (
    RuleConditionDraft,
    RuleDraft,
    RuleFieldValue,
    RuleTestDraft,
    _to_spec,
    _to_test_cases,
)
from p2p_fraud.rules.dsl import parse_rule_yaml, rule_to_yaml
from p2p_fraud.rules.testing import run_rule_tests


def _draft() -> RuleDraft:
    return RuleDraft(
        rule_id="IBAN_CHANGE_NO_4EYES",
        name="Changement d'IBAN sans validation 4-eyes",
        description="Un événement master data IBAN dont le validateur est le demandeur ou absent.",
        severity="critical",
        reason_code="IBAN_CHANGE_NO_4EYES",
        required_fields=["field"],
        match_mode="all",
        conditions=[
            RuleConditionDraft(field="field", op="eq", value="iban"),
            RuleConditionDraft(field="validated_by", op="missing"),
        ],
        positive_tests=[
            RuleTestDraft(
                name="IBAN modifié sans validateur",
                record=[
                    RuleFieldValue(field="field", value="iban"),
                    RuleFieldValue(field="new_value", value="FRXX"),
                ],
                expect_match=True,
            )
        ],
        negative_tests=[
            RuleTestDraft(
                name="IBAN modifié avec validateur distinct",
                record=[
                    RuleFieldValue(field="field", value="iban"),
                    RuleFieldValue(field="validated_by", value="manager@corp"),
                ],
                expect_match=False,
            ),
            RuleTestDraft(
                name="changement d'adresse hors périmètre",
                record=[RuleFieldValue(field="field", value="address")],
                expect_match=False,
            ),
        ],
        known_limitations=["Ne vérifie pas l'égalité demandeur/validateur (champ composite)."],
    )


def test_draft_converts_to_valid_spec_with_yaml_roundtrip():
    spec = _to_spec(_draft())
    assert spec.rule_id == "IBAN_CHANGE_NO_4EYES"
    assert parse_rule_yaml(rule_to_yaml(spec)) == spec


def test_draft_tests_convert_and_pass_on_engine():
    draft = _draft()
    spec = _to_spec(draft)
    cases = _to_test_cases(draft)
    assert len(cases) == 3
    assert cases[0].record == {"field": "iban", "new_value": "FRXX"}
    report = run_rule_tests(spec, cases)
    assert report.all_passed
