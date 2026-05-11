"""Tests P4-3 — flow OIDC end-to-end.

Mocke discovery, token endpoint et JWKS via `responses` (déjà dans dev deps).
Génère une paire RSA à la volée pour signer un id_token réaliste, puis vérifie
les 6 cas critiques :

1. Login redirige vers l'IdP avec state cookie + paramètres OIDC
2. Callback succès — code → tokens → session ouverte
3. Callback rejette state mismatch (CSRF)
4. Callback rejette nonce mismatch
5. Callback rejette signature JWT invalide
6. /me retourne l'identité sur cookie session valide ; 401 sinon
"""

from __future__ import annotations

import json
import time
from typing import Any

import pytest
import responses
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwk, jwt
from jose.constants import ALGORITHMS

from p2p_fraud.api.main import app
from p2p_fraud.api.oidc_router import _discovery_cache, _jwks_caches
from p2p_fraud.security.session_store import (
    SESSION_COOKIE_NAME,
    STATE_COOKIE_NAME,
    make_session_serializer,
    make_state_serializer,
)

ISSUER = "https://login.example.com/tenant/v2.0"
CLIENT_ID = "client-abc"
REDIRECT_URI = "http://testserver/oidc/callback"
SESSION_SECRET = "test-secret-of-at-least-32-bytes-aaaa"


