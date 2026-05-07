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
st.subheader("Vendor & Payment Integrity FR-native — fraude P2P, master data, audit signé")

st.markdown(
    """
    **Pourquoi cet outil ?** 80 % de la fraude P2P passe par un changement d'IBAN
    ou un fournisseur fictif — pas par une anomalie statistique exotique. Cet outil
    surveille **l'historique du master data fournisseur**, croise les sources publiques
    françaises (Sirene, DECP, RBE, listes de sanctions) et produit une **piste d'audit
    signée** pour ETI, cabinets d'audit et secteur public/hospitalier.
    """
)

st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    st.metric(
        "Détecteurs",
        "8",
        help=(
            "Master data, doublons, seuils, Sirene, sanctions, IForest, graphe, score. "
            "Benford reste disponible comme outil de scoping."
        ),
    )
with c2:
    st.metric(
        "Sources publiques FR",
        "4+",
        help="Sirene v3 (INSEE), DECP, RBE INPI (M2), OpenSanctions / Trésor FR",
    )
with c3:
    st.metric(
        "Audit trail",
        "Hash-chaîné",
        help="Journal immutable signé SHA-256, vérification d'intégrité native",
    )

st.divider()

st.markdown("### 📋 Parcours type")
st.markdown(
    """
    1. **📤 Upload** — exports Excel/CSV de factures fournisseurs et, en option, l'historique
       master data (changements IBAN, nom, SIREN, adresse).
    2. **🏦 Master data history** — diff IBAN / nom / dormant + détection 4-eyes manquant
       (le scénario fraude n°1 selon AFP 2026).
    3. **♊ Doublons** — fuzzy matching sur nom + bucket montant/date.
    4. **📏 Sous seuils** — détection de clusters juste sous seuil de validation.
    5. **🇫🇷 Sirene cross-check** — validation SIREN, statut, date de création vs factures.
    6. **⚖️ Sanctions / PEP** — OpenSanctions, Trésor FR, OFAC.
    7. **🤖 Anomalies ML** — Isolation Forest sur features comportementales.
    8. **🕸️ Anneaux de fraude** — graphe NetworkX `(employees ⟷ vendors)`.
    9. **🗂️ File d'investigation** — case management, statuts, clôture motivée.
    10. **📊 Synthèse / export** — risk score consolidé, export Excel + Parquet pour Power BI.
    11. **📜 Audit trail** — vérification d'intégrité du journal hash-chaîné.

    *🔢 Scoping orienté risque (Benford)* : disponible en outil ancillaire pour orienter
    l'échantillonnage JET / ISA 240, hors score consolidé par défaut.
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

        **Référentiels d'audit couverts** : ISA 240, AS 2401 (PCAOB), AICPA Audit Data Standards,
        Sapin 2 (art. 17), AFA, DORA (art. 28), AI Act (registre risque limité).
        Réutilisable pour Sapin 2 (cartographie), DORA (registre TIC), CSRD (datapoints).
        """
    )
