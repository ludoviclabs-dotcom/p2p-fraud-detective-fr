# Agent Instructions

Ce fichier sert aux agents de code compatibles avec les instructions de dépôt.

## Product summary

MandateGuard is a Payment Integrity Platform composed of:

- SEPA Direct Debit mandate vault and risk engine.
- Supplier/payment integrity risk engine.
- Shared risk core, evidence pack builder and audit ledger.

## Hard constraints

- Do not implement payment initiation in the MVP.
- Do not store full IBANs in plain text.
- Do not log PII.
- Use HMAC fingerprints for IBAN lookup.
- Use encrypted storage for sensitive fields and documents.
- Keep LLMs out of final fraud decision-making.
- Keep risk decisions explainable.
- Every detection rule requires unit tests.
- Every API endpoint requires Zod validation.
- Respect tenant isolation.

## Preferred implementation order

1. Workspace and packages.
2. Prisma schema.
3. Crypto helpers.
4. Mandate vault.
5. Risk core.
6. SEPA rules.
7. P2P rules.
8. Evidence pack.
9. Audit ledger.
10. UI screens.
11. Deployment configuration.

