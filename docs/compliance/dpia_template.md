# Analyse d'impact relative à la protection des données (DPIA)

> Pré-rempli pour le déploiement de **P2P Fraud Detective FR**.
> À adapter à votre contexte et faire valider par votre DPO.
> Conforme à la méthodologie CNIL (référentiel art. 35 RGPD, guides 1, 2 et 3).

## 1. Contexte

| Champ | Valeur |
|---|---|
| Responsable de traitement | *(votre entité juridique)* |
| Sous-traitant (le cas échéant) | *(prestataire infogérance / cloud)* |
| Délégué à la protection des données (DPO) | *(nom + email)* |
| Date de l'analyse | *(JJ/MM/AAAA)* |
| Version | 1.0 |

## 2. Description du traitement

- **Finalité principale** : détection de fraude Procure-to-Pay (factures
  fournisseurs, master data, paiements) à fins de prévention des risques
  financiers, réglementaires (LCB-FT, Sapin 2) et de protection du patrimoine
  de l'organisation.
- **Finalités secondaires** : suivi d'investigation (case management),
  reporting management, audit.
- **Base légale (art. 6 RGPD)** : intérêt légitime (art. 6.1.f) — protection
  contre la fraude. Test de mise en balance documenté en annexe.
- **Catégories de personnes concernées** :
  - utilisateurs comptables internes (saisie facture, validation),
  - personnes physiques agissant comme fournisseurs (entrepreneurs individuels,
    auto-entrepreneurs),
  - bénéficiaires effectifs des fournisseurs (RBE).
- **Catégories de données** :
  - identité (nom, prénom, raison sociale),
  - SIREN / SIRET,
  - coordonnées bancaires (IBAN, BIC) — *donnée sensible business*,
  - adresses postales,
  - identifiants techniques (user_id ERP, traces de saisie),
  - éventuelles correspondances PEP / sanctions.

## 3. Acteurs et destinataires

| Acteur | Rôle | Données accédées |
|---|---|---|
| Auditeur interne | Analyste | Findings + reason codes + cases assignés |
| Responsable contrôle interne | Manager | Tous findings + whitelist + weights |
| Comptable AP | Viewer | Findings sur factures qu'il/elle a saisies |
| DPO | Admin | Logs d'accès + registre AI Act |
| Sous-traitant infogérance | Sous-traitant | Données chiffrées au repos uniquement |

## 4. Mesures techniques et organisationnelles

| Mesure | Mise en œuvre |
|---|---|
| Chiffrement des IBAN au repos | `cryptography.Fernet` (AES-128-CBC + HMAC-SHA256), clé dans variable d'environnement P2P_FRAUD_DATA_KEY, jamais stockée en base. |
| Affichage IBAN | Masqué par défaut (`iban_masked()`) — accès au clair sur log d'accès uniquement (rôle Manager+). |
| RBAC | 4 rôles (viewer / analyst / manager / admin), check programmatique via `@requires_role`. |
| Audit log | Journal append-only chaîné par hash SHA-256, vérification d'intégrité native. Toute action sur un case et tout accès IBAN tracé. |
| Durée de conservation | Findings : 5 ans (correspond aux délais de prescription contrôle fiscal + audit légal). Audit log : 10 ans. |
| Anonymisation | À l'issue de la durée, suppression/anonymisation programmée. |
| Sécurité réseau | Déploiement on-prem possible (Streamlit + SQLite). En SaaS : TLS 1.3, isolation tenant. |
| Hébergement | *(à compléter selon votre choix : on-prem / OVHcloud / Scaleway / autre)* |

## 5. Évaluation des risques

| Risque | Vraisemblance | Gravité | Mesures |
|---|---|---|---|
| Accès illégitime aux IBAN | Moyenne | Élevée | Chiffrement Fernet + RBAC + audit log accès IBAN |
| Modification non tracée d'un case | Très faible | Élevée | Audit log immutable hash-chaîné |
| Utilisation détournée de la finalité | Faible | Moyenne | Limitation par rôle, formation utilisateurs |
| Fuite de données master data fournisseur | Faible | Moyenne | Chiffrement disque + sauvegardes chiffrées |
| Discrimination par scoring ML | Très faible | Moyenne | IF non supervisé sur features comportementales (pas RH), explicabilité par perturbation |

## 6. Droits des personnes

- **Information** : notice de transparence intégrée dans le portail interne RH +
  fournisseurs (référence à la page Gouvernance du produit).
- **Accès, rectification, effacement** : procédure documentée, contact DPO.
- **Opposition au traitement automatisé** : un finding ne déclenche jamais
  d'action automatique sur un fournisseur ; toute décision (blocage paiement,
  signalement Tracfin) reste humaine, motivée, journalisée. L'opposition est
  garantie par la nature même du produit.
- **Limitation** : possibilité d'exclure un fournisseur du scoring (whitelist
  managériale).

## 7. Décision

- [ ] Le traitement peut être mis en œuvre.
- [ ] Le traitement nécessite des mesures complémentaires : *(préciser)*.

Validation DPO : ___________________________ Date : __________
Validation Responsable de traitement : ___________________________ Date : __________
