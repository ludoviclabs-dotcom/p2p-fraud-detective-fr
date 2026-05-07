# Changelog

Toutes les évolutions notables sont documentées ici. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; le projet suit
[SemVer](https://semver.org/).

## [Unreleased]

### Ajouté
- ADR-0001 « Repositionnement produit » (Vendor & Payment Integrity FR-native).
- ADR-0002 « Benford rétrogradé » (scoping orienté risque, hors score consolidé par défaut).
- ADR-0003 « Streamlit façade démo, FastAPI prévu en M3 ».
- Sprint 1 — Master data history :
  - Modèle `VendorMasterEvent` (typé : IBAN, nom, adresse, SIREN, contact, statut, dormant).
  - Détecteur `master_data_changes` : changement d'IBAN sans 4-eyes, dormant réactivé,
    changement nom + IBAN même jour.
  - Génération synthétique d'événements master data avec ground truth `bec_iban_swap`,
    `dormant_reactivation`.
  - Page Streamlit `🏦 Master data history` avec timeline + diff coloré.
- Sprint 2 — Sanctions / PEP :
  - Client `sanctions_client` (snapshot CSV embarqué + interface OpenSanctions Yente
    optionnelle), normalisation accents/casse, scoring nominatif RapidFuzz.
  - Détecteur `sanctions` : flag `vendor_sanctioned` (CRITICAL) et `vendor_pep` (HIGH).
  - Page Streamlit `⚖️ Sanctions PEP`.
- Sprint 3 — Case management v0 :
  - Modèles `Case`, `CaseEvent`, statuts (NEW → CLOSED_*).
  - Audit log immutable chaîné par hash SHA-256 (vérification d'intégrité).
  - Service `cases.service` avec garde-fous (clôture motivée obligatoire,
    pas de modification post-clôture).
  - Page Streamlit `🗂️ File d'investigation` + `📜 Audit trail`.
- Sprint 4 — Reason codes FR + score waterfall :
  - Modèle `Contribution` ajouté à `RiskScore` (rétrocompat préservée).
  - Table `reason_codes` couvrant les 13 règles MVP, FR + citations
    référentielles (ISA 240, AFP 2026, AICPA, Sapin 2, LCB-FT).
  - `aggregate_findings_with_explanations()` produit waterfall ordonné
    par contribution + reason codes par finding.
  - `explainer.py` : `score_waterfall`, `explain_isolation_forest_row`
    (perturbation locale, sans dépendance shap), `top_contributions_summary`.
  - Page Streamlit `💡 Score Explorer` (waterfall Plotly + reason codes).
- Sprint 5 — Cockpit € exposition + fiche fournisseur 360° :
  - Service `exposure` : `compute_finding_exposure`, `aggregate_exposure_by_vendor`
    (déduplication par règle), `cockpit_summary` (KPIs CFO).
  - Service `vendor_360` : agrège profil + paiements + master data history
    + findings + sanctions, sans appel réseau.
  - Page `🎯 Cockpit` (position 0 dans la nav) : exposition totale et critique,
    cases ouverts/en retard SLA/critiques non assignés, top 10 fournisseurs.
  - Page `🪪 Fiche fournisseur 360°` : onglets Profil / Paiements / Master data /
    Findings, query param `?vendor_id=...` supporté.
- Sprint 6 — Presets ERP (SAP / Cegid / Sage / Oracle) :
  - 5 presets YAML embarqués (sap_lfa1_rbkp, cegid_loop, sage_x3, oracle_ap,
    generic_csv) avec mapping vers schéma canonique + parse dates/montants.
  - `auto_detect_preset()` : signature de colonnes (seuil 3) + fallback générique.
  - Onglet Streamlit *Connecteur ERP* dans la page Upload.
  - `pyproject.toml` : `package-data` pour inclure les YAML dans les wheels.
- Sprint 7 — Sécurité, RBAC, gouvernance IA :
  - `security.crypto` : `CryptoService` Fernet (AES-128-CBC + HMAC-SHA256),
    helpers `encrypt_iban` / `decrypt_iban` / `iban_masked`. Idempotent,
    rétrocompatible (texte clair toléré pour migration progressive).
  - `security.auth` : `AuthService` + `User` + `Role` (viewer/analyst/manager/admin),
    PBKDF2-SHA256 200k itérations, décorateur `@requires_role` programmatique
    avec mode strict via `P2P_FRAUD_AUTH_REQUIRED=1`.
  - `risk_engine` : nouveau paramètre `ml_enabled` (kill switch Isolation Forest)
    pour la page Gouvernance.
  - Templates compliance pré-remplis : DPIA (CNIL art. 35), registre AI Act
    (UE 2024/1689), registre traitements (RGPD art. 30).
  - Page `🛡️ Gouvernance` : classification AI Act + téléchargement docs +
    bascule ML + audit log avec vérification d'intégrité + tableau récap
    sécurité.

### Modifié
- README repositionné « Vendor & Payment Integrity FR-native ».
- `streamlit_app.py` : landing repositionnée, retrait de la mention « MindBridge ».
- `weights.yaml` : `benford = 0.0` par défaut, commentaire explicatif.
- `risk_engine.py` : filtre les findings `benford` avant agrégation si poids = 0.
- Page `2_🔢_Benford.py` renommée logiquement « Scoping orienté risque » (titre interne).

### Déprécié
- Le finding direct produit par Benford n'est plus pris en compte dans le score
  consolidé par défaut. La compatibilité est préservée via override explicite.
