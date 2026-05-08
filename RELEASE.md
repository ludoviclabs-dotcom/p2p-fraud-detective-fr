# Processus de release

Référence : [ADR-0005 — Release engineering](docs/decisions/0005-release-engineering-semver.md).

## Avant la release

1. La branche cible est mergée sur `main`.
2. CI verte sur `main` (pytest + ruff + smoke Streamlit).
3. Tests F1 reproductibles : `make bench-f1` ne dégrade pas les recall
   verrouillés (BEC IBAN swap ≥ 0.95, doublons ≥ 0.85).
4. Lecture finale du `CHANGELOG.md` : la section `[Unreleased]` reflète
   exactement les changements depuis le dernier tag.

## Bump de version

```bash
# 1. Décider du type de bump (cf. ADR-0005)
NEW_VERSION="0.2.0"

# 2. Mettre à jour pyproject.toml
sed -i "s/^version = .*/version = \"${NEW_VERSION}\"/" pyproject.toml

# 3. Promouvoir [Unreleased] dans CHANGELOG.md
#    Renommer en [${NEW_VERSION}] - $(date +%Y-%m-%d)
#    Ajouter une nouvelle section [Unreleased] vide

# 4. Commit
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): v${NEW_VERSION}"
```

## Tag et push

```bash
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"
git push origin main
git push origin "v${NEW_VERSION}"
```

## GitHub Release

Créer manuellement une Release à partir du tag :

1. Github → Releases → *Draft a new release*.
2. Tag : `v${NEW_VERSION}`.
3. Titre : `v${NEW_VERSION} — <résumé en une ligne>`.
4. Body : copier la section `[${NEW_VERSION}]` du `CHANGELOG.md`.
5. Marquer comme *Latest release*.

## Pré-versions (release candidates)

Pour valider chez un design partner avant promotion :

```bash
NEW_VERSION="0.3.0-rc.1"
sed -i "s/^version = .*/version = \"${NEW_VERSION}\"/" pyproject.toml
git tag -a "v${NEW_VERSION}" -m "Pre-release v${NEW_VERSION}"
git push origin "v${NEW_VERSION}"
```

Marquer la GitHub Release comme *Pre-release*.

## Post-release

- Communication interne (le cas échéant).
- Mise à jour du badge de version dans le README.
- Surveillance des incidents pendant 7 jours minimum.

## Hotfix

```bash
# Pour un bug critique sur la release courante
git checkout v${LAST_VERSION}
git checkout -b hotfix/<sujet>
# correctif + tests
git commit -m "fix: <description>"
PATCHED="0.2.1"
sed -i "s/^version = .*/version = \"${PATCHED}\"/" pyproject.toml
# CHANGELOG : ajouter [0.2.1] - <date>
git commit --amend -a
git tag -a "v${PATCHED}" -m "Hotfix v${PATCHED}"
git push origin "v${PATCHED}"
# Merger ensuite hotfix → main
```
