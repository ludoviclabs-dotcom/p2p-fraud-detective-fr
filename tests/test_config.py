"""Tests P4-1 — Settings centralisés + logging configurable."""

from __future__ import annotations

import importlib
import logging

from p2p_fraud.config import Settings, get_settings


def test_settings_default_values():
    s = Settings(_env_file=None)
    assert s.sirene_api_token == ""
    assert s.anthropic_api_key == ""
    assert s.fraud_api_secret == ""
    assert s.fraud_cases_db == "cases.db"
    assert s.oidc_issuer == ""
    assert s.oidc_scopes == "openid email profile"
    assert s.oidc_role_map == ""
    assert s.p2p_fraud_data_key == ""
    assert s.p2p_fraud_users_path == ""
    assert s.p2p_fraud_auth_required is False
    assert s.database_url == ""
    assert s.slack_webhook_url == ""
    assert s.teams_webhook_url == ""
    assert s.sentry_dsn == ""
    assert s.decp_parquet_path == ""
    assert s.log_level == "INFO"
    assert s.log_format == "text"


def test_settings_reads_legacy_env_var_names(monkeypatch):
    """Garde-fou rétrocompat : noms historiques sans préfixe (Phase 3)."""
    monkeypatch.setenv("SIRENE_API_TOKEN", "tok-123")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example.com")
    monkeypatch.setenv("OIDC_CLIENT_ID", "myapp")
    monkeypatch.setenv("OIDC_REDIRECT_URI", "https://app.example.com/callback")
    monkeypatch.setenv("FRAUD_API_SECRET", "shh")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-abc")
    monkeypatch.setenv("P2P_FRAUD_AUTH_REQUIRED", "1")
    monkeypatch.setenv("LOG_FORMAT", "json")

    s = Settings(_env_file=None)
    assert s.sirene_api_token == "tok-123"
    assert s.oidc_issuer == "https://issuer.example.com"
    assert s.oidc_client_id == "myapp"
    assert s.fraud_api_secret == "shh"
    assert s.anthropic_api_key == "sk-ant-abc"
    assert s.p2p_fraud_auth_required is True
    assert s.log_format == "json"


def test_settings_case_insensitive_env(monkeypatch):
    monkeypatch.setenv("anthropic_api_key", "key-from-lowercase")
    s = Settings(_env_file=None)
    assert s.anthropic_api_key == "key-from-lowercase"


def test_get_settings_returns_settings_instance():
    s = get_settings()
    assert isinstance(s, Settings)


def test_get_settings_picks_up_env_changes(monkeypatch):
    """Pas de cache global : chaque appel relit l'environnement."""
    monkeypatch.setenv("SIRENE_API_TOKEN", "first")
    s1 = get_settings()
    assert s1.sirene_api_token == "first"

    monkeypatch.setenv("SIRENE_API_TOKEN", "second")
    s2 = get_settings()
    assert s2.sirene_api_token == "second"


def test_oidc_config_from_env_returns_none_when_missing(monkeypatch):
    """Rétrocompat : `OIDCConfig.from_env()` retourne None si issuer absent."""
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    monkeypatch.delenv("OIDC_CLIENT_ID", raising=False)
    monkeypatch.delenv("OIDC_REDIRECT_URI", raising=False)

    from p2p_fraud.security.oidc import OIDCConfig

    assert OIDCConfig.from_env() is None


def test_oidc_config_from_env_uses_settings(monkeypatch):
    monkeypatch.setenv("OIDC_ISSUER", "https://login.microsoftonline.com/tenant/v2.0")
    monkeypatch.setenv("OIDC_CLIENT_ID", "myapp")
    monkeypatch.setenv("OIDC_REDIRECT_URI", "https://app.example.com/callback")

    from p2p_fraud.security.oidc import OIDCConfig

    cfg = OIDCConfig.from_env()
    assert cfg is not None
    assert cfg.issuer == "https://login.microsoftonline.com/tenant/v2.0"
    assert cfg.client_id == "myapp"
    assert cfg.redirect_uri == "https://app.example.com/callback"
    assert cfg.scopes == "openid email profile"


def test_configure_logging_sets_level_text_format(monkeypatch):
    from p2p_fraud import logging_setup

    importlib.reload(logging_setup)

    settings = Settings(_env_file=None, log_level="WARNING", log_format="text")
    logging_setup.configure_logging(settings=settings)

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert len(root.handlers) == 1


def test_configure_logging_idempotent_no_duplicate_handlers():
    from p2p_fraud import logging_setup

    importlib.reload(logging_setup)

    settings = Settings(_env_file=None)
    logging_setup.configure_logging(settings=settings)
    n_first = len(logging.getLogger().handlers)
    logging_setup.configure_logging(settings=settings)
    n_second = len(logging.getLogger().handlers)
    assert n_first == n_second == 1


def test_configure_logging_json_format_falls_back_gracefully():
    """En mode JSON, le formatter doit fonctionner (python-json-logger installé)
    ou tomber sur le format texte (fallback ImportError)."""
    from p2p_fraud import logging_setup

    importlib.reload(logging_setup)
    settings = Settings(_env_file=None, log_format="json")
    logging_setup.configure_logging(settings=settings)
    root = logging.getLogger()
    assert len(root.handlers) == 1
