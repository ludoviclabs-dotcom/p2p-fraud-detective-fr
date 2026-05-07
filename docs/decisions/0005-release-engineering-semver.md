# ADR-0005 — Release engineering : SemVer + tags + release notes

- Statut : Accepté
- Date : 2026-05-07

## Contexte

Le repo n'a pas encore de tag de version. Les CI passent, les détecteurs sont
stables, et le package suit une trajectoire MVP → produit. Pour permettre à un
design partner ou à un cabinet d'épingler une version connue, il faut une
politique de release explicite et reproductible.

## Décision

1. **Versioning SemVer** (`MAJOR.MINOR.PATCH`) avec règles d'incrémentation :
   - `MAJOR` : changement cassant de schéma Pydantic public (`Invoice`,
     `Finding`, `RiskScore`, `Case`) ou suppression d'une page Streamlit.
   - `MINOR` : nouveau détecteur, nouvelle page, ajout de champ optionnel,
     nouveau preset ERP.
   - `PATCH` : correction de bug, amélioration perf, mise à jour doc, lint.
2. **Tags Git** : `v<MAJOR>.<MINOR>.<PATCH>` annotés (`git tag -a`), poussés
   après merge sur `main`.
3. **CHANGELOG Keep-a-Changelog** : la section `[Unreleased]` est promue en
   `[X.Y.Z] - YYYY-MM-DD` au moment du tag.
4. **GitHub Release** : créée à partir du tag, contenu = section CHANGELOG
   correspondante.
5. **Stratégie de support** : seule la version `MAJOR` la plus récente reçoit
   des correctifs. Pas de backport pour cette phase MVP.
6. **Pré-versions** : suffixes `-rc.N` autorisés pour valider chez un design
   partner avant promotion (`v0.2.0-rc.1` → `v0.2.0`).

## Première release : v0.2.0

Le bump de `0.1.0` à `0.2.0` reflète l'addition substantielle des Sprints 1 à
8 :

- master data history (Sprint 1),
- sanctions / PEP (Sprint 2),
- case management + audit log (Sprint 3),
- reason codes + waterfall + explainer (Sprint 4),
- cockpit + vendor 360° (Sprint 5),
- presets ERP (Sprint 6),
- RBAC + crypto + DPIA + AI Act register (Sprint 7),
- vectorisation doublons + benchmark + docs site (Sprint 8 technique).

Aucun de ces changements n'est cassant pour un appelant qui utilisait `0.1.0`
(les schémas Pydantic ont été étendus par champs optionnels uniquement, le
`risk_engine` a un nouveau paramètre opt-in).

## Conséquences

- `RELEASE.md` documente le processus pas à pas.
- Le bump de version se fait dans `pyproject.toml` (`version = "0.2.0"`).
- Les CHANGELOG futurs distinguent clairement `[Unreleased]` et les sections
  taggées.
- La CI pourra à terme automatiser la création de la GitHub Release sur
  push d'un tag `v*` (non implémenté à ce stade — manuel pour `v0.2.0`).
