# Registre de traitement (RGPD art. 30)

> Pré-rempli pour le déploiement de **P2P Fraud Detective FR**. À adapter et
> intégrer au registre central de l'organisation.

| Rubrique art. 30.1 | Valeur |
|---|---|
| **Nom du traitement** | Détection de fraude P2P, monitoring master data, investigation |
| **Responsable de traitement** | *(votre entité juridique)* |
| **DPO** | *(nom + email)* |
| **Sous-traitant(s)** | *(infogérance, hébergement)* |
| **Finalité(s)** | Prévention et détection de la fraude fournisseurs ; conformité LCB-FT et Sapin 2 ; production de rapports d'audit |
| **Catégories de personnes concernées** | Comptables internes, fournisseurs personnes physiques, bénéficiaires effectifs |
| **Catégories de données** | Identité (nom, raison sociale), SIREN, IBAN/BIC, adresses, identifiants techniques (user_id), correspondances PEP/sanctions |
| **Catégories de destinataires** | Auditeurs internes, RCSI, contrôleurs, DPO, sous-traitants infogérance, autorités sur demande légale (Tracfin, AFA) |
| **Transferts hors UE** | Aucun par défaut. Si OpenSanctions Yente activé, transit via API UE — pas de transfert tiers. |
| **Durées de conservation** | Findings : 5 ans. Cases : 10 ans. Audit log : 10 ans. Master data history : durée de la relation + 5 ans. |
| **Mesures de sécurité** | Chiffrement IBAN au repos (Fernet), RBAC, audit log immutable hash-chaîné, sauvegardes chiffrées, hébergement on-prem possible |
| **Base légale** | Intérêt légitime (art. 6.1.f) — protection contre la fraude. Mise en balance documentée. |

## Mesures techniques de sécurité (synthèse art. 32)

1. **Chiffrement** : Fernet (AES-128-CBC + HMAC-SHA256) pour IBAN/BIC au repos.
2. **Pseudonymisation** : possible via masquage (`iban_masked()`) pour les
   accès sans privilège.
3. **Authentification** : PBKDF2-SHA256 200 000 itérations, sels uniques par
   user.
4. **Autorisation** : RBAC 4 rôles (viewer / analyst / manager / admin),
   décorateur `@requires_role` programmatique.
5. **Audit** : journal append-only chaîné par hash SHA-256, vérification
   d'intégrité native, export JSONL pour archivage WORM.
6. **Disponibilité** : SQLite WAL + sauvegardes quotidiennes chiffrées.
7. **Test périodique** : revue trimestrielle des accès et des journaux
   d'activité.

## Information des personnes (art. 13/14)

À intégrer dans :
- la charte informatique interne (employés saisissant des écritures),
- le portail fournisseurs (mention explicite de la finalité fraude et des
  sources publiques croisées : Sirene, RBE, OpenSanctions, Trésor FR),
- les conditions générales d'achat.
