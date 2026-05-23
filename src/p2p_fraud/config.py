"""Centralised application settings via pydantic-settings.

Lit les variables d'environnement (et `.env`) au boot. Conserve les noms
historiques sans préfixe pour rétrocompat avec la Phase 3 et les tests
existants (e.g. `SIRENE_API_TOKEN`, `OIDC_*`, `FRAUD_*`, `P2P_FRAUD_*`).

Usage :

    from p2p_fraud.config import get_settings

    s = get_settings()
    token = s.sirene_api_token
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Singleton de configuration applicative.

    Tous les champs ont une valeur par défaut sûre (chaîne vide ou booléen
    `False`) afin que `Settings()` n'échoue jamais en environnement minimal
    (Streamlit Cloud, tests). Les modules consommateurs valident la présence
    avant utilisation effective (e.g. `OIDCConfig.from_env()` retourne `None`
    si l'issuer est vide).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Sirene (INSEE) ──────────────────────────────────────────────────────
    sirene_api_token: str = ""

    # ─── Anthropic Claude ────────────────────────────────────────────────────
    anthropic_api_key: str = ""

    # ─── FastAPI ─────────────────────────────────────────────────────────────
    fraud_api_secret: str = ""
    fraud_cases_db: str = "cases.db"

    # ─── OIDC (Microsoft Entra ID / Auth0 / Keycloak) ────────────────────────
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = ""
    oidc_scopes: str = "openid email profile"
    oidc_role_map: str = ""
    # Clé HMAC pour signer les cookies de session OIDC (itsdangerous)
    oidc_session_secret: str = ""
    # URL de redirection après login OIDC (relative ou absolue)
    oidc_post_login_url: str = "/"
    # Durée maximale d'une session signée (secondes)
    oidc_session_max_age: int = 8 * 3600

    # ─── Crypto (chiffrement IBAN au repos) ──────────────────────────────────
    p2p_fraud_data_key: str = ""

    # ─── HMAC IBAN fingerprint (Sprint 1 MandateGuard) ───────────────────────
    # Secret distinct du Fernet de chiffrement. Permet de calculer un
    # `iban_fingerprint = HMAC_SHA256(secret, normalize_iban(iban))` utilisable
    # pour indexer/rechercher sans jamais stocker l'IBAN en clair (ADR-0002 du
    # spec MandateGuard). Rotation indépendante de la clé Fernet.
    # Génération recommandée :
    #     python -c "import secrets; print(secrets.token_urlsafe(32))"
    # Si vide → secret éphémère par instance (mode démo, warning au boot).
    iban_hmac_secret: str = ""

    # ─── Auth applicative ────────────────────────────────────────────────────
    p2p_fraud_users_path: str = ""
    p2p_fraud_auth_required: bool = False

    # ─── Persistance (P4-2) ──────────────────────────────────────────────────
    database_url: str = ""

    # ─── Alertes monitoring (P3.4) ───────────────────────────────────────────
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""

    # ─── Signatures Ed25519 audit log (P5-5) ─────────────────────────────────
    # Clé privée Ed25519 (base64, 32 octets bruts). Générer hors ligne :
    #     python -c "from p2p_fraud.security.signing import Ed25519Signer; \\
    #                kp = Ed25519Signer.generate(); print(kp.private_key_b64)"
    # Stocker en coffre-fort (Vault / KMS / fichier 0600 root-only).
    # Si vide → mode démo, audit log uniquement hash-chaîné SHA-256.
    p2pfd_ed25519_private_key: str = ""

    # ─── Webhook sortant B2B (P5-3) ──────────────────────────────────────────
    # Quand `webhook_url` est défini, chaque event `case.*` émis par
    # `CaseService._record_event` est POSTé en JSON signé HMAC-SHA256
    # (header `X-P2PFD-Signature: sha256=<hex>`). Retry exponentiel via
    # tenacity (3 tentatives, 1s → 2s → 4s) sur erreurs réseau uniquement.
    webhook_url: str = ""
    webhook_secret: str = ""  # secret HMAC partagé avec le SIEM destinataire
    webhook_timeout: float = 5.0  # seconds (connect + read combinés)

    # ─── Webhook ENTRANT (Sprint 5 MandateGuard) ─────────────────────────────
    # Quand un PSP/banque pousse un événement (prélèvement, mandat, ICS…)
    # vers nous, la requête doit être signée HMAC-SHA256 avec ce secret.
    # Headers attendus : X-MG-Timestamp (ISO 8601), X-MG-Signature
    # (sha256=<hex>), X-MG-Idempotency-Key (anti-replay applicatif).
    # Si vide → tout endpoint protégé par `verify_inbound_webhook` refuse
    # toute requête entrante (fail-closed).
    webhook_inbound_secret: str = ""

    # ─── Observabilité (P4-6) ────────────────────────────────────────────────
    sentry_dsn: str = ""

    # ─── DECP ────────────────────────────────────────────────────────────────
    decp_parquet_path: str = ""

    # ─── Enrichissement live (P5-1) ──────────────────────────────────────────
    # Mode "demo" : adapters synthétiques embarqués (par défaut, démo publique).
    # Mode "live" : appels HTTP réels aux sources ouvertes (data.economie.gouv.fr,
    # api.pappers.fr, api.opensanctions.org). Fallback automatique sur "demo"
    # en cas d'échec réseau (log.warning émis).
    enrichment_mode: str = "demo"  # "demo" | "live"
    decp_live_base_url: str = "https://data.economie.gouv.fr/api/explore/v2.1"
    pappers_api_key: str = ""
    pappers_base_url: str = "https://api.pappers.fr/v2"
    yente_base_url: str = "https://api.opensanctions.org"

    # ─── Logging ─────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "text"  # "text" | "json"


def get_settings() -> Settings:
    """Renvoie une instance fraîche de `Settings`.

    Pas de cache global : chaque appel relit l'environnement, ce qui simplifie
    les tests qui utilisent `monkeypatch.setenv`. Le coût est négligeable
    (validation Pydantic d'une vingtaine de champs scalaires).
    """
    return Settings()
