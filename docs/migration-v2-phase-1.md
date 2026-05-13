# Migration v2 — Phase 1 livrée (mai 2026)

> Suite directe de [Phase 0](./migration-v2-phase-0.md). Plan d'ensemble : [migration-v2.md](./migration-v2.md).
> **Statut** : ✅ types TS auto-générés, ✅ 4 composants UI + 2 pages, ✅ proxy OIDC.

## Livrables

### 1. Types TypeScript auto-générés depuis OpenAPI

- `docs/api/openapi.json` régénéré : **25 endpoints** documentés (vs 11 en v0.4).
- `packages/shared-types/src/api.ts` (1619 lignes) généré via `openapi-typescript@7`.
- `packages/shared-types/src/index.ts` ré-exporte les types courants : `CockpitKPIs`, `TopVendor`, `FindingOut`, `VendorSummary`, `TimelineEvent`, `AuditEntryOut`, `AuditPage`, `AuditVerifyResult`, `BulkResult`, `DailyPoint`.
- `apps/web/package.json` déclare `@p2pfd/shared-types: workspace:*` — résolution pnpm workspace native.
- Regénérer après changement backend : `pnpm sdk:gen-types` depuis la racine.

**Bénéfice** : tous les fetches Next.js sont désormais typés bout-en-bout. Modifier une signature Pydantic côté FastAPI casse le typecheck Next.js → garde-fou contractuel.

### 2. Composants UI primitives (style shadcn)

`apps/web/components/ui/` :

- **`Button`** (`class-variance-authority`) — 5 variants (primary, secondary, outline, ghost, danger) × 3 sizes (sm/md/lg)
- **`Card`** + `CardHeader` + `CardTitle` + `CardDescription` + `CardContent`
- **`Badge`** + **`SeverityBadge`** — auto-coloration par sévérité (critical/high/medium/low)
- **`Input`** — focus ring navy, validation visuelle

**Choix design** : pas de shadcn CLI (qui ajouterait Radix, primitives complexes). Composants locaux ~ 100 lignes au total, palette navy/charcoal/or réutilisée v0.5.

### 3. Pages migrées

**`/cases` — File d'investigation** (`apps/web/app/cases/page.tsx`) :
- Filtres dynamiques sévérité + statut
- Sélection multiple via checkboxes (header + lignes)
- **Bulk ops P5-3** intégrées : assignation N cases + clôture multiple (false_positive avec motif obligatoire) — wire vers `POST /api/v1/cases/bulk/{assign,close}`
- Tri par exposition € décroissant
- Badges de sévérité colorés
- TanStack Query + invalidate après mutations

**`/audit` — Piste d'audit** (`apps/web/app/audit/page.tsx`) :
- Pagination cursor-based (50 entrées par page)
- Bouton "Recalculer la chaîne" → `GET /api/v1/audit/verify` avec affichage clé publique Ed25519
- Statut signatures (✅/—) par entrée
- Compteur entrées signées vs hash chain only

### 4. OIDC proxy route

`apps/web/app/api/auth/[...slug]/route.ts` — proxy générique vers FastAPI `/oidc/*` :

| Méthode | Route Next.js | Forward FastAPI |
|---|---|---|
| GET | `/api/auth/login` | `/oidc/login` (302 vers IdP) |
| GET | `/api/auth/callback` | `/oidc/callback?code=...` |
| POST | `/api/auth/logout` | `/oidc/logout` |
| GET | `/api/auth/me` | `/oidc/me` |

**Pourquoi un proxy** :
1. Cookies session HMAC + state PKCE sur `vercel.app` uniquement → pas de cross-domain.
2. Le state PKCE et la signature `itsdangerous` restent côté backend FastAPI — Next.js n'a aucune logique d'auth.
3. CORS simplifié : navigateur ne parle qu'à `vercel.app`.
4. Préserve les `Set-Cookie` upstream + les redirects 302.

Si `NEXT_PUBLIC_API_URL` n'est pas configuré, le proxy renvoie un 503 explicite avec hint.

### 5. Endpoint API ajouté

`GET /api/v1/cases` (v1.py) — liste paginated avec filtres `status` / `severity` / `assignee`. Manquait en Phase 0, ajouté ici pour alimenter `/cases`.

## Validation

