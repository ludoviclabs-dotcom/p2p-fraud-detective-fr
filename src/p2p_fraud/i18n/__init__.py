"""Internationalisation FR/EN — backend YAML, fallback gracieux (P5-4).

Approche pragmatique sans dépendance externe :
- Catalogues YAML plats (clés dotées : `cockpit.title`, `nav.section_pilotage`).
- Pas de Babel/gettext (overkill pour ~250 clés et zéro plural complexe).
- Fallback transparent : si la clé manque dans la locale courante, on
  retombe sur FR ; si elle manque aussi en FR, on renvoie la clé brute.
- Cache LRU des catalogues YAML (relus une fois au boot).
- Format strings supportés via `_("clé", count=3, name="Alice")` →
  `str.format(**kwargs)`.

Usage minimal dans une page Streamlit :

    from p2p_fraud.i18n import _, init_locale_from_session
    init_locale_from_session()
    st.title(_("cockpit.title"))

Le `init_locale_from_session()` lit `st.session_state["lang"]` (posé par
le sélecteur de la sidebar) avec FR par défaut.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

# Langues supportées — ajouter une entrée si vous traduisez un nouveau YAML.
SUPPORTED_LOCALES: tuple[str, ...] = ("fr", "en")
DEFAULT_LOCALE = "fr"
LOCALES_DIR = Path(__file__).resolve().parent / "locales"

# État courant — minuscule mutable côté thread Streamlit (un seul utilisateur
# par session). Pas de problème de concurrence en pratique.
_current_locale: str = DEFAULT_LOCALE


@lru_cache(maxsize=8)
def _load_catalog(locale: str) -> dict[str, Any]:
    """Charge le fichier `locales/<locale>.yaml` en dict aplati à clés dotées."""
    path = LOCALES_DIR / f"{locale}.yaml"
    if not path.exists():
        log.warning("i18n catalog missing: %s", path)
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        log.error("i18n YAML load failed for %s: %s", locale, exc)
        return {}
    return _flatten(raw)


def _flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    """Aplatit récursivement `{a: {b: "c"}}` en `{"a.b": "c"}`."""
    out: dict[str, Any] = {}
    if isinstance(node, dict):
        for k, v in node.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(_flatten(v, key))
    else:
        out[prefix] = node
    return out


def set_locale(locale: str) -> str:
    """Définit la langue active. Bascule sur DEFAULT_LOCALE si non supportée."""
    global _current_locale
    if locale not in SUPPORTED_LOCALES:
        log.warning("Unsupported locale %r, falling back to %s", locale, DEFAULT_LOCALE)
        locale = DEFAULT_LOCALE
    _current_locale = locale
    return _current_locale


def get_locale() -> str:
    """Retourne la langue active (utile pour les composants conditionnels)."""
    return _current_locale


def init_locale_from_session(default: str = DEFAULT_LOCALE) -> str:
    """Lit `st.session_state['lang']` (set par le sélecteur sidebar) et l'applique.

    Importé localement pour éviter un cycle d'import Streamlit côté tests.
    """
    try:
        import streamlit as st  # local pour éviter dépendance hard en tests

        lang = st.session_state.get("lang", default)
    except (ImportError, RuntimeError):
        lang = default
    return set_locale(lang)


def _(key: str, **kwargs: Any) -> str:
    """Traduit `key` dans la locale courante avec fallback FR → clé brute.

    Args:
        key: identifiant dotté (`"cockpit.title"`).
        **kwargs: placeholders pour `str.format()`.

    Returns:
        Chaîne traduite, formatée si placeholders fournis. Si la clé est
        introuvable même en FR, renvoie la clé brute (utile pour repérer
        les traductions manquantes dans l'UI sans casser le rendu).
    """
    catalog = _load_catalog(_current_locale)
    value = catalog.get(key)
    if value is None and _current_locale != DEFAULT_LOCALE:
        value = _load_catalog(DEFAULT_LOCALE).get(key)
    if value is None:
        return key
    if kwargs:
        try:
            return str(value).format(**kwargs)
        except (KeyError, IndexError) as exc:
            log.warning("i18n format failed for key=%s: %s", key, exc)
            return str(value)
    return str(value)


def missing_keys(reference_locale: str = DEFAULT_LOCALE) -> dict[str, list[str]]:
    """Diagnostique : liste les clés présentes en `reference_locale` mais absentes ailleurs.

    Utile en CI pour garantir la couverture du catalogue (à brancher dans
    `tests/test_i18n.py`).
    """
    ref_keys = set(_load_catalog(reference_locale).keys())
    missing: dict[str, list[str]] = {}
    for locale in SUPPORTED_LOCALES:
        if locale == reference_locale:
            continue
        locale_keys = set(_load_catalog(locale).keys())
        diff = sorted(ref_keys - locale_keys)
        if diff:
            missing[locale] = diff
    return missing


__all__ = [
    "DEFAULT_LOCALE",
    "SUPPORTED_LOCALES",
    "_",
    "get_locale",
    "init_locale_from_session",
    "missing_keys",
    "set_locale",
]
