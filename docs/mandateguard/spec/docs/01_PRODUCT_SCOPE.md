# 01 — Périmètre produit

## Vision

Construire une plateforme de sécurité des flux bancaires appelée **MandateGuard / Payment Integrity Platform**.

La plateforme doit détecter, expliquer, documenter et prioriser les flux financiers à risque :

- prélèvements SEPA entrants ;
- mandats SEPA absents, révoqués ou incohérents ;
- paiements fournisseurs sortants ;
- changements de RIB/IBAN ;
- nouveaux bénéficiaires ;
- doublons, fractionnements, anomalies de montant ;
- dossiers de preuve auditables.

## Modules produit

### 1. SEPA Mandate Guard

Objectif : protéger contre les prélèvements SEPA non autorisés ou incohérents.

Fonctions :

- création de mandats ;
- signature ou preuve de consentement ;
- stockage chiffré ;
- révocation ;
- vérification ICS/RUM/IBAN ;
- analyse de prélèvements ;
- alertes ;
- dossier de contestation.

### 2. P2P / Supplier Payment Guard

Objectif : protéger contre les fraudes de paiement sortant.

Fonctions :

- détection de changement de RIB fournisseur ;
- nouveau bénéficiaire ;
- IBAN récemment ajouté ;
- doublon de facture ;
- paiement fractionné sous seuil ;
- violation du principe 4 yeux ;
- graphe de fraude ;
- evidence pack.

### 3. Risk Core

Objectif : mutualiser le scoring et les décisions.

Fonctions :

- interface standard de règle ;
- reason codes ;
- scoring ;
- niveaux de risque ;
- décisions ;
- explication machine-readable et user-readable.

### 4. Evidence + Ledger

Objectif : prouver ce qui a été vu, calculé, décidé et exporté.

Fonctions :

- dossier de preuve ;
- timeline ;
- hash d’intégrité ;
- audit log append-only ;
- export JSON/HTML/PDF ;
- vérification externe future.

## MVP recommandé

Le MVP doit couvrir :

1. création manuelle d’un mandat SEPA ;
2. révocation d’un mandat ;
3. import manuel/sandbox d’un prélèvement ;
4. analyse avec score et reason codes ;
5. alerte utilisateur ;
6. evidence pack ;
7. audit log ;
8. interface Risk Lab ;
9. intégration P2P en mode règles simples.

## Non-objectifs MVP

Le MVP ne doit pas :

- initier un virement ;
- initier un prélèvement ;
- se connecter directement aux comptes bancaires sans cadre légal approprié ;
- bloquer automatiquement un prélèvement auprès d’une banque ;
- faire de la décision de fraude 100 % IA ;
- stocker de données personnelles sur une chaîne publique.

## Personas

### Particulier avancé

Veut savoir si un prélèvement est légitime et préparer une contestation.

### PME / DAF

Veut surveiller mandats, prélèvements et paiements fournisseurs.

### Créancier sérieux

Veut prouver qu’il a un mandat valide, signé et non révoqué.

### Banque / PSP partenaire futur

Veut vérifier des mandats et réduire les litiges.

## User stories MVP

- En tant qu’utilisateur, je peux créer un mandat et définir un plafond.
- En tant qu’utilisateur, je peux révoquer un mandat.
- En tant qu’utilisateur, je peux importer un prélèvement observé.
- En tant qu’utilisateur, je vois si un prélèvement correspond à un mandat actif.
- En tant qu’utilisateur, je peux générer un dossier de contestation.
- En tant qu’analyste, je peux voir les signaux ayant conduit au score.
- En tant qu’admin, je peux activer ou désactiver des règles de détection.

