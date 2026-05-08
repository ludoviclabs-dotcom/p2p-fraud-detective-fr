# ADR-0001 — Repositionnement produit

- Statut : Accepté
- Date : 2026-05-07

## Contexte

Le projet a démarré sous la baseline « Mini-MindBridge open-source pour ETI françaises ».
La revue marché 2026 (AFP Payments Fraud Survey, Banque de France OSMP, IFACI Risk in
Focus, Trustpair, MindBridge, DataSnipper) montre que :

- la vérification *nom/IBAN* (VOP SEPA) est devenue gratuite depuis le 9 octobre 2025
  côté PSP : la « cross-check IBAN » brute n'est plus différenciante ;
- le scénario fraude n°1 documenté est le changement frauduleux de coordonnées
  bancaires fournisseur (BEC), or le projet ne suit pas l'historique master data ;
- les acheteurs ne sont pas convaincus par un « clone Mindbridge » : ils cherchent
  une plateforme **auditabilité + investigation + souveraineté** ;
- le terrain réel (cabinets, ETI, hôpitaux) demande on-prem-ability et exports
  Excel/Power BI signés.

## Décision

Repositionner le produit en :

> **Vendor & Payment Integrity FR-native** — détection de fraude P2P, monitoring
> du master data fournisseur, et piste d'audit signée pour ETI, cabinets d'audit
> et secteur public/hospitalier.

Les 5 fonctionnalités vendeuses 2026 sont :
1. IBAN change monitoring + 4-eyes,
2. Case management auditable + clôture motivée + WORM,
3. Vendor 360° avec graph employé–IBAN–adresse,
4. Score expliqué en français + reason codes (compatible AI Act),
5. Pack secteur public DECP + seuils CCP.

## Conséquences

- Le README, la landing page Streamlit et les docs perdent la mention « MindBridge ».
- Le détecteur Benford est rétrogradé en outil de scoping (cf. ADR-0002).
- La roadmap priorise master data history > case management > reason codes >
  three-way match > entity resolution > continuous monitoring (cf. plan d'action).
- L'architecture reste celle décrite dans `docs/architecture.md` ; aucune refonte
  du `src/p2p_fraud/` n'est requise pour Phase 0.
