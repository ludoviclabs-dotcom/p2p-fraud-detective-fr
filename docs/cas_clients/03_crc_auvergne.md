# Cas client #3 — CRC Auvergne-Rhône-Alpes (cas fictif)

> **Cas pédagogique fictif** (la CRC Auvergne n'a pas déployé l'outil).
> Illustre comment une Chambre Régionale des Comptes pourrait utiliser P2P Fraud Detective FR pour ses missions de contrôle des comptes des collectivités.

## Profil

| Caractéristique | Valeur |
|---|---|
| Type d'organisme | Chambre Régionale des Comptes (juridiction financière) |
| Périmètre | 4 200 collectivités auvergnates + établissements publics |
| Magistrats + vérificateurs | 38 (12 magistrats, 26 vérificateurs) |
| ERP cible des contrôles | Helios (DGFiP) + Cégid Public Services |
| Volume P2P annuel contrôlé | ~ 2.8 M factures cumulées sur les organismes échantillonnés |
| Profil risque | Variable — commande publique soumise au CCP 2018 + Sapin 2 |

## Mission type

Le rapporteur d'une CRC procède au contrôle des comptes et de la gestion d'une commune de 35 000 habitants (budget 70 M€) sur les exercices 2022-2024. Objectifs :

1. **Régularité** des opérations (CCP 2018, art. L. 1411-1 et suivants du CGCT) ;
2. **Sincérité** des comptes (M14, M22, M57) ;
3. **Efficience** de la commande publique ;
4. **Détection** d'éventuels indices de fraude ou de favoritisme (art. 432-14 CP).

Le vérificateur doit analyser **environ 78 000 mandats de paiement** sur la période.

## Mise en œuvre

Le projet est expérimenté en pilote sur **3 missions de contrôle** avant déploiement chambre-wide.

| Étape | Durée | Livrable |
|---|---|---|
| Adaptation outil pour M14/M22/M57 (codification PCM) | 5 j | Mapping comptes M14 → catégories P2PFD |
| Activation `ENRICHMENT_MODE=live` + Pappers + DECP | 1 j | Sources live opérationnelles |
| Importation mandats Helios → P2P FD FR | 2 j | 78 000 mandats consolidés |
| Run détecteurs + croisement DECP | 4 j | 234 findings sur les 3 communes |
| Investigation magistrat sur findings CRITICAL/HIGH | 8 j | 12 observations préliminaires |
| Audition contradictoire ordonnateur | 3 j | 7 réponses, 5 confirmations |
| Rédaction observations définitives + ROD | 5 j | 1 ROD + 1 saisine procureur |

**Effort total** : 28 jours sur 3 missions, soit ~ 9 j/mission. À comparer aux 25-30 j/mission en méthode traditionnelle.

## Findings remontés en pilote (commune fictive 35 000 hab)

### 1. Croisement DECP × marchés municipaux (P5-1)

Le détecteur `decp` croise les fournisseurs ayant touché des mandats de la commune avec le registre national des marchés publics :

| Pattern | Volume | Statut |
|---|---|---|
| Fournisseurs présents DECP ET mandatés par la commune | 14 | Investigation Sapin 2 sur fractionnement marchés |
| Fournisseurs facturant > 25 k€ HT mais aucun marché DECP | 8 | 3 cas qualifiés sans publicité (CCP art. R. 2122-8) |

### 2. Bénéficiaires effectifs (RBE Pappers)

| Pattern | Volume | Statut |
|---|---|---|
| Conjoint(e) d'élu BO d'un fournisseur communal | 1 | Délit favoritisme art. 432-14 CP investigué |
| Adjoint au maire BO d'une SCI louant à la commune | 1 | Conflit d'intérêts art. L. 1111-6 CGCT |

### 3. Structuring fractionnement (D. 561-31-1 CMF — applicable aussi aux collectivités) ?

Note pédagogique : **la commune n'est pas assujettie LCB-FT**, mais le seuil 25 k€ HT du CCP impose la mise en concurrence. Le détecteur `under_thresholds` calibré à 24 000 €/26 000 € identifie :

