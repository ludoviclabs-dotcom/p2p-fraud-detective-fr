"""Chiffrement des données sensibles (IBAN, BIC, contacts) au repos.

Conception :
- Fernet (cryptography) — AES-128-CBC + HMAC-SHA256, AEAD-equivalent.
- La clé maîtresse est lue depuis la variable d'env P2P_FRAUD_DATA_KEY.
  En l'absence, le service génère une clé éphémère (utile pour démo +
  tests) avec un warning explicite — incompatible avec un déploiement
  en production multi-process.
- Préfixe `enc:v1:` pour distinguer un IBAN chiffré d'un IBAN clair lors
  d'une migration progressive.
- `iban_masked()` ne nécessite jamais la clé — il opère sur le texte clair
  pour produire un BIC + 4 derniers chiffres affichables sans risque.
"""

from __future__ import annotations

import logging
import os
import re

from cryptography.fernet import Fernet, InvalidToken

log = logging.getLogger(__name__)

ENV_VAR = "P2P_FRAUD_DATA_KEY"
PREFIX = "enc:v1:"


def _generate_ephemeral_key() -> bytes:
    log.warning(
        "P2P_FRAUD_DATA_KEY absent — génération d'une clé éphémère. "
        "Incompatible avec un déploiement multi-process. Pour la production, "
        "exportez P2P_FRAUD_DATA_KEY=$(python -c 'from cryptography.fernet "
        "import Fernet; print(Fernet.generate_key().decode())')."
    )
    return Fernet.generate_key()


def _read_key() -> bytes:
    raw = os.environ.get(ENV_VAR, "").strip()
    if not raw:
        return _generate_ephemeral_key()
    return raw.encode("ascii") if isinstance(raw, str) else raw


class CryptoService:
    """Wrapper Fernet avec préfixe versionné et opérations idempotentes."""

    def __init__(self, key: bytes | None = None) -> None:
        self._key = key or _read_key()
        self._fernet = Fernet(self._key)

    @property
    def key(self) -> bytes:
        return self._key

    def encrypt(self, plaintext: str) -> str:
        if plaintext is None or plaintext == "":
            return ""
        if plaintext.startswith(PREFIX):
            return plaintext  # déjà chiffré, idempotent
        token = self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")
        return PREFIX + token

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        if not ciphertext.startswith(PREFIX):
            return ciphertext  # texte clair (migration progressive)
        token = ciphertext[len(PREFIX) :]
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except InvalidToken as e:
            raise ValueError("Token chiffré invalide ou clé incorrecte.") from e


# --- Helpers haut niveau ---


def encrypt_iban(iban: str | None, *, service: CryptoService | None = None) -> str:
    if iban is None:
        return ""
    svc = service or CryptoService()
    return svc.encrypt(iban)


def decrypt_iban(token: str | None, *, service: CryptoService | None = None) -> str:
    if not token:
        return ""
    svc = service or CryptoService()
    return svc.decrypt(token)


_IBAN_RE = re.compile(r"\s+")


def iban_masked(iban: str | None) -> str:
    """Retourne `FR76 **** **** **** **** **12 34` sur l'IBAN clair.

    Si l'IBAN est chiffré (préfixe `enc:v1:`), retourne `[chiffré]`. Cette
    fonction ne déchiffre jamais — elle est utilisable depuis n'importe quelle
    page sans privilèges.
    """
    if not iban:
        return ""
    if iban.startswith(PREFIX):
        return "[chiffré]"
    cleaned = _IBAN_RE.sub("", iban)
    if len(cleaned) < 8:
        return "***"
    bic_country = cleaned[:4]  # FR76 / DE89 / ...
    last4 = cleaned[-4:]
    middle_groups = max(0, (len(cleaned) - 8) // 4)
    masked_middle = " ".join(["****"] * middle_groups) if middle_groups else ""
    return f"{bic_country} {masked_middle} {last4}".strip().replace("  ", " ")
