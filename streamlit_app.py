"""Page d'accueil — P2P Fraud Detective FR.

Streamlit charge automatiquement les pages depuis `pages/` (multipage app).
Cette page fait office de landing : positionnement, étapes, lien vers la page Upload.
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.streamlit_theme import init_page

init_page(
    title="P2P Fraud Detective FR",
    surtitle="Démonstrateur d'audit P2P / AML",
    kicker=(
        "Vendor & Payment Integrity FR-native — fraude P2P, master data, audit signé. "
        "Conçu pour ETI, cabinets d'audit, fonctions publiques et organismes de contrôle "
        "(DGFiP, Tracfin, IGF, Cour des comptes, CRC)."
    ),
    page_title="P2P Fraud Detective FR — Démonstrateur d'audit",
)

st.markdown(
    """
    **Pourquoi cet outil ?** 80 % de la fraude P2P passe par un changement d'IBAN
    ou un fournisseur fictif — pas par une anomalie statistique exotique. Cet outil
    surveille **l'historique du master data fournisseur**, croise les sources publiques
    françaises (Sirene, DECP, RBE, listes de sanctions UE / OFAC / Trésor FR) et produit
    une **piste d'audit signée SHA-256** alignée sur ISA 240, AS 2401, Sapin 2, LCB-FT
    et DORA art. 28.

    *Données : fictives ou issues de sources ouvertes. Outil de démonstration, hors production.*
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
        help="Sirene v3 (INSEE), DECP, RBE INPI (M2), OpenSanctions / Trésor FR / OFAC",
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
    1. **📤 Import des données** — exports Excel/CSV de factures fournisseurs et, en option,
       l'historique master data (changements IBAN, nom, SIREN, adresse).
    2. **🏦 Référentiel — historique** — diff IBAN / nom / dormant + détection 4-eyes manquant
       (le scénario fraude n°1 selon AFP 2026).
    3. **♊ Doublons** — fuzzy matching sur nom + bucket montant/date.
    4. **📏 Fractionnement / sous-seuils** — détection de clusters juste sous seuil de validation.
    5. **🇫🇷 Contrôle Sirene** — validation SIREN, statut, date de création vs factures.
    6. **⚖️ Sanctions & PEP** — OpenSanctions, Trésor FR, OFAC.
    7. **🤖 Anomalies (ML)** — Isolation Forest sur features comportementales.
    8. **🕸️ Anneaux de fraude** — graphe NetworkX `(employees ⟷ vendors)`.
    9. **🗂️ File d'investigation** — case management, statuts, clôture motivée.
    10. **📊 Synthèse — export** — risk score consolidé, export Excel + Parquet pour Power BI.
    11. **📜 Piste d'audit** — vérification d'intégrité du journal hash-chaîné.

    *🔢 Loi de Benford* : disponible en outil ancillaire pour orienter l'échantillonnage
    JET / ISA 240, hors score consolidé par défaut.
    """
)

st.divider()

if "df_invoices" in st.session_state:
    df = st.session_state["df_invoices"]
    st.success(
        f"✅ Dataset chargé : **{len(df):,}** factures · "
        f"{df['vendor_name'].nunique():,} fournisseurs"
    )
else:
    st.info(
        "👉 Aucun dataset chargé. Direction la page **📤 Import des données** dans la barre "
        "latérale, ou utilisez le générateur synthétique pour démarrer."
    )

with st.expander("ℹ️ À propos"):
    st.markdown(
        """
        **Auteur** : Ludovic Labeaut · [github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr)
        · MIT License

        **Référentiels d'audit couverts** : ISA 240, AS 2401 (PCAOB), AICPA Audit Data Standards,
        Sapin 2 (art. 17), AFA, DORA (art. 28), AI Act (registre risque limité).
        Réutilisable pour Sapin 2 (cartographie), DORA (registre TIC), CSRD (datapoints).
        """
    )
