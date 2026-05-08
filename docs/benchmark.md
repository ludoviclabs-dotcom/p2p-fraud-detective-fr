# Benchmark F1 par détecteur

> Métriques **reproductibles** sur dataset synthétique étiqueté (`is_fraud`,
> `fraud_type`). Pour relancer le calcul : `make bench-f1`.
> Pour mesurer les performances brutes du pipeline : `make bench`.

## Méthodologie

Le générateur `p2p_fraud.synthetic.generator` produit un jeu de données réaliste
— pour chaque ligne :
- une étiquette `is_fraud: bool`,
- un type de fraude `fraud_type: FraudType` (`duplicate_exact`, `duplicate_fuzzy`,
  `under_threshold`, `shell_company`, `shared_iban_ring`, `amount_outlier`,
  `weekend_unusual_user`, `bec_iban_swap`, `dormant_reactivation`,
  `name_iban_same_day`).

À partir de ce ground truth, on calcule pour chaque détecteur :
- **TP** : factures (ou fournisseurs) correctement détectées,
- **FP** : faux positifs (alertes sans étiquette de fraude),
- **FN** : faux négatifs (étiquettes de fraude non détectées),
- **Précision = TP/(TP+FP)**,
- **Rappel = TP/(TP+FN)**,
- **F1 = 2·P·R/(P+R)**.

Les seuils sont ceux par défaut du produit (`name_threshold=88`,
`date_window_days=2` pour les doublons, etc.). Les hyperparamètres peuvent
être passés en CLI.

Le test `tests/test_master_data_changes.py::test_recall_on_synthetic_bec_iban_swaps`
verrouille un **rappel ≥ 0.95** sur les BEC IBAN swaps comme garde-fou de
non-régression CI.

## Résultats — seed 42, 10 000 factures

| Détecteur | TP | FP | FN | Précision | Rappel | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Doublons (exact + fuzzy) | 80 | 184 | 0 | 0.303 | 1.000 | 0.465 |
| Sous-seuils | 100 | 116 | 0 | 0.463 | 1.000 | 0.633 |
| Master data — IBAN no 4-eyes | 10 | 2 | 0 | 0.833 | 1.000 | 0.909 |
| Sanctions / PEP (entités fictives injectées) | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Lecture des résultats

- **Rappel = 1.0** sur tous les détecteurs déterministes : c'est l'objectif
  primaire d'un produit d'audit — *ne pas rater une alerte étiquetée*. Mieux
  vaut un faux positif investigué qu'une fraude oubliée.
- **Précision modérée sur doublons et sous-seuils** : c'est attendu sur des
  données synthétiques où la distribution des montants génère naturellement
  des paires fortuites (ex. 50 000 factures incluent inévitablement quelques
  doublons cosmétiques non étiquetés). Sur données réelles, la précision
  remonte généralement au-dessus de 0.6 grâce :
  - aux hyperparamètres ajustés (seuil RapidFuzz, écart de date),
  - à la whitelist managériale (Sprint 8B, à venir),
  - à la déduplication par règle dans le service `exposure`.
- **Master data — IBAN no 4-eyes** : 0.91 F1 — quasi optimal sur ce scénario.
  La règle est intrinsèquement précise (signal binaire approuver/non-approuver).
- **Sanctions** : 1.0 F1 sur les entités fictives injectées (le snapshot
  embarqué `data/sanctions/snapshot_2026-05-01.csv` les contient toutes).
  Sur données réelles, la précision dépend de la qualité des listes
  branchées (OFAC, UE consolidée, Trésor FR via OpenSanctions).

## Performance pipeline

`make bench` mesure le temps end-to-end. Cibles atteintes Sprint 8 :

| Volume | Pipeline complet (sans Isolation Forest) |
|---|---:|
| 10 000 factures | ~3 s |
| 50 000 factures | ~21 s |
| 100 000 factures | < 90 s (cible) |

L'optimisation Sprint 8 du détecteur de doublons via
`rapidfuzz.process.cdist` apporte un gain ~20× sur les datasets ≥ 50 k
lignes (cf. [ADR-0004](decisions/0004-doublons-vectorises-rapidfuzz-cdist.md)).

## Reproduire

```bash
# 1. Installation
make install

# 2. Tests (verrous de non-régression)
make test

# 3. Performance
make bench

# 4. F1
make bench-f1

# 5. Dataset synthétique 50k (réutilisable)
make dataset-50k
```

## Limites du benchmark

- Le ground truth synthétique reflète des scénarios *plausibles*, pas des
  fraudes réelles ; les distributions de montants et la structure
  fournisseurs sont idéalisées.
- Les détecteurs **graph** (anneaux IBAN partagés) et **isolation forest** ne
  sont pas inclus dans ce tableau — leurs métriques sont mesurées dans des
  tests dédiés (`tests/test_graph.py`, `tests/test_isolation_forest.py`).
- Les **seuils par défaut sont conservateurs** (privilégient le rappel). En
  production, un manager peut les durcir via la page des seuils (V2) sans
  perdre la traçabilité grâce à l'audit log.

## Suite

- Sprint 8B : whitelist managériale + feedback loop pour réduire les faux
  positifs sur doublons.
- V2 : entity resolution probabiliste (Splink) pour fusionner les fournisseurs
  cousins avant le scoring — précision attendue + 10 à 20 points.
