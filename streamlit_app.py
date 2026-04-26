"""Page d'accueil — P2P Fraud Detective FR.

Streamlit charge automatiquement les pages depuis `pages/` (multipage app).
Cette page fait office de landing : positionnement, étapes, lien vers la page Upload.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="P2P Fraud Detective FR",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🕵️ P2P Fraud Detective FR")
st.subheader("Mini-MindBridge open-source pour ETI françaises — détection de fraude Procure-to-Pay")

st.markdown(
    """
    **Pourquoi cet outil ?** La fraude fournisseurs (factures fictives, doublons, fournisseurs
    fantômes, détournement d'IBAN, montants juste sous seuil de validation) reste le scénario
    le plus coûteux en contrôle interne. Les outils du marché sont chers et anglo-saxons ; aucun
    n'exploite nativement les sources publiques françaises (Sirene, DECP, Annuaire des entreprises).
    """
)

st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Détecteurs", "7", help="Benford, doublons, seuils, Sirene, IForest, graphe, score")
with c2:
    st.metric("Sources publiques FR", "2", help="API Sirene v3 (INSEE) + DECP")
with c3:
    st.metric("Stack", "Python + Streamlit", help="100 % open-source, F1 mesuré sur ground truth")

st.divider()

st.markdown("### 📋 Parcours type")
st.markdown(
    """
    1. **📤 Upload** — déposez votre export Excel/CSV de factures fournisseurs (style SAP `LFA1`/`RBKP`).
    2. **🔢 Benford** — analyse de la loi de Newcomb-Benford (1er, 2 premiers, dernier chiffre).
    3. **♊ Doublons** — fuzzy matching sur nom + bucket montant/date.
    4. **📏 Sous seuils** — détection de clusters juste sous seuil de validation.
    5. **🇫🇷 Sirene cross-check** — validation SIREN, statut, date de création vs factures.
    6. **🤖 Anomalies ML** — Isolation Forest sur features comportementales.
    7. **🕸️ Anneaux de fraude** — graphe NetworkX `(employees ⟷ vendors)`.
    8. **📊 Synthèse / export** — risk score consolidé, export Excel + Parquet pour Power BI.
    """
)

st.divider()

if "df_invoices" in st.session_state:
    df = st.session_state["df_invoices"]
    st.success(
        f"✅ Dataset chargé : **{len(df):,}** factures · {df['vendor_name'].nunique():,} fournisseurs"
    )
else:
    st.info(
        "👉 Aucun dataset chargé. Direction la page **📤 Upload** dans la barre latérale, ou utilisez le générateur synthétique pour démarrer."
    )

with st.expander("ℹ️ À propos"):
    st.markdown(
        """
        **Auteur** : Ludovic Labeaut · [github.com/ludoviclabeaut/p2p-fraud-detective-fr](https://github.com/ludoviclabeaut/p2p-fraud-detective-fr)
        · MIT License

        **Référentiels d'audit couverts** : ISA 240, AS 2401 (PCAOB), AICPA Audit Data Standards.
        Réutilisable pour Sapin 2 (cartographie), DORA (registre TIC), CSRD (datapoints).
        """
    )
