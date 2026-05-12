# Cas client #2 — Foncière cotée 1.2 Md€

> **Cas pédagogique anonymisé**. Toute ressemblance avec une entreprise existante est fortuite. Aucune PII réelle.

## Profil

| Caractéristique | Valeur |
|---|---|
| Secteur | Foncière cotée (immobilier tertiaire + résidentiel) |
| CA | 1.18 Md€ (loyers + cessions, exercice 2025) |
| Effectif | 380 collaborateurs |
| Patrimoine | 2.1 Md€ d'actifs sous gestion, 1 850 baux actifs |
| Audit interne | 3 ETP + cabinet externe Forvis Mazars |
| ERP | Sage X3 + Yardi Voyager (gestion locative) |
| Volume P2P annuel | 38 000 factures + 2 800 prestataires actifs (BTP, FM, conseil) |
| Profil risque | Élevé — BTP + FM + conseil + AMLD6 obligation FR (art. R. 561-31) |

## Problématique initiale

La société, **cotée sur Euronext Paris**, est confrontée à trois obligations cumulées :

1. **AMLD6 + R. 561-31 CMF** : obligation explicite de KYC/KYB pour les foncières (depuis transposition 2024 — assujetties).
2. **Sapin 2 art. 17** : cartographie risques corruption (relations BTP intenses).
3. **CSRD art. 29** : traçabilité Scope 3 fournisseurs depuis 2026.

Le RCSI (Responsable Conformité et Sécurité des Investissements) souhaite **un outil unique** pour ces trois axes sans payer trois licences distinctes.

## Mise en œuvre

| Étape | Durée | Livrable |
|---|---|---|
| Audit existant + cadrage juridique | 5 j | Note CMF + AMLD6 mappée fonctions |
| Extraction Sage X3 + Yardi | 3 j | CSV consolidé 38 k invoices + master |
| Déploiement Docker Compose interne | 1 j | Stack auto-hébergée DMZ |
| Calibration secteur immobilier | 4 j | Seuils BTP + FM + paiements loyers ajustés |
| Activation `ENRICHMENT_MODE=live` | 1 j | DECP + Pappers + Yente configurés |
| Run + investigation cycle 1 | 12 j | 28 cases sérieux, 5 DS Tracfin |
| Rapport CAC + restitution Comex | 4 j | PPT + dossiers PDF signés Ed25519 |

**Effort total** : 30 jours-homme audit interne + 8 jours conseil Forvis externe.

## Résultats — patterns spécifiques foncière

### 1. Prestataires BTP fantômes (sociétés taxis)

Le rapport Tracfin Tome III 2024-2025 alerte sur le boom des sociétés taxis dans le BTP. Detection :

| Indice | Mesure |
|---|---|
| Sociétés créées < 6 mois | 23 prestataires sur 2 800 |
| Cumul facturé sur 90 jours | 4 dépassent 50 k€ (anormal pour une PME naissante) |
| Croisement DECP | 2 jamais titulaires d'aucun marché public (atypique pour BTP) |
| Croisement RBE Pappers | 1 BO inconnu / nationalité haute risque |

Résultat : **2 cas confirmés frauduleux**, restitution partielle 145 k€, 2 DS Tracfin transmises.

### 2. Conflits d'intérêts dirigeants locataires

Croisement RBE Pappers × dirigeants des sociétés locataires de la foncière :

- 4 cas où un BO d'une société locataire est aussi associé d'une société prestataire de la foncière → tarification potentielle anormale.
- 1 cas qualifié de conflit d'intérêts non déclaré (procédure interne RCSI ouverte).

### 3. Fractionnement honoraires conseil

12 cas de honoraires conseil juste sous 25 k€ HT (seuil interne déclaratif Comex). 7 cas explicables (missions distinctes), **5 cas requalifiés en mission unique fragmentée** par le DAI.

### 4. Sanctions UE — prestataires intermédiaires

OpenSanctions Yente live a identifié :
- 1 prestataire intermédiaire (sous-traitant d'un syndic) dont un BO est listé en sanctions UE 2024/1736 (volet défense).
- Résolution : rupture commerciale immédiate, paiements antérieurs déclarés à la DGT (Trésor).

## Verbatim RCSI

> *« On nous demandait 75 k€/an pour Quantexa, qu'on n'a pas le budget de payer chaque année. P2P Fraud Detective FR a fait la moitié du job en self-hosted, et le CAC a pris notre dossier Sapin 2 sans réserve. Le différentiel devient un budget formation. »*
>
> — RCSI, novembre 2025

## Pourquoi P2P Fraud Detective FR vs alternatives

| Concurrent évalué | Verdict | Raison principale |
|---|---|---|
| Quantexa | ❌ écarté | 75 k€/an + formation + intégration 6 mois |
| SAS AML on-prem | ❌ écarté | 150 k€ licence + 80 k€ infra |
| MindBridge | ❌ écarté | Pas d'enrichissement DECP/RBE/Sanctions live |
| Solution interne sur mesure | ❌ écarté | 6 mois dev + maintenance perpétuelle |
| P2P Fraud Detective FR | ✅ retenu | Self-hosted, sources live, MIT, FR-native |

## Pièges spécifiques foncière

1. **Yardi-Sage non alignés** : référentiel fournisseurs présent dans les deux SI avec des IDs différents → réconciliation par SIREN + RapidFuzz nom.
2. **Loyers ≠ achats** : les paiements de loyers (charges, taxes foncières) sont en flux séparé — ne pas mélanger avec le P2P fournisseurs.
3. **VAT immobilier** : pour les baux à TVA optionnelle, le scoring sur HT/TTC doit être homogène (sinon faux positifs Benford).
4. **Saisonnalité** : forte saisonnalité Q1 (taxes foncières) → recalibrer les seuils ML par trimestre.

## Données techniques

- **Volume** : 38 000 invoices × 2 800 vendors × 24 mois
- **Run complet** : 1 min 50 s sur VM 4 vCPU / 8 GB
- **Audit trail** : 2 814 entrées avec signatures Ed25519 (v0.5 prévue)
- **DS Tracfin** : 5 transmises en 12 mois (rythme cohérent avec le 211 165 / 64 000 sociétés AMLD6 nationales)
- **Conformité CAC** : Forvis Mazars a validé l'outil comme support recevable pour les diligences Sapin 2 + AMLD6

## Suite donnée

- Run hebdomadaire automatisé + webhook Teams Comité Sécurité
- Intégration au programme CSRD : extraction trimestrielle des prestataires « à risque réputationnel »
- Évaluation v0.5 pour la signature Ed25519 (exigence CAC pour archivage légal 10 ans)
- Formation 8 acheteurs achats hors loyers + 2 contrôleurs internes
