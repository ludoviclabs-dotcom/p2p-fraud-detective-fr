# 13 — Déploiement Vercel

## Cible

Vercel héberge :

- l’app Next.js ;
- les API routes ;
- les webhooks ;
- les cron jobs ;
- les jobs légers ;
- l’orchestration des analyses.

Un worker externe peut héberger :

- analytics Python lourd ;
- pandas ;
- scikit-learn ;
- NetworkX ;
- imports CSV/Excel volumineux.

## Variables d’environnement

```bash
DATABASE_URL=
APP_URL=

AUTH_SECRET=
SESSION_ENCRYPTION_KEY=

IBAN_HMAC_SECRET=
LEDGER_HMAC_SECRET=
FIELD_ENCRYPTION_KEY=
KMS_KEY_ID=

AI_GATEWAY_API_KEY=

WEBHOOK_SIGNING_SECRET=
API_KEY_PEPPER=

EMAIL_PROVIDER_API_KEY=
SMS_PROVIDER_API_KEY=

SENTRY_DSN=
LOG_LEVEL=info
```

## `vercel.json`

```json
{
  "crons": [
    {
      "path": "/api/cron/rebuild-risk-profiles",
      "schedule": "0 2 * * *"
    },
    {
      "path": "/api/cron/anchor-ledger",
      "schedule": "0 3 * * *"
    }
  ]
}
```

## Environnements

### Preview

- base de données preview ou branchée ;
- données synthétiques uniquement ;
- IA désactivable ;
- logs détaillés mais sans PII.

### Production

- secrets séparés ;
- rate limiting ;
- alerting ;
- backups ;
- monitoring ;
- audit activé ;
- redaction obligatoire.

## Déploiement recommandé

```bash
pnpm install
pnpm typecheck
pnpm lint
pnpm test
pnpm build
vercel deploy
```

## Worker Python externe

Options possibles :

- petit service containerisé ;
- job runner ;
- plateforme serverless compatible Python data ;
- machine dédiée batch.

Contrat :

```txt
Vercel Queue -> worker poll -> traitement -> callback API signé
```

## Observabilité

À instrumenter :

- nombre d’analyses ;
- score moyen ;
- alertes créées ;
- faux positifs ;
- temps de réponse API ;
- échecs worker ;
- coûts IA ;
- erreurs de redaction ;
- webhooks rejetés.

## Checklist avant production

- [ ] `DATABASE_URL` prod configurée.
- [ ] Secrets générés hors repo.
- [ ] Migrations testées.
- [ ] Seed prod désactivé.
- [ ] Logs sans PII.
- [ ] Rate limiting activé.
- [ ] Backups activés.
- [ ] Monitoring actif.
- [ ] Alertes erreurs configurées.
- [ ] Tests E2E critiques passés.

