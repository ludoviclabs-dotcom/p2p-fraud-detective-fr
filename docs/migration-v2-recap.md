# Migration v2 — Récap final (mai 2026)

> Migration Streamlit → Next.js 15 livrée en **8 phases sur une session** de
> travail intensive. Plan d'ensemble : [`migration-v2.md`](./migration-v2.md).
> Statut : ✅ tout livré · prêt pour déploiement utilisateur sur Vercel + HF Spaces.

## Vue d'ensemble

| Phase | Sujet | Routes ajoutées | PR |
|---|---|---|---|
| 0 | Monorepo + 12 endpoints + Cockpit | 3 (`/`, `/dashboard`, `/_not-found`) | [#28](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/28) |
| 1 | Types OpenAPI + UI primitives + /cases + /audit + OIDC | +3 (`/cases`, `/audit`, `/api/auth/[...slug]`) | [#29](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/29) |
| 2 | /findings + /vendors + /vendors/[id] + /score waterfall | +4 | [#30](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/30) |
| 3a | /anomalies + /master-history + /sanctions | +3 | [#31](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/31) |
| 3b | /rings sigma.js | +1 | [#32](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/32) |
| 4a | 5 contrôles + ControlPage component | +5 | [#33](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/33) |
| 4b | /upload (drag-drop streaming) + /exports (PDF & CSV) | +2 | [#34](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/34) |
| 5 | /alerts (polling 5s) + /methodology + /governance + /collab | +4 | [#35](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/35) |
| 6 | /tour (5 étapes) + LLM streaming Vendor 360° | +1 | [#36](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/36) |
| 7 | /sandbox (5 scénarios) + i18n FR/EN sélecteur sidebar | +1 | [#37](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/pull/37) |
| **8** | **CHANGELOG + bump v0.6.0 + récap (ce doc)** | — | en cours |

**Total : 26 routes Next.js + 27 endpoints API v1.**

## Stack v2 livrée

| Couche | Technologie |
|---|---|
| Frontend framework | Next.js 15.5 App Router + React 19 + Turbopack |
| Styling | Tailwind CSS v4 + shadcn-style components locaux |
| Charts | Recharts 3.8 (sparklines, scatter, waterfall) + sigma.js + graphology + ForceAtlas2 |
| State client | TanStack Query 5.66 + Zustand-free (state local par page) |
| i18n | LocaleProvider custom (FR/EN, localStorage, ~30 clés) |
| LLM streaming | SSE bout-en-bout via `fetch()` + ReadableStream parser |
| Auth | OIDC via proxy `/api/auth/[...slug]` → FastAPI |
| Upload | Multipart streaming Route Handler `runtime: "nodejs"` |
| Backend | FastAPI inchangé (`src/p2p_fraud/`) + 15 endpoints `/api/v1/*` typés Pydantic |
| Types TS | `openapi-typescript@7` régénération via Makefile |

## Métriques

| Métrique | v0.5 (Streamlit) | v0.6 (+ Next.js v2) |
|---|---|---|
| Routes interactives | 21 pages Streamlit | 21 + 26 routes Next.js |
| Endpoints REST | 11 | 27 |
| Tests Python | 370 | 370 (zéro régression) |
| Composants UI | Streamlit primitives | 5 composants shadcn-style + 1 ControlPage |
| Bundle Next.js First Load JS | — | 103 kB shared + 0-130 kB par route |
| Build time | ~ 2 min | + ~ 30 sec Next.js (turbopack) |

## Points forts

1. **Zéro régression backend** : 370 tests Python verts, Streamlit Cloud inchangé.
2. **Coexistence parfaite** : Streamlit legacy + Next.js v2 partagent le même backend FastAPI.
3. **Types bout-en-bout** : changer une signature Pydantic casse le typecheck Next.js (garde-fou contractuel).
4. **Réutilisation max** : composant `<ControlPage>` (5 pages contrôles en ~30 lignes chacune), `<LlmNarrativeStream>` autonome.
5. **Free tier strict respecté** : Vercel + HF Spaces + Neon — 0 €/mois pour la démo publique.
6. **i18n minimaliste** : 30 clés × 2 langues sans dépendance externe (`react-intl`/`next-i18next` évités).

## Limitations connues

- **OIDC cookies cross-domain** : non testé en production (le proxy Next.js → FastAPI fonctionne en local, mais les sessions HMAC cross-vercel.app/hf.space restent à valider en pilote).
- **SSE alertes** : `GET /api/v1/alerts/stream` expose maintenant l'audit log
  en Server-Sent Events, avec proxy Next.js `/api/alerts/stream` et fallback
  polling 5s lorsque le backend public n'est pas configuré.
- **Endpoint `/api/v1/vendors` (liste)** : agrégation client suffit < 1000 cases. À ajouter en backend si pilote > 1k cases.
- **i18n contenu inline** : seules les clés `nav.*` et `common.*` sont traduites — les contenus pages restent FR. Migration progressive au fil du besoin.
- **Tests front automatises** : socle Vitest en place sur la logique pure
  alertes, cockpit demo et workflow case
  (`apps/web/lib/alerts-feed.ts`, `demo-cockpit.ts`, `case-workflow.ts`).
  Baseline Playwright deja posee sur les parcours cockpit, rings, score et
  alerts. Les prochaines extensions utiles concernent surtout les composants
  critiques cote DOM et les derniers golden paths metier.

## Effort réel vs plan d'origine

| Estimation plan d'origine ([migration-v2.md](./migration-v2.md)) | Effort réel session |
|---|---|
| 95 jours-homme sur 16 semaines à temps partiel | **1 session intensive** (toute la migration livrée d'un coup) |

Le plan d'origine prévoyait 6 mois à temps partiel. La livraison effective a tenu sur quelques heures grâce à :
- Réutilisation maximale du backend Python existant (zéro réécriture)
- Composants UI primitives développés sur place (pas de shadcn CLI)
- Pages contrôles factorisées via `<ControlPage>` config-driven
- Pas de migration de données (Streamlit Cloud reste source de vérité)
- Tests typecheck TS + pytest Python + premiers tests Vitest front ciblés

## Actions manuelles utilisateur post-merge

1. **Hugging Face Spaces** — déployer le backend FastAPI :
   - https://huggingface.co/new-space → Type Docker
   - Connecter au repo GitHub `p2p-fraud-detective-fr`
   - Variable d'env : `FRAUD_API_SECRET=...`
   - URL résultante : `https://<user>-<space>.hf.space`

2. **Vercel** — déployer le frontend Next.js :
   - https://vercel.com/new → Import GitHub `p2p-fraud-detective-fr`
   - **Root Directory : `apps/web`**
   - Variables d'env :
     - `NEXT_PUBLIC_API_URL` = URL HF Spaces
     - `FRAUD_API_SECRET` = même valeur que côté HF
   - Deploy → URL `https://<projet>.vercel.app`

3. **Tag v0.6.0** — créer la release via UI GitHub :
   - https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/releases/new
   - Tag : `v0.6.0`
   - Title : `v0.6.0 — Migration v2 Next.js livrée (8 phases)`
   - Description : copier la section `[0.6.0]` du CHANGELOG.md
   - Publish → release.yml déclenche le build GHCR (3 images Docker)

4. **Optionnel — domaine custom** :
   - Acheter `votre-domaine.fr` (Namecheap ~ 5 €/an)
   - DNS : `app.votre-domaine.fr` (CNAME → Vercel) + `api.votre-domaine.fr` (CNAME → HF Spaces)
   - Permet cookies OIDC `Domain=.votre-domaine.fr` (cross-subdomain)

## Roadmap post-v0.6.0

| Phase | Sujet | Effort | Priorité |
|---|---|---|---|
| 9 | Etendre la couverture front automatisee (Vitest composants/DOM + Playwright golden paths) | 3 j | Si pilote ETI signe |
| 10 | Durcir SSE alertes (auth fine, replay durable, backpressure) | 2 j | Si volume > 100 events/min |
| 11 | i18n complet contenu inline | 5 j | Si demande pilote international |
| 12 | OIDC bout-en-bout production (cross-domain validé) | 3 j | Bloquant pilote bancaire |
| 13 | Connecteur ERP natif (SAP/Sage) | 10 j | Sur appel d'offres |
| 14 | WORM S3 archivage légal Sapin 2 | 5 j | Quand budget AWS |

**Total roadmap restant** : ~ 28 j sur 6 mois selon priorisation pilote.

## Bilan

La Migration v2 est **livrée fonctionnellement complète** dans le périmètre du
plan d'origine. La plateforme dispose désormais d'une **double UX** :

- **Streamlit Cloud** (`https://...streamlit.app/`) — démo publique gratuite,
  itérations rapides côté analyste/auditeur
- **Next.js sur Vercel** (à déployer) — cible commerciale ETI, design fintech
  contemporain, performance, types bout-en-bout

Les deux UX partagent le même backend FastAPI Python, la même base de cases,
le même audit log Ed25519. Aucune duplication de logique métier.

Décision pending : **basculer ou garder les deux** :
- **Si demande ETI confirmée** → bascule sur Next.js seul, Streamlit en sous-domaine `legacy.*` 6 mois puis archivage
- **Si phase d'observation** → garder les deux UX, capter les retours sur les deux interfaces
