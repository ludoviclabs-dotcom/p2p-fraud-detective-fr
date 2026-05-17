# CLAUDE.md

> Guide pour les agents Claude (Code, web, IDE) intervenant sur ce dépôt.
> Lis ce fichier avant toute modification produit ou documentation.

## Identité du projet

**P2P Fraud Detective FR** — démonstrateur public d'outil d'aide à la
détection, l'investigation et la documentation d'anomalies du cycle
Procure-to-Pay (achats → comptabilité → paiement).

- Cible long terme : couche spécialisée de contrôle continu de l'intégrité
  fournisseur et paiement, interopérable avec ERP, plateformes de
  facturation électronique et services VoP.
- Statut actuel : **démonstrateur public**, données 100 % synthétiques.
- Ce n'est **pas** un système LCB-FT au sens de l'art. L. 561-2 CMF
  (assujettis Tracfin), ni une solution clé en main DORA / NIS2 /
  AI Act haut risque.

## Règles d'édition strictes

Les agents Claude **doivent** respecter les règles suivantes. Elles
proviennent d'un audit de crédibilité (mai 2026) et leur non-respect a
déjà introduit des claims attaquables.

1. **Aucune jurisprudence non sourcée**. Ne pas écrire « TGI X a validé… »,
   « Cour des comptes Y a accepté… », « ACPR a publié une note du
   DATE… » sans référence vérifiable (lien Légifrance, site institutionnel,
   numéro de décision). En l'absence de source, supprimer la mention.
2. **Pas de dates futures déclaratives**. Toute date dans la documentation
   doit être ≤ date du jour ou explicitement marquée « prospective » dans
   un plan/roadmap. Ne pas dater un document du futur.
3. **Trois statuts conformité distincts** sur la page Gouvernance :
   - 🟢 **Applicable et documenté** : le projet implémente directement
     (RGPD art. 30, AI Act art. 50 risque limité, RGS B1/B2 Ed25519).
   - 🟡 **Aide à la mise en œuvre** : artefacts pour le déployeur (AMLD6
     mapping, Sapin 2, DORA, CSRD).
   - 🔵 **À configurer selon le contexte client** : NIS2, DPIA spécifique,
     RGAA complet, qualification SecNumCloud.
   Ne pas écrire « conforme à AMLD6 » sans qualification.
4. **Métriques chiffrées toujours qualifiées**. F1, recall, ROI, précision :
   préfixer systématiquement par « sur dataset synthétique étiqueté » et
   lier la page Méthodologie. Ne pas inventer de chiffres ni recopier des
   chiffres non sourcés.
5. **Conserver les bandeaux démonstrateur**. Le composant `DemoBanner` dans
   `apps/web/components/app-shell.tsx` doit rester visible sur toutes les
   pages. Le hero ne doit pas le contredire.
6. **Tracfin** : ne pas réintroduire « bouton Générer brouillon DS Tracfin »
   ni de mention laissant croire à une transmission ERMES. Le produit n'est
   pas un système opérationnel d'assujetti L. 561-2 CMF. Les exports
   d'investigation sont des documents internes annotés « démonstration
   pédagogique ».
7. **Pas de claim « RGPD-ready »** standalone. Préférer « minimisation et
   traçabilité documentées » et renvoyer vers `/governance`.
8. **Documentation produit cohérente**. Si tu modifies l'architecture, mets
   à jour `docs/architecture.md` ET `docs/migration-v2-recap.md` ET le
   README en cohérence.

## Stack technique (v0.6, mai 2026)

Monorepo hybride :

