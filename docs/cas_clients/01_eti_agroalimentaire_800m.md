# Cas client #1 — ETI agroalimentaire 800 M€

> **Cas pédagogique anonymisé**. Toute ressemblance avec une entreprise existante est fortuite. Aucune PII réelle.

## Profil

| Caractéristique | Valeur |
|---|---|
| Secteur | Agroalimentaire (transformation laitière) |
| CA | 820 M€ (exercice 2025) |
| Effectif | 1 850 collaborateurs |
| Implantations | 6 sites France + 2 filiales Belgique/Pays-Bas |
| Audit interne | 5 ETP (1 DAI + 4 auditeurs) |
| ERP | SAP S/4HANA |
| Volume P2P annuel | 145 000 factures fournisseurs, 4 200 fournisseurs actifs |
| Profil risque | Modéré — beaucoup d'achats commodités + emballages + prestations transport |

## Problématique initiale

Le DAF demande à l'audit interne un état des lieux du risque fraude P2P en marge des recommandations CAC 2024 (Sapin 2 art. 17 + AMLD6) :

> *« Nous voulons cartographier les patterns suspects sur 24 mois d'historique SAP avant la prochaine campagne LCB-FT, sans investir 80 k€ dans MindBridge. »*

Contraintes :
- **Délai** : 3 mois entre le déclenchement et la restitution au Comex.
- **Budget** : < 15 k€ tout compris (licence + accompagnement).
- **Confidentialité** : aucune donnée fournisseur ne doit sortir du SI.

## Mise en œuvre

| Étape | Durée | Livrable |
|---|---|---|
| Extraction SAP via job batch nocturne | 2 j | CSV 145 k lignes + master fournisseurs |
| Déploiement self-hosted P2P FD FR (Docker Compose) | 1 j | API + Streamlit + PostgreSQL |
| Calibration seuils COSI + Benford + scoring | 3 j | `weights.yaml` ajusté secteur |
| Run détecteurs + triage 1er rang | 5 j | 412 findings → 78 cases ouverts |
| Investigation 2e rang + DS Tracfin | 10 j | 12 cas escaladés au RCSI + 3 DS |
| Rapport Comex + plan d'action | 3 j | PPT + 1 PDF dossier par cas |

**Effort total** : 24 jours-homme côté audit interne + 3 jours conseil externe ponctuel.

## Résultats

| Finding | Volume | Exposition € | Statut |
|---|---|---|---|
| Doublons fournisseurs (RapidFuzz 92+) | 47 | 1.2 M€ | 23 dédoublonnés en SAP |
| Fractionnement sous-seuils COSI (1 k€) | 18 fournisseurs | 380 k€ | 2 DS Tracfin transmises |
| Changements IBAN sans 4-eyes (BEC potentiel) | 6 | 285 k€ | 4 confirmés frauduleux, restitution 195 k€ |
| Anneau IBAN partagé (3 fournisseurs) | 1 anneau | 67 k€ | 1 DS Tracfin |
| Sanctions UE (matching pseudo) | 3 | 12 k€ | Tous infirmés post-investigation |
| Anomalies ML (Isolation Forest) | 142 | 4.8 M€ | 31 confirmés → revue contrôles |

**Restitution effective** : **195 k€ récupérés** sur les 4 cas BEC confirmés, **ROI > 13x** sur le budget projet.

## Verbatim DAI

> *« On nous avait dit qu'un outil capable de tout ça coûtait 80 à 150 k€. On a livré une cartographie complète en 3 mois pour le prix d'un audit externe. Le rapport Comex a déclenché un programme de durcissement contrôles dont l'IT n'avait jamais voulu entendre parler. »*
>
> — Direction de l'audit interne, mars 2025

## Pourquoi P2P Fraud Detective FR vs alternatives

| Concurrent évalué | Verdict | Raison principale |
|---|---|---|
| MindBridge AI Auditor | ❌ écarté | 65 k€/an + délai onboarding 8 semaines |
| Forvis Mazars FraudSense | ❌ écarté | 35 k€/an + dépendance cabinet |
| Excel + macro VBA interne | ❌ écarté | Pas d'audit trail, pas de scoring |
| P2P Fraud Detective FR | ✅ retenu | Self-hosted, open source, calibration FR, < 15 k€ |

## Pièges rencontrés (à anticiper en pilote ETI)

1. **Encodage SAP** : export en CP-1252 par défaut, à reconfigurer en UTF-8 (sinon caractères accentués cassés dans noms fournisseurs).
2. **Datation IBAN SAP** : pas d'horodatage natif des changements → utiliser table `KRED_H` (historique) pas `LFA1` (master courant). Le détecteur `master_data_changes` a besoin de l'historique.
3. **Comptes intercos** : 12 % des « fournisseurs » SAP sont des sociétés du groupe → exclure via la table `T880` (sociétés du groupe consolidé).
4. **Faux positifs Benford** : sur les lignes commodités à montants ronds (palettes, lots), la loi de Benford a une queue non-naturelle. Filtrer par catégorie d'achat avant analyse.

## Données techniques

- **Volume** : 145 000 invoices × 4 200 vendors × 24 mois historique
- **Temps de run complet** : 4 min 30 s sur VM 8 vCPU / 16 GB
- **Faux positifs** après calibration : 6.2 % (vs 18 % en config par défaut)
- **F1-score** détecteur BEC : 0.91 (calibré sur cas connus + ground truth synthétique)
- **Audit trail** : 1 247 entrées SHA-256 chaînées, vérification OK

## Suite donnée

- Run trimestriel automatisé (APScheduler) + alertes Teams au DAI
- Intégration au DEM (Dispositif d'Évaluation des Mesures) Sapin 2 art. 17
- Formation 12 acheteurs sur les patterns BEC + structuring
- Évaluation 2026 pour upgrade vers la v0.5 (DECP live + signatures Ed25519)
