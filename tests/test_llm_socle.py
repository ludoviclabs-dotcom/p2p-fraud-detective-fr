"""Tests du socle IA de confiance (ADR-0007) — déterministes, sans appel API.

Couvre : source pack, validation de provenance, collecte récursive des
claims, ledger ai.generation (chaîne intacte), verdict technique de
l'explainer (intact / vide / rompu) et stats de feedback par règle.
"""

from __future__ import annotations

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import CaseService
from p2p_fraud.llm.ai_ledger import AI_GENERATION_KIND, log_ai_generation
from p2p_fraud.llm.audit_explainer import compute_verdict
from p2p_fraud.llm.provenance import (
    ProvenanceError,
    SourcePack,
    validate_provenance,
)
from p2p_fraud.llm.schemas import AuditChainStatus, AuditExplanation, GroundedClaim
from p2p_fraud.llm.structured import StructuredResult, _collect_claims
from p2p_fraud.schema import Finding, Severity

# ─── SourcePack ──────────────────────────────────────────────────────────────


def test_source_pack_add_and_render():
    pack = SourcePack()
    pack.add("verdict.status", "Statut", "intact")
    pack.add("verdict.n_total", "Entrées", 42)
    assert pack.ids == {"verdict.status", "verdict.n_total"}
    rendered = pack.render()
    assert "[verdict.status] Statut : intact" in rendered
    assert "[verdict.n_total] Entrées : 42" in rendered


def test_source_pack_rejects_duplicate_id():
    pack = SourcePack()
    pack.add("a", "Label", 1)
    with pytest.raises(ValueError, match="dupliqué"):
        pack.add("a", "Autre", 2)


# ─── Validation de provenance ────────────────────────────────────────────────


def _pack() -> SourcePack:
    pack = SourcePack()
    pack.add("s1", "Fait 1", "x")
    pack.add("s2", "Fait 2", "y")
    return pack


def test_provenance_valid():
    claims = [GroundedClaim(text="ok", source_ids=["s1", "s2"])]
    report = validate_provenance(claims, _pack())
    assert report.valid
    report.raise_if_invalid()  # ne lève pas


def test_provenance_unknown_source_id_rejected():
    claims = [GroundedClaim(text="hallucination", source_ids=["s1", "fantome"])]
    report = validate_provenance(claims, _pack())
    assert not report.valid
    assert report.unknown_ids == {"hallucination": ["fantome"]}
    with pytest.raises(ProvenanceError, match="sources inconnues"):
        report.raise_if_invalid()


def test_provenance_unsourced_claim_rejected():
    claims = [GroundedClaim(text="sans source", source_ids=[])]
    report = validate_provenance(claims, _pack())
    assert not report.valid
    assert report.unsourced_claims == ["sans source"]
    with pytest.raises(ProvenanceError, match="sans source"):
        report.raise_if_invalid()


def test_collect_claims_recursive():
    explanation = AuditExplanation(
        headline="Chaîne intacte.",
        explanation=[GroundedClaim(text="a", source_ids=["s1"])],
        audit_implications=[GroundedClaim(text="b", source_ids=["s2"])],
        missing_evidence=[],
        human_review_required=False,
        recommended_next_actions=["archiver"],
    )
    claims = _collect_claims(explanation)
    assert {c.text for c in claims} == {"a", "b"}


# ─── Ledger ai.generation ────────────────────────────────────────────────────


def _fake_result() -> StructuredResult[AuditExplanation]:
    return StructuredResult(
        output=AuditExplanation(
            headline="x",
            explanation=[],
            audit_implications=[],
            missing_evidence=[],
            human_review_required=True,
            recommended_next_actions=[],
        ),
        model="claude-opus-4-8",
        prompt_version="audit-explainer/1",
        input_tokens=100,
        output_tokens=50,
        cached_tokens=80,
    )


