# Déploiement Cloud Run + Cloud Scheduler (pilote ETI)

Cible : 3 services Cloud Run (api, streamlit, scheduler) + 1 Cloud Scheduler
job HTTP + 1 base PostgreSQL managée (Aiven, Neon ou Cloud SQL).

Temps total : **< 1 h** pour un pilote nominal, sans cluster Kubernetes ni VM.

## Architecture cible

```
                    ┌─────────────────────────┐
                    │   Cloud Scheduler       │
                    │  (HTTP, daily 06:00)    │
                    └──────────┬──────────────┘
                               │ POST /trigger
                               ▼
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   Streamlit  │ ───►  │  Scheduler (Run) │ ───►  │  PostgreSQL  │
│    (Run)     │       │ scheduler --once │       │   (Aiven)    │
└──────────────┘       └─────────┬────────┘       └──────────────┘
       │                         │
       ▼                         ▼
┌──────────────┐         ┌──────────────┐
│   API (Run)  │ ──────► │ Slack/Teams  │
│   FastAPI    │         │   Webhooks   │
└──────────────┘         └──────────────┘
```

## 1. Préparer PostgreSQL managé

Provisionner une base PG 14+ (recommandé Aiven Cloud `business-4` ou Cloud SQL
`db-custom-2-7680`). Récupérer l'URL :

```bash
export DATABASE_URL="postgresql://p2pfd:****@pg-host:5432/p2pfd"
alembic upgrade head        # crée le schéma — voir alembic/
```

## 2. Build et push des 3 images vers GHCR / Artifact Registry

```bash
# Tag courant
TAG=0.4.0
REPO=ghcr.io/ludoviclabs-dotcom

# API FastAPI
docker build -f Dockerfile -t $REPO/p2pfd-api:$TAG .
docker push $REPO/p2pfd-api:$TAG

# Streamlit
docker build -f Dockerfile.streamlit -t $REPO/p2pfd-streamlit:$TAG .
docker push $REPO/p2pfd-streamlit:$TAG

# Scheduler (image minimaliste, ~120 MB)
docker build -f Dockerfile.scheduler -t $REPO/p2pfd-scheduler:$TAG .
docker push $REPO/p2pfd-scheduler:$TAG
```

> Pour automatiser : `release.yml` (PR P4-6) build et push les 3 images au tag `v*.*.*`.

## 3. Déployer les 3 services Cloud Run

Variables d'environnement communes :

```bash
ENV_VARS="\
DATABASE_URL=$DATABASE_URL,\
SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL,\
OIDC_ISSUER=$OIDC_ISSUER,\
OIDC_CLIENT_ID=$OIDC_CLIENT_ID,\
OIDC_CLIENT_SECRET=$OIDC_CLIENT_SECRET,\
OIDC_SESSION_SECRET=$OIDC_SESSION_SECRET,\
FRAUD_API_SECRET=$FRAUD_API_SECRET,\
LOG_FORMAT=json,\
LOG_LEVEL=INFO"
```

### API

```bash
gcloud run deploy p2pfd-api \
  --image=$REPO/p2pfd-api:$TAG \
  --region=europe-west9 \
  --min-instances=1 --max-instances=3 \
  --memory=1Gi --cpu=1 \
  --port=8000 \
  --allow-unauthenticated \
  --set-env-vars="$ENV_VARS,OIDC_REDIRECT_URI=https://api-XYZ.run.app/oidc/callback,OIDC_POST_LOGIN_URL=https://streamlit-XYZ.run.app/"
```

### Streamlit

```bash
gcloud run deploy p2pfd-streamlit \
  --image=$REPO/p2pfd-streamlit:$TAG \
  --region=europe-west9 \
  --min-instances=1 --max-instances=2 \
  --memory=2Gi --cpu=2 \
  --port=8501 \
  --allow-unauthenticated \
  --set-env-vars="$ENV_VARS,OIDC_REDIRECT_URI=https://api-XYZ.run.app/oidc/callback"
```

