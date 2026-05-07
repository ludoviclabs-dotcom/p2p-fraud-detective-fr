"""Tests reason codes FR — Sprint 4."""

from __future__ import annotations

import pytest

from p2p_fraud.schema import Finding, Severity
from p2p_fraud.scoring.reason_codes import (
    get_reason_code,
    list_supported_rules,
    render_reason,
)


def _f(rule_id: str, evidence: dict | None = None, signal: str = "test") -> Finding:
    return Finding(
        invoice_id="INV1",
        detector="master_data",
        signal=signal,
        severity=Severity.CRITICAL,
        rule_id=rule_id,
        evidence=evidence or {},
    )


def test_supported_rules_cover_all_sprint_detectors():
    rules = list_supported_rules()
    expected = {
        "MD_IBAN_NO_4EYES",
        "MD_DORMANT_REACTIVATED",
        "MD_NAME_AND_IBAN_SAME_DAY",
        "SIRENE_404",
        "SIRENE_CEASED",
        "SIRENE_NEW_VENDOR",
        "SANCTIONS_VENDOR_HIT",
        "SANCTIONS_VENDOR_PEP",
        "DUP_EXACT",
        "DUP_FUZZY",
        "THRESHOLD_NEAR_LIMIT",
        "IFOREST_ANOMALY",
        "GRAPH_RING_SHARED_IBAN",
    }
    assert expected.issubset(set(rules))


def test_render_iban_no_4eyes_includes_evidence_fields():
    f = _f(
        "MD_IBAN_NO_4EYES",
        evidence={
            "changed_at": "2025-06-01T10:00:00+00:00",
            "changed_by": "U042",
            "exposure_eur": 12_345.0,
            "exposure_window_days": 90,
        },
    )
    text = render_reason(f)
    assert "U042" in text
    assert "2025-06-01" in text
    assert "12345" in text or "12 345" in text or "12345.0" in text
    assert "?" not in text  # toutes les clés présentes


def test_render_falls_back_for_unknown_rule_without_crash():
    f = _f("UNKNOWN_RULE_XYZ")
    text = render_reason(f)
    assert "master_data" in text
    assert "UNKNOWN_RULE_XYZ" in text


def test_render_uses_safe_placeholder_for_missing_evidence():
    # Volontairement evidence vide → les variables manquantes deviennent "?"
    f = _f("MD_IBAN_NO_4EYES", evidence={})
    text = render_reason(f)
    assert "?" in text


def test_get_reason_code_returns_object():
    rc = get_reason_code("SANCTIONS_VENDOR_HIT")
    assert rc is not None
    assert rc.rule_id == "SANCTIONS_VENDOR_HIT"
    assert "LCB-FT" in rc.citation


def test_get_reason_code_unknown_returns_none():
    assert get_reason_code("DOES_NOT_EXIST") is None


def test_render_sanctions_includes_score_and_list_source():
    f = Finding(
        invoice_id="INV1",
        detector="sanctions",
        signal="vendor_sanctioned",
        severity=Severity.CRITICAL,
        rule_id="SANCTIONS_VENDOR_HIT",
        evidence={
            "vendor_name": "Acme Test Corp",
            "matched_name": "Acme Test Corp",
            "list_source": "EU_CONSOLIDATED",
            "score": 95,
            "country": "FR",
            "reason": "Sanctions sectorielles",
        },
    )
    text = render_reason(f)
    assert "Acme Test Corp" in text
    assert "EU_CONSOLIDATED" in text
    assert "95" in text


@pytest.mark.parametrize(
    "rule_id",
    [
        "MD_IBAN_NO_4EYES",
        "MD_DORMANT_REACTIVATED",
        "MD_NAME_AND_IBAN_SAME_DAY",
        "SIRENE_404",
        "SIRENE_CEASED",
        "SIRENE_NEW_VENDOR",
        "SANCTIONS_VENDOR_HIT",
        "SANCTIONS_VENDOR_PEP",
        "DUP_EXACT",
        "DUP_FUZZY",
        "THRESHOLD_NEAR_LIMIT",
        "IFOREST_ANOMALY",
        "GRAPH_RING_SHARED_IBAN",
    ],
)
def test_all_rules_render_without_exception(rule_id: str):
    f = _f(rule_id, evidence={})
    text = render_reason(f)
    assert isinstance(text, str)
    assert len(text) > 0
