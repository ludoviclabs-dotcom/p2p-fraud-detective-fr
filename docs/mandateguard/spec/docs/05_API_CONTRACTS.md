# 05 — Contrats API

Toutes les APIs doivent :

- vérifier l’authentification ;
- vérifier `tenantId` ;
- valider l’entrée avec Zod ;
- retourner des erreurs structurées ;
- être idempotentes pour les endpoints d’ingestion ;
- créer des événements d’audit pour les actions sensibles.

## Endpoints principaux

### Mandats

```txt
POST   /api/v1/mandates
GET    /api/v1/mandates
GET    /api/v1/mandates/:id
POST   /api/v1/mandates/:id/sign
POST   /api/v1/mandates/:id/revoke
GET    /api/v1/mandates/:id/evidence
```

### Prélèvements

```txt
POST   /api/v1/debits/import
POST   /api/v1/debits/analyze
GET    /api/v1/debits
GET    /api/v1/debits/:id
GET    /api/v1/debits/:id/assessment
```

### Risk Core

```txt
POST   /api/v1/risk/assess
POST   /api/v1/risk/batch
GET    /api/v1/risk/cases
GET    /api/v1/risk/cases/:id
```

### Alertes

```txt
GET    /api/v1/alerts
POST   /api/v1/alerts/:id/ack
POST   /api/v1/alerts/:id/dismiss
POST   /api/v1/alerts/:id/dispute
```

### Evidence

```txt
POST   /api/v1/evidence
GET    /api/v1/evidence/:id
GET    /api/v1/evidence/:id/download
POST   /api/v1/evidence/:id/verify
```

### API future PSP / banque

```txt
POST   /api/v1/verify/direct-debit
```

## `POST /api/v1/risk/assess`

Endpoint central pour tous les domaines de risque.

### Requête SEPA

```json
{
  "riskDomain": "SEPA_DIRECT_DEBIT",
  "idempotencyKey": "debit_2026_05_23_001",
  "event": {
    "amountCents": 100000,
    "currency": "EUR",
    "creditorIcs": "FR18ZZZ002305",
    "creditorNameRaw": "EXEMPLE SA",
    "rum": "RUM-123",
    "debtorIbanFingerprint": "hmac_abc",
    "bookingDate": "2026-05-23"
  }
}
```

### Requête P2P / fournisseur

```json
{
  "riskDomain": "SUPPLIER_PAYMENT",
  "idempotencyKey": "payment_2026_05_23_001",
  "event": {
    "amountCents": 1840000,
    "currency": "EUR",
    "supplierName": "ALPHACOM SERVICES",
    "siren": "812446901",
    "ibanFingerprint": "hmac_xyz",
    "previousIbanFingerprint": "hmac_prev",
    "ribChangedHoursAgo": 18,
    "paymentReference": "F-2026-04419"
  }
}
```

### Réponse

```json
{
  "score": 92,
  "level": "CRITICAL",
  "decision": "BLOCK_RECOMMENDED",
  "engineVersion": "risk-core-v0.1.0",
  "domain": "SUPPLIER_PAYMENT",
  "signals": [
    {
      "code": "SUPPLIER_RIB_RECENT_CHANGE",
      "severity": "critical",
      "score": 28,
      "message": "IBAN fournisseur modifié récemment avant paiement",
      "evidence": {
        "ribChangedHoursAgo": 18
      }
    }
  ],
  "evidencePackId": "evp_123"
}
```

## Codes d’erreur standard

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": []
  }
}
```

Codes :

- `UNAUTHORIZED`
- `FORBIDDEN`
- `VALIDATION_ERROR`
- `NOT_FOUND`
- `IDEMPOTENCY_CONFLICT`
- `TENANT_MISMATCH`
- `RATE_LIMITED`
- `INTERNAL_ERROR`

## Idempotence

Les endpoints suivants doivent accepter une clé d’idempotence :

- import prélèvement ;
- analyse prélèvement ;
- analyse risk core ;
- création evidence pack ;
- webhooks.

Règle : à même `tenantId + idempotencyKey`, le service doit retourner la même ressource créée initialement ou une erreur d’incompatibilité si le payload diffère.

## Webhooks signés

Header attendu :

```txt
X-MG-Timestamp: 2026-05-23T10:00:00Z
X-MG-Signature: sha256=<hmac>
```

Protection :

- vérifier horodatage ;
- refuser replay ;
- vérifier signature HMAC ;
- stocker webhook event idempotent.

