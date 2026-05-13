"""Signatures cryptographiques Ed25519 sur l'audit trail (P5-5).

Pour les pilotes ETI réglementés (AMF, ACPR, banque, assurance, secteur
public), la non-répudiation cryptographique va au-delà du hash chain
SHA-256 existant (`cases/audit_log.py`). Ed25519 fournit :
- non-répudiation (preuve de l'auteur),
- intégrité (preuve d'absence d'altération),
- vérifiabilité externe (la clé publique peut être communiquée à un
  tiers — CAC, ACPR, Cour des comptes — sans risque opérationnel).

Pourquoi Ed25519 plutôt que RSA / ECDSA :
- Signatures déterministes (pas de fuite via nonces aléatoires faibles).
- Performances : ~1 µs / signature, ~3 µs / vérification sur CPU récent.
- Taille fixe 64 octets — coût stockage négligeable.
- RFC 8032 standard, support natif `python-cryptography` ou `PyNaCl`.

Architecture :
- Clé privée chargée depuis `Settings.p2pfd_ed25519_private_key` (base64).
  Génération hors ligne par l'admin avec `Ed25519Signer.generate()`,
  stockage dans un coffre-fort (Vault, KMS, fichier 0600 root-only).
- Clé publique exposée par l'endpoint `GET /security/public-key` pour
  permettre à n'importe quel tiers de vérifier indépendamment.
- Signatures stockées dans la colonne `signature` de l'audit log
  (backward-compatible : entrées historiques sans signature restent valides
  — `verify_chain()` ne valide que le hash chain dans ce cas).
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


class SignatureError(RuntimeError):
    """La signature est invalide ou la clé est malformée."""


def _import_ed25519():
    """Import paresseux de PyNaCl (dépendance optionnelle P5-5)."""
    try:
        from nacl.signing import SigningKey, VerifyKey

        return SigningKey, VerifyKey
    except ImportError as exc:
        raise SignatureError("PyNaCl manquant. Installer : pip install pynacl>=1.5") from exc


@dataclass
class Ed25519Keypair:
    """Paire de clés (publique + privée), encodées base64 pour transport texte."""

    private_key_b64: str
    public_key_b64: str


class Ed25519Signer:
    """Signe et vérifie des messages avec Ed25519.

    Args:
        private_key_b64: clé privée encodée base64 (32 octets bruts).
            Si vide, le signer est désactivé (no-op signatures).
    """

    def __init__(self, private_key_b64: str = "") -> None:
        self._private_key_b64 = private_key_b64.strip()
        self._signing_key = None
        self._verify_key = None
        if self._private_key_b64:
            SigningKey, _VerifyKey = _import_ed25519()
            try:
                raw = base64.b64decode(self._private_key_b64)
                if len(raw) != 32:
                    raise SignatureError(
                        f"Clé privée Ed25519 doit faire 32 octets, reçu {len(raw)}."
                    )
                self._signing_key = SigningKey(raw)
                self._verify_key = self._signing_key.verify_key
            except (ValueError, TypeError) as exc:
                raise SignatureError(f"Clé privée Ed25519 invalide : {exc}") from exc

    @property
    def enabled(self) -> bool:
        return self._signing_key is not None

    @property
    def public_key_b64(self) -> str:
        """Clé publique base64 — à publier via `GET /security/public-key`."""
        if not self.enabled:
            return ""
        return base64.b64encode(bytes(self._verify_key)).decode("ascii")

    def sign(self, message: str | bytes) -> str:
        """Signe `message` et renvoie la signature en hex (64 octets → 128 chars)."""
        if not self.enabled:
            return ""
        if isinstance(message, str):
            message = message.encode("utf-8")
        signed = self._signing_key.sign(message)
        return signed.signature.hex()

    @classmethod
    def generate(cls) -> Ed25519Keypair:
        """Génère une nouvelle paire de clés (admin offline uniquement).

        Returns:
            Keypair avec clé privée + publique en base64. À sauvegarder en
            coffre-fort. La clé publique peut être publiée librement.
        """
        SigningKey, _ = _import_ed25519()
        sk = SigningKey.generate()
        return Ed25519Keypair(
            private_key_b64=base64.b64encode(bytes(sk)).decode("ascii"),
            public_key_b64=base64.b64encode(bytes(sk.verify_key)).decode("ascii"),
        )


def verify_signature(
    *,
    message: str | bytes,
    signature_hex: str,
    public_key_b64: str,
) -> bool:
    """Vérifie une signature Ed25519 contre une clé publique.

    Utilisée à la fois en interne (`AuditLog.verify_chain()`) et par les
    tiers externes (auditeurs CAC, ACPR) via l'API + la clé publique.

    Args:
        message: payload signé (bytes ou str UTF-8).
        signature_hex: signature 64 octets en hex (128 caractères).
        public_key_b64: clé publique 32 octets en base64.

    Returns:
        `True` si la signature est valide, `False` sinon (jamais d'exception
        propagée — usage défensif côté UI / API).
    """
    if not signature_hex or not public_key_b64:
        return False
    if isinstance(message, str):
        message = message.encode("utf-8")
    try:
        _, VerifyKey = _import_ed25519()
        vk = VerifyKey(base64.b64decode(public_key_b64))
        vk.verify(message, bytes.fromhex(signature_hex))
        return True
    except Exception as exc:
        log.debug("Ed25519 verify failed: %s", exc)
        return False


def make_signer_from_settings(settings=None) -> Ed25519Signer:
    """Construit un `Ed25519Signer` depuis `Settings.p2pfd_ed25519_private_key`.

    Si la clé est vide (mode démo public), renvoie un signer désactivé
    qui produit `signature=""` (no-op transparent côté audit log).
    """
    from p2p_fraud.config import get_settings

    s = settings or get_settings()
    return Ed25519Signer(private_key_b64=s.p2pfd_ed25519_private_key)


__all__ = [
    "Ed25519Keypair",
    "Ed25519Signer",
    "SignatureError",
    "make_signer_from_settings",
    "verify_signature",
]
