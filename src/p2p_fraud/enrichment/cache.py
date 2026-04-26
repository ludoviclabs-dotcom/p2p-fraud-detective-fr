"""Façade `requests-cache` partagée entre tous les clients enrichissement.

Le cache local (SQLite) permet :
- de respecter les quotas API (Sirene v3 : 30 req/s),
- des démos reproductibles offline,
- de ne pas re-payer un appel pour un SIREN déjà vu dans la session.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import requests_cache

DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "cache"
DEFAULT_CACHE_NAME = "enrichment_http_cache"


def get_cached_session(
    *,
    cache_name: str = DEFAULT_CACHE_NAME,
    expire_after: timedelta = timedelta(days=30),
    cache_dir: Path | None = None,
    backend: str = "sqlite",
) -> requests_cache.CachedSession:
    """Retourne une session HTTP avec cache persistant.

    Args:
        cache_name: nom du fichier (sans extension).
        expire_after: TTL des entrées.
        cache_dir: dossier où stocker le cache (créé si absent).
        backend: backend requests-cache (`sqlite`, `memory`, etc.).
    """
    base = cache_dir or DEFAULT_CACHE_DIR
    base.mkdir(parents=True, exist_ok=True)
    cache_path = base / cache_name
    return requests_cache.CachedSession(
        cache_name=str(cache_path),
        backend=backend,
        expire_after=expire_after,
        allowable_methods=("GET",),
        allowable_codes=(200, 404),  # 404 (SIREN inexistant) à cacher aussi
        stale_if_error=True,
    )


def clear_cache(cache_name: str = DEFAULT_CACHE_NAME, cache_dir: Path | None = None) -> None:
    """Efface le cache local (utile en dev / tests)."""
    base = cache_dir or DEFAULT_CACHE_DIR
    sqlite_path = base / f"{cache_name}.sqlite"
    if sqlite_path.exists():
        os.remove(sqlite_path)
