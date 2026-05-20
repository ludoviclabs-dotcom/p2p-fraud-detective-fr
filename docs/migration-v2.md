# Migration v2 — Streamlit → Next.js 15 + FastAPI

> **Statut** : document historique du plan initial. L'implementation Next.js est
> desormais livree sur `main`; l'etat courant et la roadmap active vivent dans
> [`migration-v2-recap.md`](./migration-v2-recap.md).
> **Cible** : v2.0.0 — démonstrateur Next.js sur Vercel + FastAPI sur Hugging Face Spaces.
> **Date** : mai 2026. **Auteur** : Ludovic L. (avec assistance Claude Code).
> **Contrainte structurante** : free tier strict (0 €/mois), 6 mois à temps partiel, OIDC existant conservé.

## TL;DR

Migration du démonstrateur **P2P Fraud Detective FR** d'une UI Streamlit (v0.4.0) vers une plateforme Next.js 15 + FastAPI étendu. Le **cœur métier Python reste intact** : 8 détecteurs, scoring engine, audit log SHA-256, OIDC, cases service, exports PDF, scheduler — soit 274 tests à préserver. Seule l'**UI** est refondue.

Approche : **strangler fig**, Streamlit Cloud reste actif jusqu'à 80% de parité fonctionnelle puis bascule sur `legacy.*`. Effort total estimé : **~95 jours-homme sur 6 mois** (cadence ~4 j/sem à temps partiel).

## Mise a jour mai 2026

- Ce document conserve le plan initial, utile pour comprendre les arbitrages
  de fond et la cible d'architecture.
- Le repo a depuis livre la base `apps/web` et les principales routes Next.js.
- Cote qualite front, la baseline automatisee existe deja : Vitest couvre la
  logique pure alertes/cockpit/workflow/demo-investigation et Playwright couvre
  deja plusieurs parcours reels (`/dashboard`, `/rings`, `/score`, `/alerts`,
  `/cases`, `/audit`, `/upload`).
- Le travail restant n'est plus d'initialiser la migration, mais d'elargir la
  couverture DOM/composants et de fermer les derniers golden paths.

## Contexte et motivation

### Pourquoi migrer ?

| Bénéfice attendu | Critique honnête |
|---|---|
| **Wow-factor design** pour recruteurs Tracfin / IEF / DGE | Réel — Streamlit a un plafond visuel |
| **Storytelling commercial** pour LOI pilote ETI | Réel — un DSI ETI prend plus au sérieux un Next.js |
| **Graphes scalables** (sigma.js WebGL > Plotly SVG) | Marginal — vous avez < 10k nœuds en pratique |
| **API publique** pour intégration SI client | **Déjà existe** (`api/main.py`) — pas un argument de migration |
| **Performance** | Faux — Streamlit Cloud tient largement vos volumes |
| **Multi-tenancy** | Faux — vous n'avez pas d'utilisateurs concurrents |

### Pourquoi ne PAS migrer (à considérer une dernière fois)

- Streamlit Cloud est **fonctionnel et gratuit** depuis v0.3.0.
- Le score interne est à 100/100 sur les critères démonstrateur.
- 95 j-h de migration = coût d'opportunité élevé (Phase 5 P5-1 à P5-5 = ~23 j et apporte plus de valeur métier).
- Le « POC reconnaissable » est un faux problème si les **screenshots et le contenu** sont à la hauteur.

**Verdict** : migration justifiée **uniquement si** vous priorisez l'image (portfolio) et la commercialisation B2B (pilote). Si l'objectif est de pousser la valeur métier (DECP live, sandbox, webhook, i18n), suivre la Phase 5 v0.5.0 est plus rationnel.

Le présent plan suppose la décision **prise en faveur de la migration**.

## Stack cible

### Frontend — Vercel free tier

