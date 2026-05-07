# Registre AI Act — P2P Fraud Detective FR

> Pré-rempli pour conformité avec le règlement (UE) 2024/1689 (« AI Act »)
> applicable depuis le 2 août 2026 pour les systèmes haut risque.
> À adapter à votre déploiement et faire valider par votre DPO / responsable
> conformité.

## 1. Identification du système

| Champ | Valeur |
|---|---|
| Nom du système IA | P2P Fraud Detective FR |
| Version | *(version déployée)* |
| Fournisseur | *(éditeur, si différent du déployeur)* |
| Déployeur (au sens AI Act) | *(votre organisation)* |
| Responsable produit interne | *(nom + email)* |
| URL de documentation | https://github.com/ludoviclabeaut/p2p-fraud-detective-fr |

## 2. Classification AI Act

- **Catégorie** : risque limité (transparence) — le système IA détecte des
  anomalies sur des données comptables de l'organisation et propose des alertes
  à un opérateur humain. Il **ne décide pas de manière automatique** sur les
  personnes (pas de blocage de paiement automatique, pas de scoring de crédit,
  pas d'évaluation de candidats à l'emploi).
- **Article(s) applicable(s)** : art. 50 (transparence vis-à-vis des
  utilisateurs).
- **Hors haut risque (Annexe III)** : ce système ne tombe pas sous l'Annexe III
  car il ne constitue pas un système de notation sociale, scoring crédit
  individuel, ressource humaine décisionnelle, ou évaluation d'éligibilité
  sociale.
- **Justification de la classification** :
  - les findings sont systématiquement présentés à un humain (case management) ;
  - aucune décision sortante du système (paiement, blocage, sanction) n'est
    automatisée ;
  - la base de scoring concerne des **transactions** et des **fournisseurs
    personnes morales**, pas des individus en tant que tels ;
  - les personnes physiques rencontrées (employé saisissant une écriture,
    bénéficiaire effectif) ne sont jamais notées en propre.

## 3. Composants IA / ML

| Composant | Type | Donnée d'entraînement | Décision auto ? |
|---|---|---|---|
| Isolation Forest | Anomaly detection non supervisée | Comportement comptable (montants, fréquence, jours) | Non — produit un score, jamais une décision |
| Sanctions matching | Algorithme déterministe (RapidFuzz WRatio) | Listes publiques OFAC / UE / Trésor FR | Non — produit un finding |
| Master data rules | Règles déterministes | — | Non |
| Reason codes | Templates FR statiques | — | — |

> **Aucun LLM** n'est intégré dans le pipeline de scoring. L'éventuelle
> assistance GenAI (rédaction de commentaires, résumé) prévue en V3 fera
> l'objet d'une mise à jour de ce registre.

## 4. Mesures de transparence (art. 50)

- **Information utilisateur** : chaque page Streamlit contenant un score IA
  affiche un bandeau explicite : « Cette alerte est issue d'un modèle de
  détection d'anomalie ; sa lecture humaine est requise avant toute action ».
- **Reason codes en français** : chaque finding est accompagné d'une phrase FR
  explicable, avec citation référentielle (ISA 240, AFP 2026, Sapin 2…).
- **Waterfall des contributions** : l'utilisateur peut décomposer le score
  pour voir quelles règles et quels signaux ML y ont contribué.
- **Explicabilité ML** : pour chaque ligne traitée par Isolation Forest, une
  perturbation locale identifie les variables contribuant à l'anomalie.

## 5. Supervision humaine

- **Action humaine requise** : 100 % des findings nécessitent une création de
  case par un analyste pour aboutir à une action.
- **Garde-fou « 4-eyes »** : la clôture d'un case en mode CONFIRMED nécessite
  un motif non vide. Les actions sensibles (assignation, escalade) sont
  réservées au rôle ANALYST minimum.
- **Bouton de désactivation du scoring ML** : une bascule
  `enable_ml_scoring=false` permet de retirer Isolation Forest du score
  consolidé tout en conservant les règles déterministes.

## 6. Données et qualité

- **Sources de données** : exports comptables internes (factures, paiements,
  master data fournisseurs, événements ERP).
- **Pas de données biométriques, pas de données spéciales (art. 9 RGPD)**.
- **Qualité** : Pydantic au boundary, presets ERP avec parse de format,
  dataset synthétique étiqueté pour évaluer F1 par détecteur.
- **Biais et discrimination** : le scoring porte sur des transactions et des
  entités morales. Aucune évaluation par genre, origine ou orientation. Audit
  périodique recommandé pour vérifier l'absence d'effets disparates indirects
  sur des populations de fournisseurs (par taille, secteur, géographie).

## 7. Cycle de vie et journalisation

- **Versioning** : Git (https://github.com/ludoviclabeaut/p2p-fraud-detective-fr)
  + tags SemVer.
- **Modèles ML** : versionnés via `joblib`, hash SHA-256 dans
  `data/cache/iforest.joblib.sha256`.
- **Journal des décisions automatiques** : audit log immutable hash-chaîné
  (cf. service `cases.audit_log`). Vérification d'intégrité disponible.
- **Surveillance post-déploiement** : revue trimestrielle des taux de faux
  positifs, mise à jour des seuils et des reason codes.

## 8. Suppression et droit à la portabilité

- Les findings et cases peuvent être exportés en JSONL signé (page Audit Trail).
- Le DPO peut purger les données d'un fournisseur sur demande (procédure
  documentée).

## 9. Incident d'IA — procédure

- Tout dysfonctionnement substantiel (scoring incohérent, faux positifs en
  rafale, déni de service) est consigné dans le journal d'incidents (Sprint 8).
- Notification AFNIA / autorité compétente dans les délais légaux (art. 73
  AI Act) si l'incident porte sur un système haut risque (ce qui n'est pas
  le cas par défaut ici).

---

Validation DPO : ___________________________ Date : __________
Validation responsable produit : ___________________________ Date : __________
