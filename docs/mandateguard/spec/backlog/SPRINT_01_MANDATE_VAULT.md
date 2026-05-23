# Sprint 01 — Mandate Vault

## Objectif

Créer, lister, activer et révoquer des mandats SEPA.

## Tâches

- [ ] Implémenter schéma Prisma mandat.
- [ ] Implémenter `packages/crypto`.
- [ ] Implémenter `createMandate`.
- [ ] Implémenter `signMandate` simulé.
- [ ] Implémenter `revokeMandate`.
- [ ] Implémenter audit events.
- [ ] Créer routes API mandats.
- [ ] Créer UI liste mandats.
- [ ] Créer UI nouveau mandat.
- [ ] Ajouter tests unitaires et intégration.

## Critères d’acceptation

- Aucun IBAN en clair dans DB hors champ chiffré.
- Création mandat fonctionne.
- Révocation mandat fonctionne.
- Audit log créé pour création/signature/révocation.
- UI affiche IBAN masqué.

