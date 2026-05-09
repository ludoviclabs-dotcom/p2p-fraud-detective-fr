# Changelog

Toutes les évolutions notables sont documentées ici. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; le projet suit
[SemVer](https://semver.org/).

## [Unreleased]

### Ajouté
- *(prochains changements ici)*

## [0.3.0] - 2026-05-09

Refonte UX/UI institutionnelle (H1 Quick Wins + H2 Refonte intermédiaire).
Transformation « POC → démonstrateur expert » : thème clair navy/or, 6 sections
de navigation, Méthodologie complète, Gouvernance RGAA/RGPD, PDF stylé, ego-network.

### Ajouté — H1 Quick Wins
- Thème institutionnel clair navy/charcoal/or (`.streamlit/config.toml` intégral).
- Police Inter (OFL) + JetBrains Mono via `[[theme.fontFaces]]`.
- Module CSS centralisé (`streamlit_theme/css.py`) : variables design tokens, KPI
  stylés border-left navy, ribbon « DÉMONSTRATEUR · v0.3 » fixed top-right.
- Template Plotly `p2pfd` unifié (`streamlit_theme/plot.py`) — palette nav/or/alert,
  fond blanc, Inter — enregistré comme template par défaut.
- `page_header(title, surtitle, kicker)` remplace `st.title()` sur les 17 pages.
- Architecture `init_app()` / `init_page()` pour éviter le doublon `set_page_config`.
- `st.navigation` à 6 sections (loi de Miller).
- Cockpit refondu : mission + 4 KPI métiers + 6 raccourcis + demo cases seedés.
- Deep-links `?case_id`, `?invoice_id`, `?seq`.
- Wrappers `@st.cache_data` Sirene (TTL 1h) et sanctions (TTL 24h).
- 7 tests de régression theming.

### Ajouté — H2 Refonte intermédiaire
- **Méthodologie** : refonte complète (10 sections) — sources, seuils statistiques,
  calibration ML, métriques F1, limites/biais, schéma architecture, mapping référentiels.
- **Gouvernance** : déclaration RGAA 4.1 partielle, mention RGPD, tableau RBAC 4 rôles.
- **Audit trail `file.imported`** : SHA-256 fichier + n_rows journalisé à chaque upload.
- **streamlit-aggrid** sur File investigation et Fiche fournisseur 360°.
- **Ego-network interactif** (`streamlit-agraph`) — nœud central, rayon ≤ 2, 200 nœuds
  max, coloration sémantique, drill-down Fiche 360°.
- **Export PDF stylé** (`weasyprint` + Jinja2) — rapport A4 institutionnel.
- `packages.txt` pour apt deps weasyprint sur Streamlit Cloud.
- `@st.fragment` sur Score explorer.
- CI smoke test : `sleep 12`, curl health + root.
- `docs/accessibilite.md` : déclaration RGAA 4.1 partielle avec ratios de contraste.

### Modifié
- 17 pages migrées de `st.title()` vers `init_page(title, surtitle, kicker)`.
- Suppression de tous les `template="plotly_dark"` codés en dur.
- `streamlit_app.py` : pure dispatcher (`init_app()` + `st.navigation`).

### Dépendances ajoutées
- `streamlit-aggrid>=1.2.1`, `streamlit-agraph>=0.0.45`, `weasyprint>=62.0`, `jinja2>=3.1`

## [0.2.0] - 2026-05-07

Sprints 1 → 8 (technique). Repositionnement produit, master data history,
sanctions / PEP, case management + audit log, reason codes + waterfall +
explainer, cockpit € exposition, fiche fournisseur 360°, presets ERP, RBAC +
chiffrement IBAN, DPIA et registre AI Act, vectorisation des doublons et
benchmark reproductible, site MkDocs.

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
- Sprint 8 — Hardening technique :
  - ADR-0004 — vectorisation doublons fuzzy via `rapidfuzz.process.cdist`,
    gain ~20× sur 50 k factures.
  - ADR-0005 — politique de release SemVer + tags + GitHub Releases.
  - `scripts/bench_pipeline.py` : profilage end-to-end par étape.
  - `scripts/benchmark_f1.py` : F1 par détecteur sur ground truth.
  - `Makefile` : install, test, lint, format, bench, bench-f1, dataset-50k,
    docs.
  - 8 nouveaux tests d'intégration sécurité (RBAC × case service, tampering
    avancés sur audit log : suppression d'entrée, swap de hashes, prev_hash
    forgé, lifecycle complet multi-utilisateurs).
  - Site MkDocs Material (`mkdocs.yml`, `docs/index.md`, `docs/benchmark.md`),
    workflow GitHub Pages (`.github/workflows/docs.yml`).
  - `RELEASE.md` : processus pas à pas (bump, tag, GitHub Release, hotfix,
    pre-release).

### Modifié
- README repositionné « Vendor & Payment Integrity FR-native ».
- `streamlit_app.py` : landing repositionnée, retrait de la mention « MindBridge ».
- `weights.yaml` : `benford = 0.0` par défaut, commentaire explicatif.
- `risk_engine.py` : filtre les findings `benford` avant agrégation si poids = 0.
- Page `2_🔢_Benford.py` renommée logiquement « Scoping orienté risque » (titre interne).

### Déprécié
- Le finding direct produit par Benford n'est plus pris en compte dans le score
  consolidé par défaut. La compatibilité est préservée via override explicite.

## [0.1.0] - 2026-05-01

Première version publique : 7 détecteurs (Benford, doublons fuzzy, sous-seuils,
Sirene v3, Isolation Forest, anneaux NetworkX, risk score consolidé), Streamlit
multipage, dataset synthétique étiqueté, mapping ISA 240 / Sapin 2 / DORA.
