"""Tests crypto IBAN — Sprint 7."""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet

from p2p_fraud.security.crypto import (
    PREFIX,
    CryptoService,
    decrypt_iban,
    encrypt_iban,
    iban_masked,
)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Force une clé déterministe par test."""
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", key)
    yield
    os.environ.pop("P2P_FRAUD_DATA_KEY", None)


def test_encrypt_decrypt_round_trip():
    svc = CryptoService()
    iban = "FR7630001007941234567890185"
    enc = svc.encrypt(iban)
    assert enc.startswith(PREFIX)
    assert iban not in enc
    dec = svc.decrypt(enc)
    assert dec == iban


def test_encrypt_is_idempotent_on_already_encrypted():
    svc = CryptoService()
    once = svc.encrypt("FR7630001007941234567890185")
    twice = svc.encrypt(once)
    assert once == twice


def test_decrypt_passes_through_plaintext():
    """Texte clair (migration progressive) → renvoie tel quel."""
    svc = CryptoService()
    assert svc.decrypt("FR7612345") == "FR7612345"


def test_encrypt_empty_returns_empty():
    svc = CryptoService()
    assert svc.encrypt("") == ""


def test_helpers_use_default_service():
    iban = "FR7630001007941234567890185"
    enc = encrypt_iban(iban)
    assert enc.startswith(PREFIX)
    assert decrypt_iban(enc) == iban


def test_helpers_handle_none():
    assert encrypt_iban(None) == ""
    assert decrypt_iban(None) == ""


def test_iban_masked_redacts_middle():
    masked = iban_masked("FR76 3000 1007 9412 3456 7890 185")
    assert masked.startswith("FR76")
    assert masked.endswith("0185")
    assert "1234" not in masked


def test_iban_masked_returns_chiffre_label_for_encrypted():
    enc = encrypt_iban("FR7630001007941234567890185")
    assert iban_masked(enc) == "[chiffré]"


def test_invalid_key_raises_on_decrypt(monkeypatch):
    svc = CryptoService()
    enc = svc.encrypt("FR7612345")
    monkeypatch.setenv("P2P_FRAUD_DATA_KEY", Fernet.generate_key().decode())
    other = CryptoService()
    with pytest.raises(ValueError, match="invalide"):
        other.decrypt(enc)
