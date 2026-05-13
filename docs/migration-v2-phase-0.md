# Migration v2 — Phase 0 livrée (mai 2026)

> Premier sprint de la Migration v2 défini dans [`docs/migration-v2.md`](./migration-v2.md).
> **Statut** : ✅ skeleton monorepo en place, ✅ 12 endpoints API v1 + tests, ✅ Next.js 15 build OK.
> **Effort réel** : ~1 session de travail (vs 5 j estimés dans le plan d'origine).

## Livrables

### 1. Monorepo (root)

```
p2p-fraud-detective-fr/
├── pnpm-workspace.yaml          # workspace pnpm
├── package.json                 # racine — scripts web:* + sdk:gen-types
├── apps/
│   └── web/                     # Next.js 15 App Router + shadcn + Tailwind v4
├── packages/
│   └── shared-types/            # TypeScript types générés depuis OpenAPI
├── src/p2p_fraud/               # Backend Python (Streamlit + FastAPI) inchangé
└── pages/                       # Pages Streamlit (legacy v0.5) inchangées
```

**Choix d'architecture** :
- Le backend Python **reste au root** (pas déplacé sous `apps/api/`) pour ne pas casser Streamlit Cloud qui pointe sur `streamlit_app.py`.
- Seul Next.js est isolé dans `apps/web/`.
- Les types TypeScript partagés (à générer depuis OpenAPI) vivent dans `packages/shared-types/`.

### 2. API v1 — 12 endpoints typés

`src/p2p_fraud/api/v1.py` — router FastAPI préfixé `/api/v1/`, monté sur l'`app` principal avec injection du `CaseService` et de l'auth bearer via `dependency_overrides`.

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/v1/cockpit/kpis` | 4 KPI + 4 séries 30j (sparklines) |
| GET | `/api/v1/cockpit/top-vendors?limit=N` | Top fournisseurs par exposition € |
| GET | `/api/v1/findings?rule_id=&severity=&limit=` | Findings paginated avec filtres |
| GET | `/api/v1/vendors/{id}` | Fiche fournisseur agrégée |
| GET | `/api/v1/vendors/{id}/timeline?days=30` | Événements 30j (cases + audit) |
| POST | `/api/v1/cases/{id}/comment` | Ajout commentaire avec @mentions |
| POST | `/api/v1/cases/bulk/assign` | Assignation multiple |
| POST | `/api/v1/cases/bulk/close` | Clôture multiple (motif commun) |
| GET | `/api/v1/audit?cursor=&limit=` | Audit log paginated |
| GET | `/api/v1/audit/verify` | Recalcul SHA-256 + signatures Ed25519 |
| GET | `/api/v1/exports/dossier.pdf?case_id=` | Génère PDF dossier (weasyprint) |
| POST | `/api/v1/llm/narrative` | **Streaming SSE** narration Claude |

**Modèles Pydantic** : `CockpitKPIs`, `TopVendor`, `FindingOut`, `VendorSummary`, `TimelineEvent`, `CommentBody`, `BulkAssignBody`, `BulkCloseBody`, `BulkResult`, `AuditEntryOut`, `AuditPage`, `AuditVerifyResult`, `NarrativeBody`.

**Tests** : `tests/test_api_v1.py` — 16 tests FastAPI TestClient (Cockpit KPI/top-vendors, Findings filtre, Vendors summary/timeline, Cases comment/bulk, Audit list/verify, Exports PDF). **0 régression** sur les 354 tests existants.

### 3. Next.js 15 (apps/web/)

Stack minimale fonctionnelle :
- **Next.js 15.5** + React 19 + Turbopack
- **Tailwind CSS v4** (PostCSS plugin natif) — palette navy/charcoal/or v0.5 reprise
- **TanStack Query 5.66** pour les data fetches
- **next-themes** pour le dark mode
- **lucide-react** pour les icônes
- **tailwind-merge** + **clsx** pour `cn()` shadcn-style

**Pages livrées Phase 0** :
- `/` — landing avec hero + 3 cartes features + CTA Cockpit/Tour/GitHub
- `/dashboard` — Cockpit fonctionnel (4 KPI + 4 sparklines SVG + Top vendors table)

**Composants** :
- `<Sidebar>` — navigation 6 sections × 20+ pages, palette navy
- `<ThemeProvider>` — wrapper next-themes
- `<QueryProvider>` — wrapper TanStack QueryClient

**Helpers** :
- `lib/utils.ts` — `cn()`, `formatEur()`, `formatDate()` (Intl FR partout)
- `lib/api-client.ts` — fetch typé avec bearer + endpoints Cockpit

**Validation** :
```bash
$ pnpm typecheck    # ✅
$ pnpm build        # ✅ — Route /  + /dashboard générées
```

## Activer en local

```bash
# 1. Backend FastAPI (terminal 1)
export FRAUD_API_SECRET=test-secret
uvicorn p2p_fraud.api.main:app --reload --port 8000

# 2. Frontend Next.js (terminal 2)
cd apps/web
cp .env.example .env.local
# Éditer .env.local : NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm install
pnpm dev
# → http://localhost:3000
```

## Roadmap Phases 1-8

| Phase | Sprint | Livrables principaux | Effort |
|---|---|---|---|
| **0** | ✅ livré | Monorepo + 12 endpoints + Next.js skeleton + Cockpit | 1 session |
| 1 | semaines 2-3 | Auth OIDC proxy + OpenAPI types regen + composants shadcn (Card, DataTable, Badge) | 8 j |
| 2 | semaines 4-5 | Migration pages prioritaires (File d'investigation, Score explorer, Vendor 360°, Audit trail) | 10 j |
| 3 | semaines 6-7 | sigma.js Anneaux + Recharts ML Anomalies + waterfall Score | 8 j |
| 4 | semaines 8-9 | Pages Données + contrôles statistiques + Upload streaming | 8 j |
| 5 | semaines 10-11 | SSE alertes live + MDX pédagogie | 8 j |
| 6 | semaines 12-13 | Conformité/Gouvernance + Playwright E2E | 6 j |
| 7 | semaines 14-15 | Onborda Tour + LLM streaming UI + landing polish | 6 j |
| 8 | semaines 16-17 | Bascule Streamlit → legacy.* + tag v2.0.0 | 6 j |

**Total restant** : ~ 60 j-h sur 16 semaines à temps partiel.

## Validation Phase 0

- [x] `pytest --no-header` : **370 passed** (354 + 16 nouveaux v1)
- [x] `ruff check + ruff format` clean
- [x] `pnpm typecheck` clean
- [x] `pnpm build` produit `.next/` valide
- [x] Streamlit v0.5 reste intact (aucune régression — `streamlit_app.py` inchangé)
- [x] OpenAPI auto-généré expose les 12 nouveaux endpoints (`make openapi-export` → 23 endpoints au total)
- [ ] **Action manuelle utilisateur** : héberger FastAPI sur HF Spaces, configurer `NEXT_PUBLIC_API_URL` sur Vercel
- [ ] **Action manuelle utilisateur** : connecter Vercel au repo, déployer `apps/web/`

## Pièges rencontrés (notes pour les phases suivantes)

1. **`experimental.typedRoutes`** : trop tôt en Phase 0 — désactivé. Réactivable en Phase 2 quand tous les segments auront leur page.
2. **`packageManager` field** dans `package.json` racine : provoque `pnpm install` autoréférence dans le sandbox. Retiré, à remettre en local utilisateur via `corepack enable`.
3. **`findings` endpoint** : initialement basé sur audit log (pas de severity dans payload) → refait à partir des cases (qui portent severity). En Phase 5 il faudra une vraie table `findings` ou ajouter `severity` au payload `_record_event`.
4. **Cross-domain cookies OIDC** : pas encore traité — sera la difficulté n°1 de Phase 1.

## Décision pending

La Phase 0 est livrée mais **non engageante**. Trois sorties possibles :

1. **Continuer la Migration v2** vers Phase 1 (auth OIDC + premières pages migrées).
2. **Pause** sur la migration et basculer sur Phase 7 contenu commercial (vidéos, prospection LOI).
3. **Tag v0.5.0** en attente d'une vraie traction LOI ETI avant d'investir 60 j-h supplémentaires.

À trancher après revue de cette PR.
