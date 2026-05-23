# 09 — Evidence Pack et Audit Ledger

## Objectif

Pouvoir prouver :

- ce qui a été observé ;
- quand l’événement a été reçu ;
- quelles règles ont été appliquées ;
- quels signaux ont été produits ;
- quelle décision a été recommandée ;
- quels documents existaient à ce moment ;
- que le dossier n’a pas été modifié silencieusement.

## Evidence Pack

Un evidence pack est un dossier exportable lié à un risque ou une contestation.

### Structure logique

```txt
EvidencePack
├── metadata.json
├── event.json
├── assessment.json
├── findings.json
├── timeline.json
├── linked-records.json
├── audit-proof.json
├── documents/
│   ├── mandate-redacted.pdf
│   └── source-redacted.json
└── report.html / report.pdf
```

### Champs metadata

```json
{
  "evidencePackId": "evp_123",
  "tenantId": "tenant_abc",
  "caseId": "case_123",
  "createdAt": "2026-05-23T10:00:00Z",
  "formatVersion": "1.0.0",
  "hash": "sha256..."
}
```

## Ledger d’audit

Le ledger d’audit est un journal append-only hashé.

Il ne contient pas de données personnelles en clair.

Chaque événement contient :

- `tenantId` ;
- `actorId` ;
- `action` ;
- `subjectType` ;
- `subjectId` ;
- `dataHash` ;
- `previousHash` ;
- `eventHash` ;
- `createdAt`.

## Calcul du hash

```ts
import { createHash } from "node:crypto";
import canonicalize from "canonicalize";

export function computeAuditEventHash(input: {
  tenantId?: string;
  actorId?: string;
  action: string;
  subjectType: string;
  subjectId: string;
  dataHash: string;
  previousHash?: string;
}) {
  const canonical = canonicalize({
    tenantId: input.tenantId ?? null,
    actorId: input.actorId ?? null,
    action: input.action,
    subjectType: input.subjectType,
    subjectId: input.subjectId,
    dataHash: input.dataHash,
    previousHash: input.previousHash ?? null,
  });

  if (!canonical) throw new Error("Unable to canonicalize audit event");
  return createHash("sha256").update(canonical).digest("hex");
}
```

## Événements d’audit obligatoires

- `MANDATE_CREATED`
- `MANDATE_SIGNED`
- `MANDATE_REVOKED`
- `DEBIT_IMPORTED`
- `DEBIT_ANALYZED`
- `RISK_CASE_CREATED`
- `ALERT_CREATED`
- `ALERT_ACKNOWLEDGED`
- `DISPUTE_CREATED`
- `EVIDENCE_PACK_CREATED`
- `API_KEY_CREATED`
- `WEBHOOK_RECEIVED`
- `RULE_ENABLED`
- `RULE_DISABLED`

## Ancrage Merkle futur

Une fois par jour :

1. prendre tous les `AuditEvent` de la période ;
2. construire un Merkle root ;
3. stocker un `LedgerAnchor` ;
4. éventuellement publier ce root auprès d’un tiers ou d’un registre externe.

Le MVP peut se limiter à Postgres append-only + hash chain.

## Vérification

Endpoint :

```txt
POST /api/v1/evidence/:id/verify
```

Réponse :

```json
{
  "valid": true,
  "evidencePackId": "evp_123",
  "hashMatches": true,
  "auditChainValid": true,
  "checkedAt": "2026-05-23T10:00:00Z"
}
```

