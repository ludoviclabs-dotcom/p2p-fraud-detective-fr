# Runbook — incidents communs

Réponse aux incidents pour le pilote ETI. Conçu pour qu'un astreinte L1 puisse
remettre le service en marche en < 30 minutes sans escalade.

## Diagnostic rapide

```bash
# 1. Healthchecks API + Streamlit
curl -fsS https://api.<domain>/health
curl -fsS https://streamlit.<domain>/_stcore/health

# 2. Métriques Prometheus
curl -s https://api.<domain>/metrics | grep -E 'http_request_duration|http_requests_total'

# 3. Scheduler — dernier run réussi ?
gcloud run jobs executions list --job=p2pfd-scheduler-job --region=europe-west9 --limit=5

# 4. Logs récents (Cloud Logging)
gcloud logging read 'resource.type=cloud_run_revision severity>=WARNING' --limit=20 --format=json
```

## Incidents courants

### 1. API renvoie 500/503

**Symptômes** : Streamlit affiche "API non joignable". `/health` retourne 5xx.

**Causes possibles** :
- Base PG down ou en lecture seule (failover Aiven)
- Sentry SDK init échoue (DSN invalide) → l'API démarre mais leve à chaque request
- `FRAUD_API_SECRET` rotaté côté env mais pas côté reverse proxy

**Action** :
```bash
# Inspecter le dernier crash dans Sentry
gcloud run services logs read p2pfd-api --region=europe-west9 --limit=50

# Si DB down :
gcloud sql instances describe <instance>          # ou Aiven console
# Bascule en read-only ? Failover manuel si HA configuré.

# Restart sans changer la révision :
gcloud run services update p2pfd-api --region=europe-west9 \
  --update-env-vars="LAST_RESTART=$(date +%s)"
```

### 2. OIDC issuer indisponible (Entra ID en outage)

**Symptômes** : `/oidc/login` retourne 502 ou les utilisateurs ne peuvent plus se connecter.

**Action** :
- Vérifier le statut Microsoft sur https://status.azure.com/
- Activer le mode dégradé : désactiver `OIDC_ISSUER` côté env → fallback sur le `text_input` utilisateur de la page Collaboration (mode démo).
  ```bash
  gcloud run services update p2pfd-api --region=europe-west9 \
    --remove-env-vars=OIDC_ISSUER
  ```
- Communiquer aux utilisateurs : « authentification dégradée jusqu'à rétablissement Microsoft ».

### 3. Scheduler stuck — aucun run depuis > 24h

**Symptômes** : Le dashboard Cockpit affiche les mêmes alertes que la veille. Aucune nouvelle entrée dans `audit_log` (kind=`case.*`).

**Action** :
```bash
# Si mode Cloud Scheduler (--once) :
gcloud scheduler jobs run p2pfd-daily-detection --location=europe-west9

# Si mode long-running (--daily) :
gcloud run services describe p2pfd-scheduler --region=europe-west9 | grep -i status
# Si CPU throttled : vérifier --no-cpu-throttling et min-instances=1

# Forcer un run manuel local :
docker run --rm --env-file .env \
  ghcr.io/ludoviclabs-dotcom/p2p-fraud-detective-fr-scheduler:latest \
  --once --invoices /data/invoices.parquet
```

### 4. Alertes Slack/Teams non livrées

**Symptômes** : Findings critiques détectés (visibles dans `audit_log`) mais aucune notif.

**Action** :
```bash
# Vérifier la config webhook
docker run --rm --env-file .env \
  ghcr.io/ludoviclabs-dotcom/p2p-fraud-detective-fr-scheduler:latest \
  --health
# Doit afficher channels.slack=true OU teams=true

# Tester le canal manuellement
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"test depuis runbook"}' \
  "$SLACK_WEBHOOK_URL"
```

Le retry tenacity (3 essais, backoff 1s→2s→4s) couvre les outages courts. Au-delà, l'erreur est journalisée dans `audit_log` (kind=`alert.dispatch_failed`).

### 5. Latence API dégradée (p95 > 1s)

**Symptômes** : Prometheus `/metrics` montre `http_request_duration_seconds_p95` qui explose.

**Action** :
```bash
# Top endpoints lents
curl -s https://api.<domain>/metrics | grep http_request_duration_seconds_bucket | sort -t' ' -k2 -nr | head

# Si /detect est lent : dataset trop gros ? Cap côté client.
# Si /cases est lent : index manquant — vérifier avec :
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM cases ORDER BY created_at DESC LIMIT 100;"
```

### 6. Erreurs de validation OIDC (signature invalide)

**Symptômes** : `/oidc/callback` retourne 401 "Validation JWT échouée".

**Causes** : rotation de la clé JWKS chez l'IdP (Microsoft rotate ~tous les 6 mois).

**Action** : le `JWKSCache` force un refresh quand le `kid` est introuvable — ce cas devrait s'auto-résoudre. Si persiste > 5 min :
```bash
# Restart l'API pour purger les caches en mémoire
gcloud run services update p2pfd-api --region=europe-west9 \
  --update-env-vars="LAST_RESTART=$(date +%s)"
```

## Escalade

| Niveau | Délai | Contact |
|---|---|---|
| L1 (ops astreinte) | 0-30 min | runbook + Sentry alerts |
| L2 (dev backend) | 30-60 min | `@p2pfd-backend` Slack |
| L3 (architecte) | > 1h | issue GitHub + page LCM |

## Métriques SLO

| Service | SLI | SLO | Mesuré sur |
|---|---|---|---|
| API | p95 latency `/detect` | < 500ms | 7j glissants |
| API | error rate 5xx | < 1% | 7j glissants |
| Streamlit | disponibilité `/health` | 99.5% | 30j |
| Scheduler | runs/jour réussis | ≥ 1 | 30j |
| Alertes critiques | latence dispatch | < 5 min | 24h |
