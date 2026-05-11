"""Client OIDC : discovery + échange code → tokens.

Complète `oidc.py` (PKCE + URL d'authorization) avec :
- **Discovery** du document `.well-known/openid-configuration` (cached 1h)
- **Token exchange** via le `token_endpoint` de l'IdP

Pas de dépendance `authlib` : la spec OIDC est suffisamment simple pour un
client direct via `requests`. Les édges cases (refresh_token, device flow,
client credentials) sont hors périmètre P4-3.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests

log = logging.getLogger(__name__)


class OIDCDiscoveryError(RuntimeError):
    """Le document de discovery est introuvable ou invalide."""


class OIDCTokenError(RuntimeError):
    """L'échange code → tokens a échoué côté IdP."""


@dataclass
class OIDCDiscoveryDocument:
    """Sous-ensemble du document discovery utilisé par le client."""

    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    issuer: str
    end_session_endpoint: str = ""

    @classmethod
    def from_dict(cls, doc: dict[str, Any]) -> OIDCDiscoveryDocument:
        required = ("authorization_endpoint", "token_endpoint", "jwks_uri", "issuer")
        missing = [k for k in required if not doc.get(k)]
        if missing:
            raise OIDCDiscoveryError(f"Discovery doc invalide — clés manquantes : {missing}")
        return cls(
            authorization_endpoint=doc["authorization_endpoint"],
            token_endpoint=doc["token_endpoint"],
            jwks_uri=doc["jwks_uri"],
            issuer=doc["issuer"],
            end_session_endpoint=doc.get("end_session_endpoint", ""),
        )


@dataclass
class DiscoveryCache:
    """Cache TTL du document discovery par issuer."""

    ttl_seconds: int = 3600
    _docs: dict[str, OIDCDiscoveryDocument] = field(default_factory=dict)
    _fetched_at: dict[str, float] = field(default_factory=dict)

    def get(self, issuer: str, *, timeout: float = 5.0) -> OIDCDiscoveryDocument:
        now = time.monotonic()
        last = self._fetched_at.get(issuer, 0.0)
        if issuer in self._docs and (now - last) < self.ttl_seconds:
            return self._docs[issuer]
        url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
        log.debug("Fetching OIDC discovery from %s", url)
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise OIDCDiscoveryError(f"Discovery échouée pour {issuer} : {exc}") from exc
        doc = OIDCDiscoveryDocument.from_dict(resp.json())
        self._docs[issuer] = doc
        self._fetched_at[issuer] = now
        return doc


def exchange_code_for_tokens(
    *,
    token_endpoint: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
    code_verifier: str,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """POST `token_endpoint` avec grant_type=authorization_code + PKCE.

    Returns:
        Le dict des tokens (`id_token`, `access_token`, `expires_in`, ...).

    Raises:
        OIDCTokenError: si l'IdP renvoie une erreur ou un code non-200.
    """
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    if client_secret:
        payload["client_secret"] = client_secret

    try:
        resp = requests.post(
            token_endpoint,
            data=payload,
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OIDCTokenError(f"Token endpoint injoignable : {exc}") from exc

    if resp.status_code != 200:
        raise OIDCTokenError(f"Token endpoint a renvoyé {resp.status_code} : {resp.text[:300]}")

    data = resp.json()
    if "id_token" not in data:
        raise OIDCTokenError(f"Réponse sans `id_token` : {sorted(data.keys())}")
    return data
