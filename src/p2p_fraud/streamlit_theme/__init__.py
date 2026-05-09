"""Theming Streamlit centralisé — palette, CSS, Plotly, header institutionnel.

Architecture (v0.3 — st.navigation) :
- `streamlit_app.py` (entry point) appelle `init_app()` une fois en haut, puis
  configure `st.navigation(...)` et lance `pg.run()`.
- Chaque page sous `pages/` appelle `init_page(title, surtitle, kicker)` en
  premier — pas de `set_page_config` au niveau page (Streamlit l'interdit
  quand l'entry script l'a déjà appelé).
"""

from __future__ import annotations

import contextlib

import streamlit as st

from p2p_fraud.streamlit_theme.css import CSS
from p2p_fraud.streamlit_theme.header import page_header
from p2p_fraud.streamlit_theme.plot import register as register_plotly

DEMO_VERSION = "0.3"


def _menu_items() -> dict:
    return {
        "Get help": "https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr",
        "Report a bug": "https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/issues",
        "About": (
            "**P2P Fraud Detective FR** — démonstrateur public d'audit P2P / AML.\n\n"
            "Données : fictives ou issues de sources ouvertes (Sirene, sanctions UE).\n"
            f"Version {DEMO_VERSION} — 2026.\n"
            "Non destiné à un usage opérationnel."
        ),
    }


def init_app(
    *,
    page_title: str = "P2P Fraud Detective FR — Démonstrateur d'audit",
    page_icon: str = "🛡️",
) -> None:
    """À appeler une fois en haut de `streamlit_app.py` (entry point).

    Configure le `st.set_page_config` global. À ne pas appeler depuis les
    pages — Streamlit interdit deux appels par script run.
    """
    with contextlib.suppress(st.errors.StreamlitAPIException):
        st.set_page_config(
            page_title=page_title,
            page_icon=page_icon,
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items=_menu_items(),
        )


def inject_css() -> None:
    """Injecte le CSS partagé (palette, ribbon DÉMO, masquage footer Streamlit)."""
    st.markdown(CSS, unsafe_allow_html=True)


def init_page(
    *,
    title: str,
    surtitle: str,
    kicker: str | None = None,
    page_title: str | None = None,
    page_icon: str | None = None,
) -> None:
    """À appeler en tout premier dans chaque page Streamlit (sous `pg.run()`).

    - `title`     : titre principal de la page.
    - `surtitle`  : section de la nav (ex. « Pilotage », « Détection ML »).
    - `kicker`    : courte description sous le titre (optionnelle).

    Les paramètres `page_title` / `page_icon` sont conservés pour rétrocompat
    avec les anciennes signatures, mais ignorés (set_page_config est posé une
    fois par `init_app()` dans l'entry point).
    """
    del page_title, page_icon  # rétrocompat — ignorés depuis `st.navigation`
    register_plotly()
    inject_css()
    page_header(title=title, surtitle=surtitle, kicker=kicker)


__all__ = [
    "DEMO_VERSION",
    "init_app",
    "init_page",
    "inject_css",
    "page_header",
    "register_plotly",
]
