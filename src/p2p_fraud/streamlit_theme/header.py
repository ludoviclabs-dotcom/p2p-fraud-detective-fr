"""Header institutionnel partagé — sur-titre + titre + kicker."""

from __future__ import annotations

import streamlit as st


def page_header(*, title: str, surtitle: str, kicker: str | None = None) -> None:
    """Affiche un en-tête de page institutionnel.

    Convention :
    - `surtitle` : section de la nav (ex. « Pilotage », « Contrôles statistiques »).
    - `title`    : titre principal de la page.
    - `kicker`   : courte description en italique sous le titre (optionnelle).

    Remplace `st.title("...")` dans les pages.
    """
    kicker_html = (
        f'<div style="color:#5A6478; margin-top:0.35rem;">{kicker}</div>' if kicker else ""
    )
    st.markdown(
        f"""
        <div style="border-bottom:1px solid #E1E5EE; padding-bottom:0.75rem; margin-bottom:1.25rem;">
          <div style="font-size:0.78rem; color:#5A6478; text-transform:uppercase; letter-spacing:0.08em;">
            {surtitle}
          </div>
          <h1 style="margin:0.15rem 0 0; font-weight:700; color:#0F1B33; font-size:1.75rem;">
            {title}
          </h1>
          {kicker_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
