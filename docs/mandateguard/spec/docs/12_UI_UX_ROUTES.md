# 12 — UI, UX et routes

## Principes UX

- Montrer la raison, pas seulement le score.
- Toujours afficher les données sensibles masquées.
- Une alerte doit proposer une action claire.
- Distinguer “suspect” de “fraude confirmée”.
- Donner accès à l’evidence pack.
- Garder le produit compréhensible pour non-expert.

## Routes principales

```txt
/dashboard
/mandates
/mandates/new
/mandates/:id
/debits
/debits/:id
/alerts
/alerts/:id
/cases
/cases/:id
/risk-lab
/detection-studio
/evidence/:id
/admin/rules
/admin/ledger
/admin/settings
```

## Dashboard

Widgets :

- score sécurité global ;
- alertes ouvertes ;
- prélèvements récents ;
- paiements sortants récents ;
- mandats actifs/révoqués ;
- top reason codes ;
- actions à faire.

Wireframe :

```txt
┌─────────────────────────────────────────────────────┐
│ MandateGuard                                        │
├─────────────────────────────────────────────────────┤
│ Score sécurité : 82/100     Alertes ouvertes : 3    │
├───────────────────────┬─────────────────────────────┤
│ Prélèvements récents  │ Alertes critiques           │
│ EDF        89€  OK    │ ⚠ Aucun mandat actif        │
│ Orange     42€  OK    │ ⚠ Mandat révoqué            │
│ XYZPay      9€  ⚠     │ ⚠ RIB fournisseur modifié   │
├───────────────────────┴─────────────────────────────┤
│ Mandats actifs : 12 | Révoqués : 4 | À signer : 1   │
└─────────────────────────────────────────────────────┘
```

## Page alerte

Sections :

1. résumé ;
2. niveau de risque ;
3. signaux ;
4. données de l’événement ;
5. mandat ou bénéficiaire lié ;
6. timeline ;
7. actions ;
8. evidence pack.

Actions :

- reconnaître ;
- ignorer ;
- demander revue ;
- créer contestation ;
- générer evidence pack ;
- ajouter créancier en confiance ;
- bloquer futur dans règles internes.

## Risk Lab

Permet de tester un événement synthétique.

Champs :

- domaine de risque ;
- montant ;
- ICS/RUM ou bénéficiaire ;
- statut mandat ;
- RIB changé récemment ;
- fréquence ;
- historique.

Résultat :

- score ;
- reason codes ;
- décision ;
- JSON complet ;
- possibilité de créer un scénario de test.

## Detection Studio

Liste les détecteurs actifs.

Colonnes :

- code ;
- domaine ;
- version ;
- gravité ;
- état ;
- faux positifs ;
- derniers déclenchements.

Actions admin :

- activer/désactiver ;
- modifier config ;
- voir tests ;
- voir exemples.

## Page evidence

Sections :

- résumé dossier ;
- hash d’intégrité ;
- événements d’audit ;
- documents ;
- export JSON/HTML/PDF ;
- vérification.

## États vides

Prévoir des empty states utiles :

- aucun mandat ;
- aucun prélèvement ;
- aucune alerte ;
- aucun case ;
- import non configuré.

Chaque état vide doit proposer une action : créer mandat, importer CSV, lancer Risk Lab.