> **Note OIDC** : les deux services partagent le même `OIDC_SESSION_SECRET` →
> les cookies signés par l'API sont lisibles par Streamlit (via `GET /oidc/me`).
> En prod, mettre l'API et Streamlit derrière le **même domaine** (Cloud Load
> Balancer + Cloud Run NEG) pour partager les cookies httponly.

### Scheduler (long-running)

```bash
gcloud run deploy p2pfd-scheduler \
  --image=$REPO/p2pfd-scheduler:$TAG \
  --region=europe-west9 \
  --min-instances=1 --max-instances=1 \
  --memory=512Mi --cpu=0.5 \
  --no-cpu-throttling \
  --args="--daily,06:00,--invoices,/data/invoices.parquet" \
  --set-env-vars="$ENV_VARS"
```

> `--no-cpu-throttling` : indispensable pour que APScheduler tique entre les
> requêtes (sinon Cloud Run gèle le CPU).

### Scheduler (single-shot via Cloud Scheduler)

Alternative : pas de container long-running, Cloud Scheduler invoque un job
Cloud Run Jobs daily.

```bash
# Créer le job
gcloud run jobs create p2pfd-scheduler-job \
  --image=$REPO/p2pfd-scheduler:$TAG \
  --region=europe-west9 \
  --args="--once,--invoices,/data/invoices.parquet" \
  --set-env-vars="$ENV_VARS"

# Cloud Scheduler — daily 06:00 Europe/Paris
gcloud scheduler jobs create http p2pfd-daily-detection \
  --location=europe-west9 \
  --schedule="0 6 * * *" \
  --time-zone="Europe/Paris" \
  --uri="https://europe-west9-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$(gcloud config get-value project)/jobs/p2pfd-scheduler-job:run" \
  --http-method=POST \
  --oauth-service-account-email=$RUNNER_SA
```

## 4. Vérifier le déploiement

```bash
# API health
curl https://api-XYZ.run.app/health
# {"status":"ok","version":"0.3.0","at":"..."}

# OIDC discovery côté API
curl https://api-XYZ.run.app/oidc/me
# 401 attendu (pas authentifié)

# Scheduler health
gcloud run services proxy p2pfd-scheduler --port 8080 &
docker run --rm $REPO/p2pfd-scheduler:$TAG --health
# {"channels":{"slack":true,...},...}
```

## 5. Surveiller

- **Logs** : Cloud Logging filtres `resource.labels.service_name="p2pfd-scheduler"`.
- **Métriques** : Cloud Monitoring sur les 3 services (latency p95, error rate, instance count).
- **Alerting** : Webhook Slack en cas d'erreur scheduler ≥ 3 runs consécutifs.

## Annexe : variables d'environnement

| Variable | Service | Description |
|---|---|---|
| `DATABASE_URL` | api, streamlit, scheduler | URL PostgreSQL |
| `SLACK_WEBHOOK_URL` | scheduler | Incoming webhook Slack |
| `TEAMS_WEBHOOK_URL` | scheduler | Incoming webhook Teams |
| `OIDC_ISSUER` | api, streamlit | URL issuer (Entra ID / Auth0 / Keycloak) |
| `OIDC_CLIENT_ID` | api, streamlit | Application ID |
| `OIDC_CLIENT_SECRET` | api | Client secret |
| `OIDC_REDIRECT_URI` | api, streamlit | URL callback (doit pointer vers l'API) |
| `OIDC_SESSION_SECRET` | api, streamlit | HMAC key (≥ 32 octets, partagée) |
| `FRAUD_API_SECRET` | api | Bearer token statique pour `/detect`, `/score` |
| `LOG_FORMAT` | tous | `json` (recommandé prod) ou `text` |
| `LOG_LEVEL` | tous | `INFO` (recommandé) ou `DEBUG` |
