# Instructions pour Claude Code — MandateGuard

Tu travailles sur **MandateGuard**, une plateforme de sécurité des flux bancaires. Le MVP est un outil d’analyse, d’archivage, de détection, de preuve et d’assistance. Il ne doit pas initier de paiement.

## Règles non négociables

- Ne jamais logger d’IBAN complet, de nom complet, de PDF mandat, de signature, de payload bancaire brut ou de document sensible.
- Utiliser des fingerprints HMAC pour rechercher les IBAN.
- Chiffrer tous les champs sensibles au repos.
- Ne jamais mettre de données personnelles dans le ledger ou dans une blockchain.
- Les décisions de risque doivent être explicables et basées d’abord sur des règles déterministes.
- Les LLM peuvent expliquer, classifier ou rédiger, mais ne doivent jamais être le seul décideur de fraude.
- Toute entrée API doit être validée avec Zod.
- Toute règle de risque doit avoir des tests unitaires.
- Tout endpoint d’ingestion doit être idempotent.
- Toute action sensible doit créer un `AuditEvent`.
- Toutes les requêtes multi-tenant doivent vérifier explicitement `tenantId`.
- Les webhooks doivent être signés et protégés contre le replay.
- Les clés API doivent être hashées au repos.

## Architecture attendue

- App web dans `apps/web`.
- Logique métier dans `packages/`.
- Pas de logique métier lourde directement dans les route handlers.
- Prisma pour la persistance.
- Zod pour les schémas d’entrée/sortie.
- `packages/risk-core` ne doit pas dépendre de Next.js.
- `packages/sepa-sdd` contient les règles liées aux prélèvements SEPA.
- `packages/p2p-integrity` contient les règles liées aux paiements sortants/fournisseurs.
- `packages/evidence` construit les dossiers de preuve.
- `packages/ledger` gère l’audit log append-only et vérifiable.
- `packages/ai` masque les données avant toute utilisation LLM.

## Commandes qualité à exécuter avant de considérer une tâche terminée

```bash
pnpm typecheck
pnpm lint
pnpm test
```

Si des tests E2E existent pour le flux touché :

```bash
pnpm test:e2e
```

## Style de code

- TypeScript strict.
- Petites fonctions testables.
- Types explicites pour les objets de domaine.
- Erreurs métier nommées.
- Pas d’`any` sauf justification dans un commentaire.
- Pas de secrets codés en dur.
- Pas de données réelles dans les fixtures.

## Définition of Done

Une tâche est terminée seulement si :

1. Le code compile.
2. Les tests passent.
3. Les chemins d’erreur sont gérés.
4. Les données sensibles sont masquées ou chiffrées.
5. Les actions sensibles sont auditées.
6. La documentation touchée est mise à jour.

