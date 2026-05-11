"""Router FastAPI pour l'authentification OIDC end-to-end.

Endpoints exposés :
- `GET  /oidc/login` : génère PKCE + state, pose le cookie d'état, redirige vers l'IdP.
- `GET  /oidc/callback` : valide le state, échange le code contre un id_token,
  valide la signature JWT, ouvre une session signée, redirige vers `oidc_post_login_url`.
- `POST /oidc/logout` : efface le cookie de session.
- `GET  /oidc/me` : renvoie l'identité courante depuis le cookie de session (401 sinon).

Les caches (`DiscoveryCache`, `JWKSCache`) sont des singletons module — partagés entre
requêtes pour éviter de spammer l'IdP. Recyclés implicitement après TTL.

Note pilotes ETI : ce router se monte dans `api/main.py` via
`app.include_router(oidc_router)`. Streamlit interroge `GET /oidc/me` via
`requests` pour afficher l'identité côté UI (le cookie est partagé via le
même domaine ou un reverse proxy).
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from p2p_fraud.config import get_settings
from p2p_fraud.security.jwt_validator import (
    IdTokenValidationError,
    JWKSCache,
    validate_id_token,
)
from p2p_fraud.security.oidc import (
    OIDCConfig,
    make_pkce_challenge,
    map_groups_to_role,
    parse_userinfo,
)
from p2p_fraud.security.oidc_client import (
    DiscoveryCache,
    OIDCDiscoveryError,
    OIDCTokenError,
    exchange_code_for_tokens,
)
from p2p_fraud.security.session_store import (
    SESSION_COOKIE_NAME,
    STATE_COOKIE_NAME,
    STATE_MAX_AGE,
    make_session_serializer,
    make_state_serializer,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/oidc", tags=["Auth"])

# Caches singletons module — TTL gère le refresh
_discovery_cache = DiscoveryCache()
_jwks_caches: dict[str, JWKSCache] = {}


def _get_jwks_cache(jwks_uri: str) -> JWKSCache:
    if jwks_uri not in _jwks_caches:
        _jwks_caches[jwks_uri] = JWKSCache(jwks_uri=jwks_uri)
    return _jwks_caches[jwks_uri]


def _require_oidc_config() -> OIDCConfig:
    cfg = OIDCConfig.from_env()
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC non configuré (OIDC_ISSUER/CLIENT_ID/REDIRECT_URI manquants).",
        )
    return cfg


def _require_session_secret() -> str:
    secret = get_settings().oidc_session_secret
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC_SESSION_SECRET manquant — sessions OIDC désactivées.",
        )
    return secret


def _cookie_security_flags(request: Request) -> dict[str, Any]:
    """Renvoie `samesite=lax`, `httponly=True`, `secure=` selon le scheme."""
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": request.url.scheme == "https",
    }


@router.get("/login")
def login(request: Request) -> RedirectResponse:
    """Démarre le flow authorization code + PKCE."""
    cfg = _require_oidc_config()
    secret = _require_session_secret()
    discovery = _discovery_cache.get(cfg.issuer)

    pkce = make_pkce_challenge()
    state_payload = {
        "state": pkce.state,
        "nonce": pkce.nonce,
        "code_verifier": pkce.code_verifier,
    }
    state_token = make_state_serializer(secret).dumps(state_payload)

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
    authz_url = f"{discovery.authorization_endpoint}?{urlencode(params)}"

    response = RedirectResponse(url=authz_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state_token,
        max_age=STATE_MAX_AGE,
        path="/oidc",
        **_cookie_security_flags(request),
    )
    return response


@router.get("/callback")
def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    p2pfd_oidc_state: str | None = Cookie(default=None, alias=STATE_COOKIE_NAME),
) -> Response:
    """Callback OIDC — valide le state, échange le code, ouvre la session."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"IdP a renvoyé une erreur : {error} — {error_description or ''}",
        )
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paramètres `code` et `state` obligatoires.",
        )
    if not p2pfd_oidc_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cookie d'état OAuth absent — session expirée ou bloquée.",
        )

    cfg = _require_oidc_config()
    secret = _require_session_secret()
    state_payload = make_state_serializer(secret).loads(p2pfd_oidc_state)
    if state_payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cookie d'état invalide ou expiré.",
        )
    if state_payload.get("state") != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State mismatch — possible CSRF.",
        )

    try:
        discovery = _discovery_cache.get(cfg.issuer)
    except OIDCDiscoveryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    try:
        tokens = exchange_code_for_tokens(
            token_endpoint=discovery.token_endpoint,
            code=code,
            redirect_uri=cfg.redirect_uri,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret,
            code_verifier=state_payload["code_verifier"],
        )
    except OIDCTokenError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    try:
        claims = validate_id_token(
            tokens["id_token"],
            issuer=discovery.issuer,
            audience=cfg.client_id,
            nonce=state_payload["nonce"],
            jwks_cache=_get_jwks_cache(discovery.jwks_uri),
        )
    except IdTokenValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = parse_userinfo(claims)
    user["role"] = map_groups_to_role(user.get("groups", []))
    user["sub"] = claims.get("sub", "")

    session_token = make_session_serializer(
        secret, max_age=get_settings().oidc_session_max_age
    ).dumps(user)

    redirect_to = get_settings().oidc_post_login_url or "/"
    response = RedirectResponse(url=redirect_to, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=get_settings().oidc_session_max_age,
        path="/",
        **_cookie_security_flags(request),
    )
    response.delete_cookie(STATE_COOKIE_NAME, path="/oidc")
    log.info(
        "OIDC login OK — user=%s email=%s role=%s",
        user.get("username"),
        user.get("email"),
        user.get("role"),
    )
    return response


@router.post("/logout")
def logout(request: Request) -> Response:
    """Efface le cookie de session — ne contacte pas l'IdP."""
    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@router.get("/me")
def me(
    p2pfd_session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict[str, Any]:
    """Renvoie l'identité courante depuis la session, 401 sinon."""
    secret = get_settings().oidc_session_secret
    if not secret or not p2pfd_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié.")
    payload = make_session_serializer(secret, max_age=get_settings().oidc_session_max_age).loads(
        p2pfd_session
    )
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide ou expirée.",
        )
    return payload


__all__ = ["router"]
