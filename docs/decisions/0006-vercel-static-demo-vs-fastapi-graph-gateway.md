# ADR-0006 - Demo graphe Vercel statique avant passerelle FastAPI

- Statut : Accepte
- Date : 2026-05-18

## Contexte

La page Next.js `/rings` publie un graphe d'investigation P2P lisible sur Vercel
sans runtime Python. Le dataset est genere par `scripts/export_p2p_graph_demo.py`
depuis les detecteurs Python existants, puis servi par des routes Next internes.

Deux options restent possibles pour la suite :

- continuer avec un JSON statique versionne, adapte a la demo publique et aux
  previews Vercel ;
- ouvrir une passerelle Next vers FastAPI pour exposer des donnees quasi-live.

## Decision

On reste en **demo statique Vercel** pour `/rings` et le breakdown du dashboard.
La passerelle FastAPI est classee **LATER**, pas **GO**.

Le contrat `P2PDemoDataset` reste la forme cible : il doit pouvoir etre produit
par le script statique aujourd'hui, puis par une API Python demain sans refonte
du front.

## Conditions pour passer en GO API

- FastAPI expose un endpoint graphe dedie, par exemple `/api/v1/graph`, avec le
  meme contrat logique que `P2PDemoDataset`.
- Les IBAN, SIREN sensibles et preuves de detection sont masques ou haches cote
  backend avant toute reponse publique.
- L'authentification, les droits par tenant et les limites de volume sont en
  place.
- Le temps de reponse reste compatible avec une page d'audit interactive, ou la
  route Next ajoute un cache explicite.
- Les tests couvrent la parite entre export statique et payload API sur nodes,
  edges, findings, severites et `signalCounts`.

## Consequences

- Vercel reste simple a deployer : pas de dependance au runtime Python pour la
  demo publique.
- Les routes Next `/api/graph`, `/api/graph/metrics`, `/api/findings` et
  `/api/vendors/[id]` restent les points d'integration front.
- Le prochain chantier technique utile n'est pas un proxy immediat, mais la
  stabilisation du contrat de donnees et un endpoint FastAPI equivalent cote
  backend.

## Note d'implementation 2026-05-19

Le contrat est expose cote backend via `GET /api/v1/graph`. Il reutilise le
meme builder Python que `scripts/export_p2p_graph_demo.py`, renvoie les noeuds,
liens, findings, fournisseurs et metriques au format `P2PDemoDataset`, et garde
les IBAN masques avant publication.

La decision produit ne change pas : le frontend Vercel public continue de lire
le JSON statique tant que les sujets d'authentification, cache, tenant et URL
backend ne sont pas valides.
