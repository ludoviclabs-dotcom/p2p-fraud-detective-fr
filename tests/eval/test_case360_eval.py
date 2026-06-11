"""Golden set d'évaluation du Fraud Case 360 AI (Phase 3, ADR-0007).

Appelle réellement l'API Anthropic — sauté sans `ANTHROPIC_API_KEY`.
Gate de non-régression du prompt `case360/N`.

Invariants contrôlés :
- provenance 100 % (validée en code par generate_case360, le test échoue
  sur ProvenanceError) ;
- human_review_required toujours true (forcé en code, revérifié ici) ;
- cas pauvre en données → missing_evidence non vide plutôt que des faits
  inventés ;
- l'appel est journalisé au ledger ai.generation.
"""

from __future__ import annotations

import os

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.llm.case360 import generate_case360
from p2p_fraud.schema import Finding, Severity

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Éval LLM — nécessite ANTHROPIC_API_KEY",
)


def _service() -> CaseService:
    return CaseService(":memory:", audit_log=AuditLog(":memory:"))


def test_golden_iban_swap_case():
    service = _service()
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
        case.case_id,
        actor="analyste@eval",
        text="Contre-appel fournisseur en attente — numéro historique injoignable.",
    )
    case = service.get(case.case_id)
    events = service.list_events(case.case_id)

    result = generate_case360(case, events=events, audit_log=service.audit_log, actor="eval")

    dossier = result.output
    assert dossier.human_review_required is True
    assert dossier.verified_facts, "aucun fait vérifié produit"
    assert dossier.recommended_next_actions, "aucune diligence recommandée"
    # La sévérité reprise des sources ne doit pas être dégradée silencieusement.
    assert dossier.severity_assessment in {"high", "critical"}
    # Ledger journalisé dans le même audit log.
    assert any(e.kind == "ai.generation" for e in service.audit_log.all())


def test_golden_sparse_case_declares_missing_evidence():
    service = _service()
    finding = Finding(
        invoice_id="INV-VIDE",
        detector="duplicates",
        rule_id="DUP_FUZZY",
        signal="Doublon probable",
        severity=Severity.MEDIUM,
        evidence={},
    )
    case = service.create_case_from_finding(finding, actor="analyste@eval")
    case = service.get(case.case_id)

    result = generate_case360(case, events=[], audit_log=service.audit_log, actor="eval")

    dossier = result.output
    assert dossier.human_review_required is True
    # Cas pauvre : le modèle doit déclarer le manque plutôt que broder.
    assert dossier.missing_evidence or dossier.open_questions
