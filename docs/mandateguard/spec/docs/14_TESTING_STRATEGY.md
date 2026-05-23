# 14 — Stratégie de tests

## Objectifs

Garantir :

- exactitude des règles ;
- non-régression du scoring ;
- sécurité des données ;
- isolation tenant ;
- absence de PII dans les logs ;
- fonctionnement des flows clés.

## Tests unitaires

Packages à tester :

- `crypto`
- `risk-core`
- `sepa-sdd`
- `p2p-integrity`
- `ledger`
- `evidence`
- `ai/redact`

Exemples :

```txt
crypto/hmac.test.ts
crypto/masking.test.ts
risk-core/scoring.test.ts
sepa-sdd/no-active-mandate.test.ts
sepa-sdd/amount-exceeds-limit.test.ts
p2p/supplier-rib-recent-change.test.ts
ledger/append-event.test.ts
ai/redact.test.ts
```

## Tests d’intégration

Scénarios :

1. création mandat ;
2. signature/activation mandat ;
3. révocation mandat ;
4. import prélèvement valide ;
5. import prélèvement sans mandat ;
6. analyse montant supérieur plafond ;
7. création alerte ;
8. génération evidence pack ;
9. analyse paiement fournisseur avec RIB récent.

## Tests E2E

Flux Playwright :

- utilisateur crée un mandat ;
- utilisateur importe un prélèvement ;
- une alerte est générée ;
- utilisateur ouvre l’alerte ;
- utilisateur génère un evidence pack ;
- utilisateur exporte le dossier.

## Tests sécurité

Obligatoires :

- un tenant A ne peut pas lire les mandats du tenant B ;
- API sans auth refusée ;
- rôle `MEMBER` ne peut pas modifier les règles ;
- webhook non signé refusé ;
- webhook replay refusé ;
- logs ne contiennent pas d’IBAN ;
- redaction IA bloque les patterns IBAN ;
- evidence pack non public sans auth.

## Fixtures

Toutes les fixtures doivent être synthétiques.

Interdit :

- vrai IBAN ;
- vrai mandat ;
- vrai nom de personne ;
- documents clients.

## Golden tests de scoring

Créer des scénarios stables :

```txt
scenario_sepa_valid_mandate.json -> ALLOW
scenario_sepa_no_mandate.json -> DISPUTE_READY
scenario_sepa_revoked_mandate.json -> DISPUTE_READY
scenario_p2p_recent_rib_change.json -> BLOCK_RECOMMENDED
scenario_p2p_duplicate_invoice.json -> REVIEW
```

Les scores ne doivent pas changer sans décision explicite.

## CI minimale

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

CI complète :

```bash
pnpm test:e2e
pnpm test:security
```

