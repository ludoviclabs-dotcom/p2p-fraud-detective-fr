"""Tests déterministes du Fraud Case 360 AI (Phase 3, ADR-0007) — sans appel API."""

from __future__ import annotations

from p2p_fraud.cases.service import CaseService
from p2p_fraud.llm.case360 import build_case_source_pack
from p2p_fraud.llm.provenance import validate_provenance
from p2p_fraud.llm.schemas import FraudCase360, GroundedClaim, RiskSignal
from p2p_fraud.llm.structured import _collect_claims
from p2p_fraud.schema import Finding, Severity


def _make_case_with_events():
    service = CaseService(":memory:")
    finding = Finding(
        invoice_id="INV-77",
        detector="master_data",
        rule_id="IBAN_CHANGE_NO_4EYES",
        signal="IBAN modifié sans validation 4-eyes",
        severity=Severity.CRITICAL,
        evidence={"vendor_id": "V-ALPHACOM", "exposure_eur": 125000},
    )
    case = service.create_case_from_finding(finding, actor="analyste@test")
    service.comment(
        case.case_id, actor="analyste@test", text="RIB à confirmer auprès du fournisseur"
    )
    case = service.get(case.case_id)
    events = service.list_events(case.case_id)
    return case, events


def test_source_pack_contains_case_facts_and_events():
    case, events = _make_case_with_events()
    pack = build_case_source_pack(case, events)

    assert "case.id" in pack.ids
    assert "case.severity" in pack.ids
    assert "case.finding_ids" in pack.ids
    # Un source_id par événement workflow (created + commented).
    assert "event.0" in pack.ids
    assert "event.1" in pack.ids

    rendered = pack.render()
    assert case.case_id in rendered
    assert "IBAN_CHANGE_NO_4EYES::INV-77" in rendered
    assert "critical" in rendered


def test_source_pack_ids_are_citable_by_provenance():
    case, events = _make_case_with_events()
    pack = build_case_source_pack(case, events)
    claims = [
        GroundedClaim(text="Le cas est critique", source_ids=["case.severity"]),
        GroundedClaim(text="Un commentaire a été déposé", source_ids=["event.1"]),
    ]
    assert validate_provenance(claims, pack).valid


def test_risk_signal_is_collected_as_grounded_claim():
    dossier = FraudCase360(
        executive_summary="Synthèse.",
        severity_assessment="critical",
        verified_facts=[GroundedClaim(text="fait", source_ids=["case.id"])],
        risk_signals=[
            RiskSignal(
                text="IBAN modifié sans 4-eyes",
                source_ids=["case.finding_ids"],
                rule_id="IBAN_CHANGE_NO_4EYES",
                severity="critical",
            )
        ],
        contradictions=[],
        missing_evidence=["RIB d'origine non fourni"],
        open_questions=["Le fournisseur a-t-il confirmé le changement ?"],
        human_review_required=True,
        recommended_next_actions=["Contre-appel fournisseur sur numéro connu"],
    )
    claims = _collect_claims(dossier)
    # Le RiskSignal hérite de GroundedClaim → collecté pour la provenance.
    assert {c.text for c in claims} == {"fait", "IBAN modifié sans 4-eyes"}
