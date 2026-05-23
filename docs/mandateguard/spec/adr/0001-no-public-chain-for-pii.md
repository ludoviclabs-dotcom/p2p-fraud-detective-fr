# ADR 0001 — Ne pas utiliser de blockchain publique pour les données personnelles

## Statut

Accepté.

## Contexte

Le produit manipule des IBAN, mandats, signatures, historiques de prélèvements et dossiers de contestation.

Ces données sont sensibles et parfois personnelles. Une blockchain publique est immuable et difficilement compatible avec la suppression ou la rectification.

## Décision

Le MVP n’utilise pas de blockchain publique contenant des données personnelles.

Les données complètes sont stockées hors chaîne, chiffrées.

Le ledger ne contient que :

- hashes ;
- commitments ;
- event ids ;
- timestamps ;
- previousHash ;
- eventHash.

## Conséquences

Avantages :

- meilleure conformité ;
- moins de fuite de données ;
- architecture plus simple ;
- preuve d’intégrité suffisante pour le MVP.

Inconvénients :

- pas de décentralisation réelle au départ ;
- besoin d’un mécanisme futur d’ancrage tiers si nécessaire.

