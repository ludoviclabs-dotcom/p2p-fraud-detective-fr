"""Tests du moteur de risk score consolidé."""

from __future__ import annotations

from p2p_fraud.schema import Finding, Severity
from p2p_fraud.scoring.risk_engine import aggregate_findings, severity_band, to_dataframe


def _f(invoice_id: str, detector: str, severity: Severity) -> Finding:
    return Finding(
        invoice_id=invoice_id,
        detector=detector,
        signal="test",
        severity=severity,
        rule_id=f"{detector.upper()}_TEST",
    )


def test_no_findings_returns_empty():
    assert aggregate_findings([]) == {}


def test_single_critical_finding():
    findings = [_f("INV1", "duplicates", Severity.CRITICAL)]  # weight 1.0 × 1.0 × 60 = 60
    scores = aggregate_findings(findings)
    assert "INV1" in scores
    assert scores["INV1"].score == 60.0
    assert scores["INV1"].findings_count == 1


def test_score_capped_at_100():
    findings = [
        _f("INV1", "duplicates", Severity.CRITICAL),
        _f("INV1", "sirene", Severity.CRITICAL),  # weight 1.2 × 1.0 × 60 = 72
        _f("INV1", "graph", Severity.CRITICAL),  # weight 1.5 × 1.0 × 60 = 90
    ]
    scores = aggregate_findings(findings)
    assert scores["INV1"].score == 100.0


def test_severity_low_contributes_less():
    findings = [_f("INV1", "duplicates", Severity.LOW)]  # 1.0 × 0.1 × 60 = 6
    scores = aggregate_findings(findings)
    assert scores["INV1"].score == 6.0


def test_breakdown_per_detector():
    findings = [
        _f("INV1", "duplicates", Severity.HIGH),
        _f("INV1", "sirene", Severity.MEDIUM),
    ]
    scores = aggregate_findings(findings)
    bd = scores["INV1"].breakdown
    assert "duplicates" in bd
    assert "sirene" in bd
    assert bd["duplicates"] > 0


def test_to_dataframe_sorted():
    findings = [
        _f("LOW", "duplicates", Severity.LOW),
        _f("HIGH", "duplicates", Severity.CRITICAL),
        _f("MED", "duplicates", Severity.MEDIUM),
    ]
    df = to_dataframe(aggregate_findings(findings))
    assert df.iloc[0]["invoice_id"] == "HIGH"
    assert df.iloc[-1]["invoice_id"] == "LOW"


def test_severity_band():
    assert severity_band(0) == "AUCUN"
    assert severity_band(10) == "FAIBLE"
    assert severity_band(30) == "MOYEN"
    assert severity_band(60) == "ÉLEVÉ"
    assert severity_band(85) == "CRITIQUE"


def test_custom_detector_weights():
    findings = [_f("INV1", "duplicates", Severity.CRITICAL)]
    scores_default = aggregate_findings(findings)
    scores_doubled = aggregate_findings(findings, detector_weights={"duplicates": 2.0})
    # 60 → 100 (capé)
    assert scores_doubled["INV1"].score >= scores_default["INV1"].score
