"""Page Méthodologie — pédagogie auditeur.

Mapping des 7 détecteurs sur les référentiels d'audit (ISA 240, AS 2401, AICPA),
explication des seuils Nigrini, références bibliographiques. Argument structurant
pour le CV : démontrer que l'outil n'est pas qu'un script ML mais bien aligné
sur les normes professionnelles.
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Méthodologie",
    surtitle="Gouvernance",
    kicker=("ISA 240, Sapin 2, AI Act, sources"),
)
st.caption("Mapping des détecteurs sur les référentiels professionnels.")

st.markdown(
    """
    Cet outil **complète** l'audit, il ne se substitue pas au jugement professionnel.
    Chaque alerte produite est un *signal faible* à investiguer, pas une preuve de fraude.
    Toute alerte doit être documentée par une revue manuelle (pièce justificative,
    entretien, contrôle de matérialité).
    """
)

st.divider()
st.subheader("🗺️ Mapping détecteurs ↔ référentiels")

st.markdown(
    """
    | Détecteur | ISA 240 | AS 2401 (PCAOB) | Sapin 2 | DORA |
    |---|---|---|---|---|
    | Benford (F1D / F2D / LD) | §32 (b) | §52 | — | — |
    | Doublons (exact + fuzzy) | §32 (b) | §52 | Art. 17 (4) | — |
    | Sous seuils | §32 (b) | §52 | Art. 17 (4) | — |
    | Sirene cross-check | — | — | Art. 17 (3) DD tiers | Art. 28 |
    | Isolation Forest | §32 (a) | §52 | — | — |
    | Anneaux NetworkX | §32 (b) | §52 | Art. 17 (4) | — |
    """
)

st.divider()
st.subheader("📐 Loi de Newcomb-Benford — seuils Nigrini")

st.markdown(
    """
    Le **MAD (Mean Absolute Deviation)** mesure l'écart moyen entre les fréquences
    observées et celles prédites par Benford. Les seuils suivants viennent de
    **Nigrini, *Benford's Law: Applications for Forensic Accounting, Auditing, and Fraud Detection***
    (Wiley, 2012) :

    | Test | Conforme | Acceptable | Marginalement non-conforme | Non-conforme |
    |---|---|---|---|---|
    | **F1D** (1 chiffre) | < 0,006 | 0,006 – 0,012 | 0,012 – 0,015 | > 0,015 |
    | **F2D** (2 chiffres) | < 0,0012 | 0,0012 – 0,0018 | 0,0018 – 0,0022 | > 0,0022 |
    | **LD** (dernier) | < 0,0008 | 0,0008 – 0,0012 | 0,0012 – 0,0016 | > 0,0016 |

    Le **F2D** est le test le plus diagnostique en audit : il offre la meilleure
    granularité sans tomber dans le bruit du dernier chiffre.
    """
)

st.divider()
st.subheader("⚖️ Sévérité — comment elle est calculée")

st.markdown(
    """
    Chaque finding porte une sévérité **LOW / MEDIUM / HIGH / CRITICAL** déterminée
    par le détecteur :

    - **CRITICAL** : signal qui ne peut pas être expliqué par le bruit
      (doublon strict, IBAN partagé entre vendors distincts, SIREN inexistant,
      fournisseur radié).
    - **HIGH** : signal fort nécessitant une revue (doublon fuzzy, cluster ≥ 3
      sous-seuils par fournisseur, fournisseur créé < 90 j avant 1ère facture,
      anneau de fournisseurs liés).
    - **MEDIUM** : signal isolé non clusterisé (sous-seuil unique, anomalie
      Benford F2D).
    - **LOW** : tendance générale à surveiller (Benford acceptable mais avec
      légère dérive).

    Le **risk_score 0-100** consolide tous les findings d'une facture via la
    formule :

    ```
    raw = Σ_finding (detector_weight × severity_multiplier × 60)
    score = min(100, raw)
    ```

    Les pondérations sont dans `src/p2p_fraud/scoring/weights.yaml`, **éditables**
    sans toucher au code.
    """
)

st.divider()
st.subheader("📊 Performance mesurée sur ground truth synthétique")

st.markdown(
    """
    Sur le dataset `medium_dataset` (10 000 factures avec 7 patterns de fraude
    étiquetés) :

    | Détecteur | Recall | Précision | F1 |
    |---|---|---|---|
    | Doublons | **1.000** | 0.30 | 0.47 |
    | Sous-seuils | **1.000** | 0.46 | 0.63 |
    | Anneaux IBAN (graph) | **1.000** | élevée | élevé |
    | Isolation Forest (outliers étiquetés) | 0.62 | — | — |

    **Pourquoi un Recall = 1.000 prime sur le F1 en audit** : le coût d'une fraude
    ratée (faux négatif) est très supérieur au coût d'investiguer une fausse
    alerte (faux positif). Les détecteurs sont calibrés *agressifs* ; la
    précision se règle ensuite via les sliders Streamlit ou `weights.yaml`.

    Les chiffres sont reproductibles : `pytest -s tests/`.
    """
)

st.divider()
st.subheader("📚 Références")

st.markdown(
    """
    - Nigrini, M. J. (2012). *Benford's Law: Applications for Forensic Accounting,
      Auditing, and Fraud Detection*. Wiley.
    - IFAC. **ISA 240** — *The Auditor's Responsibilities Relating to Fraud in
      an Audit of Financial Statements*.
    - PCAOB. **AS 2401** — *Consideration of Fraud in a Financial Statement Audit*.
    - AICPA. *Audit Data Standards* — modèles G/L Detail, Vendor Master, AP Trial Balance.
    - INSEE. **API Sirene v3.11** — référentiel officiel des entreprises françaises.
    - Loi n° 2016-1691 du 9 décembre 2016 (**Sapin 2**), art. 17.
    - Règlement (UE) **2022/2554 — DORA**, art. 28 (registre des prestataires TIC).
    - Liu, F. T., Ting, K. M., Zhou, Z. H. (2008). *Isolation Forest*. ICDM.
    """
)
