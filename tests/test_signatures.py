"""Tests P5-5 — signatures Ed25519 sur l'audit log.

Couvre :
- Génération de paire de clés.
- Round-trip sign → verify_signature OK.
- Altération du payload → verify détecte l'altération.
- AuditLog avec signer : signe chaque entrée.
- AuditLog.verify_chain(public_key) valide les signatures.
- Backward compat : entrées sans signature passent verify_chain.
- Signer désactivé (clé vide) → signatures vides, audit OK.
"""

from __future__ import annotations

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.security.signing import (
    Ed25519Signer,
    SignatureError,
    verify_signature,
)

# ───────────────────────── Génération + sign/verify ──────────────────────────


def test_generate_keypair_returns_valid_base64() -> None:
    kp = Ed25519Signer.generate()
    assert kp.private_key_b64
    assert kp.public_key_b64
    import base64

    assert len(base64.b64decode(kp.private_key_b64)) == 32
    assert len(base64.b64decode(kp.public_key_b64)) == 32


def test_sign_and_verify_round_trip() -> None:
    kp = Ed25519Signer.generate()
    signer = Ed25519Signer(private_key_b64=kp.private_key_b64)
    message = "audit_log_hash_abcdef0123"
    sig = signer.sign(message)
    assert len(sig) == 128  # 64 bytes hex
    assert verify_signature(
        message=message,
        signature_hex=sig,
        public_key_b64=signer.public_key_b64,
    )


def test_verify_detects_tampered_message() -> None:
    kp = Ed25519Signer.generate()
    signer = Ed25519Signer(private_key_b64=kp.private_key_b64)
    sig = signer.sign("original_message")
    assert not verify_signature(
        message="tampered_message",
        signature_hex=sig,
        public_key_b64=signer.public_key_b64,
    )


def test_verify_detects_wrong_public_key() -> None:
    kp1 = Ed25519Signer.generate()
    kp2 = Ed25519Signer.generate()
    signer = Ed25519Signer(private_key_b64=kp1.private_key_b64)
    sig = signer.sign("msg")
    # Vérification avec une clé publique d'une autre paire
    assert not verify_signature(
        message="msg",
        signature_hex=sig,
        public_key_b64=kp2.public_key_b64,
    )


def test_verify_handles_empty_inputs_gracefully() -> None:
    assert not verify_signature(message="x", signature_hex="", public_key_b64="abc")
    assert not verify_signature(message="x", signature_hex="ab", public_key_b64="")


def test_signer_disabled_when_no_key() -> None:
    signer = Ed25519Signer(private_key_b64="")
    assert signer.enabled is False
    assert signer.sign("x") == ""
    assert signer.public_key_b64 == ""


def test_signer_rejects_malformed_key() -> None:
    with pytest.raises(SignatureError):
        Ed25519Signer(private_key_b64="not-base64!")
    with pytest.raises(SignatureError):
        # Trop court (base64 de 4 octets)
        Ed25519Signer(private_key_b64="aGVsbG8=")


# ───────────────────────── Intégration AuditLog ──────────────────────────────


def test_audit_log_signs_entries_when_signer_enabled() -> None:
    kp = Ed25519Signer.generate()
    signer = Ed25519Signer(private_key_b64=kp.private_key_b64)
    log = AuditLog(":memory:", signer=signer)
    log.append(actor="alice", kind="test.event", payload={"x": 1})
    entries = log.all()
    assert len(entries) == 1
    assert entries[0].signature  # non-vide
    # Vérification individuelle
    assert verify_signature(
        message=entries[0].hash,
        signature_hex=entries[0].signature,
        public_key_b64=signer.public_key_b64,
    )


def test_audit_log_without_signer_writes_empty_signatures() -> None:
    """Mode démo (pas de clé) — l'audit log fonctionne sans signature."""
    log = AuditLog(":memory:")
    log.append(actor="alice", kind="test.event", payload={"x": 1})
    entries = log.all()
    assert entries[0].signature == ""


def test_verify_chain_validates_signatures_when_public_key_provided() -> None:
    kp = Ed25519Signer.generate()
    signer = Ed25519Signer(private_key_b64=kp.private_key_b64)
    log = AuditLog(":memory:", signer=signer)
    for i in range(5):
        log.append(actor=f"user-{i}", kind="test.event", payload={"i": i})

    ok, invalid = log.verify_chain(public_key_b64=signer.public_key_b64)
    assert ok is True
    assert invalid == []


def test_verify_chain_without_public_key_still_validates_hash_chain() -> None:
    """Backward compat : verify_chain() sans clé publique ignore les signatures."""
    log = AuditLog(":memory:")  # Pas de signer → entrées sans signature
    log.append(actor="alice", kind="x", payload={})
    log.append(actor="bob", kind="y", payload={})
    ok, invalid = log.verify_chain()
    assert ok is True
    assert invalid == []


def test_verify_chain_handles_mixed_signed_and_unsigned_entries() -> None:
    """v0.4 → v0.5 migration : entrées historiques sans sig + nouvelles signées."""
    # Démarre sans signer (équivalent v0.4)
    log = AuditLog(":memory:")
    log.append(actor="legacy-user", kind="v0.4.entry", payload={})

    # Active le signer en cours de route (équivalent upgrade v0.5)
    kp = Ed25519Signer.generate()
    log._signer = Ed25519Signer(private_key_b64=kp.private_key_b64)
    log.append(actor="new-user", kind="v0.5.entry", payload={"after_upgrade": True})

    # Vérification : entrée legacy doit être OK (pas de sig à vérifier)
    ok, invalid = log.verify_chain(public_key_b64=log._signer.public_key_b64)
    assert ok is True, f"invalid entries: {invalid}"
