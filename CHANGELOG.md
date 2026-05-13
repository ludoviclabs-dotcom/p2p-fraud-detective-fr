# Changelog

Toutes les évolutions notables sont documentées ici. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; le projet suit
[SemVer](https://semver.org/).

## [Unreleased]

## [0.6.0] - 2026-05-13

Migration v2 — frontend Next.js 15 livré en 8 phases sur une session de
travail. Le code Streamlit (legacy v0.5.0) reste intact et fonctionnel ;
le nouveau frontend Next.js sur Vercel + FastAPI étendu sur HF Spaces
constitue la cible v2 sans dette de migration.

### Added

- **Monorepo pnpm workspace** : `apps/web/` (Next.js 15) + `packages/shared-types/` (TS depuis OpenAPI) + backend Python inchangé
- **Frontend Next.js 15** App Router + Tailwind v4 + React 19 + Turbopack — **26 routes** :
  - Pilotage : `/`, `/dashboard`, `/tour` (5 étapes), `/sandbox` (5 scénarios), `/cases` (bulk ops), `/alerts` (polling 5s), `/collab`
  - Données : `/upload` (drag-drop streaming), `/master-history` (timeline), `/sirene`
  - Contrôles : `/benford`, `/duplicates`, `/structuring`, `/sanctions`, `/decp-rbe`
  - ML : `/anomalies` (Recharts scatter), `/rings` (sigma.js WebGL), `/score` (waterfall), `/findings`
  - Investigation : `/vendors`, `/vendors/[id]` (sparkline + LLM streaming), `/exports` (PDF + CSV), `/audit` (Ed25519 verify)
  - Gouvernance : `/methodology`, `/governance`
- **i18n FR/EN** : `LocaleProvider` + sélecteur 🇫🇷/🇬🇧 sidebar + persistance localStorage
- **15 nouveaux endpoints API v1** typés Pydantic (`/api/v1/*`) :
  - Cockpit : `/cockpit/kpis`, `/cockpit/top-vendors`
  - Findings/Vendors : `/findings`, `/vendors/{id}`, `/vendors/{id}/timeline`
  - Cases : `/cases`, `/cases/{id}/comment`, `/cases/bulk/assign`, `/cases/bulk/close`
  - Audit : `/audit`, `/audit/verify`
  - Exports : `/exports/dossier.pdf` (weasyprint streaming)
  - LLM : `/llm/narrative` (SSE streaming Claude)
  - Graph : `/rings` (NetworkX → JSON nodes/edges)
  - Sandbox : `/scenarios` (5 scénarios métadonnées)
- **Composants UI** : `<Button>` (5 variants × 3 sizes via cva), `<Card>`, `<Badge>` + `<SeverityBadge>`, `<Input>`, `<ControlPage>` (réutilisable pour 5 contrôles statistiques)
- **OIDC proxy** Next.js `/api/auth/[...slug]` → FastAPI `/oidc/*`
- **Multipart streaming proxy** `/api/uploads` (Route Handler `runtime: "nodejs"`, body streamé via `duplex: "half"`)
- **TypeScript types auto-générés** depuis OpenAPI (1900+ lignes) — garde-fou contractuel bout-en-bout
- **Visualisations** : Recharts (sparklines, scatter, waterfall) + sigma.js + graphology + ForceAtlas2 (anneaux WebGL) + composants SVG custom
- **LLM streaming** : SSE bout-en-bout `POST /api/v1/llm/narrative` → React state → UI live (cursor pulsant)
- 8 docs/migration-v2-phase-{0-8}.md détaillant chaque phase

### Changed

- README et docs/ enrichis pour la coexistence Streamlit (legacy) + Next.js (v2)
- Backend FastAPI : versions des SDKs ajustées, OpenAPI exporté à 27 endpoints

### Backward compatibility

- Streamlit Cloud (`streamlit_app.py` + `pages/*.py`) **inchangé et toujours fonctionnel**.
- 274 → 370 tests Python verts (+96 sur Phase 5 + nouveaux endpoints v1).
- Tous les endpoints API existants (`/detect`, `/score`, `/cases`, `/oidc/*`) conservés sans rupture.

### Migration v0.5 → v0.6

```bash
# 1. Pas de breaking change sur le backend Python — pas d'action requise
pip install -e .

# 2. Pour utiliser le nouveau frontend Next.js (optionnel)
pnpm install
cd apps/web
cp .env.example .env.local
# Définir NEXT_PUBLIC_API_URL = URL FastAPI
pnpm dev

# 3. Déploiement production
# - Backend : Hugging Face Spaces (Docker, gratuit, 16 GB RAM)
# - Frontend : Vercel (root: apps/web/, env: NEXT_PUBLIC_API_URL)
# - DB : Neon free (Postgres 0.5 GB scale-to-zero)
```

### État cible (production pilote ETI)

```
Vercel (Next.js v2) → REST → HF Spaces (FastAPI Python)
                              → Neon (PostgreSQL)
                              → OpenSanctions Yente / DECP / Pappers
Streamlit Cloud (legacy v0.5) reste en service sur sous-domaine
                                 distinct jusqu'à confirmation pilote
```



## [0.5.0] - 2026-10-31

Phase 5 — Commercialisation B2B : 5 PRs livrées (P5-1 → P5-5). Sources live
réglementaires, sandbox interactive, intégration B2B (webhook + SDK),
bilinguisme FR/EN, conformité prouvée par signatures Ed25519.

### Added

- **P5-1 — Sources live DECP / Pappers / OpenSanctions Yente**
  - `enrichment/decp_live.py` adapter `data.economie.gouv.fr/decp-v3` (ODbL, cache 7j)
  - `enrichment/pappers_live.py` RBE via `api.pappers.fr`
  - `enrichment/yente_client.py` sanctions consolidées
  - `Settings.enrichment_mode = "demo" | "live"` + fallback graceful
  - `docs/sources_de_donnees.md`
- **P5-2 — Sandbox + comparatif SOTA + 3 cas clients**
  - `pages/20_🎮_Sandbox.py` (5 scénarios déterministes)
  - `synthetic/scenarios.py` (`load_scenario(name)`)
  - `docs/comparatif_sota.md` vs MindBridge / PwC / KPMG / Deloitte / SAS / NICE / Quantexa
  - `docs/cas_clients/` (ETI 800M€, foncière 1.2Md€, CRC Auvergne)
- **P5-3 — Webhook CloudEvents + SDK Makefile + bulk ops**
  - `webhooks/dispatcher.py` HMAC-SHA256 + tenacity retry
  - `webhooks/events.py` 8 events (`case.*` + `webhook.test`)
  - Endpoint `POST /webhook/test`
  - Bulk ops AgGrid (assign / close / export)
  - Makefile `openapi-export` + `sdk-python` + `sdk-typescript`
- **P5-4 — i18n FR/EN + recherche globale + sparkline**
  - `i18n/__init__.py` + `locales/{fr,en}.yaml` (~80 clés parité parfaite)
  - Sélecteur 🇫🇷 FR / 🇬🇧 EN sidebar
  - Recherche globale Cockpit
  - Sparkline trend 30j Vendor 360°
- **P5-5 — Ed25519 + tests E2E AppTest + coverage gate**
  - `security/signing.py` (PyNaCl, génération + sign + verify)
  - Audit log colonne `signature` nullable (backward-compat v0.4)
  - Endpoint `GET /security/public-key`
  - `tests/e2e/test_pages_apptest.py` (6 smoke AppTest)
  - `pyproject.toml` `[tool.coverage.report] fail_under = 75`
  - `docs/conformite_signatures.md`

### Changed

- `Settings` étendu : `enrichment_mode`, `pappers_api_key`, `yente_base_url`, `webhook_url`, `webhook_secret`, `webhook_timeout`, `p2pfd_ed25519_private_key`
- `CaseService.__init__(webhook_dispatcher=...)` optionnel
- `AuditLog.__init__(signer=...)` optionnel
- `AuditLog.verify_chain(public_key_b64=...)` vérifie aussi les signatures
- Sandbox = 2e entrée de la section 🧭 Pilotage

### Hors scope volontaire (reportés v0.6)

- WORM S3 archivage 10 ans (nécessite budget AWS — documenté roadmap)
- Backup PostgreSQL automatique Glacier (idem)
- Landing Astro statique GitHub Pages
- 8 vidéos Loom (scripts texte dans `docs/cas_clients/`)

### Migration v0.4 → v0.5

```bash
# 1. Nouvelle dépendance obligatoire
pip install "pynacl>=1.5"

# 2. Variables d'env optionnelles (mode démo conservé si non définies)
export ENRICHMENT_MODE=live
export PAPPERS_API_KEY=pk_live_xxx
export WEBHOOK_URL=https://siem.entreprise.fr/p2pfd
export WEBHOOK_SECRET=shared-hmac-secret
export P2PFD_ED25519_PRIVATE_KEY=$(python -c "from p2p_fraud.security.signing import Ed25519Signer; print(Ed25519Signer.generate().private_key_b64)")
```

- Colonne `audit_log.signature` ajoutée automatiquement au boot (ALTER TABLE défensif).
- Pas de breaking change API : tous les endpoints v0.4 restent compatibles.

## [0.4.0] - 2026-08-31

Phase 4 — Hardening foundation : 6 PRs livrées (P4-1 → P4-6) pour passer de
démonstrateur à pilote ETI déployable. Settings centralisés, SQLAlchemy multi-
backend, OIDC end-to-end, scheduler externalisé, observabilité Sentry +
Prometheus, release workflow GHCR.

### Migration guide v0.3 → v0.4

**Variables d'environnement** (nouvelles, optionnelles sauf mention) :
- `DATABASE_URL` — bascule en PostgreSQL en production (SQLite reste défaut).
- `OIDC_SESSION_SECRET` — **obligatoire si OIDC est actif** (≥ 32 octets aléatoires).
- `OIDC_POST_LOGIN_URL` — URL absolue de redirection post-login (défaut `/`).
- `SENTRY_DSN` — observabilité erreurs (opt-in).
- `LOG_FORMAT=json` recommandé en prod (Cloud Logging / Loki compatible).

**Schéma DB** : `alembic upgrade head` recommandé avant promotion v0.4 (aucune
nouvelle migration mais autogenerate est désormais bindé sur `Base.metadata`).

**Logs** : sortie sur `stderr` (12-factor canonique) au lieu de stdout. Ajuster
les pipelines de collecte si nécessaire.

**API FastAPI** : nouveaux endpoints `/oidc/login`, `/oidc/callback`,
`/oidc/logout`, `/oidc/me`, `/metrics`. `/health` retourne désormais `version=0.4.0`.

### Ajouté — Phase 4 / PR P4-6 (Observabilité + release)
- `sentry-sdk[fastapi]>=2.0` activé conditionnellement via `SENTRY_DSN`
  (`traces_sample_rate=0.1`, `send_default_pii=False`, release tag automatique).
- `prometheus-fastapi-instrumentator>=7.0` expose `/metrics` (latency p50/p95/p99,
  request rate, status codes par endpoint). Exclu de l'OpenAPI public.
- `.github/workflows/release.yml` — déclenché sur tag `v*.*.*` :
  - Build matrix des 3 images (api / streamlit / scheduler) avec OCI labels.
  - Push sur GHCR (`ghcr.io/<owner>/<repo>-{api,streamlit,scheduler}:<tag>`).
  - GitHub Release auto avec extraction de la section CHANGELOG.
- `tests/load/api_smoke.js` — k6 sur `/health`, `/detect`, `/score` ; SLO p95 < 500ms,
  error rate < 1% @ 50 VUs / 60s.
- `tests/load/k6.dockerfile` — image k6 reproductible (`grafana/k6:0.55.0`).
- `docs/runbook.md` — incidents communs (API 5xx, OIDC outage, scheduler stuck,
  alertes non livrées, latence dégradée, JWKS rotation).
- `docs/oidc-setup.md` — guide pas-à-pas Entra ID + Auth0 + Keycloak.

### Modifié — Phase 4 / PR P4-6
- `__init__.py`, `pyproject.toml`, `api/main.py` : bump 0.3.0 → 0.4.0.

### Ajouté — Phase 4 / PR P4-5 (Cockpit + governance)
- Cockpit : 4 sparklines tendance 30 jours (cases créés/clôturés/critiques,
  activité audit trail), Plotly minimaliste fill="tozeroy".
- Page Gouvernance — section "⚖️ Pondérations" : éditeur YAML inline pour
  `scoring/weights.yaml` avec validation atomique + audit log `weights.updated`.
- Page Gouvernance — section "🗑️ RGPD art. 17" : purge persistante par
  `created_by` avec double confirmation + audit log `rgpd.erasure`.
- `scoring/weights_editor.py` — `validate_weights_yaml`, `write_weights`
  (sans dep Streamlit, testable).
- `CaseService.purge_user_data(target_user, *, actor) -> int`.
- 18 tests (13 weights validator + 5 RGPD purge).

### Ajouté — Phase 4 / PR P4-4 (Scheduler externalisé)
- `scheduler/__main__.py` — CLI 3 modes : `--once`, `--daily HH:MM`, `--health`.
  Provider de factures pluggable (CSV/Parquet/Excel via `--invoices`).
- `scheduler/runner.py` — `run_detection_once()` réentrante + `DetectionRunResult`.
- Retry tenacity sur les canaux (3 essais, 1s→2s→4s, erreurs réseau uniquement).
- `Dockerfile.scheduler` — image ~120 MB sans Streamlit/FastAPI/weasyprint.
- `docs/deployment-cloud-run.md` — runbook pilote ETI < 1h.
- `docker-compose.yml` : service `scheduler` ajouté.
- 15 tests CLI/runner.

### Modifié — Phase 4 / PR P4-4
- `logging_setup.py` : handlers vers `stderr` (12-factor).
- Fix import cassé pré-existant `detect_threshold_splits` → `detect_under_threshold`.

### Ajouté — Phase 4 / PR P4-3 (OIDC end-to-end)
- `security/jwt_validator.py` — `JWKSCache` TTL 1h + `validate_id_token` via
  python-jose (signature RS256, iss/aud/exp/nonce, leeway NTP).
- `security/session_store.py` — sessions HMAC-SHA256 itsdangerous, cookies
  httponly/samesite=lax/secure (compatible scale-out, pas de state serveur).
- `security/oidc_client.py` — `DiscoveryCache` + `exchange_code_for_tokens()`.
- `api/oidc_router.py` — 4 endpoints (`/oidc/login`, `/callback`, `/logout`, `/me`).
- 9 tests (login redirect, callback succès, state mismatch CSRF, nonce replay,
  signature invalide, /me 401/200, logout, 503).

### Modifié — Phase 4 / PR P4-3
- `streamlit_app.py` : bouton sidebar **🔑 Se connecter (OIDC)**.
- `pages/19_Collaboration.py` : interroge `/oidc/me`, affiche claims + rôle RBAC.
- `api/main.py` : monte `oidc_router`. Fix imports cassés pré-existants.

### Ajouté — Phase 4 / PR P4-1 (Hardening foundation)
- `p2p_fraud.config.Settings` (pydantic-settings) — singleton de configuration
  applicative qui centralise les 13 variables d'environnement précédemment
  dispersées dans 6 modules. Noms historiques conservés pour rétrocompat
  (`SIRENE_API_TOKEN`, `OIDC_*`, `FRAUD_*`, `P2P_FRAUD_*`).
- `p2p_fraud.logging_setup.configure_logging()` — configuration centralisée du
  root logger avec format `text` ou `json` (python-json-logger) selon
  `LOG_FORMAT`. Idempotent, appelable depuis Streamlit, FastAPI, scheduler CLI.
- `tests/test_config.py` — 10 tests unitaires (rétrocompat env vars, parsing
  case-insensitive, idempotence du logging, fallback gracieux JSON).
- `.env.example` étendu avec toutes les variables connues + commentaires.
- Dépendances : `pydantic-settings>=2.0`, `python-json-logger>=2.0`.

### Modifié — Phase 4 / PR P4-1
- `src/p2p_fraud/enrichment/sirene_client.py`, `llm/narrative_generator.py`,
  `api/main.py`, `security/oidc.py`, `security/auth.py`, `security/crypto.py`
  — remplacement des `os.environ.get(...)` par `get_settings()`.
- `streamlit_app.py` et `api/main.py` appellent `configure_logging()` au boot.

### Préparé — Phase 4
- Champs `Settings.database_url`, `slack_webhook_url`, `teams_webhook_url`,
  `sentry_dsn` exposés en amont des PRs P4-2 / P4-6.

### Ajouté — Phase 4 / PR P4-2 (SQLAlchemy + PostgreSQL switch)
- `src/p2p_fraud/persistence/` — couche persistance SQLAlchemy 2.0 :
  - `models.py` : ORM `CaseRow`, `CaseEventRow`, `AuditLogRow`, `MentionRow`,
    `AlertHistoryRow` partagés sur `Base.metadata` unique. Colonnes + index
    alignés sur la migration Alembic existante.
  - `engine.py` : `make_engine(database_url, db_path, echo)` factory qui
    bascule sur SQLite (`:memory:` / fichier) ou PostgreSQL via `DATABASE_URL`.
    `StaticPool` pour les tests in-memory.
- `tests/integration/` — suite PostgreSQL :
  - `conftest.py` : fixture `pg_engine` skippée si `INTEGRATION_DATABASE_URL`
    absent ; reset de schéma + truncate per-test pour isolation.
  - `test_postgres.py` : 4 scénarios (cycle complet `CaseService`, intégrité
    chaîne audit log, `MentionStore.for_user`, validation metadata Alembic).
- Marker pytest `integration` enregistré dans `pyproject.toml` ; addopts
  `-m 'not integration'` par défaut → unit suite reste rapide.
- Job CI `integration` (`.github/workflows/ci.yml`) avec service Postgres 16.

### Modifié — Phase 4 / PR P4-2
- `src/p2p_fraud/cases/service.py`, `cases/audit_log.py`, `cases/mentions.py`,
  `alerts/store.py` — remplacement de `sqlite3.connect` par SQLAlchemy
  `Engine` + `text()` avec named params. API publique des stores **inchangée**
  (rétrocompat des 232 tests existants, zéro régression).
- Tous les stores acceptent désormais un kwarg `engine: Engine | None = None`
  pour partager une connexion (utile pour tests d'intégration et déploiement
  multi-store sur la même base).
- `alembic/env.py` — bind `target_metadata = Base.metadata`. Déverrouille
  `alembic revision --autogenerate` pour les futures évolutions de schéma.

### Dépendances
- `sqlalchemy>=2.0` (déjà présent depuis P3.7) — promu dépendance
  fonctionnelle des stores.

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
