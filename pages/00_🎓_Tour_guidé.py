"""Page Tour guidé — découverte interactive en 5 étapes (Phase 6).

Onboarding institutionnel pour visiteur Tracfin / IEF / DGE / pilote ETI.
Permet de comprendre la plateforme en moins de 3 minutes sans cliquer
ailleurs que sur « Suivant ».

Approche pragmatique sans dépendance JS externe (Onborda nécessiterait
React, hors périmètre Streamlit). État géré via `st.session_state["tour_step"]`,
persistance implicite à travers la session utilisateur, deep-links
`?tour_step=N` pour reprise depuis un partage de lien.
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.i18n import _, init_locale_from_session
from p2p_fraud.streamlit_theme import init_page

init_locale_from_session()

init_page(
    title=_("tour.title"),
    surtitle=_("tour.surtitle"),
    kicker=_("tour.kicker"),
)

TOTAL_STEPS = 5
REPO_URL = "https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr"

# ─── Initialisation de l'état (avec support deep-link ?tour_step=N) ──────────
if "tour_step" not in st.session_state:
    qp_step = st.query_params.get("tour_step", "1")
    try:
        st.session_state["tour_step"] = max(1, min(int(qp_step), TOTAL_STEPS))
    except (TypeError, ValueError):
        st.session_state["tour_step"] = 1

current = st.session_state["tour_step"]

# Sync deep-link URL avec l'état
if str(current) != st.query_params.get("tour_step", ""):
    st.query_params["tour_step"] = str(current)

# ─── Barre de progression + skip ─────────────────────────────────────────────
col_progress, col_skip = st.columns([4, 1])
with col_progress:
    st.progress(current / TOTAL_STEPS, text=_("tour.progress", current=current, total=TOTAL_STEPS))
with col_skip:
    if current < TOTAL_STEPS + 1 and st.button(
        _("tour.btn_skip"), use_container_width=True, key="tour_skip"
    ):
        st.session_state["tour_step"] = TOTAL_STEPS + 1
        st.rerun()

st.divider()


# ─── Contenu par étape ───────────────────────────────────────────────────────
def _render_step(step: int) -> None:
    title = _(f"tour.step{step}_title")
    body = _(f"tour.step{step}_body")
    st.markdown(f"### {title}")
    st.markdown(body)


if current == 1:
    _render_step(1)
elif current == 2:
    _render_step(2)
    st.info("💡 Sandbox accessible directement depuis la sidebar (2e entrée du Pilotage).")
elif current == 3:
    _render_step(3)
    st.info("💡 Cockpit = page d'accueil par défaut au démarrage de l'app.")
elif current == 4:
    _render_step(4)
    st.info(
        "💡 La narration LLM apparaît directement sous la Fiche 360° en streaming "
        "(`st.write_stream` + Anthropic SDK)."
    )
elif current == 5:
    _render_step(5)
    st.info(
        "💡 La page **Audit trail** propose un bouton « Vérifier signatures Ed25519 » "
        "+ « Recalculer la chaîne de hash »."
    )
else:
    # Étape de fin
    st.success(f"## {_('tour.cta_done_title')}")
    st.markdown(_("tour.cta_done_body"))
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.page_link("pages/20_🎮_Sandbox.py", label=_("tour.cta_explore_sandbox"), icon="🎮")
    with col_b:
        st.page_link("pages/0_🎯_Cockpit.py", label=_("tour.cta_open_cockpit"), icon="🎯")
    with col_c:
        st.page_link("pages/16_🛡️_Gouvernance.py", label=_("tour.cta_open_governance"), icon="🛡️")
    with col_d:
        st.link_button(_("tour.cta_view_repo"), url=REPO_URL, use_container_width=True)
    st.divider()
    if st.button(_("tour.btn_restart"), use_container_width=False, key="tour_restart"):
        st.session_state["tour_step"] = 1
        st.rerun()

# ─── Navigation Précédent / Suivant ──────────────────────────────────────────
if current <= TOTAL_STEPS:
    st.divider()
    col_prev, col_spacer, col_next = st.columns([1, 2, 1])
    with col_prev:
        if current > 1 and st.button(
            f"⬅️ {_('tour.btn_prev')}",
            use_container_width=True,
            key=f"tour_prev_{current}",
        ):
            st.session_state["tour_step"] = current - 1
            st.rerun()
    with col_next:
        next_label = _("tour.btn_done") if current == TOTAL_STEPS else _("tour.btn_next")
        if st.button(
            f"{next_label} ➡️",
            type="primary",
            use_container_width=True,
            key=f"tour_next_{current}",
        ):
            st.session_state["tour_step"] = current + 1
            st.rerun()
