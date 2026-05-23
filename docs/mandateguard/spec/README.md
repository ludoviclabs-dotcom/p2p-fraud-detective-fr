# MandateGuard / Payment Integrity Platform — Dossier Claude Code

Ce dossier contient une spécification Markdown découpée pour construire une plateforme de sécurité des flux bancaires.

Le produit est organisé en deux modules complémentaires :

1. **SEPA Mandate Guard** : coffre-fort de mandats SEPA, analyse des prélèvements entrants, détection d’anomalies ICS/RUM/IBAN, révocation, dossier de contestation.
2. **P2P / Supplier Payment Guard** : analyse des paiements sortants, changements de RIB fournisseur, nouveaux bénéficiaires, doublons, sous-seuils, graphes de fraude, evidence pack.

Le cœur commun s’appelle **Risk Core** : règles explicables, reason codes, scoring, décisions, evidence pack et audit ledger.

## Comment utiliser ce dossier avec Claude Code

Copier ces fichiers à la racine du dépôt, puis demander à Claude Code de lire dans cet ordre :

1. `CLAUDE.md`
2. `docs/00_MANIFEST.md`
3. `docs/01_PRODUCT_SCOPE.md`
4. `docs/02_ARCHITECTURE_VISUELLE.md`
5. `docs/03_ARCHITECTURE_CODE.md`
6. `docs/15_ROADMAP_BACKLOG.md`
7. `docs/16_PROMPTS_CLAUDE_CODEX.md`

Ensuite, travailler par sprint en utilisant les tâches de `backlog/`.

## Objectif technique

Stack cible :

- Next.js App Router
- TypeScript strict
- pnpm workspaces
- Prisma + Postgres
- Zod
- Vitest + Playwright
- Vercel pour web, API, crons et orchestration
- Worker Python optionnel pour analytics batch lourdes : pandas, scikit-learn, NetworkX

## Non-objectifs du MVP

Le MVP ne doit pas :

- initier des paiements ;
- se présenter comme une banque ;
- bloquer réellement des prélèvements sans intégration PSP/banque ;
- stocker d’IBAN en clair ;
- envoyer de données personnelles non masquées à un LLM ;
- utiliser une blockchain publique contenant des données personnelles.

## Résultat attendu du MVP

Un produit web permettant de :

- créer et révoquer des mandats SEPA ;
- importer des prélèvements ;
- analyser chaque événement avec un score explicable ;
- créer des alertes ;
- générer un dossier de contestation ;
- conserver une piste d’audit vérifiable ;
- tester des scénarios dans un Risk Lab.

