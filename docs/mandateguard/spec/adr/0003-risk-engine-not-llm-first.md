# ADR 0003 — Le moteur de risque n’est pas LLM-first

## Statut

Accepté.

## Contexte

Les décisions de risque doivent être explicables, testables et auditables.

Un LLM peut halluciner, varier dans le temps et exposer des risques de confidentialité.

## Décision

Le moteur de risque v0 est basé sur :

- règles déterministes ;
- reason codes ;
- scoring explicable ;
- tests unitaires ;
- evidence pack.

Le LLM est limité à :

- explication ;
- résumé ;
- rédaction ;
- classification non critique.

## Conséquences

Avantages :

- auditabilité ;
- reproductibilité ;
- confiance utilisateur ;
- meilleure conformité.

Inconvénients :

- moins flexible au début ;
- nécessite d’ajouter manuellement des règles.

