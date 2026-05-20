# API Risk Score

`POST /api/risk/score` score une transaction synthétique P2P ou Procure-to-Pay.

## Requête

Le body accepte directement une transaction ou un objet `{ "transaction": ... }`.

Champs minimum :

- `transactionId`
- `createdAt`
- `amount`
- `currency`
- `rail`
- `payer.id`
- `beneficiary.id`
- `beneficiary.iban`

## Réponse

```json
{
  "score": 91,
  "level": "CRITICAL",
  "decision": "BLOCK_RECOMMENDED",
  "typology": "APP_FRAUD_BANK_IMPERSONATION",
  "reasonCodes": [],
  "detectorScores": [],
  "recommendedActions": [],
  "modelVersion": "risk-engine-demo-v1",
  "generatedAt": "2026-05-20T09:30:00.000Z"
}
```

## Scénarios

`GET /api/risk/scenarios` retourne six scénarios synthétiques. Si
`HF_SYNTHETIC_SCENARIOS_URL` est configurée, l'API tente de charger la source
Hugging Face côté serveur. En cas d'absence, timeout ou payload invalide, elle
retombe sur les scénarios locaux versionnés dans le repo.

## Evidence Pack

`POST /api/evidence/export` retourne :

- `evidencePack` JSON ;
- `printableHtml` pour impression ou revue.

## Tests de validation

- `GET /api/risk/scenarios` doit retourner 6 scénarios synthétiques et un
  `disclaimer`.
- `POST /api/risk/score` doit toujours borner le score entre 0 et 100.
- Un faux conseiller bancaire doit produire un niveau `CRITICAL`.
- Un paiement normal doit produire `LOW` ou `MEDIUM`.
- Les cas IBAN mismatch, urgence narrative et QR mismatch doivent générer des
  reason codes explicables.
- `POST /api/evidence/export` doit inclure `caseId`, `transaction`, `score`,
  `reasonCodes`, `detectorScores`, `timeline`, `graphSummary`,
  `recommendedActions`, `analystNotes`, `auditTrail` et `disclaimer`.

## Configuration Hugging Face / Vercel

La source Hugging Face est optionnelle et doit rester serveur :

```txt
HF_SYNTHETIC_SCENARIOS_URL=https://...
HF_TOKEN=hf_... # uniquement si dataset privé
```

Si l'URL est absente, en timeout ou retourne un payload invalide, l'API utilise
les scénarios locaux versionnés. Ce fallback doit être visible dans l'interface.

## Limites

Cette API est un démonstrateur professionnel. Elle n'exécute aucune décision
bancaire réelle, ne collecte pas de données personnelles réelles et n'est pas
une certification conformité.
