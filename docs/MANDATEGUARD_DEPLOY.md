# Déploiement MandateGuard — checklist Sprint 5

Topologie cible :

```
[Vercel]                    [Backend Python]
Next.js (apps/web)   ──▶    FastAPI (Railway / Fly.io / Render / VM)
  ├─ /risk-lab-sepa             ├─ /api/v1/mandates
  ├─ /mandates (TODO)           ├─ /api/v1/debits/{import,analyze}
  └─ /api/v1/[...path]          ├─ /api/v1/evidence/{create,verify,report}
       (proxy)                  ├─ /api/v1/risk/assess
                                └─ /api/v1/webhooks/debit (signé)
                                       │
                                       ├─ Postgres (mandats, debits, evidence)
                                       └─ Object storage (rapports HTML)
```

## Variables d'environnement

### Côté Vercel (Next.js)

| Variable | Valeur | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://api.mandateguard.fr` | URL publique du backend FastAPI |

### Côté backend (FastAPI)

| Variable | Obligatoire | Description |
|---|:-:|---|
| `DATABASE_URL` | ✅ | URL SQLAlchemy Postgres en prod, ex. `postgresql+psycopg2://user:pass@host:5432/dbname` |
| `P2P_FRAUD_DATA_KEY` | ✅ | Clé Fernet (44 chars) pour chiffrement IBAN au repos |
| `IBAN_HMAC_SECRET` | ✅ | Secret HMAC séparé pour fingerprint IBAN (rotation indépendante) |
| `WEBHOOK_INBOUND_SECRET` | ✅ pour pilote | Secret HMAC partagé avec le PSP/banque qui pousse les prélèvements |
| `FRAUD_API_SECRET` | ✅ | Bearer token pour auth API (à remplacer par OIDC en B2B) |
| `P2PFD_ED25519_PRIVATE_KEY` | ⚠️ | Clé privée Ed25519 pour signer l'audit chain (sinon hash-chain SHA-256 seul) |
| `OIDC_*` | optionnel | Microsoft Entra ID / Auth0 / Keycloak — voir `config.py` |
| `WEBHOOK_URL` + `WEBHOOK_SECRET` | optionnel | Webhook SORTANT pour pousser les events cases vers un SIEM |
| `SENTRY_DSN` | recommandé | Observabilité erreurs |
| `LOG_LEVEL` | optionnel | `INFO` (défaut) ou `DEBUG` |
| `LOG_FORMAT` | optionnel | `text` (défaut) ou `json` (recommandé en prod) |

### Génération des secrets

```bash
# Fernet (P2P_FRAUD_DATA_KEY)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# HMAC secrets (IBAN_HMAC_SECRET, WEBHOOK_INBOUND_SECRET)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Ed25519 (P2PFD_ED25519_PRIVATE_KEY)
python -c "from p2p_fraud.security.signing import Ed25519Signer; print(Ed25519Signer.generate().private_key_b64)"
```

## Étapes de déploiement

### 1. Backend FastAPI

```bash
# 1. Provisionner Postgres + créer la DB
createdb mandateguard_prod

# 2. Définir les env vars (cf. table ci-dessus)
export DATABASE_URL=...
export P2P_FRAUD_DATA_KEY=...
export IBAN_HMAC_SECRET=...
export WEBHOOK_INBOUND_SECRET=...
export FRAUD_API_SECRET=...

# 3. Lancer les migrations (5 migrations Alembic)
alembic upgrade head

# 4. Démarrer le serveur (gunicorn recommandé)
gunicorn -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 30 \
  p2p_fraud.api.main:app
```

### 2. Frontend Vercel

```bash
# Depuis apps/web (ou via l'intégration GitHub)
vercel --prod
# Définir NEXT_PUBLIC_API_URL dans Vercel project settings
```

Le `vercel.json` inclut :
- headers de sécurité (HSTS, X-Frame-Options, Referrer-Policy)
- cache-control no-store sur `/api/*` (la fraîcheur prime sur la perf pour les verdicts)
- déploiement région `cdg1` (souveraineté française des données)

## Sécurité — checklist pré-pilote

- [ ] `DATABASE_URL` pointe vers Postgres avec backups quotidiens activés
- [ ] Tous les secrets stockés dans un secret manager (Vercel envs, Railway envs, AWS Secrets Manager…), jamais en clair dans le repo
- [ ] `IBAN_HMAC_SECRET` ≠ `P2P_FRAUD_DATA_KEY` (rotations indépendantes)
- [ ] `WEBHOOK_INBOUND_SECRET` partagé out-of-band avec le PSP/banque
- [ ] Migrations Alembic appliquées : `alembic current` affiche `d3e4f5a6b7c8 (head)`
- [ ] Test end-to-end pilote : créer mandat → signer → ingérer prélèvement → vérifier evidence pack
- [ ] Rate limiting devant FastAPI (cloudflare, nginx, Vercel WAF…)
- [ ] Logs prod sans PII (vérifier `LOG_FORMAT=json` + redaction côté logger)
- [ ] Endpoint `POST /api/v1/webhooks/debit` testé avec le secret du PSP
- [ ] Audit log Ed25519 activé (`P2PFD_ED25519_PRIVATE_KEY` défini)

## Webhook entrant : intégration PSP

Le PSP (ou la banque) qui pousse les prélèvements doit signer chaque requête :

```python
import hmac, hashlib, json
from datetime import datetime, UTC

body = json.dumps({
    "source": "psp",
    "idempotency_key": "psp-evt-2026-001",
    "creditor_ics": "FR18ZZZ002305",
    "creditor_name_raw": "EDF SA",
    "rum": "RUM-EDF-001",
    "amount_cents": 8900,
    "currency": "EUR",
    "debtor_iban": "FR7630001007941234567890185",
}, separators=(",", ":")).encode("utf-8")

signature = "sha256=" + hmac.new(SHARED_SECRET, body, hashlib.sha256).hexdigest()

# POST https://api.mandateguard.fr/api/v1/webhooks/debit
# Headers :
#   X-MG-Timestamp: <ISO8601 UTC, ex. 2026-05-23T10:00:00Z>
#   X-MG-Signature: sha256=<hex>
#   X-MG-Idempotency-Key: psp-evt-2026-001
#   Content-Type: application/json
```

Réponse : HTTP 202 avec le verdict d'analyse :

```json
{
  "received_at": "2026-05-23T10:00:00+00:00",
  "idempotency_key": "psp-evt-2026-001",
  "analysis": {
    "event_id": "dbt-...",
    "decision": "DISPUTE_READY" | "BLOCK_RECOMMENDED" | "REVIEW" | "ALERT_USER" | "ALLOW_MONITOR" | "ALLOW",
    "score": 80,
    "level": "CRITICAL",
    "engine_version": "sepa-v0.1.0",
    "signals": [...]
  }
}
```

## Observabilité minimale recommandée

| Métrique | Source | Alerte si |
|---|---|---|
| Latence p95 `/api/v1/debits/analyze` | Sentry / Prometheus | > 500 ms |
| Taux d'erreur 5xx | Sentry | > 1 % sur 5 min |
| Webhooks rejetés (signature/replay) | logs structurés | spike anormal |
| Audit chain integrity | cron `verify_chain()` | KO une seule fois |
| Couverture tests | CI | < 75 % |
