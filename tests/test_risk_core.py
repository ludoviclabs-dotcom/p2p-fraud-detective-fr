"""Tests Risk Core — Sprint 1 MandateGuard.

Couvre :
- types (RiskSignal, RiskAssessmentResult immutability)
- scoring (combine_signals, to_level, decide)
- engine (assess + version, domain mismatch detection)
- reason_codes (registre, lookup, par domaine)
- adapter finding_bridge (Finding → RiskSignal)
- adapter master_data wrappé en RiskRule (end-to-end avec détecteur existant)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from p2p_fraud.risk_core import (
    RiskAssessmentResult,
    RiskDecision,
    RiskDomain,
    RiskEngine,
    RiskLevel,
    RiskRule,
    RiskSignal,
    Severity,
    combine_signals,
    decide,
    to_level,
)
from p2p_fraud.risk_core.adapters.finding_bridge import (
    DEFAULT_SCORE_BY_SEVERITY,
    finding_to_signal,
)
from p2p_fraud.risk_core.adapters.master_data_rules import (
    IbanChangeWithoutFourEyesRule,
    SupplierPaymentContext,
    build_supplier_payment_rules,
)
from p2p_fraud.risk_core.reason_codes import (
    REASON_CODES,
    get_reason_code_meta,
    list_codes_for_domain,
)
from p2p_fraud.schema import Finding, MasterDataField, VendorMasterEvent

# ─── Types ───────────────────────────────────────────────────────────────────


def test_risk_signal_is_frozen():
    s = RiskSignal(
        code="TEST_CODE",
        title="Titre",
        message="Message",
        severity=Severity.HIGH,
        score=50,
    )
    with pytest.raises((ValueError, TypeError)):
        s.score = 99  # type: ignore[misc]


def test_risk_signal_validates_score_range():
    with pytest.raises(Exception):  # noqa: B017 (pydantic ValidationError)
        RiskSignal(code="X", title="t", message="m", severity=Severity.LOW, score=150)


def test_assessment_result_is_frozen():
    r = RiskAssessmentResult(
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
        score=50,
        level=RiskLevel.MEDIUM,
        decision=RiskDecision.ALERT_USER,
        engine_version="test-1.0.0",
    )
    with pytest.raises((ValueError, TypeError)):
        r.score = 99  # type: ignore[misc]


# ─── Scoring ─────────────────────────────────────────────────────────────────


def _sig(severity: Severity, score: int, code: str = "TEST") -> RiskSignal:
    return RiskSignal(
        code=code,
        title="t",
        message="m",
        severity=severity,
        score=score,
    )


def test_combine_signals_empty():
    assert combine_signals([]) == 0


def test_combine_signals_caps_at_100():
    sigs = [_sig(Severity.CRITICAL, 80), _sig(Severity.HIGH, 50)]
    assert combine_signals(sigs) == 100


def test_combine_signals_sums():
    sigs = [_sig(Severity.MEDIUM, 25), _sig(Severity.LOW, 8)]
    assert combine_signals(sigs) == 33


def test_to_level_critical_forced_by_severity():
    """Un seul signal critical → CRITICAL même si score modéré."""
    sigs = [_sig(Severity.CRITICAL, 40)]  # score 40 but critical severity
    assert to_level(40, sigs) == RiskLevel.CRITICAL


def test_to_level_critical_by_score():
    sigs = [_sig(Severity.HIGH, 80)]
    assert to_level(80, sigs) == RiskLevel.CRITICAL


def test_to_level_thresholds():
    assert to_level(70, [_sig(Severity.HIGH, 70)]) == RiskLevel.HIGH
    assert to_level(50, [_sig(Severity.MEDIUM, 50)]) == RiskLevel.MEDIUM
    assert to_level(20, [_sig(Severity.LOW, 20)]) == RiskLevel.LOW
    assert to_level(0, []) == RiskLevel.LOW


def test_decide_dispute_ready_requires_critical_and_high_score():
    assert decide(85, [_sig(Severity.CRITICAL, 85)]) == RiskDecision.DISPUTE_READY


def test_decide_block_recommended_at_75():
    assert decide(75, [_sig(Severity.HIGH, 75)]) == RiskDecision.BLOCK_RECOMMENDED


def test_decide_review_at_60():
    assert decide(60, [_sig(Severity.HIGH, 60)]) == RiskDecision.REVIEW


def test_decide_alert_user_at_30():
    assert decide(30, [_sig(Severity.MEDIUM, 30)]) == RiskDecision.ALERT_USER


def test_decide_allow_monitor_at_15():
    assert decide(15, [_sig(Severity.LOW, 15)]) == RiskDecision.ALLOW_MONITOR


def test_decide_allow_below_15():
    assert decide(10, [_sig(Severity.LOW, 10)]) == RiskDecision.ALLOW
    assert decide(0, []) == RiskDecision.ALLOW


# ─── Reason codes registre ───────────────────────────────────────────────────


def test_registry_contains_sepa_codes():
    """Le registre couvre les reason codes SEPA du spec MandateGuard §06."""
    expected = {
        "NO_ACTIVE_MANDATE",
        "MANDATE_REVOKED",
        "MANDATE_AMOUNT_EXCEEDED",
        "RUM_MISMATCH",
        "ICS_MISMATCH",
    }
    assert expected.issubset(REASON_CODES.keys())


def test_registry_contains_supplier_codes():
    expected = {
        "NEW_BENEFICIARY",
        "SUPPLIER_RIB_RECENT_CHANGE",
        "FOUR_EYES_BREACH",
        "DUPLICATE_INVOICE",
    }
    assert expected.issubset(REASON_CODES.keys())


def test_get_reason_code_meta_known():
    meta = get_reason_code_meta("NO_ACTIVE_MANDATE")
    assert meta is not None
    assert meta.domain == RiskDomain.SEPA_DIRECT_DEBIT
    assert meta.default_severity == Severity.CRITICAL


def test_get_reason_code_meta_unknown():
    assert get_reason_code_meta("DOES_NOT_EXIST") is None


def test_list_codes_for_domain_sepa():
    sepa = list_codes_for_domain(RiskDomain.SEPA_DIRECT_DEBIT)
    assert "NO_ACTIVE_MANDATE" in sepa
    assert "MANDATE_REVOKED" in sepa
    # Pas de codes purement P2P
    assert "FOUR_EYES_BREACH" not in sepa


def test_list_codes_for_domain_supplier():
    supplier = list_codes_for_domain(RiskDomain.SUPPLIER_PAYMENT)
    assert "FOUR_EYES_BREACH" in supplier
    assert "DUPLICATE_INVOICE" in supplier
    assert "NO_ACTIVE_MANDATE" not in supplier


# ─── Engine ──────────────────────────────────────────────────────────────────


class _SyntheticRule:
    """Règle de test qui retourne toujours le même signal."""

    def __init__(self, code: str, severity: Severity, score: int, domain: RiskDomain):
        self.id = code
        self.version = "1.0.0"
        self.domain = domain
        self._sig = RiskSignal(
            code=code,
            title=f"Titre {code}",
            message="msg",
            severity=severity,
            score=score,
        )

    def evaluate(self, ctx: object) -> list[RiskSignal]:
        return [self._sig]


def test_engine_assess_empty_rules():
    engine = RiskEngine(
        [],
        engine_version="test-1.0.0",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
    )
    result = engine.assess(None)
    assert result.score == 0
    assert result.level == RiskLevel.LOW
    assert result.decision == RiskDecision.ALLOW
    assert result.signals == []
    assert result.engine_version == "test-1.0.0"


def test_engine_assess_single_critical_rule():
    rule = _SyntheticRule("NO_ACTIVE_MANDATE", Severity.CRITICAL, 80, RiskDomain.SEPA_DIRECT_DEBIT)
    engine = RiskEngine(
        [rule],
        engine_version="sepa-v0.1.0",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
    )
    result = engine.assess(None)
    assert result.score == 80
    assert result.level == RiskLevel.CRITICAL
    assert result.decision == RiskDecision.DISPUTE_READY
    assert len(result.signals) == 1
    assert result.signals[0].code == "NO_ACTIVE_MANDATE"


def test_engine_assess_multiple_rules_combined():
    rules = [
        _SyntheticRule("R1", Severity.HIGH, 50, RiskDomain.SUPPLIER_PAYMENT),
        _SyntheticRule("R2", Severity.MEDIUM, 25, RiskDomain.SUPPLIER_PAYMENT),
    ]
    engine = RiskEngine(rules, engine_version="p2p-v0.1.0", domain=RiskDomain.SUPPLIER_PAYMENT)
    result = engine.assess(None)
    assert result.score == 75
    assert result.decision == RiskDecision.BLOCK_RECOMMENDED


def test_engine_rejects_rules_from_other_domain():
    bad = _SyntheticRule("X", Severity.HIGH, 50, RiskDomain.SUPPLIER_PAYMENT)
    with pytest.raises(ValueError, match="autre domaine"):
        RiskEngine(
            [bad],
            engine_version="test",
            domain=RiskDomain.SEPA_DIRECT_DEBIT,
        )


def test_engine_exposes_version_and_domain():
    engine = RiskEngine(
        [],
        engine_version="sepa-v0.1.0",
        domain=RiskDomain.SEPA_DIRECT_DEBIT,
    )
    assert engine.engine_version == "sepa-v0.1.0"
    assert engine.domain == RiskDomain.SEPA_DIRECT_DEBIT
    assert engine.rules == ()


def test_engine_rule_protocol_runtime_check():
    """`RiskRule` doit être un Protocol runtime-checkable."""
    rule = _SyntheticRule("X", Severity.LOW, 5, RiskDomain.SUPPLIER_PAYMENT)
    assert isinstance(rule, RiskRule)


# ─── Adapter Finding → RiskSignal ────────────────────────────────────────────


def test_finding_to_signal_uses_registry_title():
    finding = Finding(
        invoice_id="INV-1",
        detector="master_data",
        signal="iban_change_without_4eyes",
        severity=Severity.CRITICAL,
        rule_id="MD_IBAN_NO_4EYES",
        evidence={"vendor_id": "V1"},
    )
    # MD_IBAN_NO_4EYES n'est pas dans le registre Risk Core canonique
    # (seul `FOUR_EYES_BREACH` y est). Vérifions que le fallback titre fonctionne.
    sig = finding_to_signal(finding)
    assert sig.code == "MD_IBAN_NO_4EYES"
    assert sig.score == DEFAULT_SCORE_BY_SEVERITY[Severity.CRITICAL]
    assert sig.severity == Severity.CRITICAL
    assert sig.evidence == {"vendor_id": "V1"}


def test_finding_to_signal_with_rule_id_remap():
    finding = Finding(
        invoice_id="INV-1",
        detector="master_data",
        signal="four_eyes_breach",
        severity=Severity.HIGH,
        rule_id="MD_IBAN_NO_4EYES",
    )
    sig = finding_to_signal(finding, rule_id_to_code={"MD_IBAN_NO_4EYES": "FOUR_EYES_BREACH"})
    assert sig.code == "FOUR_EYES_BREACH"
    # Le titre vient du registre canonique
    assert "4-eyes" in sig.title.lower() or "yeux" in sig.title.lower()


def test_finding_to_signal_severity_score_mapping():
    """Toutes les sévérités ont un score calibré."""
    for severity in Severity:
        finding = Finding(
            invoice_id="INV-X",
            detector="d",
            signal="s",
            severity=severity,
            rule_id="ANY",
        )
        sig = finding_to_signal(finding)
        assert sig.score == DEFAULT_SCORE_BY_SEVERITY[severity]


# ─── End-to-end : adapter master_data via RiskEngine ─────────────────────────


def test_e2e_master_data_rule_via_risk_engine():
    """Bout-en-bout : détecteur master_data wrappé en RiskRule, exécuté par
    le RiskEngine, produit un RiskAssessmentResult avec décision attendue.

    Scénario : IBAN modifié sans 4-eyes, paiement de 10k€ dans la fenêtre.
    Le détecteur doit produire un finding CRITICAL → signal score 80 →
    décision DISPUTE_READY (CRITICAL severity + score ≥80).
    """
    # 1 événement IBAN sans approbateur
    events = (
        VendorMasterEvent(
            event_id="ev-1",
            vendor_id="VENDOR-A",
            field=MasterDataField.IBAN,
            old_value="FR7611111111111111111111111",
            new_value="FR7622222222222222222222222",
            changed_at=datetime(2026, 1, 10, tzinfo=UTC),
            changed_by="alice",
            approved_by=None,  # 4-eyes manquant
        ),
    )
    # 1 facture postérieure de 10k€
    invoices = pd.DataFrame(
        [
            {
                "invoice_id": "INV-100",
                "vendor_id": "VENDOR-A",
                "amount": 10_000.0,
                "invoice_date": "2026-01-15",
            }
        ]
    )
    ctx = SupplierPaymentContext(invoices=invoices, master_data_events=events)
    engine = RiskEngine(
        list(build_supplier_payment_rules()),
        engine_version="p2p-md-v0.1.0",
        domain=RiskDomain.SUPPLIER_PAYMENT,
    )
    result = engine.assess(ctx)
    assert result.score >= 80
    assert result.level == RiskLevel.CRITICAL
    assert result.decision == RiskDecision.DISPUTE_READY
    assert any(s.code == "MD_IBAN_NO_4EYES" for s in result.signals)
    assert result.engine_version == "p2p-md-v0.1.0"


def test_e2e_master_data_no_findings_when_4eyes_respected():
    """Si l'IBAN est modifié avec approbateur distinct, aucun finding."""
    events = (
        VendorMasterEvent(
            event_id="ev-1",
            vendor_id="VENDOR-A",
            field=MasterDataField.IBAN,
            old_value="FR7611111111111111111111111",
            new_value="FR7622222222222222222222222",
            changed_at=datetime(2026, 1, 10, tzinfo=UTC),
            changed_by="alice",
            approved_by="bob",  # 4-eyes respecté
        ),
    )
    invoices = pd.DataFrame(
        [
            {
                "invoice_id": "INV-100",
                "vendor_id": "VENDOR-A",
                "amount": 10_000.0,
                "invoice_date": "2026-01-15",
            }
        ]
    )
    ctx = SupplierPaymentContext(invoices=invoices, master_data_events=events)
    rule = IbanChangeWithoutFourEyesRule()
    signals = rule.evaluate(ctx)
    assert signals == []


def test_e2e_no_events_no_signals():
    invoices = pd.DataFrame(columns=["invoice_id", "vendor_id", "amount", "invoice_date"])
    ctx = SupplierPaymentContext(invoices=invoices, master_data_events=())
    engine = RiskEngine(
        list(build_supplier_payment_rules()),
        engine_version="p2p-md-v0.1.0",
        domain=RiskDomain.SUPPLIER_PAYMENT,
    )
    result = engine.assess(ctx)
    assert result.score == 0
    assert result.decision == RiskDecision.ALLOW
