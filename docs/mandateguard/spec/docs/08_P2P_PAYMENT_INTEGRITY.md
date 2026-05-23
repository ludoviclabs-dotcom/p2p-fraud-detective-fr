# 08 — P2P / Supplier Payment Integrity

## Objectif

Intégrer intelligemment les concepts de P2P Fraud Detective comme module complémentaire à MandateGuard.

Ce module protège les paiements sortants :

- fournisseurs ;
- bénéficiaires ;
- virements ;
- changements d’IBAN ;
- doublons de factures ;
- fractionnement sous seuil ;
- validation non conforme.

## Positionnement

MandateGuard SEPA traite les **pull payments** : prélèvements subis.

P2P Payment Integrity traite les **push payments** : paiements émis.

Les deux partagent :

- Risk Core ;
- reason codes ;
- evidence pack ;
- audit ledger ;
- UI Risk Lab ;
- graph analysis.

## Détecteurs P2P prioritaires

### 1. Nouveau bénéficiaire

Signaux :

- bénéficiaire jamais vu ;
- IBAN jamais vu ;
- IBAN ajouté récemment ;
- nom bénéficiaire incohérent.

Reason codes :

- `NEW_BENEFICIARY`
- `NEW_IBAN`
- `IBAN_RECENTLY_ADDED`
- `IBAN_NAME_MISMATCH`

### 2. Changement de RIB fournisseur

Signaux :

- RIB modifié moins de 24h avant paiement ;
- changement non validé par second approbateur ;
- IBAN pays différent ;
- fournisseur dormant réactivé.

Reason codes :

- `SUPPLIER_RIB_RECENT_CHANGE`
- `FOUR_EYES_BREACH`
- `IBAN_COUNTRY_CHANGED`
- `SUPPLIER_DORMANT_REACTIVATED`

### 3. Doublons et fractionnement

Signaux :

- facture identique ;
- montant identique proche dans le temps ;
- référence similaire ;
- plusieurs paiements sous seuil à un même fournisseur.

Reason codes :

- `DUPLICATE_INVOICE`
- `SPLIT_PAYMENTS`
- `UNUSUAL_AMOUNT`

### 4. Graphe de fraude

Signaux :

- même IBAN partagé par plusieurs fournisseurs ;
- fournisseur relié à des cas à risque ;
- cluster d’IBAN ou entités suspect ;
- réseau de comptes mules.

Reason codes :

- `GRAPH_SHARED_IBAN`
- `GRAPH_HIGH_RISK_CLUSTER`

## Worker Python optionnel

Les traitements rapides restent en TypeScript.

Les traitements lourds peuvent être confiés à un service Python :

- pandas pour ingestion CSV/Excel ;
- fuzzy matching massif ;
- scikit-learn / Isolation Forest ;
- NetworkX pour graphes ;
- exports batch.

Architecture :

```txt
Vercel API -> Queue -> Worker Python -> API callback / DB
```

## Contrat avec le worker Python

### Requête

```json
{
  "jobId": "job_123",
  "tenantId": "tenant_abc",
  "jobType": "P2P_BATCH_ANALYSIS",
  "inputStorageKey": "imports/p2p/batch.csv",
  "options": {
    "runGraphAnalysis": true,
    "runFuzzyDuplicates": true,
    "runIsolationForest": false
  }
}
```

### Réponse

```json
{
  "jobId": "job_123",
  "status": "COMPLETED",
  "findings": [
    {
      "code": "DUPLICATE_INVOICE",
      "severity": "high",
      "score": 55,
      "message": "Facture potentiellement dupliquée",
      "evidence": {
        "invoiceRef": "F-2026-04419",
        "matchedInvoiceRef": "F-2026-04418"
      }
    }
  ]
}
```

## Écran P2P conseillé

Routes :

- `/supplier-risk`
- `/beneficiaries`
- `/payment-instructions`
- `/cases?domain=SUPPLIER_PAYMENT`
- `/risk-lab?domain=SUPPLIER_PAYMENT`

## Attention produit

Ne pas promettre “100 % des fraudes détectées”.

Promesse recommandée :

> Détecter, expliquer et documenter les paiements à risque avec une piste d’audit vérifiable.

