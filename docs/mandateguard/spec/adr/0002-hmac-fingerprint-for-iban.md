# ADR 0002 — Utiliser HMAC pour les fingerprints IBAN

## Statut

Accepté.

## Contexte

Le produit doit rechercher des mandats et prélèvements par IBAN sans stocker l’IBAN en clair.

Un hash simple d’IBAN est vulnérable aux attaques par dictionnaire car l’espace des IBAN est structuré.

## Décision

Utiliser un HMAC secret :

```txt
ibanFingerprint = HMAC_SHA256(IBAN_HMAC_SECRET, normalizedIban)
```

Stocker séparément :

- `ibanCiphertext` pour restitution autorisée ;
- `ibanFingerprint` pour recherche.

## Conséquences

Avantages :

- recherche possible ;
- meilleure protection qu’un hash simple ;
- compatible multi-tenant.

Points d’attention :

- rotation de secret à prévoir ;
- secret stocké dans KMS ou secret manager ;
- ne jamais exposer le fingerprint comme donnée publique stable.

