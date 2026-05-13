# Migration v2 — Phase 2 livrée (mai 2026)

> Suite directe de [Phase 1](./migration-v2-phase-1.md). Plan d'ensemble : [migration-v2.md](./migration-v2.md).
> **Statut** : ✅ 4 nouvelles pages migrées (Findings, Vendors index, Vendor 360°, Score waterfall).

## Livrables

### Pages migrées

| Route | Description | Charts |
|---|---|---|
| `/findings` | Liste filtrable des findings (rule_id + severity + recherche libre) | — |
| `/vendors` | Index agrégé par vendor_id (exposition, n_cases, sévérité max) | — |
| `/vendors/[id]` | Fiche 360° : 4 KPI + sparkline 30j + tabs (Profil/Timeline/Findings) | Recharts AreaChart |
| `/score` | Waterfall des contributions à l'exposition cumulée | Recharts stacked BarChart |

### Recharts intégré

- Ajouté `recharts@3.8.1` dans `apps/web/package.json`
- `/score` : waterfall via `BarChart` stacked avec offset invisible (technique standard pour effet cascade)
- `/vendors/[id]` : `AreaChart` avec gradient navy pour la sparkline trend 30j
- Tooltips formatés `Intl.NumberFormat('fr-FR')` partout
- Réutilisation des couleurs sémantiques (`#a23e48` critical, `#c97b1f` high, etc.)

### Détails par page

**`/findings`** — Filtres dynamiques (severity, rule_id, recherche libre client-side), wire vers `GET /api/v1/findings`. Cellule vendor_id cliquable → `/vendors/[id]`.

**`/vendors`** — Agrégation client-side depuis `listCases({limit: 1000})`. Pas d'endpoint dédié pour cette Phase 2 (le backend a `GET /vendors/{id}` mais pas de liste). Sévérité max calculée via ranking.

**`/vendors/[id]`** — Tabs natifs (pas Radix). Sparkline construite depuis `getVendorTimeline(id, 30)` agrégé par jour. 4 KPI (Nom, SIREN, Paiements, Cases). Bannières alertes (sanctioned/PEP). Bouton "Narration LLM" disabled (à câbler Phase 6 avec streaming SSE Vercel AI SDK).

**`/score`** — Top 15 cases triés par exposition. Waterfall avec :
- Bar invisible offset (effet cascade)
- Bar value coloré par sévérité (Cell par Cell)
- Tooltip custom (rank, case_id, titre, contribution, cumul)
- Table détaillée en dessous avec cumul progressif

## Validation

```bash
$ pnpm typecheck       ✅
$ pnpm build           ✅ 10 routes (8 statiques + 2 dynamic + not-found)
$ pytest --no-header   ✅ 370 passed
```

Tailles bundles (First Load JS) :
- `/findings`     : 121 kB
- `/vendors`      : 120 kB
- `/vendors/[id]` : **226 kB** (Recharts inclus)
- `/score`        : **229 kB** (Recharts inclus, partagé avec `/vendors/[id]`)

Recharts est split-chunk : 130 kB seulement à la première visite, puis cached.

## Architecture front Phase 2

```
apps/web/app/
├── findings/page.tsx         # nouveau Phase 2
├── vendors/
│   ├── page.tsx              # nouveau Phase 2 — index
│   └── [id]/page.tsx         # nouveau Phase 2 — Fiche 360°
└── score/page.tsx            # nouveau Phase 2 — waterfall
```

## Roadmap restante

| Phase | Sprint | Livrables | Effort | Status |
|---|---|---|---|---|
| 0 | sem 1 | Monorepo + 12 endpoints + Cockpit | 1 j | ✅ |
| 1 | sem 2-3 | Types OpenAPI + UI + Cases + Audit + OIDC | ~1 j | ✅ |
| **2** | **sem 4-5** | **Findings + Vendors + Score waterfall** | **~1 j** | **✅** |
| 3 | sem 6-7 | sigma.js Anneaux + Recharts ML scatter + Master data timeline | 8 j |  |
| 4 | sem 8-9 | Pages Données + contrôles + Upload streaming + Synthèse export | 8 j |  |
| 5 | sem 10-11 | SSE alertes live + MDX pédagogie | 8 j |  |
| 6 | sem 12-13 | Tour guidé Onborda + LLM streaming Vendor 360° | 6 j |  |
| 7 | sem 14-15 | Sandbox Next.js + i18n FR/EN | 6 j |  |
| 8 | sem 16-17 | Bascule legacy + tag v2.0.0 | 6 j |  |

**Restant** : ~ 45 j-h sur 13 semaines.

## Pièges rencontrés

1. **Recharts SSR** : pas de problème ici car les pages sont `"use client"`. Si un jour on veut SSR un graphique, utiliser `dynamic(() => import("..."), { ssr: false })`.
2. **Waterfall offset** : technique standard = stacked BarChart avec une `Bar dataKey="invisible" fill="transparent"` qui pousse la barre value vers le haut.
3. **Pas d'endpoint vendors list** : agrégation client-side depuis `listCases`. Pourrait être un endpoint backend dédié en Phase 4 si besoin (>1000 cases côté pilote).
4. **TanStack Query staleTime** : par défaut 60s — convient pour les démos. Pour live alerts (Phase 5) il faudra forcer `staleTime: 0` ou utiliser SSE.

## Décision pending

Phase 2 livrée. Prochaine option : Phase 3 (sigma.js Anneaux + ML scatter + Master data). Ou pause pour tester sur Vercel + HF Spaces avec données réelles.
