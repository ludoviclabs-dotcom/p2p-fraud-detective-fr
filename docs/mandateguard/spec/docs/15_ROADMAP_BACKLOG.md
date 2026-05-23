# 15 — Roadmap et backlog

## Phase 0 — Cadrage

Livrables :

- périmètre MVP ;
- non-objectifs réglementaires ;
- architecture validée ;
- choix stockage/chiffrement ;
- plan de tests ;
- documents `CLAUDE.md` et `AGENTS.md`.

Critère de fin : le projet est prêt à être codé sans ambiguïté majeure.

## Phase 1 — Setup technique

Livrables :

- monorepo pnpm ;
- Next.js App Router ;
- Prisma ;
- packages vides ;
- CI ;
- lint/typecheck/test ;
- déploiement Vercel preview.

## Phase 2 — Crypto + DB

Livrables :

- schéma Prisma ;
- migrations ;
- client DB ;
- HMAC IBAN ;
- masking ;
- chiffrement champs ;
- audit event hash.

## Phase 3 — Mandate Vault

Livrables :

- création mandat ;
- liste mandats ;
- activation/signature simulée ;
- révocation ;
- commitment hash ;
- audit events.

## Phase 4 — Risk Core

Livrables :

- types ;
- rule interface ;
- scoring ;
- decisions ;
- reason codes ;
- tests.

## Phase 5 — SEPA Engine

Livrables :

- normalisation prélèvement ;
- matching mandat ;
- règles SEPA v0 ;
- endpoint `/api/v1/debits/analyze` ;
- alertes.

## Phase 6 — Evidence Pack + Ledger

Livrables :

- génération pack JSON ;
- génération HTML ;
- hash pack ;
- vérification ledger ;
- export.

## Phase 7 — UI MVP

Livrables :

- dashboard ;
- liste mandats ;
- création mandat ;
- liste prélèvements ;
- détail alerte ;
- evidence view ;
- risk lab.

## Phase 8 — P2P module v0

Livrables :

- `SUPPLIER_PAYMENT` domain ;
- règles nouveaux bénéficiaires ;
- règle RIB récent ;
- règle four-eyes ;
- règle doublon simple ;
- UI risk lab P2P.

## Phase 9 — IA explicative

Livrables :

- redaction ;
- explication d’alerte ;
- lettre contestation template + IA ;
- fallback sans IA ;
- tests de non-fuite.

## Phase 10 — Worker Python

Livrables :

- service worker ;
- contrat JSON ;
- batch analysis ;
- graph analysis ;
- callback signé ;
- observabilité.

## Priorité absolue pour le MVP

1. sécurité données ;
2. moteur explicable ;
3. evidence pack ;
4. expérience utilisateur claire ;
5. déploiement simple ;
6. pas d’ambiguïté réglementaire.