```
/                                  ← racine
├── streamlit_app.py               ← UI legacy v0.5 (Streamlit Cloud)
├── pages/                         ← 21 pages Streamlit
├── src/p2p_fraud/                 ← Backend Python : FastAPI + détecteurs
│   ├── api/                       ← Routes /api/v1/* (FastAPI)
│   ├── detectors/                 ← 8 détecteurs réels (Benford, doublons,
│   │                                 sanctions, anneaux IBAN, sous-seuils,
│   │                                 Isolation Forest, master data, sirene)
│   ├── enrichment/                ← Sirene v3, DECP DuckDB, RBE, sanctions
│   ├── scoring/                   ← Risk engine + weights.yaml
│   ├── cases/                     ← Case management + audit log
│   ├── security/                  ← OIDC, RBAC, Fernet IBAN, Ed25519
│   ├── llm/                       ← Anthropic Claude (narratif interne)
│   ├── export/                    ← Excel hyperliens, Parquet, PDF
│   └── synthetic/                 ← Générateur datasets étiquetés
├── apps/web/                      ← UI v2 Next.js 15 (App Router)
│   ├── app/                       ← Routes (home, dashboard, cases,
│   │                                 vendors, governance, methodology,
│   │                                 about, sandbox, …)
│   └── components/                ← UI + locale-provider + app-shell
├── packages/shared-types/         ← Types OpenAPI auto-générés
├── docs/                          ← Architecture, méthodologie, conformité,
│                                    migration v2, sources de données
├── tests/                         ← pytest (fixtures, integration, e2e)
└── data/                          ← Sanctions, samples synthétiques
```

Voir `docs/architecture.md` pour le détail.

## Commandes courantes

```bash
# Frontend Next.js v2
pnpm install                       # install root + workspaces
pnpm web:dev                       # dev server (apps/web)
pnpm web:build                     # build production
pnpm sdk:gen-types                 # régénère les types depuis OpenAPI

# Backend Python (FastAPI)
pip install -e ".[dev]"
uvicorn p2p_fraud.api.main:app --reload --port 8000

# Frontend Streamlit (legacy)
streamlit run streamlit_app.py

# Tests
pytest -q --cov=src/p2p_fraud
ruff check .
ruff format --check .

# Génération dataset synthétique
python -m p2p_fraud.synthetic.generator \
  --output data/synthetic/dataset_50k.csv --rows 50000
```

## Branches git

- `main` — branche stable, base des releases.
- `claude/setup-procurement-agent-XzcZY` — itération actuelle (correctifs
  P0 de crédibilité issus du deep research mai 2026).
- Toute nouvelle itération doit ouvrir sa propre branche `claude/<intent>`.

## Tests et CI avant commit

Avant tout commit qui touche la documentation publique ou les pages web :

```bash
# Vérifier qu'aucun claim invérifiable n'a été réintroduit
grep -rn "TGI Paris 2025\|Cour des comptes 2024\|ACPR 2026 note" . \
  --include="*.md" --include="*.tsx" --include="*.ts"
# → doit retourner 0

# Vérifier qu'aucune date future absurde ne traîne
grep -rn "Document mis à jour octobre 2026\|Document mis à jour décembre 2026" docs/
# → doit retourner 0

# Build Next.js
cd apps/web && pnpm build
```

## Références produit

- Rapport de deep research (mai 2026) — diagnostic et trajectoire produit.
- Roadmap V1 → V4 — voir le plan de mise en œuvre (démonstrateur → POC →
  pilote → produit SaaS).
- `docs/migration-v2-recap.md` — état de la migration Streamlit → Next.js.
- `docs/methodologie-audit.md` — mapping ISA 240 / AS 2401 / Sapin 2 / DORA.

## Quand demander avant d'agir

Demander à l'utilisateur avant de :

- Modifier les claims chiffrés (F1, ROI, recall) au-delà de leur
  qualification « synthétique ».
- Toucher au backend `src/p2p_fraud/` quand la consigne portait uniquement
  sur la documentation ou l'UI.
- Pousser sur `main`. Toujours préférer une branche feature.
- Activer des dépendances payantes (Pappers plan supérieur, AWS S3 WORM,
  partenaire VoP) dans le code par défaut.

Ne pas demander pour :

- Corriger une typo, une date passée, un claim invérifiable identifié par
  les règles ci-dessus.
- Ajouter des mentions de limites ou de supervision humaine.
