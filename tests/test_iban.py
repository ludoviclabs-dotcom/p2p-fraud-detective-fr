"""Tests du module IBAN — Sprint 1 MandateGuard.

Couvre : normalisation, fingerprint HMAC, masquage, comparaison.
Inclut tests anti-leak : un fingerprint ne doit jamais contenir l'IBAN clair.
"""

from __future__ import annotations

import re

import pytest

from p2p_fraud.security import iban as iban_mod
from p2p_fraud.security.iban import (
    fingerprints_match,
    iban_fingerprint,
    mask_iban,
    normalize_iban,
)


@pytest.fixture(autouse=True)
def _stable_secret(monkeypatch):
    """Force un secret HMAC déterministe pour rendre les tests reproductibles."""
    monkeypatch.setenv("IBAN_HMAC_SECRET", "test-secret-do-not-use-in-prod-32bytes!")


# ─── normalize_iban ──────────────────────────────────────────────────────────


def test_normalize_removes_spaces_and_uppercases():
    assert normalize_iban("fr76 3000 1007 9412 3456 7890 185") == "FR7630001007941234567890185"


def test_normalize_is_idempotent():
    once = normalize_iban("FR7630001007941234567890185")
    twice = normalize_iban(once)
    assert once == twice


def test_normalize_handles_none_and_empty():
    assert normalize_iban(None) == ""
    assert normalize_iban("") == ""
    assert normalize_iban("   ") == ""


def test_normalize_strips_unicode_spaces():
    # espace insécable U+00A0, tabulation
    assert normalize_iban("FR76 3000\t1007") == "FR7630001007"


# ─── iban_fingerprint ────────────────────────────────────────────────────────


def test_fingerprint_is_64_hex_chars():
    fp = iban_fingerprint("FR7630001007941234567890185")
    assert len(fp) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", fp)


def test_fingerprint_stable_for_same_input():
    a = iban_fingerprint("FR7630001007941234567890185")
    b = iban_fingerprint("FR7630001007941234567890185")
    assert a == b


def test_fingerprint_insensitive_to_formatting():
    """Espaces et casse ne doivent pas changer le fingerprint."""
    a = iban_fingerprint("FR76 3000 1007 9412 3456 7890 185")
    b = iban_fingerprint("fr7630001007941234567890185")
    c = iban_fingerprint("FR7630001007941234567890185")
    assert a == b == c


def test_fingerprint_different_for_different_ibans():
    a = iban_fingerprint("FR7630001007941234567890185")
    b = iban_fingerprint("FR7630001007941234567890186")  # dernier digit diff
    assert a != b


def test_fingerprint_changes_with_secret(monkeypatch):
    a = iban_fingerprint("FR7630001007941234567890185")
    monkeypatch.setenv("IBAN_HMAC_SECRET", "different-secret-totally-distinct!")
    # Force la relecture du secret
    iban_mod._load_secret.cache_clear() if hasattr(iban_mod._load_secret, "cache_clear") else None
    b = iban_fingerprint("FR7630001007941234567890185")
    assert a != b


def test_fingerprint_empty_for_empty_input():
    assert iban_fingerprint("") == ""
    assert iban_fingerprint(None) == ""


def test_fingerprint_explicit_secret_overrides_env(monkeypatch):
    fp = iban_fingerprint("FR7630001007941234567890185", secret=b"custom-secret")
    fp2 = iban_fingerprint("FR7630001007941234567890185", secret=b"custom-secret")
    assert fp == fp2
    # Différent de celui calculé avec le secret env
    env_fp = iban_fingerprint("FR7630001007941234567890185")
    assert fp != env_fp


# ─── Anti-leak ───────────────────────────────────────────────────────────────


def test_fingerprint_does_not_contain_iban():
    """Le fingerprint hex ne doit jamais contenir l'IBAN clair (sanity check)."""
    iban = "FR7630001007941234567890185"
    fp = iban_fingerprint(iban)
    # Sous-chaînes IBAN qui ne devraient pas apparaître
    for chunk in [iban, iban[:8], iban[-8:], "FR7630", "7890185"]:
        assert chunk.lower() not in fp.lower(), f"fingerprint leaks chunk {chunk!r}"


# ─── mask_iban ───────────────────────────────────────────────────────────────


def test_mask_preserves_country_and_last4():
    masked = mask_iban("FR7630001007941234567890185")
    assert masked.startswith("FR76")
    assert masked.endswith("0185")


def test_mask_redacts_middle_digits():
    masked = mask_iban("FR7630001007941234567890185")
    # Aucun digit du milieu ne doit apparaître
    for chunk in ["3000", "1007", "9412", "3456", "7890", "30001007", "1234567"]:
        assert chunk not in masked, f"mask leaks chunk {chunk!r}: {masked!r}"


def test_mask_handles_empty():
    assert mask_iban(None) == ""
    assert mask_iban("") == ""


def test_mask_short_iban():
    assert mask_iban("FR76") == "****"
    assert mask_iban("FR7612") == "****"


def test_mask_works_on_formatted_input():
    """Doit normaliser avant masquage."""
    masked = mask_iban("FR76 3000 1007 9412 3456 7890 185")
    assert masked.startswith("FR76")
    assert masked.endswith("0185")


# ─── fingerprints_match ──────────────────────────────────────────────────────


def test_match_true_for_identical():
    fp = iban_fingerprint("FR7630001007941234567890185")
    assert fingerprints_match(fp, fp)


def test_match_false_for_different():
    a = iban_fingerprint("FR7630001007941234567890185")
    b = iban_fingerprint("FR7630001007941234567890186")
    assert not fingerprints_match(a, b)


def test_match_false_for_empty():
    assert not fingerprints_match("", "abc")
    assert not fingerprints_match("abc", "")
    assert not fingerprints_match("", "")
