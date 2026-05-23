# Manifest des documents

## Fichiers racine

- `README.md` : vue d’ensemble du dossier.
- `CLAUDE.md` : instructions principales pour Claude Code.
- `AGENTS.md` : instructions génériques pour agents de code.

## Spécifications produit et architecture

- `docs/01_PRODUCT_SCOPE.md` : périmètre produit, modules, MVP, non-objectifs.
- `docs/02_ARCHITECTURE_VISUELLE.md` : diagrammes Mermaid.
- `docs/03_ARCHITECTURE_CODE.md` : architecture du monorepo, packages, responsabilités.
- `docs/04_DATA_MODEL_PRISMA.md` : modèle de données cible Prisma.
- `docs/05_API_CONTRACTS.md` : endpoints et contrats JSON.
- `docs/06_RISK_ENGINE.md` : moteur d’analyse et de détection.
- `docs/07_SEPA_MANDATE_GUARD.md` : module prélèvements SEPA et mandats.
- `docs/08_P2P_PAYMENT_INTEGRITY.md` : module paiements sortants/fournisseurs.
- `docs/09_EVIDENCE_LEDGER.md` : evidence pack et ledger d’audit.
- `docs/10_SECURITY_RGPD_COMPLIANCE.md` : sécurité, RGPD, conformité.
- `docs/11_AI_MODULE.md` : module IA, redaction, limites.
- `docs/12_UI_UX_ROUTES.md` : routes et écrans.
- `docs/13_DEPLOYMENT_VERCEL.md` : déploiement Vercel et worker externe.
- `docs/14_TESTING_STRATEGY.md` : tests unitaires, intégration, E2E, sécurité.
- `docs/15_ROADMAP_BACKLOG.md` : roadmap par phases.
- `docs/16_PROMPTS_CLAUDE_CODEX.md` : prompts prêts à coller.
- `docs/17_REFERENCES_A_VALIDER.md` : références à relire avant production.

## ADR

- `adr/0001-no-public-chain-for-pii.md`
- `adr/0002-hmac-fingerprint-for-iban.md`
- `adr/0003-risk-engine-not-llm-first.md`
- `adr/0004-python-worker-for-heavy-analytics.md`

## Backlog

- `backlog/SPRINT_00_SETUP.md`
- `backlog/SPRINT_01_MANDATE_VAULT.md`
- `backlog/SPRINT_02_RISK_ENGINE.md`
- `backlog/SPRINT_03_EVIDENCE_LEDGER.md`
- `backlog/SPRINT_04_UI_AND_DEPLOY.md`

