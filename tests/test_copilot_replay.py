"""Tests déterministes du copilote, du replay et du narratif scénarios (P5-P6)."""

from __future__ import annotations

import pytest

from p2p_fraud.llm.copilot import QUESTIONS, ask_copilot
from p2p_fraud.llm.provenance import validate_provenance
from p2p_fraud.llm.scenario_narrative import build_scenario_source_pack
from p2p_fraud.llm.schemas import GroundedClaim
from p2p_fraud.synthetic.scenarios import get_scenario_meta, list_scenarios

# ─── Copilote : catalogue ────────────────────────────────────────────────────


def test_copilot_catalog_is_complete_and_consistent():
    # Les 4 questions du brief sont couvertes.
    assert set(QUESTIONS) == {
        "why_severity",
        "deterministic_signals",
        "missing_to_conclude",
        "failed_control",
    }
    for qid, question in QUESTIONS.items():
        assert question.question_id == qid
        assert question.label_fr.endswith("?")
        assert len(question.instruction) > 30


def test_copilot_rejects_unknown_question_before_any_api_call():
    # KeyError levée AVANT toute lecture de clé API / appel réseau.
    with pytest.raises(KeyError, match="Question inconnue"):
        ask_copilot("question_libre", case=None)  # type: ignore[arg-type]


# ─── Narratif scénarios : source pack ────────────────────────────────────────


def test_scenario_source_pack_covers_meta():
    meta = get_scenario_meta("bec_iban_swap")
    pack = build_scenario_source_pack(meta)
    assert pack.ids == {
        "scenario.name",
        "scenario.title",
        "scenario.pillar",
        "scenario.severity",
        "scenario.short",
        "scenario.detectors",
        "scenario.target_vendor",
        "scenario.storyline",
    }
    rendered = pack.render()
    assert "bec_iban_swap" in rendered
    assert meta.title in rendered


def test_scenario_source_pack_works_for_all_scenarios():
    for meta in list_scenarios():
        pack = build_scenario_source_pack(meta)
        claims = [GroundedClaim(text="t", source_ids=["scenario.detectors"])]
        assert validate_provenance(claims, pack).valid
