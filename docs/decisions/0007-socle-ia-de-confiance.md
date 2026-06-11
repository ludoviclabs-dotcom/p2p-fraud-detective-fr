# ADR-0007 — Socle IA de confiance et cadrage des features IA

- Statut : Accepté
- Date : 2026-06-10

## Contexte

La roadmap IA prévoit 6 features (Fraud Case 360 AI, Detection Studio,
Risk Replay, Assistant analyste, Synthetic Generator, Audit Log Explainer).
Avant de les construire, trois décisions structurantes devaient être actées,
plus la définition du socle technique commun.

## Décision A — Recentrage produit : Procure-to-Pay

Le produit est recentré sur la fraude **Procure-to-Pay** (audit fournisseurs /
factures, ISA 240, Sapin 2, LCB-FT) — là où vivent les actifs réels :
9 détecteurs déterministes, risk engine, audit log signé Ed25519, conformité.

La page Next.js `detection-studio` actuelle (détecteurs « paiement
particulier » : APP fraud, scam narrative, QR code, device risk — scoring
100 % client-side, déconnecté du moteur Python) est **requalifiée en démo**.
Elle sera remplacée par le vrai Detection Studio (authoring de règles YAML
branché au backend) en Phase 4 de la roadmap. Aucune nouvelle feature ne
s'appuie sur `apps/web/lib/risk/scoreEngine.ts`.

## Décision B — Orchestration IA côté Python/FastAPI

Toute la couche IA (génération structurée, grounding, ledger) vit dans
`src/p2p_fraud/llm/` et est exposée via `/api/v1/...`. Le frontend Next.js
est consommateur. Justification :

- accès direct aux sources factuelles (détecteurs, audit log) sans
  duplication de logique en TypeScript ;
- la clé `ANTHROPIC_API_KEY` reste côté serveur ;
- les appels IA sont journalisés dans le **même audit log signé** que le
  reste du produit ;
- le patron existe déjà (`llm/narrative_generator.py`).

Conformément à l'ADR-0006, le site Vercel public reste une démo statique :
les pages Next.js des features IA embarquent un fallback démo quand
`NEXT_PUBLIC_API_URL` est absent, et basculent sur le FastAPI quand il est
configuré.

## Décision C — Modèle Claude par tâche

| Tâche | Modèle | Justification |
|---|---|---|
| Génération structurée critique (Case 360, draft de règles, Audit Explainer) | `claude-opus-4-8` | Qualité maximale sur sortie engageante ; 5 $/25 $ par MTok |
| Narratif d'audit, copilote Q&A (volume) | `claude-sonnet-4-6` | Bon ratio qualité/coût ; 3 $/15 $ par MTok ; déjà utilisé par `narrative_generator` |
| Classification légère (routing, tri) | `claude-haiku-4-5` | 1 $/5 $ par MTok |

Le modèle est un paramètre par appel (jamais codé en dur dans la logique),
avec ces valeurs en défaut par tâche. Paramètres : pas de `temperature`
(retiré sur Opus 4.7+), `thinking` adaptatif si pertinent.

## Le socle (transversal — construit une fois, réutilisé par les 6 features)

1. **Sortie structurée garantie** : `output_config.format` (structured
   outputs natifs de l'API, schéma Pydantic via `client.messages.parse()`).
   Remplace l'approche « tool-use forcé » du brief initial : la conformité
   au schéma est garantie par l'API elle-même, pas par le prompt.
   Module : `llm/structured.py`.
2. **Schéma unique** : les schémas IA sont définis en Pydantic
   (`llm/schemas.py`), source de vérité unique. Le frontend consomme le JSON
   typé (pas de duplication Zod).
3. **Validateur de provenance** : chaque claim généré cite des `source_ids` ;
   du code vérifie que chaque id existe dans le source pack fourni au
   modèle. Claim non sourcé ou id inconnu → rejeté/marqué. On ne fait
   jamais confiance au LLM pour la citation. Module : `llm/provenance.py`.
4. **Chemin « preuve insuffisante »** : tous les schémas portent
   `missing_evidence` et `human_review_required` ; le prompt système impose
   de déclarer le manque plutôt que de combler.
5. **Human-in-the-loop** : aucune feature IA ne déclenche de décision
   automatique (blocage paiement, clôture de cas). L'IA produit des
   recommandations de revue humaine.
6. **Ledger d'appels IA** : chaque appel est journalisé dans l'audit log
   signé (kind `ai.generation`) avec version de prompt, modèle, tokens
   (input/output/cachés), source_ids et feature. Module : `llm/ai_ledger.py`.
7. **Redaction PII fail-closed** : `ai/redact.py` est appliqué avant tout
   envoi au modèle ; `is_safe_for_llm(raise_on_leak=True)` bloque l'appel
   si une fuite subsiste.
8. **Harnais d'évaluation** : golden set par feature dans `tests/eval/`,
   métriques % claims sourcés / hallucinations ; les tests déterministes
   (provenance, redaction, ledger) tournent en CI sans clé API, les évals
   LLM sont `skip` sans `ANTHROPIC_API_KEY`.

## Feature pilote

L'**Audit Log Explainer** (Phase 2 roadmap) est la première feature bâtie
sur ce socle : la vérification crypto reste 100 % déterministe
(`AuditLog.verify_chain`) ; le LLM traduit uniquement le verdict technique
en langage audit, sans jamais prétendre avoir vérifié lui-même.

## Conséquences

- Chaque nouvelle feature IA doit être inscrite au registre AI Act
  (`docs/compliance/`) avant mise en production.
- Le coût IA est traçable par agrégation des entrées `ai.generation` du
  ledger.
- La boucle de feedback détection (verdicts `closed_false_positive` déjà
  capturés par `CaseStatus`) est exposée en stats par détecteur, prérequis
  du backtest Detection Studio (Phase 4).
