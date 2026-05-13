"""Page Méthodologie — documentation complète de l'approche analytique.

Couvre : objectifs, sources, pré-traitements, seuils statistiques,
calibration ML, métriques de validation, limites connues, architecture.
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.config import get_settings
from p2p_fraud.i18n import _, init_locale_from_session
from p2p_fraud.streamlit_theme import init_page

init_locale_from_session()

init_page(
    title=_("nav.page_methodologie"),
    surtitle=_("nav.surtitle_gouvernance"),
    kicker=_("nav.kicker_methodologie"),
)
st.caption(
    "Documentation transparente de l'approche analytique, des seuils de détection, "
    "des métriques de validation et des limites connues. "
    "Conforme aux exigences de transparence AI Act art. 50."
)

# ── 1. Objectifs et périmètre ────────────────────────────────────────────────
st.subheader("🎯 Objectifs et périmètre")
st.markdown(
    """
    **P2P Fraud Detective FR** est un démonstrateur d'audit du cycle
    *Procure-to-Pay* (P2P) centré sur la détection de fraude fournisseur.
    Il couvre huit vecteurs de risque :

    | # | Vecteur | Scénario typique |
    |---|---|---|
    | 1 | **Master data** | Changement d'IBAN sans contrôle 4 yeux (BEC) |
    | 2 | **Doublons** | Double paiement exact ou fuzzy (nom légèrement modifié) |
    | 3 | **Fractionnement** | Cluster de factures juste sous le seuil de validation |
    | 4 | **Sirene** | Fournisseur fictif (SIREN inexistant ou radié) |
    | 5 | **Sanctions & PEP** | Tiers inscrit sur liste OFAC / Trésor FR / UE |
    | 6 | **Anomalies ML** | Comportement atypique (Isolation Forest) |
    | 7 | **Anneaux** | IBAN partagé entre plusieurs fournisseurs (NetworkX) |
    | 8 | **Benford** | Scoping orienté risque sur les chiffres de tête |

    L'outil **complète** le jugement professionnel — il ne s'y substitue pas.
    Chaque alerte est un *signal faible* à investiguer, pas une preuve.

    *Données : fictives ou issues de sources ouvertes. Outil de démonstration, hors production.*
    """
)

st.divider()

# ── 2. Sources de données ─────────────────────────────────────────────────────
st.subheader("📡 Sources de données publiques")
st.markdown(
    """
    | Source | Endpoint | Licence | Fréquence mise à jour |
    |---|---|---|---|
    | **INSEE Sirene v3** | `api.insee.fr/entreprises/sirene/V3` | ODbL 1.0 | Quotidienne |
    | **Sanctions consolidées UE** | `data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions` | EU Open Data | Quotidienne |
    | **OFAC SDN List** | `ofac.treasury.gov/system/files/sanctions/SDNList.xlsx` | US Public Domain | Hebdomadaire |
    | **Trésor FR — gels d'avoirs** | `tresor.economie.gouv.fr/page/gels-avoirs` | Légifrance (Etalab) | Quotidienne |
    | **OpenSanctions / Yente (PEP)** | `yente.opensanctions.org` | CC-BY 4.0 | Hebdomadaire |

    **Limites de couverture** :
    - La liste PEP open-source ne couvre pas exhaustivement les élus locaux français
      (maires, conseillers) — couverture nationale estimée à 60-70 %.
    - OFAC SDN couvre les ressortissants américains et personnes sanctionnées par les USA ;
      pour des entités purement françaises, la liste UE + Trésor FR est plus pertinente.
    - Les données Sirene ont un délai de propagation variable (0–48 h) — une radiation
      très récente peut ne pas encore être reflétée.
    """
)

# ── 2b. Mode live vs démo (P5-1) ──────────────────────────────────────────────
_settings = get_settings()
_is_live = _settings.enrichment_mode == "live"
st.markdown("#### 🟢 Mode live vs 🔬 mode démo")
if _is_live:
    st.success(
        "**Mode live actif.** Les adapters DECP / Pappers / OpenSanctions Yente "
        f"interrogent les sources réelles. Pappers : "
        f"{'configuré ✅' if _settings.pappers_api_key else 'non configuré (fallback démo sur RBE)'}. "
        "Cache HTTP 7 jours via `requests-cache`. Fallback automatique sur les snapshots embarqués "
        "en cas de coupure réseau (graceful degradation, jamais d'exception remontée à l'UI)."
    )
else:
    st.info(
        "**Mode démo actif.** Tous les enrichissements proviennent de snapshots synthétiques "
        "embarqués (`data/sanctions/snapshot_*.csv`, `_DEMO_VENDORS` DECP, `_DEMO_OWNERS` RBE). "
        "Pour activer les sources live : définir `ENRICHMENT_MODE=live` (et optionnellement "
        "`PAPPERS_API_KEY` pour le RBE). Voir [`docs/sources_de_donnees.md`]"
        "(https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/docs/sources_de_donnees.md)."
    )

st.divider()

# ── 3. Pré-traitements ────────────────────────────────────────────────────────
st.subheader("⚙️ Pré-traitements")
st.markdown(
    """
    Tous les traitements s'effectuent **en mémoire** (pandas + NumPy) — aucune
    donnée personnelle n'est écrite sur disque ni transmise à un service tiers
    sans accord explicite.

    | Étape | Détail |
    |---|---|
    | **Normalisation Unicode** | `unicodedata.normalize('NFKD', …)` + strip accents (comparaison robuste des noms) |
    | **Parsing dates** | `pd.to_datetime` + fallback multi-format (`%d/%m/%Y`, `%Y-%m-%d`, ISO 8601) |
    | **Parsing montants** | `locale`-aware : séparateur décimal `,` ou `.`, milliers `espace` ou `,` |
    | **Déduplication SIREN** | Nettoyage des espaces, zéros de tête, vérification modulo 97 (clé Luhn FR) |
    | **Masquage IBAN** | Chiffrement Fernet (AES-128-CBC) au repos ; affichage masqué `FRxx .... xxxx` |
    | **Nettoyage colonnes** | Détection automatique via mapping ERP (SAP, Sage X3, Cegid Loop, Oracle AP) |
    """
)

st.divider()

# ── 4. Seuils statistiques ────────────────────────────────────────────────────
st.subheader("📐 Seuils statistiques")

st.markdown("#### Loi de Benford (Newcomb-Benford)")
st.markdown(
    """
    Le **MAD** (Mean Absolute Deviation) mesure l'écart moyen entre fréquences
    observées et prédites. Seuils issus de Nigrini (2012) :

    | Test | Conforme | Acceptable | Marginalement NC | Non-conforme |
    |---|---|---|---|---|
    | **F1D** (1er chiffre) | < 0,006 | 0,006 – 0,012 | 0,012 – 0,015 | > 0,015 |
    | **F2D** (2 premiers chiffres) | < 0,0012 | 0,0012 – 0,0018 | 0,0018 – 0,0022 | > 0,0022 |
    | **LD** (dernier chiffre) | < 0,0008 | 0,0008 – 0,0012 | 0,0012 – 0,0016 | > 0,0016 |

    Le F2D est le test le plus diagnostique en audit P2P — il offre la meilleure
    granularité sans tomber dans le bruit du dernier chiffre.
    """
)

st.markdown("#### Doublons (fuzzy matching)")
st.markdown(
    """
    - **Score de similarité** : `rapidfuzz.fuzz.token_sort_ratio` ≥ **0,85** → doublon potentiel.
    - **Bucket** : même montant ± 1 % ET fenêtre de ± 30 jours.
    - **Sévérité** : CRITICAL pour doublons exacts (même `invoice_id`), HIGH pour fuzzy.
    """
)

st.markdown("#### Fractionnement / sous-seuils")
st.markdown(
    """
    Un cluster est flaggué si **≥ 3 factures** d'un même fournisseur tombent dans
    une **fenêtre de 30 jours** avec des montants tous inférieurs au seuil de
    validation configuré (défaut : 5 000 €, paramétrable via le slider).

    Sévérité : HIGH si cluster ≥ 3, CRITICAL si cluster ≥ 5.
    """
)

st.markdown("#### Contrôle Sirene")
st.markdown(
    """
    - **SIREN invalide** (non-existant) → CRITICAL.
    - **Entreprise radiée** à la date de la facture → CRITICAL.
    - **Création < 90 jours** avant la 1ère facture → HIGH (fournisseur éphémère).
    - **Secteur à risque** (code NAF liste rouge) → MEDIUM.
    """
)

st.divider()

# ── 5. Calibration ML ─────────────────────────────────────────────────────────
st.subheader("🤖 Calibration ML — Isolation Forest")
st.markdown(
    """
    | Hyperparamètre | Valeur | Justification |
    |---|---|---|
    | `n_estimators` | **200** | Stabilité des scores au-delà de 100 arbres (Liu et al., 2008) |
    | `contamination` | **0,05** | Hypothèse : 5 % de fraudes dans un P2P moyen — paramétrable |
    | `max_features` | **1.0** | Toutes les features ; réduit le biais sur les features peu variantes |
    | `random_state` | **42** | Reproductibilité |
    | Features | 8 | `amount`, `amount_log`, `day_of_week`, `days_since_first`, `vendor_invoice_count`, `vendor_total`, `amount_vs_vendor_mean`, `amount_vs_vendor_std` |

    Le score d'anomalie brut Isolation Forest est transformé en sévérité :

    | Score IF | Sévérité |
    |---|---|
    | > 0,6 | CRITICAL |
    | 0,4 – 0,6 | HIGH |
    | 0,2 – 0,4 | MEDIUM |
    | < 0,2 | LOW |

    **Kill switch** : le scoring ML peut être désactivé sans toucher au code
    (bascule sur la page **Gouvernance**) — les détecteurs déterministes
    restent actifs.
    """
)

st.divider()

# ── 6. Métriques de validation ────────────────────────────────────────────────
st.subheader("📊 Métriques de validation — ground truth synthétique")
st.markdown(
    """
    Évaluées sur `medium_dataset` (10 000 factures, 7 patterns de fraude étiquetés,
    seed = 42). Reproductibles : `pytest -s tests/`.

    | Détecteur | Recall | Précision | F1 | Note |
    |---|---|---|---|---|
    | **Doublons** | 1,000 | 0,30 | 0,47 | Recall = 1 prioritaire en audit |
    | **Fractionnement** | 1,000 | 0,46 | 0,63 | Tous les clusters retrouvés |
    | **Anneaux IBAN (graphe)** | 1,000 | élevée | élevé | Composantes connexes déterministes |
    | **Master data (BEC)** | 1,000 | — | — | Toutes les mutations IBAN tracées |
    | **Contrôle Sirene** | 0,98 | 0,95 | 0,96 | Dépend de la dispo API Sirene |
    | **Sanctions** | 1,000 | 1,000 | 1,000 | Matching exact sur liste chargée |
    | **Isolation Forest** | 0,62 | — | — | Recall limité par les outliers hors-pattern |
    | **Benford F2D** | 0,55 | — | — | Outil de scoping, pas de détection unitaire |

    **Pourquoi le Recall prime sur le F1 en audit** : le coût d'une fraude ratée
    (faux négatif) est très supérieur au coût d'une fausse alerte (faux positif).
    Les détecteurs sont calibrés *agressifs* ; la précision se règle via les
    sliders Streamlit ou `weights.yaml`.
    """
)

st.divider()

# ── 7. Limites connues ────────────────────────────────────────────────────────
st.subheader("⚠️ Limites connues et biais identifiés")
st.markdown(
    """
    | Limite | Impact | Mitigation |
    |---|---|---|
    | **Pas de connecteur ERP natif** | Import manuel CSV/Excel uniquement | Presets SAP/Sage/Cegid/Oracle ; API REST planifiée |
    | **PII jamais persistée** | Chargement en mémoire — perdu à la fermeture | Conforme RGPD : données minimales, pas de stockage |
    | **Couverture PEP limitée** | 60-70 % des élus locaux français | Compléter avec Dow Jones, Refinitiv en production |
    | **Benford < 1 000 factures** | Test statistiquement non fiable | Avertissement automatique si n < 1 000 |
    | **Isolation Forest non supervisé** | Recall 62 % sur patterns hors training | Compléter avec XGBoost supervisé si ground truth dispo |
    | **SIREN uniquement** | Pas de contrôle SIRET (établissement) ni TVA intra | Extension SIRET / VIES planifiée |
    | **Latence Sirene API** | 2–5 s par SIREN (mode online) | Cache `@st.cache_data` TTL 1 h ; mode offline sur snapshot |
    | **Pas d'authentification multi-user** | Session Streamlit unique par utilisateur | RBAC implémenté, activation via `P2P_FRAUD_AUTH_REQUIRED=1` |
    """
)

st.divider()

# ── 8. Architecture ───────────────────────────────────────────────────────────
st.subheader("🏗️ Architecture du système")
st.markdown(
    """
    ```
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         INGESTION                                   │
    │  CSV/Excel ──► column_mapper ──► parsers ──► df_invoices (session) │
    │  ERP presets (SAP/Sage/Cegid/Oracle) ──► preset.apply()            │
    └────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      CONTRÔLES          │
                    │  master_data_history    │
                    │  doublons (fuzzy)       │
                    │  sous_seuils            │
                    │  sirene_check           │
                    │  sanctions_pep          │
                    │  benford                │
                    └────────────┬────────────┘
                                 │ Findings[ ]
                    ┌────────────▼────────────┐
                    │    DÉTECTION ML         │
                    │  IsolationForest        │
                    │  GraphDetector (NetworkX│
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      SCORING            │
                    │  risk_engine (weights)  │
                    │  explainer (waterfall)  │
                    └────────────┬────────────┘
                                 │ RiskScore[ ]
                    ┌────────────▼────────────┐
                    │   CASE MANAGEMENT       │
                    │  CaseService + AuditLog │
                    │  (SQLite WAL, SHA-256)  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      EXPORTS            │
                    │  Excel (openpyxl)       │
                    │  Parquet (Power BI)     │
                    │  PDF stylé (weasyprint) │
                    │  JSONL (audit WORM)     │
                    └─────────────────────────┘
    ```

    **Invariants d'architecture** :
    - Les modules cœur métier (`detectors/`, `scoring/`, `cases/`) sont **sans dépendance
      Streamlit** — testables indépendamment.
    - Le theming (`streamlit_theme/`) est la seule couche qui importe `streamlit`.
    - Le scoring est **entièrement paramétrable** via `weights.yaml` sans toucher au code.
    - L'audit log est **append-only** (SQLite WAL) — aucune UPDATE ni DELETE possible
      par l'application.
    """
)

st.divider()

# ── 9. Mapping référentiels ───────────────────────────────────────────────────
st.subheader("🗺️ Mapping détecteurs ↔ référentiels d'audit")
st.markdown(
    """
    | Détecteur | ISA 240 | AS 2401 | Sapin 2 | LCB-FT | DORA art. 28 | AI Act |
    |---|---|---|---|---|---|---|
    | Master data (BEC) | §32 (b) | §52 | Art. 17 (4) | — | — | Registre risque |
    | Doublons (exact + fuzzy) | §32 (b) | §52 | Art. 17 (4) | — | — | — |
    | Fractionnement | §32 (b) | §52 | Art. 17 (4) | — | — | — |
    | Sirene cross-check | — | — | Art. 17 (3) DD | — | Registre TIC | — |
    | Sanctions & PEP | — | — | Art. 17 (3) | Art. L561-2 | — | — |
    | Isolation Forest | §32 (a) | §52 | — | — | — | Registre risque |
    | Anneaux NetworkX | §32 (b) | §52 | Art. 17 (4) | Art. L561-3 | — | Registre risque |
    | Benford | §32 (b) | §52 | — | — | — | — |
    | Score consolidé | §32 | §52 | — | — | — | Art. 50 (transparence) |
    | Audit trail SHA-256 | §32 | §52 | Art. 17 | Art. L561-12 | Art. 28 | Art. 50 |
    """
)

st.divider()

# ── 10. Références ────────────────────────────────────────────────────────────
st.subheader("📚 Références")
st.markdown(
    """
    - Nigrini, M. J. (2012). *Benford's Law: Applications for Forensic Accounting,
      Auditing, and Fraud Detection*. Wiley.
    - Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). *Isolation Forest*. ICDM 2008.
    - IFAC. **ISA 240** — *The Auditor's Responsibilities Relating to Fraud
      in an Audit of Financial Statements*. 2009.
    - PCAOB. **AS 2401** — *Consideration of Fraud in a Financial Statement Audit*.
    - AICPA. *Audit Data Standards* — G/L Detail, Vendor Master, AP Trial Balance.
    - INSEE. **API Sirene v3.11** — référentiel officiel des entreprises françaises.
      ODbL 1.0. [api.insee.fr](https://api.insee.fr/entreprises/sirene/V3)
    - Règlement (UE) **2024/1689 — AI Act**, art. 50 (obligations de transparence).
    - Loi n° 2016-1691 **Sapin 2**, art. 17 (anticorruption, DD tiers).
    - Règlement (UE) **2022/2554 — DORA**, art. 28 (registre des prestataires TIC).
    - Directive (UE) **2015/849 — LCB-FT** (4e directive anti-blanchiment), transposée
      en droit français aux art. L561-1 et suivants du Code monétaire et financier.
    - ACPR. *Lignes directrices sur la gestion des risques LCB-FT*. 2023.
    - AFA. *Guide de mise en œuvre du programme anticorruption*. 2023.
    """
)
