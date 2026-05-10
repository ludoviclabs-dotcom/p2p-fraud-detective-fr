"""OIDC / OAuth2 — authentification fédérée pour déploiements collaboratifs.

Compatible :
- **Microsoft Entra ID** (Azure AD) — tenant unique ou multi-tenant
- **Auth0**
- **Keycloak**
- **Google Workspace**

Le flow `authorization_code` PKCE est privilégié pour les apps web.

Configuration via variables d'environnement :
- `OIDC_ISSUER` : URL de l'issuer (e.g. `https://login.microsoftonline.com/{tenant_id}/v2.0`)
- `OIDC_CLIENT_ID` : identifiant de l'application
- `OIDC_CLIENT_SECRET` : secret applicatif (laisser vide pour PKCE pur)
- `OIDC_REDIRECT_URI` : URL de callback (e.g. `https://yourapp.com/oidc/callback`)
- `OIDC_SCOPES` : scopes demandés, par défaut `openid email profile`

Pour Microsoft Entra ID, le mapping des claims standards :
- `preferred_username` → username applicatif
- `email` → email
- `groups` → rôles RBAC (à mapper vers viewer/analyst/manager/admin via `OIDC_ROLE_MAP`)

Note : ce module fournit la **construction des URLs** et la **vérification basique
des claims**. Pour un usage production, intégrer une librairie validée
(`authlib`, `python-jose`) — ce module documente l'intégration sans
dépendance lourde.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

log = logging.getLogger(__name__)

DEFAULT_SCOPES = "openid email profile"


@dataclass
class OIDCConfig:
    """Configuration d'un fournisseur OIDC."""

    issuer: str
    client_id: str
    redirect_uri: str
    scopes: str = DEFAULT_SCOPES
    client_secret: str = ""

    @classmethod
    def from_env(cls) -> OIDCConfig | None:
        issuer = os.environ.get("OIDC_ISSUER", "")
        client_id = os.environ.get("OIDC_CLIENT_ID", "")
        redirect_uri = os.environ.get("OIDC_REDIRECT_URI", "")
        if not (issuer and client_id and redirect_uri):
            return None
        return cls(
            issuer=issuer,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scopes=os.environ.get("OIDC_SCOPES", DEFAULT_SCOPES),
            client_secret=os.environ.get("OIDC_CLIENT_SECRET", ""),
        )


@dataclass
class PKCEChallenge:
    code_verifier: str
    code_challenge: str
    state: str
    nonce: str


def make_pkce_challenge() -> PKCEChallenge:
    """Génère un challenge PKCE (S256) pour OAuth2 authorization code flow."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PKCEChallenge(
        code_verifier=verifier,
        code_challenge=challenge,
        state=secrets.token_urlsafe(24),
        nonce=secrets.token_urlsafe(24),
    )


def build_authorization_url(
    cfg: OIDCConfig, *, pkce: PKCEChallenge, prompt: str | None = None
) -> str:
    """Construit l'URL d'autorisation OIDC (browser redirect)."""
    params = {
        "response_type": "code",
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "scope": cfg.scopes,
        "state": pkce.state,
        "nonce": pkce.nonce,
        "code_challenge": pkce.code_challenge,
        "code_challenge_method": "S256",
    }
    if prompt:
        params["prompt"] = prompt
    return f"{cfg.issuer.rstrip('/')}/authorize?{urlencode(params)}"


def map_groups_to_role(groups: list[str], *, role_map: dict | None = None) -> str:
    """Mappe les groupes Entra ID / Keycloak vers les 4 rôles RBAC.

    Le mapping est paramétrable via la variable d'environnement
    `OIDC_ROLE_MAP` au format JSON, e.g. :
        {"DG-Audit": "admin", "Audit-Senior": "manager", "Audit-Junior": "analyst"}

    Hiérarchie de fallback : admin > manager > analyst > viewer.
    """
    if role_map is None:
        raw = os.environ.get("OIDC_ROLE_MAP", "")
        try:
            role_map = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            log.warning("OIDC_ROLE_MAP n'est pas un JSON valide — ignoré")
            role_map = {}

    rank = {"admin": 4, "manager": 3, "analyst": 2, "viewer": 1}
    best_role = "viewer"
    best_rank = 1
    for grp in groups:
        role = role_map.get(grp)
        if role and rank.get(role, 0) > best_rank:
            best_role = role
            best_rank = rank[role]
    return best_role


def parse_userinfo(claims: dict) -> dict:
    """Extrait username, email, groupes depuis les claims OIDC standards."""
    username = (
        claims.get("preferred_username")
        or claims.get("email", "").split("@")[0]
        or claims.get("sub", "")
    )
    return {
        "username": username,
        "email": claims.get("email", ""),
        "name": claims.get("name", username),
        "groups": claims.get("groups", []) or claims.get("roles", []),
    }
