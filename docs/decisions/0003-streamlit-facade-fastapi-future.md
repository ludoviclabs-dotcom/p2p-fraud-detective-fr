# ADR-0003 — Streamlit comme façade démo, FastAPI prévu en M3

- Statut : Accepté
- Date : 2026-05-07

## Contexte

Streamlit est aujourd'hui à la fois la façade utilisateur et l'orchestrateur du
pipeline. Cela convient pour la démo et l'usage par un auditeur seul, mais pose
trois problèmes pour aller en production chez un client ETI :

- pas de multi-utilisateur sécurisé natif (sessions partagées via `session_state`) ;
- pas d'API consommable par un workflow n8n / Power Automate / SAP RFC ;
- couplage fort entre logique métier et UI, qui complique tests d'intégration et
  packaging on-prem.

## Décision

- Phase 1 (MVP) : Streamlit reste l'interface unique. Tout le code métier vit
  dans `src/p2p_fraud/` et est testable indépendamment de Streamlit.
- Phase 2 (M3, mois 3 du plan d'action) : ajout d'une façade **FastAPI** dans
  `src/p2p_fraud/api/`, exposant `/ingest`, `/detect`, `/cases`, `/vendors/{id}`.
  Streamlit consommera l'API via httpx (mode démo) ou directement le package
  Python (mode embarqué).
- Phase 3 : on-prem packaging (Docker + Helm) avec FastAPI comme backend et
  Streamlit servi en option.

## Conséquences

- Aucune logique métier ne doit être ajoutée *uniquement* dans `pages/*.py` ;
  toute nouvelle feature passe par un module dans `src/p2p_fraud/`.
- Les nouveaux services (case management, audit log, sanctions) sont conçus dès
  Phase 1 avec une API Python claire pour pouvoir être wrappés en FastAPI sans
  réécriture.