def test_ai_ledger_appends_signed_chain_entry():
    log = AuditLog(":memory:")
    entry = log_ai_generation(
        log,
        actor="analyste@test",
        feature="audit_explainer",
        result=_fake_result(),
        source_ids=["verdict.status", "verdict.n_total"],
        human_review_required=True,
    )
    assert entry.kind == AI_GENERATION_KIND
    assert entry.payload["feature"] == "audit_explainer"
    assert entry.payload["prompt_version"] == "audit-explainer/1"
    assert entry.payload["model"] == "claude-opus-4-8"
    assert entry.payload["input_tokens"] == 100
    assert entry.payload["source_ids"] == ["verdict.n_total", "verdict.status"]
    assert entry.payload["human_review_required"] is True
    # L'entrée s'insère dans la chaîne hash sans la casser.
    valid, invalid = log.verify_chain()
    assert valid and not invalid


# ─── Verdict technique de l'Audit Explainer ─────────────────────────────────


def test_compute_verdict_empty():
    log = AuditLog(":memory:")
    verdict = compute_verdict(log)
    assert verdict.chain_status is AuditChainStatus.EMPTY
    assert verdict.n_total == 0


def test_compute_verdict_intact():
    log = AuditLog(":memory:")
    log.append(actor="t", kind="case.created", payload={"case_id": "C1"})
    log.append(actor="t", kind="case.closed", payload={"case_id": "C1"})
    verdict = compute_verdict(log)
    assert verdict.chain_status is AuditChainStatus.INTACT
    assert verdict.n_total == 2
    assert verdict.invalid_seqs == []


def test_compute_verdict_broken_after_tamper():
    from sqlalchemy import text

    log = AuditLog(":memory:")
    log.append(actor="t", kind="case.created", payload={"case_id": "C1"})
    log.append(actor="t", kind="case.closed", payload={"case_id": "C1"})
    # Altération a posteriori d'une entrée → la chaîne doit casser.
    with log._engine.begin() as conn:
        conn.execute(text('UPDATE audit_log SET payload = \'{"case_id":"C2"}\' WHERE seq = 1'))
    verdict = compute_verdict(log)
    assert verdict.chain_status is AuditChainStatus.BROKEN
    assert 1 in verdict.invalid_seqs


def test_verdict_source_pack_ids_stable():
    log = AuditLog(":memory:")
    pack = compute_verdict(log).to_source_pack()
    assert pack.ids == {
        "verdict.status",
        "verdict.n_total",
        "verdict.n_signed",
        "verdict.invalid_seqs",
        "verdict.signatures_checked",
    }


# ─── Feedback stats par règle (boucle de feedback détection) ────────────────


def _finding(rule_id: str, invoice_id: str) -> Finding:
    return Finding(
        invoice_id=invoice_id,
        detector="duplicates",
        rule_id=rule_id,
        signal="test",
        severity=Severity.HIGH,
        evidence={},
    )


def test_feedback_stats_aggregates_closure_verdicts_by_rule():
    from p2p_fraud.api.v1 import cases_feedback_stats

    service = CaseService(":memory:")
    c1 = service.create_case_from_finding(_finding("DUP_EXACT", "INV1"), actor="t")
    c2 = service.create_case_from_finding(_finding("DUP_EXACT", "INV2"), actor="t")
    c3 = service.create_case_from_finding(_finding("IBAN_CHANGE", "INV3"), actor="t")
    service.create_case_from_finding(_finding("DUP_EXACT", "INV4"), actor="t")  # reste ouvert
    service.close(c1.case_id, CaseStatus.CLOSED_FALSE_POSITIVE, actor="t", reason="fp")
    service.close(c2.case_id, CaseStatus.CLOSED_CONFIRMED, actor="t", reason="fraude")
    service.close(c3.case_id, CaseStatus.CLOSED_REJECTED, actor="t", reason="hors scope")

    stats = cases_feedback_stats("anonymous", service)

    assert stats.n_cases_closed == 3
    by_rule = {r.rule_id: r for r in stats.rules}
    assert by_rule["DUP_EXACT"].n_false_positive == 1
    assert by_rule["DUP_EXACT"].n_confirmed == 1
    assert by_rule["DUP_EXACT"].false_positive_rate == pytest.approx(0.5)
    assert by_rule["IBAN_CHANGE"].n_rejected == 1
    assert by_rule["IBAN_CHANGE"].false_positive_rate == 0.0