@pytest.fixture(autouse=True)
def _clear_caches():
    _discovery_cache._docs.clear()
    _discovery_cache._fetched_at.clear()
    _jwks_caches.clear()
    yield


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("OIDC_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("OIDC_REDIRECT_URI", REDIRECT_URI)
    monkeypatch.setenv("OIDC_SCOPES", "openid email profile")
    monkeypatch.setenv("OIDC_SESSION_SECRET", SESSION_SECRET)
    monkeypatch.setenv("OIDC_POST_LOGIN_URL", "/")
    monkeypatch.setenv("OIDC_SESSION_MAX_AGE", "3600")
    yield


@pytest.fixture
def rsa_keypair():
    """Paire RSA + JWK public + kid stable pour signer/valider."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.PEM,
        format=__import__("cryptography").hazmat.primitives.serialization.PrivateFormat.PKCS8,
        encryption_algorithm=__import__(
            "cryptography"
        ).hazmat.primitives.serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.PEM,
        format=__import__(
            "cryptography"
        ).hazmat.primitives.serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pub_jwk = jwk.construct(public_pem.decode(), ALGORITHMS.RS256).to_dict()
    pub_jwk["kid"] = "test-kid"
    pub_jwk["use"] = "sig"
    pub_jwk["alg"] = "RS256"
    return private_pem.decode(), pub_jwk


def _discovery_doc() -> dict[str, Any]:
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/authorize",
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/.well-known/jwks.json",
        "end_session_endpoint": f"{ISSUER}/logout",
    }


def _make_id_token(private_pem: str, *, nonce: str, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "sub": "user-123",
        "iat": now,
        "exp": now + 3600,
        "nonce": nonce,
        "preferred_username": "alice",
        "email": "alice@example.com",
        "name": "Alice Tester",
        "groups": ["DG-Audit"],
    }
    claims.update(overrides)
    return jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": "test-kid"})


@pytest.fixture
def client(env):
    return TestClient(app, follow_redirects=False)


@responses.activate
def test_login_redirects_to_idp_with_state_cookie(client):
    responses.add(
        responses.GET,
        f"{ISSUER}/.well-known/openid-configuration",
        json=_discovery_doc(),
    )
    r = client.get("/oidc/login")
    assert r.status_code == 302
    location = r.headers["location"]
    assert location.startswith(f"{ISSUER}/authorize?")
    for required in ("response_type=code", f"client_id={CLIENT_ID}", "code_challenge_method=S256"):
        assert required in location
    assert STATE_COOKIE_NAME in r.cookies


@responses.activate
def test_callback_success_opens_session(client, rsa_keypair):
    private_pem, pub_jwk = rsa_keypair
    responses.add(
        responses.GET,
        f"{ISSUER}/.well-known/openid-configuration",
        json=_discovery_doc(),
    )
    responses.add(responses.GET, f"{ISSUER}/.well-known/jwks.json", json={"keys": [pub_jwk]})

    state_serializer = make_state_serializer(SESSION_SECRET)
    state_payload = {"state": "STATE-1", "nonce": "NONCE-1", "code_verifier": "VERIFIER-1"}
    state_cookie = state_serializer.dumps(state_payload)
    id_token = _make_id_token(private_pem, nonce="NONCE-1")
    responses.add(
        responses.POST,
        f"{ISSUER}/token",
        json={"id_token": id_token, "access_token": "AT", "expires_in": 3600},
    )

    client.cookies.set(STATE_COOKIE_NAME, state_cookie)
    r = client.get("/oidc/callback", params={"code": "CODE-1", "state": "STATE-1"})
    assert r.status_code == 302, r.text
    assert SESSION_COOKIE_NAME in r.cookies
    session = make_session_serializer(SESSION_SECRET, max_age=3600).loads(
        r.cookies[SESSION_COOKIE_NAME]
    )
    assert session["email"] == "alice@example.com"
    assert session["role"] == "viewer"  # default sans OIDC_ROLE_MAP


@responses.activate
def test_callback_rejects_state_mismatch(client):
    responses.add(
        responses.GET,
        f"{ISSUER}/.well-known/openid-configuration",
        json=_discovery_doc(),
    )
    state_cookie = make_state_serializer(SESSION_SECRET).dumps(
        {"state": "EXPECTED", "nonce": "N", "code_verifier": "V"}
    )
    client.cookies.set(STATE_COOKIE_NAME, state_cookie)
    r = client.get("/oidc/callback", params={"code": "C", "state": "ATTACKER"})
    assert r.status_code == 400
    assert "State mismatch" in r.json()["detail"]


@responses.activate
def test_callback_rejects_nonce_mismatch(client, rsa_keypair):
    private_pem, pub_jwk = rsa_keypair
    responses.add(
        responses.GET,
        f"{ISSUER}/.well-known/openid-configuration",
        json=_discovery_doc(),
    )
    responses.add(responses.GET, f"{ISSUER}/.well-known/jwks.json", json={"keys": [pub_jwk]})

    state_cookie = make_state_serializer(SESSION_SECRET).dumps(
        {"state": "S", "nonce": "EXPECTED-NONCE", "code_verifier": "V"}
    )
    id_token = _make_id_token(private_pem, nonce="WRONG-NONCE")
    responses.add(responses.POST, f"{ISSUER}/token", json={"id_token": id_token})

    client.cookies.set(STATE_COOKIE_NAME, state_cookie)
    r = client.get("/oidc/callback", params={"code": "C", "state": "S"})
    assert r.status_code == 401
    assert "Nonce" in r.json()["detail"]


@responses.activate
def test_callback_rejects_invalid_signature(client, rsa_keypair):
    _, pub_jwk = rsa_keypair
    # Génère une SECONDE paire — la signature ne correspondra pas à la JWK publiée.
    other_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pem = other_priv.private_bytes(
        encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.PEM,
        format=__import__("cryptography").hazmat.primitives.serialization.PrivateFormat.PKCS8,
        encryption_algorithm=__import__(
            "cryptography"
        ).hazmat.primitives.serialization.NoEncryption(),
    ).decode()

    responses.add(
        responses.GET,
        f"{ISSUER}/.well-known/openid-configuration",
        json=_discovery_doc(),
    )
    responses.add(responses.GET, f"{ISSUER}/.well-known/jwks.json", json={"keys": [pub_jwk]})

    state_cookie = make_state_serializer(SESSION_SECRET).dumps(
        {"state": "S", "nonce": "N", "code_verifier": "V"}
    )
    bad_token = _make_id_token(other_pem, nonce="N")  # signé avec la mauvaise clé
    responses.add(responses.POST, f"{ISSUER}/token", json={"id_token": bad_token})

    client.cookies.set(STATE_COOKIE_NAME, state_cookie)
    r = client.get("/oidc/callback", params={"code": "C", "state": "S"})
    assert r.status_code == 401
    assert "Validation JWT" in r.json()["detail"]


def test_me_unauthenticated_returns_401(client):
    r = client.get("/oidc/me")
    assert r.status_code == 401


def test_me_returns_payload_on_valid_session(client):
    payload = {
        "sub": "user-9",
        "username": "bob",
        "email": "bob@example.com",
        "name": "Bob",
        "groups": [],
        "role": "analyst",
    }
    cookie = make_session_serializer(SESSION_SECRET, max_age=3600).dumps(payload)
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    r = client.get("/oidc/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "bob@example.com"
    assert body["role"] == "analyst"


def test_logout_clears_session_cookie(client):
    cookie = make_session_serializer(SESSION_SECRET, max_age=3600).dumps({"sub": "x"})
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    r = client.post("/oidc/logout")
    assert r.status_code == 200
    assert r.json() == {"status": "logged_out"}
    # Le cookie est invalidé via Set-Cookie max-age=0
    set_cookie = r.headers.get("set-cookie", "")
    assert SESSION_COOKIE_NAME in set_cookie


def test_login_returns_503_when_oidc_not_configured(monkeypatch):
    for var in ("OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_REDIRECT_URI", "OIDC_SESSION_SECRET"):
        monkeypatch.delenv(var, raising=False)
    c = TestClient(app, follow_redirects=False)
    r = c.get("/oidc/login")
    assert r.status_code == 503


# Helper exporté pour aider quand on inspecte les payloads en debug
_ = json
