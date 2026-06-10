"""Golden set du copilote, du Risk Replay et du narratif scénarios (P5-P6).

Appelle réellement l'API Anthropic — sauté sans `ANTHROPIC_API_KEY`.
Gates de non-régression des prompts copilot/N, risk-replay/N et
scenario-narrative/N.
"""

from __future__ import annotations

import os

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.llm.copilot import ask_copilot
from p2p_fraud.llm.replay import generate_replay
from p2p_fraud.llm.scenario_narrative import generate_scenario_narrative
from p2p_fraud.schema import Finding, Severity
from p2p_fraud.synthetic.scenarios import get_scenario_meta

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Éval LLM — nécessite ANTHROPIC_API_KEY",
)


def _case_with_history():
    service = CaseService(":memory:", audit_log=AuditLog(":memory:"))
    finding = Finding(
        invoice_id="INV-2026-0412",
        detector="master_data",
        rule_id="IBAN_CHANGE_NO_4EYES",
        signal="IBAN modifié sans validation 4-eyes 6 jours avant paiement",
        severity=Severity.CRITICAL,
        evidence={"vendor_id": "V-ALPHACOM", "exposure_eur": 125000},
    )
    case = service.create_case_from_finding(finding, actor="analyste@eval")
    service.comment(
        case.case_id, actor="analyste@eval", text="Contre-appel fournisseur en attente."
    )
    service.escalate(
        case.case_id, actor="analyste@eval", channel="audit-workflow", reason="Exposition élevée"
    )
    return service, service.get(case.case_id), service.list_events(case.case_id)


def test_golden_copilot_why_severity():
    service, case, events = _case_with_history()
    result = ask_copilot(
        "why_severity", case, events=events, audit_log=service.audit_log, actor="eval"
    )
    answer = result.output
    assert answer.human_review_required is True
    assert answer.answer_short.strip()
    assert answer.evidence, "réponse sans preuve sourcée"
    assert answer.recommended_next_action.strip()
    assert any(e.kind == "ai.generation" for e in service.audit_log.all())


def test_golden_copilot_missing_to_conclude_declares_uncertainty():
    service, case, events = _case_with_history()
    result = ask_copilot(
        "missing_to_conclude", case, events=events, audit_log=service.audit_log, actor="eval"
    )
    answer = result.output
    assert answer.human_review_required is True
    # La question porte sur le manque : la réponse doit en identifier.
    assert answer.uncertainties or answer.evidence


def test_golden_replay_chronological_steps():
    service, case, events = _case_with_history()
    result = generate_replay(
        case, events=events, audit_log=service.audit_log, actor="eval"
    )
    replay = result.output
    assert replay.human_review_required is True
    assert 3 <= len(replay.steps) <= 10
    for step in replay.steps:
        assert step.evidence, f"étape sans preuve : {step.title}"
        assert step.reviewer_question.strip()


def test_golden_scenario_narrative_detectors_grounded():
    log = AuditLog(":memory:")
    meta = get_scenario_meta("bec_iban_swap")
    result = generate_scenario_narrative(meta, audit_log=log, actor="eval")
    narrative = result.output
    assert narrative.human_review_required is True
    assert narrative.fraud_story, "récit vide"
    assert narrative.false_positive_traps, "aucun piège faux-positif"
    # Les détecteurs annoncés doivent venir des sources, pas être inventés.
    assert set(narrative.expected_detectors) <= set(meta.detectors)
    assert any(e.kind == "ai.generation" for e in log.all())
