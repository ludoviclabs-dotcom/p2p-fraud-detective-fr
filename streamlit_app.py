"""P2P Fraud Detective FR — entry point Streamlit avec `st.navigation`.

Le Cockpit (`pages/0_🎯_Cockpit.py`) est la page par défaut au chargement.
Les 17 pages sont regroupées en 6 sections (loi de Miller : 7 ± 2).
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.streamlit_theme import init_app

init_app()


pages = {
    "🧭 Pilotage": [
        st.Page(
            "pages/0_🎯_Cockpit.py",
            title="Cockpit",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "pages/10_🗂️_File_d_investigation.py",
            title="File d'investigation",
            icon=":material/inbox:",
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

with st.sidebar:
    st.divider()
    if st.button(
        "🗑️ Purger la session",
        help="RGPD — droit à l'effacement. Supprime toutes les données chargées en mémoire.",
        use_container_width=True,
    ):
        keys_to_clear = [k for k in list(st.session_state.keys()) if k != "current_user"]
        for k in keys_to_clear:
            del st.session_state[k]
        st.toast("Session purgée — toutes les données ont été effacées.", icon="🗑️")

pg.run()
