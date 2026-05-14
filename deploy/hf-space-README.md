---
title: P2P Fraud Detective FR — API
emoji: 🛡️
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 8000
pinned: false
license: mit
short_description: Backend FastAPI — détection de fraude P2P / AML FR-native
---

# P2P Fraud Detective FR — Backend API

Backend FastAPI du démonstrateur **P2P Fraud Detective FR** — détection de
fraude sur le cycle Procure-to-Pay (Benford, Isolation Forest, NetworkX,
anneaux IBAN, sanctions OpenSanctions, DECP, RBE INPI).

Ce Space est **synchronisé automatiquement** depuis le dépôt GitHub
[`ludoviclabs-dotcom/p2p-fraud-detective-fr`](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr)
via le workflow `.github/workflows/hf-sync.yml`. Ne pas éditer directement ici.

## Endpoints

- `GET /health` — liveness probe
- `GET /docs` — documentation OpenAPI interactive (Swagger UI)
- `POST /detect`, `POST /detect/csv`, `POST /score` — détection & scoring
- `GET /api/v1/*` — 16 endpoints typés pour le frontend Next.js
- `GET /security/public-key` — clé publique Ed25519 (vérification audit trail)

## Configuration

Variables d'environnement (Settings → Variables and secrets) :

| Variable | Rôle |
|---|---|
| `FRAUD_API_SECRET` | Bearer token partagé avec le frontend Vercel |
| `DATABASE_URL` | PostgreSQL Neon (optionnel — SQLite `:memory:` sinon) |
| `ENRICHMENT_MODE` | `demo` (défaut) ou `live` |
| `ANTHROPIC_API_KEY` | Narration LLM Claude (optionnel) |
| `P2PFD_ED25519_PRIVATE_KEY` | Signatures audit trail (optionnel) |

## Frontend

Le frontend Next.js est déployé séparément sur Vercel et consomme cette API
via `NEXT_PUBLIC_API_URL`. Démo Streamlit legacy : voir le README GitHub.
