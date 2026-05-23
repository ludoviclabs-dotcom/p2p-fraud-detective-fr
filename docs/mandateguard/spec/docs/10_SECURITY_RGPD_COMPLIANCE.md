# 10 — Sécurité, RGPD et conformité

Ce document ne remplace pas un avis juridique. Il sert de garde-fou produit et technique.

## Principes

- Minimisation des données.
- Chiffrement des données sensibles.
- Séparation stricte par tenant.
- Pas de PII dans le ledger.
- Pas de PII dans les logs.
- Pas de données réelles dans les fixtures.
- Export et suppression des données utilisateur.
- Décisions de risque explicables.

## Données sensibles

Données à considérer sensibles :

- IBAN ;
- nom/prénom ;
- raison sociale liée à une personne ;
- mandat PDF ;
- signature ;
- preuve d’identité ;
- historique de prélèvements ;
- historique de paiements ;
- documents fournisseurs ;
- payload bancaire brut.

## Stratégie IBAN

Pour chaque IBAN :

1. normaliser : suppression espaces, uppercase ;
2. chiffrer pour stockage : `ibanCiphertext` ;
3. générer un HMAC pour recherche : `ibanFingerprint` ;
4. afficher uniquement masqué : `FR76 **** **** **** 1234`.

Exemple :

```ts
export function maskIban(iban: string) {
  const normalized = iban.replace(/\s+/g, "").toUpperCase();
  if (normalized.length < 8) return "****";
  return `${normalized.slice(0, 4)} **** **** **** ${normalized.slice(-4)}`;
}
```

## Logs

Interdit dans les logs :

- IBAN complet ;
- nom complet ;
- PDF ;
- signature ;
- payload brut ;
- clé API ;
- secret ;
- token de session.

Utiliser un logger qui redacted automatiquement :

```ts
logger.info("Debit analyzed", {
  tenantId,
  debitEventId,
  creditorIcsMasked,
  score,
  decision,
});
```

## Auth et RBAC

Rôles :

- `OWNER` : gestion tenant et clés.
- `ADMIN` : règles, utilisateurs, configuration.
- `ANALYST` : analyse, cases, evidence packs.
- `MEMBER` : lecture et actions utilisateur.

Toutes les requêtes DB doivent filtrer par `tenantId` sauf services admin internes explicitement encadrés.

## Webhooks

- Signature HMAC.
- Timestamp requis.
- Fenêtre de tolérance courte.
- Détection replay.
- Idempotency key.

## LLM / IA

Avant tout appel LLM :

- redacter IBAN ;
- retirer noms complets si non nécessaires ;
- remplacer IDs internes par pseudonymes ;
- ne transmettre que les reason codes, montants, dates approximatives si possible ;
- ne jamais envoyer PDF mandat brut.

## Conformité paiement

Le MVP doit rester hors initiation de paiement.

Dès que le produit fournit des services d’information sur comptes, d’initiation de paiement ou d’exécution de paiement, il faut vérifier le statut réglementaire nécessaire : partenariat PSP, agent, enregistrement ou agrément.

## Signature électronique

Une signature “clé privée maison” n’est pas équivalente à une signature électronique qualifiée.

Pour un produit sérieux :

- prévoir une intégration avec un prestataire de signature ;
- conserver preuve, horodatage et empreinte ;
- distinguer signature simple, avancée et qualifiée ;
- documenter la valeur probatoire attendue.

## Blockchain / ledger

Interdit :

- mettre un IBAN en clair dans une blockchain ;
- mettre un mandat complet dans une blockchain ;
- mettre des données personnelles immuables sans mécanisme de suppression.

Acceptable :

- hash/commitment ;
- audit hash chain ;
- Merkle root ;
- registre permissionné futur ;
- données complètes hors chaîne et chiffrées.

## Checklist sécurité avant prod

- [ ] Auth forte configurée.
- [ ] RBAC testé.
- [ ] Tenant isolation testée.
- [ ] Secrets hors repo.
- [ ] IBAN jamais loggé.
- [ ] LLM redaction testée.
- [ ] Webhooks signés.
- [ ] API rate limiting.
- [ ] Backups DB testés.
- [ ] Export RGPD disponible.
- [ ] Suppression/anonymisation disponible.
- [ ] Audit log vérifiable.
- [ ] Revue juridique effectuée.