| Pattern | Volume | Statut |
|---|---|---|
| Fournisseurs facturant systématiquement 22-24 k€ HT | 5 | 3 cas avérés de fractionnement |
| Bons de commande émis le 1er et le 15 du mois (rythme suspect) | 12 | 4 cas requalifiés en marché unique |

### 4. Sanctions UE — vérification générique

| Pattern | Volume | Statut |
|---|---|---|
| Matchings positifs avec snapshot UE consolidé | 0 | Conformité OK |

## Conformité juridique du dispositif

Le code des juridictions financières (L. 111-1 et suivants) confère aux CRC un **droit de communication étendu** sur les comptes des organismes contrôlés. L'outil :

- ✅ Garde toutes les données **dans le SI de la CRC** (self-hosted Docker)
- ✅ **Audit trail SHA-256** chaîné conforme aux exigences d'archivage
- ✅ **RGPD art. 6.1.e** — exécution d'une mission d'intérêt public
- ✅ **Loi 78-17 art. 88-1** — accès des juridictions financières aux données

## Verbatim magistrat (cas fictif)

> *« Le différentiel par rapport à nos macros Excel internes, c'est l'audit trail SHA-256 et l'enrichissement DECP. Sur le cas du conjoint BO, on a pu prouver le lien en 5 minutes via Pappers — au lieu de 3 jours de recoupements manuels. Le procureur a pris notre saisine sans poser de question sur la méthode. »*
>
> — Magistrat rapporteur (cas pédagogique fictif)

## Pourquoi P2P Fraud Detective FR vs alternatives pour les CRC

| Alternative | Verdict | Raison |
|---|---|---|
| Macros Excel internes | ❌ insuffisant | Pas d'audit trail, pas de scoring, pas d'enrichissement live |
| ANTICOR (outil DGFiP) | ⚠️ non disponible CRC | Réservé services DGFiP |
| MindBridge | ❌ écarté | Pas calibré commande publique CCP 2018 |
| SAS AML | ❌ écarté | 200 k€+ — hors budget Cour des comptes / CRC |
| **P2P Fraud Detective FR** | ✅ candidat sérieux | Open source MIT, self-hosted, FR-native, audit trail conforme |

## Pièges spécifiques contrôle public

1. **Codification M14 ≠ PCG** : adapter les mappings (compte 6068 « autres matières et fournitures » M14 vs 606 PCG).
2. **Mandats vs factures** : un mandat peut regrouper plusieurs factures → désagrégation préalable nécessaire.
3. **Sous-régies** : les comptes hors mandats (régies d'avances et de recettes) nécessitent un détecteur dédié.
4. **Saisonnalité publique** : pic décembre (clôture exercice budgétaire) → ne pas surinterpréter le rythme.

## Si déploiement réel CRC envisagé

Pour qu'une CRC déploie P2P Fraud Detective FR en production, il faudrait :

- Module dédié codification M14/M22/M57 (1-2 semaines de développement)
- Format ROD (Rapport d'Observations Définitives) — template d'export
- Intégration optionnelle avec **Helios** (DGFiP) pour ingestion automatique
- Hébergement souverain : **Cloud Pi de la DGFiP** ou **Outscale Sovereign Cloud** (qualifié SecNumCloud)
- Convention d'utilisation Cour des comptes + accord ARCEP / CNIL

Ces évolutions ne sont pas dans la roadmap publique 2026. Elles seraient à étudier sur projet dédié.

## Données techniques (extrapolation pilote)

- **Volume** : 78 000 mandats × 1 200 fournisseurs × 36 mois
- **Run complet** : 2 min 40 s sur VM 4 vCPU / 8 GB
- **Audit trail** : 4 218 entrées SHA-256 chaînées
- **Faux positifs** (calibré commune) : 8.4 %
- **F1-score** détecteur DECP : 0.88 (validation par échantillon manuel)
