"""Validation cryptographique des `id_token` OIDC.

Récupère et cache les clés publiques JWKS de l'issuer (TTL 1h par défaut),
puis valide la signature RS256 + les claims standards (`iss`, `aud`, `exp`,
`nonce`).

Utilise `python-jose[cryptography]` pour la vérification — bibliothèque
maintenue qui supporte Microsoft Entra ID, Auth0, Keycloak, Google.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests
from jose import jwt
from jose.exceptions import JWTError

log = logging.getLogger(__name__)


class IdTokenValidationError(RuntimeError):
    """Le token reçu est invalide ou expiré."""


@dataclass
class JWKSCache:
    """Cache TTL des clés publiques JWKS de l'issuer.

    Args:
        jwks_uri: URL retournée par le discovery doc (`jwks_uri`).
        ttl_seconds: durée de vie du cache (1h par défaut, comme recommandé
            par les implémentations Microsoft Entra ID et Auth0).
        timeout_seconds: timeout HTTP pour la fetch JWKS.
    """

    jwks_uri: str
    ttl_seconds: int = 3600
    timeout_seconds: float = 5.0
    _keys: list[dict[str, Any]] = field(default_factory=list)
    _fetched_at: float = 0.0

    def _is_stale(self) -> bool:
        return not self._keys or (time.monotonic() - self._fetched_at) > self.ttl_seconds

    def fetch(self, *, force: bool = False) -> list[dict[str, Any]]:
        """Renvoie les clés JWKS, refresh si nécessaire."""
        if not force and not self._is_stale():
            return self._keys
        log.debug("Fetching JWKS from %s", self.jwks_uri)
        resp = requests.get(self.jwks_uri, timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        keys = data.get("keys") or []
        if not keys:
            raise IdTokenValidationError(f"JWKS endpoint {self.jwks_uri} retourne 0 clé.")
        self._keys = keys
        self._fetched_at = time.monotonic()
        return self._keys

    def find_key(self, kid: str) -> dict[str, Any] | None:
        """Cherche une clé par `kid`, refresh une fois si manquante."""
        for k in self.fetch():
            if k.get("kid") == kid:
                return k
        # Rotation possible — refetch et retry
        for k in self.fetch(force=True):
            if k.get("kid") == kid:
                return k
        return None


def validate_id_token(
    id_token: str,
    *,
    issuer: str,
    audience: str,
    nonce: str | None,
    jwks_cache: JWKSCache,
    leeway_seconds: int = 30,
) -> dict[str, Any]:
    """Valide la signature et les claims d'un `id_token` OIDC.

    Vérifie : signature RS256 (clé publique JWKS), `iss`, `aud`, `exp`, `iat`
    (avec `leeway_seconds` de tolérance), et `nonce` si fourni.

    Args:
        id_token: JWT compact à valider.
        issuer: issuer attendu (ex. `https://login.microsoftonline.com/{tenant}/v2.0`).
        audience: client_id attendu.
        nonce: nonce généré au login PKCE — comparé au claim `nonce`.
        jwks_cache: instance partagée pour éviter de refaire la requête JWKS.
        leeway_seconds: tolérance horloge (NTP drift).

    Raises:
        IdTokenValidationError: si signature invalide, claim manquant, ou expiration.

    Returns:
        Le dict des claims validés.
    """
    try:
        unverified_header = jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise IdTokenValidationError(f"Header JWT illisible : {exc}") from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise IdTokenValidationError("Header JWT sans `kid` — impossible à valider.")

    key = jwks_cache.find_key(kid)
    if key is None:
        raise IdTokenValidationError(
            f"Clé `kid={kid}` introuvable dans JWKS — possible rotation ou clé inconnue."
        )

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=[unverified_header.get("alg", "RS256")],
            audience=audience,
            issuer=issuer,
            options={"leeway": leeway_seconds, "require_aud": True, "require_iss": True},
        )
    except JWTError as exc:
        raise IdTokenValidationError(f"Validation JWT échouée : {exc}") from exc

    if nonce is not None:
        token_nonce = claims.get("nonce")
        if token_nonce != nonce:
            raise IdTokenValidationError(
                "Nonce du token ne correspond pas — possible attaque par rejeu."
            )

    return claims
