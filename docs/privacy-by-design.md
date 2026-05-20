# Privacy By Design

Le Workbench est conçu pour rester démontrable sans données personnelles réelles.

## Principes

- Données synthétiques par défaut.
- Aucun token Hugging Face exposé au navigateur.
- Fallback local si la source Hugging Face est absente ou indisponible.
- Pas de fingerprinting réel : les signaux device sont des flags de démo.
- Pas de dark web scraping.
- Pas de promesse de détection bancaire production-grade.
- Décision finale humaine.

## Hugging Face

Les variables `HF_SYNTHETIC_SCENARIOS_URL` et `HF_SYNTHETIC_CASES_URL` peuvent
pointer vers des datasets JSON synthétiques. Si un dataset privé est utilisé,
`HF_TOKEN` doit rester côté serveur dans l'environnement Vercel ou local.

## Evidence Pack

L'evidence pack exporté contient les champs nécessaires à la démonstration :
transaction synthétique, score, reason codes, détecteurs, timeline, graphe,
notes analyste et audit trail simulé.
