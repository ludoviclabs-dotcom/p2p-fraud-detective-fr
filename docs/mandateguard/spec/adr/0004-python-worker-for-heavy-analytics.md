# ADR 0004 — Worker Python pour analytics lourdes

## Statut

Proposé.

## Contexte

Le module P2P peut nécessiter pandas, fuzzy matching massif, NetworkX, scikit-learn et batch CSV/Excel volumineux.

Ces traitements sont moins adaptés à des API synchrones serverless.

## Décision

Garder le chemin critique en TypeScript sur Vercel.

Externaliser les traitements lourds dans un worker Python appelé via queue.

## Conséquences

Avantages :

- API rapide ;
- analytics plus puissante ;
- séparation claire ;
- meilleure scalabilité batch.

Inconvénients :

- une infrastructure supplémentaire ;
- gestion des callbacks ;
- observabilité multi-service.

