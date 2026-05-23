# Sprint 02 — Risk Engine SEPA

## Objectif

Analyser un prélèvement SEPA avec un score explicable.

## Tâches

- [ ] Implémenter `packages/risk-core`.
- [ ] Implémenter reason codes.
- [ ] Implémenter scoring.
- [ ] Implémenter `packages/sepa-sdd`.
- [ ] Ajouter règles SEPA v0.
- [ ] Ajouter endpoint `/api/v1/debits/analyze`.
- [ ] Créer alertes si score élevé.
- [ ] Ajouter fixtures synthétiques.
- [ ] Ajouter golden tests.

## Critères d’acceptation

- Prélèvement avec mandat actif = `ALLOW`.
- Prélèvement sans mandat = `DISPUTE_READY`.
- Mandat révoqué = `DISPUTE_READY`.
- Montant supérieur plafond = alerte critique.
- Chaque signal est explicable.