```bash
$ pnpm typecheck              # ✅
$ pnpm build                  # ✅ 6 routes (/, /audit, /cases, /dashboard, /api/auth/[...slug], /_not-found)
$ pytest --no-header          # ✅ 370 passed
$ ruff check + format         # ✅ clean
$ python -c "from p2p_fraud.api.main import app; print(len(app.routes))"
# 30 endpoints (vs 29 en Phase 0 — ajout /api/v1/cases)
```

## Architecture front Phase 1

```
apps/web/
├── app/
│   ├── layout.tsx              # Sidebar + ThemeProvider + QueryProvider
│   ├── page.tsx                # Landing
│   ├── dashboard/page.tsx      # Cockpit (4 KPI + 4 sparklines + top vendors)
│   ├── cases/page.tsx          # File d'investigation + bulk ops
│   ├── audit/page.tsx          # Piste d'audit + verify chain
│   └── api/auth/[...slug]/route.ts  # OIDC proxy
├── components/
│   ├── sidebar.tsx
│   ├── theme-provider.tsx
│   ├── query-provider.tsx
│   └── ui/
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       └── input.tsx
└── lib/
    ├── api-client.ts           # Typed fetch + 10 endpoints
    └── utils.ts                # cn(), formatEur(), formatDate()

packages/shared-types/
├── src/
│   ├── api.ts                  # auto-généré (1619 lignes, 25 endpoints)
│   └── index.ts                # re-exports + aliases
└── package.json
```

## Roadmap restante

| Phase | Sprint | Livrables principaux | Effort | Status |
|---|---|---|---|---|
| 0 | sem 1 | Monorepo + 12 endpoints + Cockpit | 1 j | ✅ |
| **1** | **sem 2-3** | **Types OpenAPI + UI primitives + Cases + Audit + OIDC proxy** | **~1 j** | **✅** |
| 2 | sem 4-5 | Score explorer (waterfall) + Vendor 360° (tabs + sparkline) + Findings list | 8 j |  |
| 3 | sem 6-7 | sigma.js Anneaux + Recharts ML scatter + Master data timeline | 8 j |  |
| 4 | sem 8-9 | Pages Données + contrôles + Upload streaming + Synthèse export | 8 j |  |
| 5 | sem 10-11 | SSE alertes live + MDX pédagogie Méthodologie/Gouvernance | 8 j |  |
| 6 | sem 12-13 | Tour guidé Onborda + LLM streaming Vendor 360° | 6 j |  |
| 7 | sem 14-15 | Sandbox commerciale Next.js + i18n FR/EN | 6 j |  |
| 8 | sem 16-17 | Bascule Streamlit → legacy.* + tag v2.0.0 + GHCR | 6 j |  |

**Restant** : ~ 50 j-h sur 14 semaines.

## Actions manuelles utilisateur après merge

1. **Si déjà déployé sur Vercel** : redéploiement automatique au push sur `main`. Vérifier que `/cases` et `/audit` chargent (avec backend FastAPI accessible).
2. **Si pas encore déployé** : suivre les instructions Phase 0 (HF Spaces + Vercel + variables d'env).
3. Pour activer l'OIDC en pilote : configurer `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_REDIRECT_URI` côté FastAPI (HF Spaces). Le `redirect_uri` doit pointer vers `https://<vercel-app>/api/auth/callback`.

## Pièges rencontrés

1. **`@p2pfd/shared-types` non résolu** : il faut déclarer la dépendance `workspace:*` dans `apps/web/package.json` + `"exports"` field dans le package partagé.
2. **`FindingOut` namespace collision** : 2 schémas `FindingOut` (main.py + v1.py) → openapi-typescript génère `p2p_fraud__api__v1__FindingOut`. Aliasé proprement dans `shared-types/src/index.ts`.
3. **Champs optionnels Pydantic `Field(default_factory=list)`** : générés `T | undefined` côté TS → utiliser `?? []` dans les composants.
4. **Multi-package pnpm install** : nécessaire après chaque changement de `workspace` deps. Pas de cache cassé sinon.

## Décision pending

Phase 1 livrée. Prochaine option : Phase 2 (Score explorer waterfall + Vendor 360° complet + Findings list). Ou pause si vous voulez tester le déploiement Vercel + HF Spaces avant d'enchaîner.
