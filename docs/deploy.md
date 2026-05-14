# Déploiement — P2P Fraud Detective FR v0.6.0

> Guide consolidé : tag release + backend FastAPI (HF Spaces) + frontend Next.js (Vercel).
> Cible : free tier strict, 0 €/mois. Voir aussi [`migration-v2-recap.md`](./migration-v2-recap.md).

## Vue d'ensemble

```
┌─────────────────┐     REST /api/v1/*      ┌──────────────────────┐
│  Vercel         │ ──────────────────────► │  Hugging Face Spaces │
│  Next.js v2     │ ◄────── SSE LLM ─────── │  FastAPI (Docker)    │
│  apps/web/      │                         │  src/p2p_fraud/      │
└─────────────────┘                         └──────────┬───────────┘
                                                        │ SQLAlchemy
                                            ┌───────────▼──────────┐
                                            │  Neon (PostgreSQL)   │
                                            │  free 0.5 GB         │
                                            └──────────────────────┘
Streamlit Cloud (legacy v0.5) reste actif sur son URL d'origine,
indépendamment — même backend Python, aucune migration de données.
```

## 1. Tag release `v0.6.0`

Déclenche `release.yml` → build 3 images Docker (api, streamlit, scheduler) sur GHCR.

Via l'UI GitHub :
1. https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/releases/new
2. **Choose a tag** → taper `v0.6.0` → « Create new tag: v0.6.0 on publish »
3. **Target** : `main`
4. **Release title** : `v0.6.0 — Migration v2 Next.js livrée (8 phases)`
5. **Description** : copier la section `[0.6.0]` du [`CHANGELOG.md`](../CHANGELOG.md)
6. **Publish release**

Suivi du build : https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/actions

## 2. Backend FastAPI → Hugging Face Spaces

HF Spaces offre un vrai free tier Docker (16 GB RAM, pas de sleep), seule option gratuite viable pour FastAPI en 2026.

### Création du Space

1. https://huggingface.co/new-space
2. **Space name** : `p2p-fraud-detective-api`
3. **License** : MIT
4. **Space SDK** : **Docker** → « Blank »
5. **Hardware** : CPU basic (gratuit)
6. Visibilité : Public ou Private au choix

### Configuration — déploiement automatisé (recommandé)

Le workflow [`.github/workflows/hf-sync.yml`](../.github/workflows/hf-sync.yml)
synchronise automatiquement le backend vers le Space HF. **Aucune manipulation
git côté HF** — il suffit d'ajouter 2 secrets GitHub :

1. **Générer un token HF** : https://huggingface.co/settings/tokens → « New token »
   → rôle **Write** → copier le token.

2. **Ajouter les secrets GitHub** : Settings → Secrets and variables → Actions
   → New repository secret :
   | Secret | Valeur |
   |---|---|
   | `HF_TOKEN` | le token HF write généré ci-dessus |
   | `HF_SPACE_ID` | `<user>/p2p-fraud-detective-api` (ex. `ludoviclabs/p2p-fraud-detective-api`) |

3. **Déclencher le sync** :
   - Manuel : onglet **Actions** → « Sync backend → Hugging Face Spaces » → « Run workflow »
   - Automatique : à chaque tag `v*.*.*` poussé

Le workflow assemble le bundle (`src/`, `data/`, `Dockerfile`, deps + `README.md`
généré depuis `deploy/hf-space-README.md`) et le force-push vers le Space. HF
build l'image Docker (~3-5 min).

### Configuration — manuelle (alternative)

Si tu préfères pousser à la main depuis ton poste :
```bash
git clone https://huggingface.co/spaces/<user>/p2p-fraud-detective-api hf-space
cd hf-space
cp -r ../p2p-fraud-detective-fr/src ../p2p-fraud-detective-fr/data .
cp ../p2p-fraud-detective-fr/Dockerfile ../p2p-fraud-detective-fr/pyproject.toml ../p2p-fraud-detective-fr/requirements.txt .
cp ../p2p-fraud-detective-fr/deploy/hf-space-README.md README.md
git add . && git commit -m "Deploy FastAPI backend" && git push
```

### Variables d'environnement (Settings → Variables and secrets)

