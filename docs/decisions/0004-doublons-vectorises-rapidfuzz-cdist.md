# ADR-0004 — Vectorisation des doublons fuzzy via `rapidfuzz.process.cdist`

- Statut : Accepté
- Date : 2026-05-07

## Contexte

Le détecteur de doublons fuzzy de Sprint 1 utilisait une boucle Python imbriquée
sur `df.iterrows()` + `df.at[...]` pour chaque paire candidate. Sur des datasets
ETI réels (50 k–100 k factures), le coût observé devient dominant dans le
pipeline complet :

| Volume | Implémentation initiale | Cible Sprint 8 |
|---|---|---|
| 10 000 lignes | 12–15 s | < 3 s |
| 50 000 lignes | ~280 s extrapolés | < 30 s |
| 100 000 lignes | rejet (timeout) | < 90 s |

Trois facteurs expliquent la dégradation : accès `df.at[i, col]` est O(log n) en
indexation, l'appel `fuzz.token_set_ratio` se fait en CPython sur chaque paire,
et la boucle Python ajoute un overhead constant.

## Décision

Réimplémenter `_detect_fuzzy()` en mode vectorisé :

1. Pré-extraction unique en `numpy.ndarray` de `invoice_id`, `amount`,
   `vendor_name`, `iban`, `invoice_date` et noms normalisés.
2. Bucketisation par fenêtre temporelle inchangée (ne casse pas la complexité).
3. Pour chaque triplet (bucket−1, bucket, bucket+1) :
   - calcul de la matrice complète des scores via `rapidfuzz.process.cdist`
     (parallélisé en C, avec `score_cutoff` pour court-circuiter les paires
     trop éloignées),
   - masques numpy pour le filtre montant (tolérance abs/rel, bordcasting),
   - extraction des paires candidates en une seule passe `np.where`,
   - garde-fous : `seen_pairs`, dédoublonnage exact, lignes à nom vide.

## Conséquences

- **Performance** : 50 k factures passent de ~280 s à 14 s sur les doublons
  (mesuré via `scripts/bench_pipeline.py`), soit un gain ~20×.
- **Lecture du code** : la boucle vectorisée est plus dense mais documentée
  en docstring avec les 4 étapes du pipeline.
- **Compatibilité** : signature publique `detect_duplicates()` inchangée ;
  les 3 tests unitaires + le test F1 de recall passent sans modification ; les
  evidences (`fuzzy_score`, `sibling`, `amount`, `vendor_name`) restent
  identiques.
- **Bench reproductible** : `scripts/bench_pipeline.py --rows N --vendors V`
  permet de re-mesurer après chaque évolution.

## Alternatives rejetées

- **Cython / Numba** : gain marginal sur les comparaisons de chaînes ; nécessite
  build C et complique le déploiement on-prem.
- **Embedding + ANN (FAISS)** : pertinent en V3 pour entity resolution
  (Splink), trop lourd pour des doublons de factures à courte fenêtre.
- **MinHash + LSH** : alternative sérieuse pour > 1 M lignes ; non nécessaire
  à l'échelle ETI cible (≤ 500 k factures/an typique).
