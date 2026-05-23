"""Tests LLM redaction — Sprint 5 MandateGuard.

Couvre :
- redact_iban_patterns : remplace tout IBAN-like
- redact_text : redaction multi-pattern (IBAN + ICS + emails + long digits)
- redact_risk_input : récursif, préserve les champs structurés
- is_safe_for_llm : détecte fuites résiduelles, raise_on_leak option
- IBAN fingerprint HMAC (64 hex sans préfixe pays) n'est PAS confondu avec IBAN
"""

from __future__ import annotations

import pytest

from p2p_fraud.ai import (
    LeakingFieldError,
    RedactionConfig,
    is_safe_for_llm,
    redact_iban_patterns,
    redact_risk_input,
    redact_text,
)

# ─── redact_iban_patterns ────────────────────────────────────────────────────


def test_redact_iban_pattern_replaces_typical_iban():
    out = redact_iban_patterns("Mon IBAN est FR7630001007941234567890185, merci.")
    assert "FR76" not in out
    assert "[IBAN_REDACTED]" in out


def test_redact_iban_handles_iban_with_spaces():
    out = redact_iban_patterns("FR76 3000 1007 9412 3456 7890 185")
    assert "1234" not in out
    assert "[IBAN_REDACTED]" in out


def test_redact_iban_handles_lowercase():
    out = redact_iban_patterns("fr7630001007941234567890185")
    assert "[IBAN_REDACTED]" in out


def test_redact_iban_preserves_text_around():
    out = redact_iban_patterns("Avant FR7630001007941234567890185 après.")
    assert "Avant" in out
    assert "après." in out


def test_redact_iban_does_not_match_hmac_fingerprint():
    """Un fingerprint HMAC fait 64 hex chars sans préfixe pays → pas matché."""
    hmac_fp = "ab" * 32  # 64 hex chars
    out = redact_iban_patterns(f"fingerprint={hmac_fp}")
    assert hmac_fp in out  # préservé


# ─── redact_text ─────────────────────────────────────────────────────────────


def test_redact_text_masks_ics():
    out = redact_text("Créancier ICS : FR18ZZZ002305")
    assert "FR18ZZZ002305" not in out
    assert "FR18" in out  # début préservé pour traçabilité
    assert "305" in out  # fin préservée


def test_redact_text_removes_email():
    out = redact_text("Contact : alice@example.fr")
    assert "alice@example.fr" not in out
    assert "[EMAIL_REDACTED]" in out


def test_redact_text_masks_long_digit_sequences():
    out = redact_text("SIREN 812446901 et téléphone 0612345678")
    # SIREN (9) NOT redacted (LONG_DIGIT_SEQ = 10+)
    assert "812446901" in out
    # Téléphone (10) redacted
    assert "0612345678" not in out
    assert "[NUMBER_REDACTED]" in out


def test_redact_text_handles_none_and_empty():
    assert redact_text(None) == ""
    assert redact_text("") == ""


# ─── redact_risk_input ───────────────────────────────────────────────────────


def test_redact_risk_input_preserves_structured_fields():
    payload = {
        "code": "NO_ACTIVE_MANDATE",
        "score": 80,
        "severity": "critical",
        "decision": "DISPUTE_READY",
        "message": "IBAN suspect : FR7630001007941234567890185",
    }
    out = redact_risk_input(payload)
    # Champs préservés
    assert out["code"] == "NO_ACTIVE_MANDATE"
    assert out["score"] == 80
    assert out["severity"] == "critical"
    # Texte redacté
    assert "FR7630001007941234567890185" not in out["message"]
    assert "[IBAN_REDACTED]" in out["message"]


def test_redact_risk_input_recurses_into_nested_dicts():
    payload = {
        "event": {
            "details": "iban=FR7630001007941234567890185",
        }
    }
    out = redact_risk_input(payload)
    assert "FR7630001007941234567890185" not in out["event"]["details"]


def test_redact_risk_input_recurses_into_lists():
    payload = {
        "signals": [
            {"message": "FR7630001007941234567890185 first"},
            {"message": "FR7630001007941234567890186 second"},
        ]
    }
    out = redact_risk_input(payload)
    for sig in out["signals"]:
        assert "FR76" not in sig["message"]


def test_redact_risk_input_preserves_numeric_amounts():
    payload = {"amount_cents": 8900, "currency": "EUR"}
    out = redact_risk_input(payload)
    assert out["amount_cents"] == 8900


# ─── is_safe_for_llm ─────────────────────────────────────────────────────────


def test_is_safe_returns_true_for_clean_payload():
    payload = {"code": "X", "message": "Tout va bien"}
    assert is_safe_for_llm(payload) is True


def test_is_safe_returns_false_when_iban_leaks():
    payload = {"message": "FR7630001007941234567890185"}
    assert is_safe_for_llm(payload) is False


def test_is_safe_raise_on_leak_raises_with_field_path():
    payload = {"event": {"raw": "FR7630001007941234567890185"}}
    with pytest.raises(LeakingFieldError) as exc:
        is_safe_for_llm(payload, raise_on_leak=True)
    assert "event.raw" in str(exc.value)


def test_is_safe_string_input():
    assert is_safe_for_llm("Hello world")
    assert not is_safe_for_llm("FR7630001007941234567890185")


def test_is_safe_ignores_preserve_fields():
    """Les champs structurés (`code`, `rule_id`) ne sont pas scannés."""
    # ce serait douteux d'avoir un IBAN dans un `code`, mais on documente le
    # comportement : preserve_fields skip le scan
    payload = {"code": "FR7630001007941234567890185"}
    assert is_safe_for_llm(payload)


# ─── End-to-end : pipeline complet ───────────────────────────────────────────


def test_pipeline_redact_then_verify_is_safe():
    """Le payload redacté DOIT passer is_safe_for_llm."""
    payload = {
        "message": "Mandat FR7630001007941234567890185 révoqué",
        "creditor_ics": "FR18ZZZ002305",
        "contact": "alice@example.fr",
        "details": {
            "old_iban": "FR7611111111111111111111111",
            "phone": "0612345678",
        },
    }
    redacted = redact_risk_input(payload)
    assert is_safe_for_llm(redacted) is True


def test_custom_config_disables_email_redaction():
    cfg = RedactionConfig(redact_emails=False)
    out = redact_text("contact alice@example.fr", config=cfg)
    assert "alice@example.fr" in out
