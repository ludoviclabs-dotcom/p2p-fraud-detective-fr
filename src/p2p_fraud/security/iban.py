"""IBAN fingerprint HMAC + normalisation — Sprint 1 MandateGuard.

Sépare la *recherche* (HMAC SHA-256 stable, déterministe pour requêtes/JOIN)
du *stockage chiffré* (Fernet dans `crypto.py`, déchiffrable côté serveur).

Pourquoi un HMAC plutôt qu'un hash simple ?
- L'espace des IBAN est petit et structuré (code pays + clé contrôle + BBAN
  régulé). Un SHA-256 nu serait vulnérable au dictionnaire offline.
- HMAC avec secret rend le précalcul d'arc-en-ciel inutile.
- Le secret est rotatable indépendamment de la clé de chiffrement Fernet.

Garanties :
- `normalize_iban` est idempotente et insensible à la casse / aux espaces.
- `iban_fingerprint` est stable pour un même secret + IBAN normalisé.
- `mask_iban` ne nécessite pas le secret (UI publique safe).
- Aucune fonction ne logge l'IBAN clair ni le fingerprint (le fingerprint
  reste tout de même une donnée corrélable — ne jamais l'exposer publiquement).
"""

from __future__ import annotations

import hmac
import logging
import secrets
from hashlib import sha256

from p2p_fraud.config import get_settings

log = logging.getLogger(__name__)

_ENV_VAR = "IBAN_HMAC_SECRET"


def _load_secret() -> bytes:
    """Lit le secret HMAC depuis Settings, génère éphémère sinon."""
    raw = (get_settings().iban_hmac_secret or "").strip()
    if raw:
        return raw.encode("utf-8")
    log.warning(
        "%s absent — secret HMAC IBAN éphémère généré. Les fingerprints "
        "ne seront pas cohérents entre process/restart. Pour la production, "
        "exportez %s=$(python -c 'import secrets; print(secrets.token_urlsafe(32))').",
        _ENV_VAR,
        _ENV_VAR,
    )
    return secrets.token_bytes(32)


def normalize_iban(iban: str | None) -> str:
    """Forme canonique d'un IBAN pour fingerprint stable.

    - retire tous les espaces (ASCII + Unicode)
    - met en majuscules
    - ne valide pas la clé de contrôle (responsabilité d'un validateur dédié)
    """
    if not iban:
        return ""
    return "".join(iban.split()).upper()


def iban_fingerprint(iban: str | None, *, secret: bytes | None = None) -> str:
    """HMAC-SHA256(secret, normalize_iban(iban)) en hex.

    Retourne "" si l'IBAN est vide. Le secret est lu depuis l'env si non fourni.
    """
    normalized = normalize_iban(iban)
    if not normalized:
        return ""
    key = secret if secret is not None else _load_secret()
    return hmac.new(key, normalized.encode("ascii"), sha256).hexdigest()


def mask_iban(iban: str | None) -> str:
    """Masque l'IBAN pour affichage public : `FR76 **** **** **** 0185`.

    Conserve uniquement le code pays + clé contrôle (4 premiers caractères)
    et les 4 derniers chiffres. Pas de besoin du secret HMAC.
    """
    normalized = normalize_iban(iban)
    if not normalized:
        return ""
    if len(normalized) < 8:
        return "****"
    head = normalized[:4]
    tail = normalized[-4:]
    middle_groups = max(0, (len(normalized) - 8) // 4)
    middle = " ".join(["****"] * middle_groups) if middle_groups else ""
    if middle:
        return f"{head} {middle} {tail}"
    return f"{head} {tail}"


def fingerprints_match(a: str, b: str) -> bool:
    """Comparaison en temps constant de deux fingerprints (anti-timing).

    Utile pour vérifier qu'un IBAN entrant matche un fingerprint stocké
    sans révéler la longueur du préfixe différent.
    """
    if not a or not b:
        return False
    return hmac.compare_digest(a, b)
