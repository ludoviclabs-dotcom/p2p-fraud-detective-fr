"""P2P Fraud Detective FR — entry point Streamlit avec `st.navigation`.

Le Cockpit (`pages/0_🎯_Cockpit.py`) est la page par défaut au chargement.
Les 17 pages sont regroupées en 6 sections (loi de Miller : 7 ± 2).
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.config import get_settings
from p2p_fraud.logging_setup import configure_logging
from p2p_fraud.streamlit_theme import init_app

configure_logging()
init_app()


def _oidc_login_url() -> str | None:
    """Renvoie l'URL absolue du endpoint /oidc/login si l'API est joignable.

    Le déploiement pilote ETI hébérge FastAPI et Streamlit derrière le même
    reverse proxy (cookies partagés). En démo Streamlit Cloud, OIDC reste
    inactif (variables d'env absentes) → le bouton ne s'affiche pas.
    """
    s = get_settings()
    if not (s.oidc_issuer and s.oidc_client_id and s.oidc_redirect_uri):
        return None
    # On déduit l'URL de login en remplaçant le path du redirect_uri par /oidc/login
    base = s.oidc_redirect_uri.rsplit("/oidc/", 1)[0]
    return f"{base}/oidc/login"


pages = {
    "🧭 Pilotage": [
        st.Page(
            "pages/0_🎯_Cockpit.py",
            title="Cockpit",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "pages/00_🎓_Tour_guidé.py",
            title="Tour guidé",
            icon=":material/school:",
        ),
        st.Page(
            "pages/20_🎮_Sandbox.py",
            title="Sandbox commerciale",
            icon=":material/play_circle:",
        ),
        st.Page(
            "pages/10_🗂️_File_d_investigation.py",
            title="File d'investigation",
            icon=":material/inbox:",
        ),
        st.Page(
            "pages/18_🔔_Alertes.py",
            title="Alertes & monitoring",
            icon=":material/notifications_active:",
        ),
        st.Page(
            "pages/19_👥_Collaboration.py",
            title="Collaboration multi-user",
            icon=":material/groups:",
        ),
    ],
    "🗂️ Données": [
        st.Page(
            "pages/1_📤_Upload.py",
            title="Import des données",
            icon=":material/upload:",
        ),
        st.Page(
            "pages/3_🏦_Master_data_history.py",
            title="Référentiel — historique",
            icon=":material/history:",
        ),
        st.Page(
            "pages/6_🇫🇷_Sirene_check.py",
            title="Contrôle Sirene",
            icon=":material/verified:",
        ),
    ],
    "🧮 Contrôles statistiques": [
        st.Page(
            "pages/2_🔢_Benford.py",
            title="Loi de Benford",
            icon=":material/bar_chart:",
        ),
        st.Page(
            "pages/4_♊_Doublons.py",
            title="Doublons",
            icon=":material/content_copy:",
        ),
        st.Page(
            "pages/5_📏_Sous_seuils.py",
            title="Fractionnement / sous-seuils",
            icon=":material/horizontal_rule:",
        ),
        st.Page(
            "pages/9_⚖️_Sanctions_PEP.py",
            title="Sanctions & PEP",
            icon=":material/gavel:",
        ),
        st.Page(
            "pages/17_🏛️_DECP_RBE.py",
            title="DECP & RBE INPI",
            icon=":material/account_balance:",
        ),
    ],
    "🤖 Détection ML": [
        st.Page(
            "pages/7_🤖_Anomalies_ML.py",
            title="Anomalies (ML)",
            icon=":material/psychology:",
        ),
        st.Page(
            "pages/8_🕸️_Anneaux_fraude.py",
            title="Anneaux de fraude",
            icon=":material/hub:",
        ),
        st.Page(
            "pages/14_💡_Score_explorer.py",
            title="Explorateur de score",
            icon=":material/insights:",
        ),
    ],
    "🔎 Investigation & restitution": [
        st.Page(
            "pages/15_🪪_Fiche_fournisseur_360.py",
            title="Fiche fournisseur 360°",
            icon=":material/account_circle:",
        ),
        st.Page(
            "pages/11_📊_Synthèse_export.py",
            title="Synthèse — export",
            icon=":material/description:",
        ),
        st.Page(
            "pages/13_📜_Audit_trail.py",
            title="Piste d'audit",
            icon=":material/fingerprint:",
        ),
    ],
    "📚 Gouvernance & méthode": [
        st.Page(
            "pages/12_📚_Méthodologie.py",
            title="Méthodologie",
            icon=":material/menu_book:",
        ),
        st.Page(
            "pages/16_🛡️_Gouvernance.py",
            title="Gouvernance",
            icon=":material/shield_person:",
        ),
    ],
}

pg = st.navigation(pages, position="sidebar", expanded=True)

# i18n P5-4 : initialise la locale dès le démarrage (lit st.session_state["lang"]).
from p2p_fraud.i18n import _, init_locale_from_session  # noqa: E402

init_locale_from_session()

with st.sidebar:
    st.divider()
    # Sélecteur de langue (P5-4)
    _lang_choice = st.radio(
        _("common.language"),
        options=["🇫🇷 FR", "🇬🇧 EN"],
        index=0 if st.session_state.get("lang", "fr") == "fr" else 1,
        horizontal=True,
        key="lang_radio",
    )
    _new_lang = "fr" if _lang_choice.startswith("🇫🇷") else "en"
    if _new_lang != st.session_state.get("lang", "fr"):
        st.session_state["lang"] = _new_lang
        st.rerun()
    st.divider()
    _login_url = _oidc_login_url()
    if _login_url:
        st.link_button(
            f"🔑 {_('common.signin_oidc')}",
            url=_login_url,
            use_container_width=True,
            help="Authentification fédérée Microsoft Entra ID / Auth0 / Keycloak.",
        )
    if st.button(
        f"🗑️ {_('common.purge_session')}",
        help=_("common.purge_help"),
        use_container_width=True,
    ):
        keys_to_clear = [
            k for k in list(st.session_state.keys()) if k not in ("current_user", "lang")
        ]
        for k in keys_to_clear:
            del st.session_state[k]
        st.toast(_("common.toast_session_purged"), icon="🗑️")

pg.run()
