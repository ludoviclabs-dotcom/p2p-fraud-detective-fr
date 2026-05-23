# 16 — Prompts prêts à coller dans Claude Code / Codex

## Prompt 1 — Initialisation monorepo

```txt
Lis CLAUDE.md, AGENTS.md et docs/00_MANIFEST.md.

Crée le squelette du monorepo MandateGuard avec :
- Next.js App Router dans apps/web
- TypeScript strict
- pnpm workspaces
- Prisma dans packages/db
- packages/domain, crypto, risk-core, sepa-sdd, p2p-integrity, evidence, ledger, ai
- Vitest
- ESLint/Prettier

Ne crée pas encore de logique paiement.
Ajoute des scripts pnpm : typecheck, lint, test, build.
Respecte toutes les règles PII de CLAUDE.md.
```

## Prompt 2 — Prisma schema

```txt
Implémente le schéma Prisma à partir de docs/04_DATA_MODEL_PRISMA.md.

Ajoute :
- migration initiale
- client Prisma dans packages/db/src/client.ts
- repositories de base pour Tenant, User, Mandate, DebitEvent, RiskAssessment, AuditEvent
- seed avec données 100 % synthétiques et IBAN fictifs uniquement

Ne logge aucune donnée sensible.
```

## Prompt 3 — Crypto package

```txt
Implémente packages/crypto.

Fonctions :
- normalizeIban
- maskIban
- ibanFingerprint par HMAC SHA-256
- encryptField/decryptField avec interface adaptable KMS
- canonicalJson

Ajoute tests unitaires :
- HMAC stable
- masquage correct
- normalisation correcte
- aucune fonction ne logge l’IBAN
```

## Prompt 4 — Risk Core

```txt
Implémente packages/risk-core à partir de docs/06_RISK_ENGINE.md.

Créer :
- types Severity, RiskSignal, RiskDecision, RiskAssessmentResult
- interface RiskRule
- RiskEngine générique
- combineSignals
- toLevel
- decide
- reason-codes registry

Ajoute tests unitaires pour scoring et décisions.
```

## Prompt 5 — SEPA Engine v0

```txt
Implémente packages/sepa-sdd.

Créer :
- types SepaDebitEvent, SepaRiskContext
- normalizer
- matcher mandat
- règles : NO_ACTIVE_MANDATE, MANDATE_REVOKED, AMOUNT_EXCEEDS_LIMIT, RUM_MISMATCH, ICS_MISMATCH, UNUSUAL_FREQUENCY
- sepaRiskEngine

Ajoute fixtures synthétiques et tests unitaires pour chaque règle.
```

## Prompt 6 — API Analyse prélèvement

```txt
Implémente POST /api/v1/debits/analyze.

Contraintes :
- auth obligatoire
- validation Zod
- idempotencyKey obligatoire
- tenant isolation
- appelle packages/sepa-sdd
- sauvegarde DebitEvent et RiskAssessment
- crée Alert si score >= seuil
- crée AuditEvent DEBIT_ANALYZED

Ajoute tests d’intégration.
```

## Prompt 7 — Evidence + Ledger

```txt
Implémente packages/ledger et packages/evidence.

Ledger :
- append event
- compute event hash
- verify chain

Evidence :
- build JSON pack
- render HTML report
- compute hash
- store metadata EvidencePack

Ajouter endpoint POST /api/v1/evidence et GET /api/v1/evidence/:id.
```

## Prompt 8 — UI MVP

```txt
Construis l’UI MVP dans apps/web :
- /dashboard
- /mandates
- /mandates/new
- /debits
- /alerts
- /alerts/:id
- /risk-lab
- /evidence/:id

Utilise données masquées.
Affiche les reason codes clairement.
Une alerte doit montrer : score, niveau, signaux, action recommandée et bouton evidence pack.
```

## Prompt 9 — P2P module v0

```txt
Implémente packages/p2p-integrity.

Domaine : SUPPLIER_PAYMENT.
Règles :
- NEW_BENEFICIARY
- NEW_IBAN
- IBAN_RECENTLY_ADDED
- SUPPLIER_RIB_RECENT_CHANGE
- FOUR_EYES_BREACH
- DUPLICATE_INVOICE simple
- SPLIT_PAYMENTS simple

Expose le domaine via POST /api/v1/risk/assess.
Ajoute Risk Lab pour SUPPLIER_PAYMENT.
```

## Prompt 10 — IA explicative

```txt
Implémente packages/ai.

Créer :
- redactRiskInput
- explainRiskAlert
- draftSepaDisputeLetter
- fallback templates sans IA

Tests obligatoires :
- refuser payload contenant IBAN complet
- ne jamais envoyer rawJson complet au modèle
- produire une explication même sans IA
```

