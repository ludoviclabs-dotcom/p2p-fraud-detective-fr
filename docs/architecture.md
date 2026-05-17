# Architecture

> Version du document : mai 2026 — produit v0.6.0
> Stack hybride : **Next.js 15** (UI v2, cible commerciale) + **Streamlit** (UI v0.5 legacy, démo Cloud) + **FastAPI** (backend Python unifié)
> Décision d'architecture associée : [`decisions/0003-streamlit-facade-fastapi-future.md`](decisions/0003-streamlit-facade-fastapi-future.md)

## Vue d'ensemble

```
┌────────────────────────────────────────────────────────────────────────┐
│                          UTILISATEURS                                  │
│   (visiteur démo · recruteur · DAF · audit · conformité · pilote ETI)  │
└──────────────────┬───────────────────────────────────────┬─────────────┘
                   │                                       │
                   ▼                                       ▼
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│  apps/web (Next.js 15 — v2)      │    │  streamlit_app.py + pages/       │
│  Cible commerciale ETI           │    │  Démo publique Streamlit Cloud   │
│  ├─ App Router · React 19        │    │  21 pages multipage              │
│  ├─ Tailwind v4 · shadcn-style   │    │  st.session_state · sans backend │
│  ├─ Recharts · sigma · visx      │    │  externe                         │
│  ├─ TanStack Query/Table         │    │                                  │
│  ├─ /api/auth/[...slug] (OIDC)   │    │                                  │
│  └─ /api/uploads (multipart)     │    │                                  │
└──────────────┬───────────────────┘    └──────────────┬───────────────────┘
               │ REST + SSE                            │ Imports Python directs
               ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       src/p2p_fraud/  (FastAPI + métier)                │
│                                                                          │
│   api/        ─►  FastAPI routes /api/v1/*  (OpenAPI, OIDC, CORS)        │
│   ingestion/  ─►  Parseurs Excel/CSV, mapping LFA1/RBKP                  │
│   detectors/  ─►  Master data history · Doublons · Sous-seuils ·        │
│                   Sirene v3 · Sanctions/PEP · Isolation Forest ·         │
│                   Anneaux IBAN (NetworkX) · Benford (scoping)            │
│   enrichment/ ─►  Sirene v3 · DECP DuckDB · RBE (Pappers) · sanctions    │
│   scoring/    ─►  Risk engine · weights.yaml · reason codes FR           │
│   cases/      ─►  Case management · audit log SHA-256 hash-chaîné        │
│   security/   ─►  Signatures Ed25519 · OIDC · RBAC 4 rôles · Fernet IBAN │
│   llm/        ─►  Anthropic Claude — narratif d'investigation (interne)  │
│   export/     ─►  Excel hyperliens · Parquet · PDF signé                 │
│   scheduler/  ─►  APScheduler (tâches récurrentes)                       │
│   synthetic/  ─►  Générateur datasets étiquetés (démo + tests)           │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │ SQLAlchemy ORM · Alembic
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Persistance : SQLite (dev) · PostgreSQL (prod, Neon en démo)           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Stack v0.6 (mai 2026)

| Couche | Technologie | Localisation |
|---|---|---|
| Frontend v2 (cible commerciale) | Next.js 15.1+ · React 19 · Turbopack · TypeScript strict | `apps/web/` |
| Frontend v0.5 (démo legacy) | Streamlit 1.36+ multipage | `streamlit_app.py` + `pages/` |
| Styling | Tailwind CSS v4 · composants shadcn-style locaux | `apps/web/components/ui/` |
| Charts | Recharts · sigma.js + graphology · visx | `apps/web/components/` |
| State client | TanStack Query 5 (state local par page) | `apps/web/components/query-provider.tsx` |
| i18n | LocaleProvider custom FR/EN (~55 clés `nav.*` + `common.*`) | `apps/web/components/locale-provider.tsx` |
| Backend | FastAPI 0.111 + Uvicorn (Python 3.11+) | `src/p2p_fraud/api/` |
| Auth | OIDC fédéré (Entra ID · Auth0 · Keycloak) via proxy Next.js | `src/p2p_fraud/api/oidc_router.py` |
| ORM | SQLAlchemy 2 + Alembic | `src/p2p_fraud/persistence/` |
| LLM | Anthropic Claude (narratif d'investigation interne) | `src/p2p_fraud/llm/` |
| Types bout-en-bout | `openapi-typescript@7` régénération via Makefile | `packages/shared-types/` |
| Observabilité | Sentry · Prometheus · alertes Slack/Teams | `src/p2p_fraud/alerts/` |

## Flux de données

1. **Upload** (Excel/CSV) → `ingestion.parsers.load_invoices()` → DataFrame canonique validé Pydantic v2
2. **Détecteurs** (parallèles) consomment ce DataFrame, produisent chacun une liste de `Finding`
3. **Enrichissement** (Sirene v3 / DECP / RBE / sanctions) ajoute `Finding` complémentaires (ex. SIREN inexistant, RBE opaque)
4. **Risk engine** agrège tous les `Finding` par `invoice_id` → `RiskScore` 0-100 avec waterfall des contributions
5. **Case management** crée/met à jour les cas pour les findings au-dessus du seuil, journalise les actions
6. **Audit log** : chaque action est hash-chaînée (SHA-256 sur `prev_hash`) ; en pilote, signature Ed25519 ajoutée
7. **Export** : `.xlsx` (auditeur) · `.parquet` (Power BI) · `.pdf` signé (audit / CAC) · JSONL signé (conservation légale)

## Coexistence des deux UI

La migration v2 (livrée mai 2026, voir `migration-v2-recap.md`) introduit une **double UX partageant le même backend** :

- **Streamlit Cloud** (v0.5) — démo publique gratuite, itérations rapides côté analyste/auditeur, 21 pages multipage. `st.session_state` pour la persistance par session.
- **Next.js sur Vercel** (v0.6) — cible commerciale, design contemporain, types bout-en-bout, performance. Routes documentées dans `migration-v2-recap.md`.

Les deux UI consomment la même logique métier dans `src/p2p_fraud/` : aucune duplication de détecteurs, de scoring ou de schémas Pydantic. La migration ultérieure vers Next.js seul (avec archivage Streamlit) est conditionnée à la traction commerciale.

## Choix techniques structurants

| Décision | Raison |
|---|---|
| Pydantic v2 au boundary (Invoice / Finding / RiskScore / Case) | Validation à l'entrée, contrats explicites, sérialisation JSON gratuite, OpenAPI auto-généré |
| pandas DataFrame côté détecteurs | Performance vectorisée, écosystème mature, lecture Parquet/CSV/Excel |
| `is_fraud` + `fraud_type` ground truth dans le générateur synthétique | Permet de calculer F1 par détecteur sur dataset reproductible |
| DuckDB pour DECP | Analytique OLAP locale, pas de serveur, lit Parquet natif |
| `requests-cache` SQLite pour Sirene | Respect quota INSEE 30 req/s et démo offline reproductible |
| Streamlit multipage (legacy) | 1 fichier = 1 vue, navigation auto, idéal pour démo Cloud sans backend dédié |
| Next.js App Router (v2) | Streaming SSR, types bout-en-bout, déploiement Vercel, design fintech |
| Audit log hash-chaîné SHA-256 + Ed25519 (optionnel) | Intégrité prouvable + non-répudiation (RFC 8032, eIDAS, ANSSI RGS B1/B2) |
| Chiffrement IBAN au repos (Fernet AES-128-CBC + HMAC-SHA256) | Minimisation et protection des coordonnées bancaires en base |
| RBAC 4 rôles (`viewer / analyst / manager / admin`) | Séparation des privilèges, 4-eyes sur clôture CONFIRMED |

## Réutilisabilité

- `enrichment/sirene_client.py` → projets Sapin 2 due diligence, DORA registre TIC
- `scoring/risk_engine.py` → projets de cartographie risques fournisseur, achats publics
- `synthetic/generator.py` → projets Journal Entry Testing, process mining SoD
- Composant `<ControlPage>` (Next.js) → factorisation des pages de contrôle (Benford, doublons, sanctions, rings, structuring)

## Limites architecturales connues

Voir `migration-v2-recap.md` section "Limitations connues" :

- OIDC cookies cross-domain : non testé en production
- SSE alertes : polling 5s en v0.6 (vrai SSE bout-en-bout reporté)
- Endpoint `/api/v1/vendors` (liste) : agrégation client, à muter en backend si pilote > 1k cases
- i18n contenu inline : `nav.*` + `common.*` traduits, contenus de pages restent FR
- Pas de tests Vitest côté front (typecheck TS fait office de garantie)
- Connecteurs ERP natifs absents (extraction CSV manuelle requise)

Ces limites sont assumées pour la phase démonstrateur et seront traitées selon la trajectoire pilote → produit (cf. roadmap dans `migration-v2-recap.md`).