| Variable | Valeur | Obligatoire |
|---|---|---|
| `FRAUD_API_SECRET` | secret bearer partagé avec Vercel | recommandé |
| `DATABASE_URL` | URL Neon (cf. §4) | si persistance souhaitée |
| `ENRICHMENT_MODE` | `demo` ou `live` | non (défaut `demo`) |
| `PAPPERS_API_KEY` | clé Pappers | non (mode live RBE) |
| `ANTHROPIC_API_KEY` | clé Claude | non (narration LLM) |
| `P2PFD_ED25519_PRIVATE_KEY` | clé Ed25519 base64 | non (signatures audit) |
| `WEBHOOK_URL` / `WEBHOOK_SECRET` | SIEM destinataire | non |

URL résultante : `https://<user>-p2p-fraud-detective-api.hf.space`

Smoke test : `curl https://<user>-p2p-fraud-detective-api.hf.space/health`

## 3. Frontend Next.js → Vercel

### Import du projet

1. https://vercel.com/new → Import `ludoviclabs-dotcom/p2p-fraud-detective-fr`
2. Vercel détecte automatiquement `vercel.json` à la racine :
   - **Framework** : Next.js (auto)
   - **Build Command** : `pnpm --filter @p2pfd/web build` (depuis vercel.json)
   - **Install Command** : `pnpm install --frozen-lockfile` (depuis vercel.json)
   - **Output Directory** : `apps/web/.next` (depuis vercel.json)
3. **Root Directory** : laisser à la racine du repo (le `vercel.json` gère le ciblage `apps/web`).

> Si Vercel demande quand même un Root Directory, mettre `apps/web` et il ignorera le `vercel.json` racine — les deux approches fonctionnent.

### Variables d'environnement (Settings → Environment Variables)

| Variable | Valeur |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<user>-p2p-fraud-detective-api.hf.space` |
| `FRAUD_API_SECRET` | même valeur que côté HF Spaces |

### Déploiement

`Deploy` → URL `https://<projet>.vercel.app`. Chaque push sur `main` redéploie automatiquement (cf. `vercel.json` → `git.deploymentEnabled.main`).

Smoke test :
- `https://<projet>.vercel.app/` → landing
- `https://<projet>.vercel.app/dashboard` → Cockpit avec KPI live depuis HF Spaces

## 4. Base de données → Neon (optionnel)

Sans `DATABASE_URL`, le backend utilise SQLite `:memory:` (données perdues au redémarrage du Space — acceptable pour démo).

Pour la persistance :
1. https://neon.tech → New Project (free tier 0.5 GB, scale-to-zero)
2. Copier la connection string `postgresql://...`
3. La définir comme `DATABASE_URL` dans les variables HF Spaces
4. Les tables sont créées automatiquement au boot (`Base.metadata.create_all`)

## 5. Domaine custom (optionnel, ~ 5 €/an)

Recommandé pour les pilotes ETI réels — permet les cookies OIDC cross-subdomain :
- `app.votre-domaine.fr` → CNAME vers Vercel
- `api.votre-domaine.fr` → CNAME vers HF Spaces
- Permet `OIDC_REDIRECT_URI=https://app.votre-domaine.fr/api/auth/callback`
  et cookies `Domain=.votre-domaine.fr`

## Checklist de mise en production

- [ ] Tag `v0.6.0` poussé → 3 images GHCR publiées
- [ ] HF Space créé, `/health` répond 200
- [ ] `FRAUD_API_SECRET` identique côté HF et Vercel
- [ ] Vercel déployé, `/dashboard` affiche des KPI
- [ ] `ENRICHMENT_MODE=live` testé si pilote (sinon `demo`)
- [ ] Streamlit Cloud legacy toujours accessible (non impacté)
- [ ] `docs/migration-v2-recap.md` Roadmap Phase 9+ revue selon priorités pilote

## Coût mensuel total (free tier strict)

| Service | Plan | Coût |
|---|---|---|
| Vercel | Hobby | 0 € |
| Hugging Face Spaces | CPU basic | 0 € |
| Neon | Free | 0 € |
| Streamlit Cloud | Community | 0 € |
| GHCR (images Docker) | Public | 0 € |
| **Total** | | **0 €/mois** |

Coûts variables uniquement si activés : Anthropic API (narration LLM, ~ 0.01 €/génération), domaine custom (~ 5 €/an).
