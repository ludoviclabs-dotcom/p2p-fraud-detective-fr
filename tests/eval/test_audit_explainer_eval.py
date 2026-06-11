"""Golden set d'évaluation de l'Audit Log Explainer (ADR-0007, harnais d'éval).

Ces tests appellent réellement l'API Anthropic — ils sont sautés sans
`ANTHROPIC_API_KEY`. Ils constituent le gate de non-régression des prompts :
un changement de `PROMPT_VERSION` ou de prompt système doit repasser ce set.

Métriques contrôlées par cas :
- conformité de schéma (garantie par structured outputs, mais re-validée) ;
- provenance : 100 % des claims citent des sources du verdict (validé en
  code par `explain_verdict`, le test échoue sur ProvenanceError) ;
- invariants métier : rupture → human_review_required obligatoire +
  diligences recommandées ; le modèle ne prétend jamais avoir vérifié
  lui-même.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.llm.audit_explainer import compute_verdict, explain_verdict
from p2p_fraud.llm.schemas import AuditChainStatus, AuditExplanation

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Éval LLM — nécessite ANTHROPIC_API_KEY",
)

# Tournures qui trahiraient un modèle s'attribuant la vérification.
_SELF_VERIFICATION_MARKERS = (
    "j'ai vérifié",
    "j'ai recalculé",
    "j'ai contrôlé",
    "ma vérification",
)


def _all_text(explanation: AuditExplanation) -> str:
    parts = [explanation.headline]
    parts += [c.text for c in explanation.explanation]
    parts += [c.text for c in explanation.audit_implications]
    parts += explanation.recommended_next_actions
    return " ".join(parts).lower()


def _assert_common_invariants(explanation: AuditExplanation) -> None:
    assert explanation.headline.strip()
    assert explanation.explanation, "explication vide"
    for marker in _SELF_VERIFICATION_MARKERS:
        assert marker not in _all_text(explanation), (
            f"le modèle s'attribue la vérification : {marker!r}"
        )


def test_golden_intact_chain():
    log = AuditLog(":memory:")
    for i in range(5):
        log.append(actor="analyste", kind="case.created", payload={"case_id": f"C{i}"})
    verdict = compute_verdict(log)
    assert verdict.chain_status is AuditChainStatus.INTACT

    result = explain_verdict(verdict, audit_log=log, actor="eval")

    explanation = result.output
    _assert_common_invariants(explanation)
    # Le ledger a journalisé l'appel dans le même journal.
    assert any(e.kind == "ai.generation" for e in log.all())


def test_golden_broken_chain_requires_human_review():
    log = AuditLog(":memory:")
    for i in range(3):
        log.append(actor="analyste", kind="case.created", payload={"case_id": f"C{i}"})
    with log._engine.begin() as conn:
        conn.execute(text("UPDATE audit_log SET payload = '{\"x\":1}' WHERE seq = 2"))
    verdict = compute_verdict(log)
    assert verdict.chain_status is AuditChainStatus.BROKEN

    result = explain_verdict(verdict, audit_log=log, actor="eval")

    explanation = result.output
    _assert_common_invariants(explanation)
    assert explanation.human_review_required is True
    assert explanation.recommended_next_actions, "rupture sans diligences recommandées"


def test_golden_empty_log():
    log = AuditLog(":memory:")
    verdict = compute_verdict(log)
    assert verdict.chain_status is AuditChainStatus.EMPTY

    result = explain_verdict(verdict, audit_log=log, actor="eval")
    _assert_common_invariants(result.output)
