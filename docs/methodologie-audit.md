# Méthodologie d'audit — référentiels couverts

## ISA 240 — *The Auditor's Responsibilities Relating to Fraud in an Audit of Financial Statements*

Norme internationale d'audit (IFAC). Impose au CAC de :
- Identifier et évaluer les risques de fraude dus à des écritures inappropriées (« management override of controls »).
- Tester les écritures comptables sélectionnées sur des critères basés risque (`§32-§33`).

**Couverture par cet outil** :
- Tests Benford (1er, 2 premiers, dernier chiffre) → détection d'écritures fabriquées
- Détection des écritures week-end / utilisateur non-comptable
- Détection des montants juste sous seuil de validation
- Détection des doublons (saisies multiples)

## AS 2401 — *Consideration of Fraud in a Financial Statement Audit* (PCAOB)

Équivalent US d'ISA 240, applicable aux entités cotées SEC. Mêmes exigences de tests JET.

## AICPA Audit Data Standards (ADS)

Standards américains de structuration des données pour audit, incluant les modèles G/L Detail, Vendor Master, AP Trial Balance.

**Couverture** : le schéma `Invoice` est aligné sur ADS-VM/AP, ce qui facilite l'ingestion d'exports SAP, Oracle, Sage, Cegid.

## Sapin 2 (loi française n° 2016-1691)

Article 17 — programme anti-corruption obligatoire pour entités > 500 salariés et 100 M€ CA. Exige une **cartographie des risques de corruption** et des contrôles comptables.

**Réutilisation** : le `risk_engine` et le `sirene_client` de cet outil seront réutilisés par le **projet 4 du portfolio** (Sapin 2 Risk Cartography Dashboard).

## DORA (règlement UE 2022/2554)

Applicable depuis le 17 janvier 2025 aux entités financières. Article 28 impose un **registre des prestataires TIC** au format ITS 2025/302.

**Réutilisation** : le `sirene_client` (validation LEI/SIREN) sera intégré au **projet 5 du portfolio** (DORA Vendor Registry).

## Mapping détaillé détecteur ↔ exigence

| Détecteur | ISA 240 | AS 2401 | Sapin 2 | DORA |
|---|---|---|---|---|
| Benford | §32 (b) | §52 | — | — |
| Doublons | §32 (b) | §52 | Art. 17 (4) | — |
| Sous seuils | §32 (b) | §52 | Art. 17 (4) | — |
| Sirene cross-check | — | — | Art. 17 (3) DD tiers | Art. 28 |
| Isolation Forest | §32 (a) | §52 | — | — |
| Anneaux fraude | §32 (b) | §52 | Art. 17 (4) | — |

## Limites

Cet outil est un **complément** à l'audit, pas un substitut. Il identifie des **anomalies** (signaux faibles), pas des fraudes prouvées. Toute alerte doit être documentée par une investigation manuelle (pièce justificative, entretien, contrôle de matérialité).