- **Next.js 15** App Router, TypeScript, Turbopack
- **shadcn/ui** + **Tailwind CSS v4** (palette navy/charcoal/or reprise de v0.3)
- **TanStack Query** (données) + **TanStack Table** (DataTables) + **TanStack Router**-like (Next.js routing)
- **React Hook Form + Zod** (formulaires)
- **Zustand** (état UI client)
- **Recharts + visx** (graphiques) — **pas Tremor** (racheté Vercel, risque de deprecation)
- **sigma.js + graphology** (graphes denses, dynamic import `ssr: false`)
- **React Flow / xyflow** (vues d'enquête éditables — phase 7)
- **next-themes** (dark mode)
- **next-mdx-remote** (pages pédagogie / méthodologie)
- **Vercel AI SDK** (`ai` package) + **Claude API** pour LLM streaming
- **Onborda** (tour guidé)
- **Lucide** (icônes)
- **Geist + Geist Mono** (polices via `next/font`)

### Backend — Hugging Face Spaces (Docker FastAPI, vrai free)

- Code Python **inchangé** : `src/p2p_fraud/**` reste tel quel
- `api/main.py` **étendu** avec 12 endpoints (cf. §6)
- Image Docker existante adaptée (`Dockerfile` actuel, juste renommer `libgdk-pixbuf-2.0-0` déjà fait)
- Pas de scheduler dans le container web (HF Spaces n'aime pas les long-running) → garder le `scheduler/__main__.py` ailleurs (GitHub Actions cron, ou local en dev)

### Persistance

- **Neon free** (PostgreSQL 16, 0.5 GB, scale-to-zero) — SQLAlchemy URL `postgresql://...`
- **Apache AGE** : **abandonné en v2.0** (pas de free tier disponible). NetworkX en mémoire continue à fonctionner pour les anneaux de fraude. Reporté à v2.1 quand budget Railway disponible.
- **Upstash Redis free** (10k commands/jour) — pub/sub SSE
- **Vercel Blob free** (1 GB) — pour les PDF exports temporaires

### Auth — OIDC existant (P4-3 conservé)

- Le flow PKCE vit côté FastAPI (existant : `src/p2p_fraud/api/oidc_router.py`)
- Next.js consomme via route handlers proxy (`/api/auth/*`)
- Session cookie HMAC `itsdangerous` partagé via le proxy (pas cross-domain)
- **Pas de Clerk**, **pas de NextAuth.js** — réutilisation totale

### Observabilité

- **Sentry free** (5k events/mois) — front + back
- **Vercel Analytics** (gratuit, Core Web Vitals)
- **PostHog free** (1M events/mois) — parcours visiteur

## Architecture cible

```
                  ┌────────────────────────────────┐
                  │  VISITEUR (recruteur / pilote) │
                  └────────────┬───────────────────┘
                               │ HTTPS
                               ▼
              ┌────────────────────────────────────┐
              │  Vercel free (Next.js 15)          │
              │  ├─ App Router : 20 pages          │
              │  ├─ shadcn/ui + Tailwind v4        │
              │  ├─ Recharts + visx + sigma.js     │
              │  ├─ TanStack Query/Table           │
              │  ├─ next-themes (dark mode)        │
              │  ├─ /api/auth/* (OIDC proxy)       │
              │  ├─ /api/sse (proxy Redis SSE)     │
              │  └─ /api/llm/* (proxy Claude)      │
              └──┬───────────────────┬─────────────┘
                 │ HTTPS REST        │ SSE / WebHooks
                 ▼                   ▼
       ┌─────────────────────────────────────────┐
       │  HF Spaces (Docker FastAPI free, 16 GB) │
       │  ├─ api/main.py (existant + 12 ext)     │
       │  ├─ src/p2p_fraud/** (INCHANGÉ)         │
       │  ├─ NetworkX in-memory                  │
       │  ├─ weasyprint PDF                      │
       │  ├─ OIDC discovery + JWKS (P4-3)        │
       │  └─ Sentry SDK + Prometheus (P4-6)      │
       └───┬─────────────┬───────────────────────┘
           │ SQLAlchemy  │ pub/sub
           ▼             ▼
   ┌──────────────┐  ┌──────────────┐
   │ Neon free PG │  │ Upstash Redis│
   │ (0.5 GB,     │  │ (10k cmd/j)  │
   │  scale-to-0) │  └──────────────┘
   └──────────────┘
   ┌──────────────────────────────────┐
   │ Streamlit Cloud v0.4 (legacy)    │
   │ → 301 vers /legacy après bascule │
   └──────────────────────────────────┘
```

## Cartographie de migration page par page

| Streamlit (v0.4) | Next.js cible | Effort | Risque |
|---|---|---|---|
| `pages/0_🎯_Cockpit.py` | `app/dashboard/page.tsx` — 4 KPI + 4 sparklines | 2 j | Plotly → visx |
| `pages/1_📤_Upload.py` | `app/upload/page.tsx` | 2 j | Multipart streaming |
| `pages/2_🔢_Benford.py` | `app/controls/benford/page.tsx` | 1.5 j | Histogramme |
| `pages/3_🏦_Master_data_history.py` | `app/data/master-history/page.tsx` | 2 j | Timeline visx |
| `pages/4_♊_Doublons.py` | `app/controls/duplicates/page.tsx` | 1.5 j | Bas |
| `pages/5_📏_Sous_seuils.py` | `app/controls/structuring/page.tsx` | 1.5 j | Bas |
| `pages/6_🇫🇷_Sirene_check.py` | `app/data/sirene/page.tsx` | 1 j | Bas |
| `pages/7_🤖_Anomalies_ML.py` | `app/ml/anomalies/page.tsx` | 2 j | Scatter Recharts |
| `pages/8_🕸️_Anneaux_fraude.py` | `app/ml/rings/page.tsx` — **sigma.js** | 4 j | streamlit-agraph → sigma |
| `pages/9_⚖️_Sanctions_PEP.py` | `app/controls/sanctions/page.tsx` | 1.5 j | Bas |
| `pages/10_🗂️_File_d_investigation.py` | `app/cases/page.tsx` — DataTable + bulk ops | 3 j | streamlit-aggrid → TanStack Table |
| `pages/11_📊_Synthèse_export.py` | `app/exports/page.tsx` | 1 j | Trigger PDF côté API |
| `pages/12_📚_Méthodologie.py` | `app/learn/page.tsx` MDX | 2 j | Markdown → MDX |
| `pages/13_📜_Audit_trail.py` | `app/audit/page.tsx` | 2 j | Chain verify UI |
| `pages/14_💡_Score_explorer.py` | `app/ml/score/page.tsx` — waterfall | 3 j | Waterfall custom |
| `pages/15_🪪_Fiche_fournisseur_360.py` | `app/vendors/[id]/page.tsx` | 4 j | Tabs + plusieurs DataTables |
| `pages/16_🛡️_Gouvernance.py` | `app/governance/page.tsx` | 2 j | Weights editor → Monaco |
| `pages/17_🏛️_DECP_RBE.py` | `app/data/decp-rbe/page.tsx` | 1.5 j | Bas |
| `pages/18_🔔_Alertes.py` | `app/alerts/page.tsx` — **SSE live** | 3 j | Stream Upstash |
| `pages/19_👥_Collaboration.py` | `app/collab/page.tsx` | 2 j | OIDC + @mentions |

**Sous-total pages** : ~40 j

## Endpoints FastAPI à ajouter (12 manquants)

L'`api/main.py` actuel n'expose que `/detect`, `/score`, `/cases`. À compléter pour couvrir l'UI Next.js :

```
GET    /api/v1/cockpit/kpis              # 4 KPI + 4 séries 30j
GET    /api/v1/cockpit/top-vendors       # Top 10 exposition
GET    /api/v1/findings                  # paginated, filtres rule_id/severity/since
GET    /api/v1/vendors/{id}              # fiche 360° complète
GET    /api/v1/vendors/{id}/timeline     # paiements + master data + findings 30j
POST   /api/v1/cases/{id}/comment        # commentaire + @mentions parsing
POST   /api/v1/cases/bulk/assign         # assignation multiple
POST   /api/v1/cases/bulk/close          # clôture multiple (motif commun)
GET    /api/v1/audit                     # audit log paginated
GET    /api/v1/audit/verify              # SHA-256 chain integrity check
POST   /api/v1/uploads                   # multipart streaming
GET    /api/v1/exports/dossier.pdf?id=   # PDF weasyprint
GET    /api/v1/alerts/stream             # SSE Server-Sent Events
POST   /api/v1/llm/narrative             # streaming Claude pour Vendor 360°
```

Effort : **3 j**. La logique métier existe déjà côté services, c'est de l'exposition.

## Pièges de compatibilité — 15 critiques

| # | Piège | Solution |
|---|---|---|
| 1 | **Cookies cross-domain OIDC** (`vercel.app` ≠ `hf.space`) | Tout via route handlers Next.js (proxy server-side) — cookies session uniquement sur le domaine Vercel |
| 2 | **Locale FR** (`1 234,56 €`) | Composants `<Money>`, `<DateLocal>` partagés — `Intl.NumberFormat('fr-FR')` ; jamais `.toLocaleString()` nu |
| 3 | **Timezone `Europe/Paris`** | `date-fns-tz` partout, sentinelle CI qui interdit `new Date(string)` direct |
| 4 | **SSR + WebGL** (sigma.js, monaco) | `dynamic(() => import(...), { ssr: false })` + skeleton |
| 5 | **`st.session_state` → état persistant** | Zustand (client) + TanStack Query (serveur). Pas de `useState` pour data métier |
| 6 | **`@st.cache_data` → caching** | Cache côté FastAPI (`@functools.cache` + `requests-cache` existant) + TanStack Query côté React |
| 7 | **`@st.fragment` → re-render isolation** | RSC par défaut, `'use client'` minimal, `useTransition` pour les updates |
| 8 | **CSRF** | Cookie session `SameSite=Strict` + double-submit token pour POST cross-origin |
| 9 | **Uploads volumineux** | Route handler `runtime: 'nodejs'`, streaming `request.body` → forward FastAPI (pas de buffering RAM) |
| 10 | **PDF download** | FastAPI renvoie `application/pdf`, Next.js stream `<a download>` (pas d'iframe blob) |
| 11 | **Émojis dans URLs** | Slugs propres : `/cases`, `/vendors`, `/ml/rings` — pas d'émoji dans les routes |
| 12 | **Plotly template `p2pfd`** | Pas portable. Créer `<ChartContainer>` qui applique navy/or à Recharts/visx via CSS variables shadcn |
| 13 | **`streamlit-aggrid` bulk select** | TanStack Table `enableRowSelection` + `<RowSelectionToolbar>` flottant style Notion |
| 14 | **OIDC PKCE state** | Vit côté FastAPI (P4-3 existant). Next.js ne touche **jamais** au state |
| 15 | **HF Spaces cold start** | GitHub Actions cron `*/10 * * * *` → `curl /health`. Acceptable en démo, pas en pilote |

## Plan en 8 phases — 6 mois, ~95 j-h

### Phase 0 — Préparation (semaine 1, 5 j)

- [ ] Monorepo `p2p-fraud-detective-v2/` : `apps/web` (Next.js) + `apps/api` (référence vers ce repo) + `packages/shared-types`
- [ ] Branche `legacy/streamlit` archivant l'état v0.4 actuel
- [ ] Étendre `api/main.py` avec les 12 endpoints (cf. §6)
- [ ] Déployer FastAPI sur HF Spaces, valider `/health`
- [ ] Provisionner Neon free + tester migrations Alembic
- [ ] Configurer Vercel + domaine placeholder

### Phase 1 — Fondations Next.js (semaines 2-3, 8 j)

- [ ] `pnpm create next-app@latest apps/web --typescript --tailwind --app --turbopack`
- [ ] shadcn/ui init + thème navy/charcoal/or (reprise design tokens v0.3)
- [ ] `next-themes` + dark mode par défaut
- [ ] Layout : sidebar (6 sections) + topbar + ribbon « DÉMONSTRATEUR v2 »
- [ ] Auth flow OIDC : route handlers proxy `/api/auth/*` → FastAPI `/oidc/*`
- [ ] TanStack Query setup
- [ ] Client OpenAPI typé : `pnpm dlx openapi-typescript .../openapi.json -o packages/shared-types/api.ts`
- [ ] **Première page bout-en-bout** : `/dashboard` (Cockpit)

### Phase 2 — Détecteurs prioritaires (semaines 4-5, 10 j)

- [ ] Cockpit complet (4 KPI Tremor-like + 4 sparklines visx)
- [ ] File d'investigation (TanStack Table + bulk ops)
- [ ] Score explorer (waterfall Recharts custom)
- [ ] Fiche fournisseur 360° (tabs + plusieurs DataTables + sparkline)
- [ ] Audit trail (avec chain verify)
- [ ] Composants partagés : `<SeverityBadge>`, `<Money>`, `<DateLocal>`, `<FindingCard>`, `<RoleGuard>`

### Phase 3 — Graphes & ML (semaines 6-7, 8 j)

- [ ] sigma.js + graphology sur Anneaux de fraude
- [ ] Anomalies ML scatter + drill-down Vendor 360°
- [ ] Score explorer waterfall
- [ ] SHAP-like breakdown component

### Phase 4 — Données & contrôles (semaines 8-9, 8 j)

- [ ] Benford, Doublons, Sous-seuils, Sanctions/PEP, Sirene, DECP/RBE
- [ ] Upload drag-drop avec progress streaming
- [ ] Master data history (timeline visx)
- [ ] Synthèse export (trigger PDF FastAPI)

### Phase 5 — Temps réel + pédagogie (semaines 10-11, 8 j)

- [ ] SSE route handler `/api/alerts/stream` ↔ Upstash Redis
- [ ] Page Alertes feed live
- [ ] Module pédagogique MDX : 5 patterns (smurfing, layering, cycles, fan-in/out, mules)
- [ ] Timeline AMLR/AMLD6/AMLA

### Phase 6 — Conformité, gouvernance, exports (semaines 12-13, 6 j)

- [ ] Audit trail avec chain verification UI
- [ ] Gouvernance (RBAC + RGPD + weights editor Monaco)
- [ ] Méthodologie (MDX, reprise contenu v0.4)
- [ ] Etendre Playwright de la baseline actuelle a des golden paths relies a un backend reel

### Phase 7 — Tour guidé + LLM + polish (semaines 14-15, 6 j)

- [ ] Onborda 5 étapes (Cockpit → Vendor 360° → findings → narration LLM → export)
- [ ] LLM streaming Claude via Vercel AI SDK
- [ ] Landing hero animée (Magic UI optionnel)
- [ ] Page About + Méthodologie no-PII

### Phase 8 — Bascule + retrait Streamlit (semaines 16-17, 6 j)

- [ ] Pages restantes (Collaboration, etc.)
- [ ] Completer la couverture Playwright bout-en-bout sur les flux avec backend reel, auth et persistence
- [ ] Streamlit Cloud → `legacy.votredomaine.com` avec 301 / bannière
- [ ] README bilingue (FR doctrine, EN stack)
- [ ] Vidéo démo 90s
- [ ] **Tag v2.0.0** + annonce LinkedIn

**Total estimé** : 55 j de pages + 30 j de fondations/infra/tests + 10 j de buffer = **~95 j-h**

## Tests et non-régression

- **274 tests Python existants** : **aucun à toucher**. La logique métier reste sur FastAPI. ✅
- **Tests E2E Playwright** : baseline deja livree sur plusieurs parcours
  cockpit/rings/score/alerts/cases/audit/upload ; cible restante = les flux
  relies a un backend reel, l'auth et les integrations.
- **Vitest** cote Next.js : logique pure deja couverte sur alertes, cockpit demo
  et workflow case ; a etendre aux composants critiques (`<Money>`,
  `<DataTable>`, `<SeverityBadge>`, `<ChartContainer>`)
- **Contract tests** : `openapi-typescript` régénéré à chaque PR + CI check de drift schéma

## Décisions structurantes — synthèse

| Décision | Choix v2 | Justification (free tier + 6 mois) |
|---|---|---|
| Hébergement frontend | **Vercel free** | Standard Next.js, previews Git, free tier généreux |
| Hébergement backend | **Hugging Face Spaces** Docker | Seul vrai free 2026, no sleep, 16 GB RAM |
| Base de données | **Neon free** + NetworkX in-memory | AGE reporté v2.1 (pas de free tier) |
| Auth | **OIDC existant** (P4-3) | Évite Clerk vendor lock-in, déjà fait |
| Charts | **Recharts + visx** | Tremor = risque deprecation Vercel |
| Graphe principal | **sigma.js + graphology** | WebGL, écosystème algos |
| Vue d'enquête | **React Flow / xyflow** (phase 7) | Éditeur de nœuds inégalé |
| State client | **Zustand + TanStack Query** | Standard 2026 |
| Forms | **React Hook Form + Zod** | Type-safe, intégration shadcn `<Form>` |
| PDF | **weasyprint** côté FastAPI (existant) | Ne pas réécrire |
| LLM | **Vercel AI SDK + endpoint FastAPI** | `useChat` hook + streaming SSE |
| Tests | **Playwright + Vitest + pytest** | Pyramid classique |
| Tour guidé | **Onborda** | Next.js-first, Framer Motion natif |
| Observabilité | **Sentry + PostHog + Vercel Analytics** | Standard, free tiers |

## Off-ramps (plans de repli)

| Si... | Alors... |
|---|---|
| HF Spaces ne tient pas la charge en démo | Fly.io free (sleep accepté) ou 5 €/mois Railway hobby si LOI signée |
| Migration trop longue (> 4 mois) | Garder Streamlit pour back-office (Audit, Gouvernance, Méthodologie) — Next.js uniquement pour Cockpit + Dashboard + Vendor 360° + landing |
| sigma.js trop complexe | Cytoscape.js (plus simple, 3-5k nœuds OK pour vous) ou iframe streamlit-agraph |
| OIDC cross-domain casse | Domaine custom (5 €/an Namecheap) avec sous-domaines `app.` (Vercel) + `api.` (HF) → cookies `Domain=.yourdomain.com` |
| Neon 0.5 GB saturé | Supabase free (500 MB) + `postgres_fdw` ou bascule SQLite + Vercel Blob |
| Sentry 5k events dépassé | Self-host GlitchTip (open source, compat Sentry SDK) sur HF Spaces |

## Risques juridiques et conformité

1. **Aucune PII réelle**, jamais. Bannière permanente « 🔒 Données synthétiques » sur chaque écran.
2. Déclaration de soupçon stylisée porte la mention **« démonstration pédagogique, non transmissible à Tracfin »**.
3. Page Méthodologie et Mentions légales explicites, sources publiques citées (Tracfin, ACPR, AMLA, GAFI, Légifrance).
4. **Licences** : éviter Intro.js (AGPL) et toute lib AGPL. shadcn/ui, sigma.js, graphology, Recharts, visx, React Flow, Onborda sont tous MIT.

## Premiers commits si décision validée

1. `docs(migration-v2): plan d'architecture` — **ce commit**
2. `chore: monorepo skeleton apps/web + packages/shared-types`
3. `feat(api): expose 12 endpoints manquants pour la v2`
4. `chore(api): Dockerfile HF Spaces + déploiement`
5. `feat(web): Next.js 15 + shadcn + auth OIDC proxy + dashboard skeleton`
6. `feat(web): Cockpit complet (4 KPI + 4 sparklines visx)`

## Décision pending

Ce plan reste **non-engageant** tant que les premiers commits d'implémentation ne sont pas poussés. Trois sorties possibles à l'issue de la lecture :

1. **GO migration** : commit 2 démarre la semaine prochaine, Streamlit reste en service comme legacy.
2. **GO Phase 5 v0.5.0 d'abord** : on prolonge Streamlit jusqu'en octobre 2026 (DECP live, sandbox, webhook, i18n, Ed25519) puis on évalue si la migration est encore nécessaire.
3. **NO-GO** : Streamlit Cloud reste la cible long-terme, on consacre les 95 j à du contenu métier et commercial (typologies Tracfin enrichies, démos vidéo, LOI ETI).

À trancher après revue de ce document.

---

**Références** :
- Plan d'origine : `compass_artifact_wfce9c51de713946a4bd4781ac6d9c0d77` (Claude research, mai 2026)
- Plan Phase 5 v0.5.0 : `/root/.claude/plans/starry-enchanting-karp.md`
- Rapport Tracfin 2024-2025 Tome III « État de la menace »
- Règlement (UE) 2024/1624 AMLR — applicable 10 juillet 2027
