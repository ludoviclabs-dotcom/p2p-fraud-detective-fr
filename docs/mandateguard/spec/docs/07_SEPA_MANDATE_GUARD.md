# 07 — SEPA Mandate Guard

## Objectif

Créer un coffre-fort de mandats SEPA et analyser les prélèvements entrants afin de détecter :

- absence de mandat ;
- mandat révoqué ;
- RUM inconnue ;
- ICS incohérent ;
- montant supérieur au plafond ;
- périodicité anormale ;
- créancier nouveau ;
- prélèvements fractionnés.

## Entités métier

### Mandat

Champs principaux :

- `mandateId`
- `tenantId`
- `debtorAccountId`
- `creditorId`
- `creditorIcs`
- `rum`
- `scheme`: `SDD_CORE` ou `SDD_B2B`
- `status`
- `maxAmountCents`
- `frequency`
- `validFrom`
- `validTo`
- `signedAt`
- `revokedAt`
- `commitmentHash`

### Prélèvement observé

Champs principaux :

- `amountCents`
- `currency`
- `creditorIcs`
- `creditorNameRaw`
- `rum`
- `bookingDate`
- `dueDate`
- `debtorIbanFingerprint`
- `source`
- `idempotencyKey`

## Flux création mandat

1. L’utilisateur saisit les informations du mandat.
2. L’IBAN est normalisé.
3. L’IBAN est chiffré pour stockage.
4. Un fingerprint HMAC est généré pour recherche.
5. Le mandat est créé en `DRAFT`.
6. Une preuve de signature ou confirmation est ajoutée.
7. Le mandat passe en `ACTIVE`.
8. Un `commitmentHash` est calculé.
9. Un `AuditEvent` est créé.

## Flux révocation mandat

1. L’utilisateur demande la révocation.
2. Vérification des droits.
3. Passage du mandat à `REVOKED`.
4. Création d’une révision.
5. Calcul d’un nouveau commitment.
6. Audit `MANDATE_REVOKED`.
7. Les futurs prélèvements correspondant à ce mandat déclenchent une alerte critique.

## Matching prélèvement → mandat

Ordre recommandé :

1. `tenantId`
2. `debtorIbanFingerprint`
3. `creditorIcs`
4. `rum`
5. statut `ACTIVE`

Cas ambigus :

- RUM absente : chercher par IBAN + ICS, mais signaler `RUM_MISSING`.
- Nom créancier différent : ne pas bloquer seul, mais signaler `CREDITOR_NAME_MISMATCH`.
- Plusieurs mandats candidats : signaler `AMBIGUOUS_MANDATE_MATCH`.

## Pseudocode analyse SEPA

```ts
export async function assessSepaDirectDebit(command: AssessSepaCommand) {
  const event = normalizeSepaDebit(command.event);

  const mandate = await mandateRepository.findActiveCandidate({
    tenantId: command.tenantId,
    debtorIbanFingerprint: event.debtorIbanFingerprint,
    creditorIcs: event.creditorIcs,
    rum: event.rum,
  });

  const context = await buildSepaRiskContext({
    tenantId: command.tenantId,
    event,
    mandate,
  });

  const assessment = await sepaRiskEngine.assess(context);

  await riskRepository.saveAssessment({
    tenantId: command.tenantId,
    eventId: event.id,
    assessment,
  });

  if (assessment.score >= 60) {
    await alertService.createFromAssessment(assessment);
  }

  if (assessment.decision === "DISPUTE_READY") {
    await evidenceService.prepareSepaDisputePack(event.id);
  }

  return assessment;
}
```

## Evidence Pack SEPA

Un dossier de contestation doit contenir :

- identifiant du prélèvement ;
- montant ;
- date ;
- ICS ;
- RUM ;
- créancier brut ;
- mandat lié ou absence de mandat ;
- statut du mandat ;
- preuve de révocation le cas échéant ;
- signaux de risque ;
- timeline ;
- hash d’intégrité ;
- lettre de contestation générée depuis template.

## API future de vérification pré-débit

Endpoint futur :

```txt
POST /api/v1/verify/direct-debit
```

Réponse :

```json
{
  "decision": "BLOCK_RECOMMENDED",
  "score": 92,
  "signals": [
    { "code": "NO_ACTIVE_MANDATE", "severity": "critical" }
  ],
  "engineVersion": "sepa-sdd-v0.1.0"
}
```

Cette API ne bloque réellement que si une banque ou un PSP partenaire l’intègre.

