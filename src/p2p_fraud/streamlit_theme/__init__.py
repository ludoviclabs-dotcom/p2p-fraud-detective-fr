"""Theming Streamlit centralisé — palette, CSS, Plotly, header institutionnel.

Usage canonique en tête de chaque page Streamlit :

    from p2p_fraud.streamlit_theme import init_page

    init_page(
        title="Cockpit",
        surtitle="Pilotage",
        kicker="Vue consolidée des risques P2P",
    )

`init_page` s'occupe de :
1. `st.set_page_config(...)` (doit être le premier appel Streamlit) ;
2. injection du CSS partagé (palette navy/charcoal/or, ribbon DÉMO) ;
3. enregistrement du template Plotly « p2pfd » ;
4. affichage de l'en-tête institutionnel (sur-titre + titre + kicker).
"""

from __future__ import annotations

import contextlib

import streamlit as st

from p2p_fraud.streamlit_theme.css import CSS
from p2p_fraud.streamlit_theme.header import page_header
from p2p_fraud.streamlit_theme.plot import register as register_plotly

DEMO_VERSION = "0.3"

_PAGE_CONFIG_DONE = False
_PLOTLY_REGISTERED = False


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


def inject_css() -> None:
    """Injecte le CSS partagé (palette, ribbon DÉMO, masquage footer Streamlit)."""
    st.markdown(CSS, unsafe_allow_html=True)


def init_page(
    *,
    title: str,
    surtitle: str,
    kicker: str | None = None,
    page_title: str | None = None,
    page_icon: str = "🛡️",
) -> None:
    """À appeler en tout premier dans chaque page Streamlit.

    Les pages déjà chargées continuent de fonctionner si `set_page_config` a
    déjà été appelé — Streamlit autorise un seul appel par session de page,
    on garde donc une garde idempotente.
    """
    global _PAGE_CONFIG_DONE, _PLOTLY_REGISTERED

    if not _PAGE_CONFIG_DONE:
        # `set_page_config` peut être déjà appelé par Streamlit lors d'une
        # transition entre pages — on ignore alors silencieusement.
        with contextlib.suppress(st.errors.StreamlitAPIException):
            st.set_page_config(
                page_title=page_title or f"{title} — P2P Fraud Detective FR",
                page_icon=page_icon,
                layout="wide",
                initial_sidebar_state="expanded",
                menu_items=_menu_items(),
            )
        _PAGE_CONFIG_DONE = True

    if not _PLOTLY_REGISTERED:
        register_plotly()
        _PLOTLY_REGISTERED = True

    inject_css()
    page_header(title=title, surtitle=surtitle, kicker=kicker)


__all__ = ["DEMO_VERSION", "init_page", "inject_css", "page_header", "register_plotly"]
