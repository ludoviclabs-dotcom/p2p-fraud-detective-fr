# 03 — Architecture code

## Monorepo cible

```txt
mandateguard/
  apps/
    web/
      app/
        (public)/
        (app)/
          dashboard/
          mandates/
          debits/
          alerts/
          cases/
          risk-lab/
          detection-studio/
          evidence/
          admin/
        api/
          v1/
            mandates/
            debits/
            risk/
            alerts/
            disputes/
            evidence/
            webhooks/
          cron/
      components/
      lib/
      middleware.ts

  packages/
    domain/
      src/
        types.ts
        errors.ts
        money.ts
        idempotency.ts

    db/
      prisma/
        schema.prisma
        migrations/
      src/
        client.ts
        repositories/

    crypto/
      src/
        hmac.ts
        encryption.ts
        masking.ts
        canonical-json.ts

    risk-core/
      src/
        types.ts
        rule.ts
        engine.ts
        scoring.ts
        decision.ts
        reason-codes.ts
        orchestrator.ts

    sepa-sdd/
      src/
        mandate-vault.ts
        debit-analyzer.ts
        sepa-normalizer.ts
        creditor-id.ts
        rules/
          no-active-mandate.ts
          mandate-revoked.ts
          amount-exceeds-limit.ts
          rum-mismatch.ts
          ics-mismatch.ts
          unusual-frequency.ts

    p2p-integrity/
      src/
        beneficiary-risk.ts
        supplier-payment-risk.ts
        invoice-risk.ts
        rules/
          new-beneficiary.ts
          supplier-rib-recent-change.ts
          four-eyes-breach.ts
          duplicate-invoice.ts
          split-payment.ts
        adapters/
          python-worker-client.ts
          local-demo-client.ts

    evidence/
      src/
        build-pack.ts
        render-html.ts
        render-json.ts
        render-pdf.ts
        storage.ts

    ledger/
      src/
        append-event.ts
        verify-chain.ts
        merkle.ts
        adapters/
          postgres-ledger.ts
          mock-ledger.ts

    ai/
      src/
        redact.ts
        explain-risk.ts
        dispute-draft.ts
        prompts.ts

    notifications/
      src/
        email.ts
        sms.ts
        webhook.ts

    observability/
      src/
        logger.ts
        metrics.ts
        audit.ts

  services/
    p2p-analytics-worker/
      src/
        p2p_fraud/
          ingestion/
          detectors/
          scoring/
          graph/
          export/
      pyproject.toml

  docs/
  adr/
  backlog/
  CLAUDE.md
  AGENTS.md
  package.json
  pnpm-workspace.yaml
  turbo.json
  vercel.json
```

## Règles de dépendance

```txt
apps/web -> packages/*
packages/sepa-sdd -> packages/risk-core, domain, db, crypto, ledger
packages/p2p-integrity -> packages/risk-core, domain, db, crypto
packages/risk-core -> packages/domain uniquement
packages/evidence -> domain, db, ledger
packages/ai -> domain uniquement + client LLM
packages/db -> Prisma uniquement
```

`risk-core` doit rester pur et testable : aucune dépendance Next.js, Prisma ou Vercel.

## Contrat d’un package métier

Chaque package métier doit fournir :

- types exportés ;
- services applicatifs ;
- tests unitaires ;
- fixtures synthétiques ;
- erreurs métier ;
- aucune dépendance directe à l’UI.

## Pattern route handler

Un route handler Next.js ne doit faire que :

1. authentifier ;
2. valider l’entrée Zod ;
3. appeler un service applicatif ;
4. mapper la réponse HTTP ;
5. gérer les erreurs connues.

Exemple :

```ts
export async function POST(req: Request) {
  const session = await requireSession();
  const body = CreateMandateSchema.parse(await req.json());

  const result = await createMandate({
    tenantId: session.tenantId,
    actorId: session.userId,
    input: body,
  });

  return Response.json(result, { status: 201 });
}
```

## Pattern service applicatif

Un service applicatif contient :

- validations métier ;
- accès repository ;
- audit ;
- idempotence ;
- appels à d’autres packages.

```ts
export async function analyzeDebit(command: AnalyzeDebitCommand) {
  const normalized = normalizeDebit(command.input);
  const event = await debitRepository.upsertByIdempotencyKey(normalized);
  const context = await buildSepaRiskContext(command.tenantId, event);
  const assessment = await sepaRiskEngine.assess(context);
  await riskRepository.saveAssessment(event.id, assessment);
  await ledger.append({ action: "DEBIT_ANALYZED", subjectId: event.id });
  return assessment;
}
```

## Convention de noms

- `*Input` : entrée API validée.
- `*Command` : entrée service avec contexte auth.
- `*Context` : données enrichies pour une décision.
- `*Result` : sortie métier.
- `*Repository` : accès DB.
- `*Rule` : règle déterministe de risque.
- `*Adapter` : intégration externe.

