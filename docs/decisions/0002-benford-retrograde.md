# ADR-0002 — Benford rétrogradé en outil de scoping

- Statut : Accepté
- Date : 2026-05-07

## Contexte

La loi de Newcomb-Benford figure parmi les sept détecteurs d'origine du produit.
Sur les jeux de données d'audit P2P réels :

- la précision (qualité d'alerte) reste basse : un test F1D ou F2D non conforme
  signale une *population à examiner*, pas une *transaction frauduleuse* ;
- la non-conformité Benford est souvent expliquée par des seuils métiers
  légitimes (validation 1 000 / 5 000 / 10 000 €), des prix unitaires
  catalogue, ou une concentration de fournisseurs ;
- les comités d'audit ne savent pas quoi faire d'un finding « Benford
  non-conforme sur la facture INVxxxxx » ;
- inclure Benford comme finding direct au même niveau que doublons ou
  changement d'IBAN dilue la lisibilité du score consolidé.

## Décision

Rétrograder Benford en **outil de scoping orienté risque** :

1. Le poids `benford` dans `weights.yaml` passe de `0.5` à `0.0` par défaut.
2. Le module `detectors/benford.py` est conservé tel quel ; il alimente une
   page Streamlit dédiée (« Scoping orienté risque ») et n'apparaît plus
   dans le score consolidé sauf décision explicite (override
   `detector_weights={"benford": ...}` côté script).
3. Le `risk_engine` filtre tout finding `detector="benford"` avant agrégation,
   en mode strict (uniquement avec sévérité `INFO` future ou poids non-nul).
4. La page `pages/2_🔢_Benford.py` reste accessible mais signale clairement
   son rôle d'orientation (sélection de populations à échantillonner pour
   tests JET / ISA 240).

## Conséquences

- La rétro-compatibilité est préservée : un appelant qui passe `detector_weights`
  explicite peut réactiver Benford.
- Les tests existants `test_benford.py` et `test_risk_engine.py` doivent rester
  verts (ce qui est le cas car `test_risk_engine.py` n'utilise pas le détecteur
  Benford comme finding par défaut).
- L'utilisateur final voit un score plus interprétable et moins de bruit en
  démo.
