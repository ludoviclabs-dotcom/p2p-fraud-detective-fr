# Plan d'action — Audit P2P Fraud Detective FR (2026)

> **Document de pilotage.** Transforme l'audit FraudTech déposé
> (`P2P_Fraud_Detective_FR_audit.md`) en plan d'exécution séquencé et chiffré.
> Chaque action pointe le **fichier réel** du dépôt à créer ou modifier et
> l'**article réglementaire** concerné.
>
> Cibles institutionnelles : Tracfin, DGSI, DGT, Big 4 / CAC 40, DAF, CAC, RSSI.
> Langue : français ; noms d'outils et citations réglementaires en VO.
> Déploiement audité : `https://p2p-fraud-detective-fr-web.vercel.app`.

---

## TL;DR exécutif

P2P Fraud Detective FR est **le plus avancé des deux démonstrateurs** : 26 outils,
8 détecteurs en cascade documentés (métriques F1), page Méthodologie de niveau
quasi-commercial, **audit log Ed25519 vérifiable par tiers** (`/audit/verify`),
page Gouvernance riche. Le saut « enterprise » tient à **trois chantiers**, pas
à « plus de features » :

1. **Passer du synthétique au réel** — connecteurs souverains tracés en
   production (Sirene déjà là, **DG Trésor gels**, **VIES**) + ERP/banque.
2. **Durcir la preuve** — **horodatage qualifié RFC 3161 / eIDAS** + stockage
   **WORM** par-dessus la signature Ed25519 (recevabilité juridique).
3. **Ajouter les contrôles paiement manquants** — **Verification of Payee**
   (nom↔IBAN, aligné IPR 2024/886), **validation IBAN structurelle (mod-97)**,
   contrôles **VAT/VIES** anti-carrousel.

Le vrai actif différenciant : **souveraineté + explicabilité + recevabilité
d'audit**.

### Exécution en 4 sprints

| Sprint | Horizon | Briques | Priorité dominante |
|---|---|---|---|
| **0** | ≤ 2 sem. | VIES + IBAN mod-97 · disclosure synthétique-vs-réel · audit statut « live » | Quick wins |
| **1** | 30 j | DG Trésor gels (Yente) · provenance layer v1 | **P0** |
| **2** | 60 j | Verification of Payee · Splink confidence · VAT/carrousel + prix | P1 |
| **3** | 90 j | RFC 3161/eIDAS + WORM · monitoring continu · control library + evidence pack signé | **P0** + P1 |
| **Vision** | 6-12 mois | ERP natifs · DORA register · migration souveraine · model cards versionnés | P2 |

---

## 1. État des lieux — gaps de l'audit ↔ code du dépôt

L'audit vise ce dépôt : chaque gap se rattache à un fichier réel. Légende :
✅ présent · 🟡 partiel · ❌ à créer.

| Gap | Sujet | État | Fichiers d'ancrage |
|---|---|:--:|---|
| — | Audit log Ed25519 + `/audit/verify` | ✅ | `src/p2p_fraud/security/signing.py`, `src/p2p_fraud/cases/audit_log.py`, `src/p2p_fraud/api/v1.py` (`GET /api/v1/audit/verify`), `apps/web/app/audit/page.tsx` |
| — | 8 détecteurs en cascade | ✅ | `src/p2p_fraud/detectors/` + `src/p2p_fraud/scoring/weights.yaml` |
| **G1** | Connecteurs souverains réels (DG Trésor) + ERP/banque | 🟡 | `src/p2p_fraud/enrichment/yente_client.py`, `sanctions_client.py`, `sirene_client.py`, `decp_client.py` · DG Trésor ❌, ERP ❌ |
| **G2** | Horodatage RFC 3161/eIDAS + WORM | ❌ | `src/p2p_fraud/security/signing.py`, `src/p2p_fraud/cases/audit_log.py` · WORM = roadmap `docs/conformite_signatures.md` (l.153-193) |
| **G3** | Verification of Payee nom↔IBAN + IBAN mod-97 | ❌ | à créer : `src/p2p_fraud/detectors/`, `src/p2p_fraud/enrichment/` |
| **G4** | Monitoring continu / re-screening planifié | 🟡 | `src/p2p_fraud/scheduler/runner.py`, `__main__.py`, `Dockerfile.scheduler` |
| **G5** | Data provenance layer formalisé | 🟡 | `src/p2p_fraud/llm/provenance.py`, `apps/web/lib/risk/evidence-pack.ts` |
| **G6** | Contrôles TVA/VIES + carrousel | ❌ | à créer : connecteur VIES dans `src/p2p_fraud/enrichment/` |
| **G7** | Control library exportable | 🟡 | `apps/web/app/governance/page.tsx`, `docs/compliance/` |
| **G8** | Model cards + DPIA versionnés | 🟡 | `docs/model-card-risk-engine.md`, `docs/compliance/dpia_template.md` |
| **G9** | Entity resolution Splink (confiance/lien) | ❌ | `src/p2p_fraud/detectors/duplicates.py` (RapidFuzz seul aujourd'hui) |
| — | Evidence pack signé (PDF/ZIP/JSON tiers) | 🟡 | `apps/web/lib/risk/evidence-pack.ts`, `apps/web/app/api/evidence/export/route.ts` (JSON/HTML non signé) |

---

## 2. Séquencement par sprints

Colonnes : `Réf.` = gap + article · `Fichiers cibles` = ancrage code ·
`Effort` (F/M/É) · `Prio` · `Dépend de`.

### Sprint 0 — Quick wins (≤ 2 semaines)

| # | Tâche | Réf. | Fichiers cibles | Effort | Prio | Dépend de |
|---|---|---|---|:--:|:--:|---|
| S0.1 | Validation IBAN structurelle (ISO 13616, mod-97) + détection de changement de juridiction banque (FR→DE/CY) | G3 / ISO 13616 | nouveau `src/p2p_fraud/detectors/iban_validation.py` ; branchement `master_data_changes.py` | F | P1 | — |
| S0.2 | Connecteur VIES (validation TVA intracommunautaire, gratuit) | G6 / VIES | nouveau `src/p2p_fraud/enrichment/vies_client.py` (+ `cache.py`) | F | P1 | — |
| S0.3 | Généraliser la disclosure **synthétique-vs-réel** + **limitation statements** par détecteur | Crédibilité / AI Act art. 50 | `apps/web/app/methodology/page.tsx`, bandeaux par écran | F | P1 | — |
| S0.4 | Vérifier écran-par-écran le statut « live » des connecteurs (Sirene/DECP/RBE) | Caveat audit | `apps/web/app/sirene/`, `decp`, audit visuel | F | P1 | — |

### Sprint 1 — 30 jours

| # | Tâche | Réf. | Fichiers cibles | Effort | Prio | Dépend de |
|---|---|---|---|:--:|:--:|---|
| S1.1 | Brancher **DG Trésor gels** (`fr_tresor_gels_avoir`) sur le screening Yente souverain | G1 / LCB-FT | `src/p2p_fraud/enrichment/yente_client.py`, `sanctions_client.py` ; dataset DG Trésor | M | **P0** | — |
| S1.2 | **Provenance layer v1** au niveau données (source, timestamp, fraîcheur/TTL, confiance, statut vérifié/inféré/simulé) | G5 | étendre `src/p2p_fraud/llm/provenance.py` + schéma `cases` ; surface `apps/web/lib/risk/evidence-pack.ts` | M | **P0** | — |

### Sprint 2 — 60 jours

| # | Tâche | Réf. | Fichiers cibles | Effort | Prio | Dépend de |
|---|---|---|---|:--:|:--:|---|
| S2.1 | **Verification of Payee** nom↔IBAN sur le master fournisseur (résultats *match/close/no match/other*) | G3 / IPR 2024/886 | nouveau `src/p2p_fraud/detectors/verification_of_payee.py` ; intégration `master_data_changes.py` | M | P1 | S0.1 |
| S2.2 | **Splink** : entity resolution probabiliste + **score de confiance par lien** (fournisseur/IBAN/utilisateur/événement) | G9 | nouveau `src/p2p_fraud/detectors/entity_resolution.py` à côté de `duplicates.py` | M | P1 | — |
| S2.3 | Contrôles **VAT/VIES + carrousel** (incohérence pays) + **variations anormales de prix** (z-score/IQR, règle du faisceau) | G6 | nouveau `src/p2p_fraud/detectors/vat_carousel.py`, `price_anomaly.py` ; `weights.yaml` | M | P2 | S0.2 |

### Sprint 3 — 90 jours

| # | Tâche | Réf. | Fichiers cibles | Effort | Prio | Dépend de |
|---|---|---|---|:--:|:--:|---|
| S3.1 | **Horodatage qualifié RFC 3161 / eIDAS** (jeton `.tsr` vérifiable hors-ligne) par-dessus Ed25519 | G2 / eIDAS | `src/p2p_fraud/security/signing.py`, `src/p2p_fraud/cases/audit_log.py` | M | **P0** | — |
| S3.2 | Stockage **WORM** (S3 Object Lock COMPLIANCE) sur l'audit log | G2 | `src/p2p_fraud/cases/audit_log.py` (`export_jsonl`) ; cf. roadmap `docs/conformite_signatures.md` | M | **P0** | S3.1 |
| S3.3 | **Monitoring continu** : re-screening planifié (fournisseur/dirigeant/IBAN/sanctions/BE) + stream d'alertes daté | G4 / AMLR art. 26 | étendre `src/p2p_fraud/scheduler/runner.py`, `__main__.py`, `alerts/channels.py` | M | P1 | S1.1 |
| S3.4 | **Control library** exportable (mapping ISA 240 / Sapin 2 / LCB-FT / AMLR / DORA), CSV/JSON | G7 | `apps/web/app/governance/page.tsx` ; nouveau export `apps/web/lib/risk/` ; `docs/compliance/` | F | P1 | — |
| S3.5 | **Evidence pack signé unifié** (PDF/ZIP/JSON vérifiable tiers) par-dessus la chaîne Ed25519 + horodatage | Crédibilité / Audit | `apps/web/lib/risk/evidence-pack.ts`, `apps/web/app/api/evidence/export/route.ts` | M | P1 | S3.1 |

### Vision 6-12 mois

| # | Tâche | Réf. | Fichiers cibles | Effort | Prio | Dépend de |
|---|---|---|---|:--:|:--:|---|
| V.1 | Connecteurs **ERP natifs** (SAP / Sage / Cegid) sur master fournisseur + flux factures | G1 | nouveau `src/p2p_fraud/ingestion/` (connecteurs) | É | P2 | — |
| V.2 | **DORA register of information** (alimentation registre prestataires TIC depuis Sirene) | DORA 2022/2554 art. 28 | nouveau module + `src/p2p_fraud/enrichment/sirene_client.py` | M | P2 | — |
| V.3 | Migration souveraine OVHcloud/Scaleway (déclenchée au 1ᵉʳ pilote signé) | Souveraineté | infra / `deploy/` | É | P2 | — |
| V.4 | **Model cards versionnés** par détecteur (AI Act art. 50) | G8 / AI Act art. 50 | étendre `docs/model-card-risk-engine.md` ; `docs/compliance/ai_act_register.md` | F | P2 | — |

---

## 3. Checklist de tickets exécutables

Blocs prêts à coller en issues GitHub. Cocher au fil de l'avancement.

### P0 — critiques

---

#### [P0] Brancher le registre DG Trésor des gels sur le screening Yente

- **Labels** : `P0`, `detection`, `credibility`, `sprint-1`
- **Réf. audit** : G1 · LCB-FT · source de droit `fr_tresor_gels_avoir`
- **Contexte** : OpenSanctions/Yente est déjà câblé (`yente_client.py`,
  `sanctions_client.py`), mais le **registre national des gels DG Trésor**
  (`gels-avoirs.dgtresor.gouv.fr`, API JSON/XML gratuite, horodaté) n'est pas
  branché. C'est une source de droit citable, souveraine.
- **Fichiers cibles** : `src/p2p_fraud/enrichment/yente_client.py`,
  `src/p2p_fraud/enrichment/sanctions_client.py`, dataset snapshot DG Trésor.
- **Critères d'acceptation** :
  - [ ] Dataset DG Trésor ingéré (gels UE + ONU + nationaux) avec horodatage source.
  - [ ] Le détecteur Sanctions/PEP matche contre DG Trésor en plus d'OFAC/UE.
  - [ ] Dégradation gracieuse vers snapshot offline si l'API est indisponible.
  - [ ] Source + timestamp affichés dans le finding (reason code FR).
  - [ ] Test Python couvrant un hit DG Trésor connu.
- **Dépendances** : aucune · **Effort** : Moyen

---

#### [P0] Provenance layer v1 généralisé au niveau données

- **Labels** : `P0`, `credibility`, `audit`, `sprint-1`
- **Réf. audit** : G5
- **Contexte** : la provenance existe au niveau LLM (`llm/provenance.py`,
  `SourcePack`) et evidence pack, mais pas comme métadonnée systématique sur
  chaque donnée enrichie. L'audit demande : source, timestamp d'acquisition,
  fraîcheur (TTL), niveau de confiance, statut vérifié/inféré/simulé.
- **Fichiers cibles** : `src/p2p_fraud/llm/provenance.py` (extension),
  schéma `cases`, `apps/web/lib/risk/evidence-pack.ts` (surface UI).
- **Critères d'acceptation** :
  - [ ] Modèle de métadonnée provenance réutilisable (source / timestamp / TTL / confiance / statut).
  - [ ] Chaque donnée enrichie (Sirene, sanctions, DECP…) porte sa provenance.
  - [ ] Badge UI : vert = vérifié source officielle horodatée ; gris = inféré ; rayé = simulé.
  - [ ] La provenance est incluse dans l'evidence pack exporté.
  - [ ] Tests sur la validation/expiration TTL.
- **Dépendances** : aucune · **Effort** : Moyen

---

#### [P0] Horodatage qualifié RFC 3161 / eIDAS sur l'audit log

- **Labels** : `P0`, `audit`, `credibility`, `sprint-3`
- **Réf. audit** : G2 · eIDAS
- **Contexte** : l'audit log est signé Ed25519 et vérifiable
  (`/audit/verify`), mais **sans horodatage qualifié tiers**. Un jeton RFC 3161
  (`.tsr`) émis par une TSA qualifiée UE est vérifiable hors-ligne (OpenSSL) et
  durcit la recevabilité juridique.
- **Fichiers cibles** : `src/p2p_fraud/security/signing.py`,
  `src/p2p_fraud/cases/audit_log.py`.
- **Critères d'acceptation** :
  - [ ] Appel TSA qualifiée UE → jeton `.tsr` attaché à l'entrée d'audit.
  - [ ] Vérification hors-ligne du jeton documentée (commande OpenSSL).
  - [ ] `/audit/verify` valide chaîne Ed25519 **et** horodatage qualifié.
  - [ ] Dégradation gracieuse + statut explicite si la TSA est indisponible.
  - [ ] Test Python : altération du timestamp → vérification échoue.
- **Dépendances** : aucune · **Effort** : Moyen

---

#### [P0] Stockage WORM de l'audit log

- **Labels** : `P0`, `audit`, `sprint-3`
- **Réf. audit** : G2
- **Contexte** : WORM est documenté en roadmap (`conformite_signatures.md`
  l.153-193) mais non implémenté. `export_jsonl()` est conçu pour l'archivage,
  sans intégration S3 Object Lock.
- **Fichiers cibles** : `src/p2p_fraud/cases/audit_log.py` (`export_jsonl`).
- **Critères d'acceptation** :
  - [ ] Export audit log vers bucket S3 Object Lock mode COMPLIANCE (immutabilité prouvable).
  - [ ] Politique de rétention paramétrable, documentée Sapin 2.
  - [ ] Procédure de vérification d'intégrité de l'archive WORM.
  - [ ] Test/CI mock S3 (moto ou équivalent).
- **Dépendances** : S3.1 (horodatage) · **Effort** : Moyen

---

### P1 — élevées

---

#### [P1] Verification of Payee (nom↔IBAN) sur le master fournisseur

- **Labels** : `P1`, `detection`, `sprint-2`
- **Réf. audit** : G3 · IPR — Règlement (UE) 2024/886 (VoP obligatoire zone euro
  depuis le 9 oct. 2025)
- **Contexte** : contrôle amont nom↔IBAN avant paiement (pas l'exécution
  bancaire). Résultats normalisés : *match / close match / no match / other*.
- **Fichiers cibles** : nouveau `src/p2p_fraud/detectors/verification_of_payee.py`,
  intégration `src/p2p_fraud/detectors/master_data_changes.py`.
- **Critères d'acceptation** :
  - [ ] Comparaison nom déclaré ↔ titulaire IBAN, sortie normalisée 4 états.
  - [ ] Signal levé sur *no match* / *close match* dans le scoring (`weights.yaml`).
  - [ ] Reason code FR explicite.
  - [ ] Tests couvrant les 4 états.
- **Dépendances** : S0.1 (validation IBAN) · **Effort** : Moyen

---

#### [P1] Validation IBAN structurelle (mod-97) + changement de juridiction

- **Labels** : `P1`, `detection`, `sprint-0`
- **Réf. audit** : G3 · ISO 13616
- **Contexte** : esquissé dans le scénario ALPHACOM (FR→DE), à généraliser comme
  contrôle systématique.
- **Fichiers cibles** : nouveau `src/p2p_fraud/detectors/iban_validation.py`,
  branchement `master_data_changes.py`.
- **Critères d'acceptation** :
  - [ ] Validation checksum mod-97 + structure par pays.
  - [ ] Détection de changement de juridiction banque sur le master fournisseur.
  - [ ] Signal + reason code FR.
  - [ ] Tests IBAN valides/invalides + cas FR→DE/CY.
- **Dépendances** : aucune · **Effort** : Faible

---

#### [P1] Connecteur VIES + contrôles carrousel TVA

- **Labels** : `P1`, `detection`, `sprint-0`/`sprint-2`
- **Réf. audit** : G6 · VIES
- **Contexte** : validation TVA intracommunautaire temps réel = pivot
  anti-carrousel. Détecter incohérence pays livraison/facturation/entité +
  entité récemment immatriculée + IBAN hors zone + montant sous seuil.
- **Fichiers cibles** : nouveau `src/p2p_fraud/enrichment/vies_client.py`,
  nouveau `src/p2p_fraud/detectors/vat_carousel.py`, `weights.yaml`.
- **Critères d'acceptation** :
  - [ ] Validation TVA via VIES (SOAP/REST) avec cache et dégradation gracieuse.
  - [ ] Détecteur carrousel (règle du faisceau : ≥ N signaux convergents).
  - [ ] Reason codes FR.
  - [ ] Tests numéro TVA valide/invalide + scénario carrousel.
- **Dépendances** : aucune · **Effort** : Faible→Moyen

---

#### [P1] Splink — entity resolution + score de confiance par lien

- **Labels** : `P1`, `detection`, `sprint-2`
- **Réf. audit** : G9
- **Contexte** : aujourd'hui RapidFuzz (`duplicates.py`) seul. Splink (MoJ, MIT)
  ajoute un record linkage probabiliste explicable avec score par lien.
- **Fichiers cibles** : nouveau `src/p2p_fraud/detectors/entity_resolution.py`.
- **Critères d'acceptation** :
  - [ ] Modèle Splink sur fournisseur/IBAN/utilisateur/événement.
  - [ ] Score de confiance par arête exposé dans le graphe (`detectors/graph.py`).
  - [ ] Visualisation explicative du lien.
  - [ ] Tests sur un jeu de doublons connus.
- **Dépendances** : aucune · **Effort** : Moyen

---

#### [P1] Monitoring continu / re-screening planifié

- **Labels** : `P1`, `detection`, `credibility`, `sprint-3`
- **Réf. audit** : G4 · AMLR art. 26
- **Contexte** : un socle scheduler existe (`scheduler/runner.py`, `--daily`,
  `Dockerfile.scheduler`). À étendre en re-screening planifié multi-entités +
  stream d'alertes daté.
- **Fichiers cibles** : `src/p2p_fraud/scheduler/runner.py`,
  `src/p2p_fraud/scheduler/__main__.py`, `src/p2p_fraud/alerts/channels.py`.
- **Critères d'acceptation** :
  - [ ] Re-screening planifié fournisseur/dirigeant/IBAN/sanctions/BE.
  - [ ] Détection de delta (nouveau hit) → alerte datée.
  - [ ] Canal d'alerte (Slack/Teams/SMTP) déclenché sur changement.
  - [ ] Tests sur la détection de delta.
- **Dépendances** : S1.1 (DG Trésor) · **Effort** : Moyen

---

#### [P1] Control library exportable (mapping référentiels)

- **Labels** : `P1`, `credibility`, `audit`, `sprint-3`
- **Réf. audit** : G7
- **Contexte** : la gouvernance affiche les mappings (`governance/page.tsx`,
  `docs/compliance/`) mais sans export structuré. Cible : matrice rule_id →
  contrôle (ISA 240 / Sapin 2 / LCB-FT / AMLR / DORA), CSV/JSON.
- **Fichiers cibles** : `apps/web/app/governance/page.tsx`, nouvel export
  `apps/web/lib/risk/`, `docs/compliance/`.
- **Critères d'acceptation** :
  - [ ] Matrice de contrôles exportable CSV + JSON.
  - [ ] Chaque finding pointe son article (CMF, ISA 240, Sapin 2, DORA).
  - [ ] Bouton d'export dans la page Gouvernance.
  - [ ] Test Vitest sur la génération de l'export.
- **Dépendances** : aucune · **Effort** : Faible

---

#### [P1] Evidence pack signé unifié (PDF/ZIP/JSON vérifiable tiers)

- **Labels** : `P1`, `audit`, `credibility`, `sprint-3`
- **Réf. audit** : Crédibilité/Audit (artefact)
- **Contexte** : evidence pack actuel = JSON + HTML non signé
  (`evidence-pack.ts`, `evidence/export/route.ts`). À durcir en dossier signé
  vérifiable par un tiers, adossé à la chaîne Ed25519 + horodatage RFC 3161.
- **Fichiers cibles** : `apps/web/lib/risk/evidence-pack.ts`,
  `apps/web/app/api/evidence/export/route.ts`.
- **Critères d'acceptation** :
  - [ ] Dossier signé (PDF + JSON + clé de vérification) généré en un clic.
  - [ ] Intégrité rattachée à la chaîne Ed25519 + jeton horodatage.
  - [ ] Procédure de vérification tierce documentée.
  - [ ] Test Vitest sur la cohérence du pack.
- **Dépendances** : S3.1 (horodatage) · **Effort** : Moyen

---

### P2 — moyennes / vision

---

#### [P2] Variations anormales de prix (z-score / IQR, règle du faisceau)

- **Labels** : `P2`, `detection`, `sprint-2`
- **Réf. audit** : G6 (volet prix)
- **Fichiers cibles** : nouveau `src/p2p_fraud/detectors/price_anomaly.py`,
  `weights.yaml`.
- **Critères d'acceptation** :
  - [ ] z-score/IQR sur l'historique prix unitaire par catégorie d'achat.
  - [ ] Jamais un signal isolé (règle du faisceau).
  - [ ] Reason code FR + tests.
- **Effort** : Moyen

---

#### [P2] Model cards versionnés par détecteur (AI Act art. 50)

- **Labels** : `P2`, `credibility`, `audit`, `vision`
- **Réf. audit** : G8 · AI Act art. 50
- **Fichiers cibles** : `docs/model-card-risk-engine.md`,
  `docs/compliance/ai_act_register.md`.
- **Critères d'acceptation** :
  - [ ] Une model card versionnée par détecteur (inputs/outputs/limites).
  - [ ] Lien depuis le registre AI Act.
- **Effort** : Faible

---

#### [P2] Connecteurs ERP natifs (SAP / Sage / Cegid)

- **Labels** : `P2`, `detection`, `vision`
- **Réf. audit** : G1 (volet ERP)
- **Fichiers cibles** : nouveau module sous `src/p2p_fraud/ingestion/`.
- **Critères d'acceptation** :
  - [ ] Connecteur master fournisseur + flux factures (≥ 1 ERP).
  - [ ] Mapping vers le modèle interne + provenance.
- **Effort** : Élevé

---

#### [P2] DORA register of information

- **Labels** : `P2`, `credibility`, `vision`
- **Réf. audit** : DORA (UE) 2022/2554 art. 28
- **Fichiers cibles** : nouveau module + `src/p2p_fraud/enrichment/sirene_client.py`.
- **Critères d'acceptation** :
  - [ ] Aide à l'alimentation du registre prestataires TIC depuis Sirene.
- **Effort** : Moyen

---

#### [P2] Migration souveraine OVHcloud / Scaleway

- **Labels** : `P2`, `credibility`, `vision`
- **Réf. audit** : Souveraineté (déclenchée au 1ᵉʳ pilote signé)
- **Fichiers cibles** : infra, `deploy/`.
- **Critères d'acceptation** :
  - [ ] Trajectoire de migration documentée et déclenchable.
- **Effort** : Élevé

---

## 4. Tableau de bord de priorisation

Reprise du tableau Impact/Effort/Crédibilité/Priorité de l'audit, enrichi du
**sprint cible** et du **point d'ancrage code**.

| Brique | Impact | Effort | Crédib. | Prio | Sprint | Ancrage code |
|---|:--:|:--:|:--:|:--:|:--:|---|
| DG Trésor + Yente | 9/10 | M | 10/10 | **P0** | 1 | `enrichment/yente_client.py` |
| RFC 3161/eIDAS + WORM | 4/10 | F-M | 10/10 | **P0** | 3 | `security/signing.py`, `cases/audit_log.py` |
| Provenance layer | 6/10 | M | 10/10 | **P0** | 1 | `llm/provenance.py` |
| Verification of Payee | 8/10 | M | 8/10 | P1 | 2 | `detectors/verification_of_payee.py` (à créer) |
| VIES + IBAN mod-97 | 7/10 | F | 7/10 | P1 | 0 | `enrichment/vies_client.py`, `detectors/iban_validation.py` (à créer) |
| Monitoring continu | 7/10 | M | 9/10 | P1 | 3 | `scheduler/runner.py` |
| Splink entity resolution | 8/10 | M | 8/10 | P1 | 2 | `detectors/entity_resolution.py` (à créer) |
| Control library exportable | 3/10 | F | 9/10 | P1 | 3 | `app/governance/page.tsx` |
| Evidence pack signé | 5/10 | M | 9/10 | P1 | 3 | `lib/risk/evidence-pack.ts` |
| Contrôles prix / carrousel TVA | 6/10 | M | 6/10 | P2 | 2 | `detectors/vat_carousel.py`, `price_anomaly.py` (à créer) |
| Model cards (AI Act) | 1/10 | F | 8/10 | P2 | Vision | `docs/model-card-risk-engine.md` |
| Connecteurs ERP natifs | 9/10 | É | 7/10 | P2 | Vision | `ingestion/` |
| Migration souveraine OVH/Scaleway | 3/10 | É | 10/10 | P2 | Vision | `deploy/` |

---

## 5. Repères réglementaires (sources primaires)

- **ISA 240** — responsabilités de l'auditeur face à la fraude (test des
  écritures, présomption de risque sur la reconnaissance du revenu, Benford
  comme scoping) ; version révisée effective pour les exercices ouverts à
  compter du **15 décembre 2026**.
- **IPR — Règlement (UE) 2024/886** (Instant Payments / VoP) : adopté le
  13 mars 2024, en vigueur le 8 avril 2024 ; **VoP obligatoire zone euro depuis
  le 9 octobre 2025**.
- **Sapin 2** (art. 17) — dispositif anticorruption.
- **DORA — Règlement (UE) 2022/2554** — registre prestataires TIC (art. 28),
  oversight CTPP.
- **LCB-FT FR** — COSI (D.561-31-1 / R.561-31-2 CMF) ; DS via plateforme
  **ERMES** (arrêté du 23 janvier 2025) ; lignes directrices conjointes
  **ACPR-Tracfin du 23 avril 2025**.
- **AMLD6 — Directive (UE) 2024/1640** ; **AMLR — Règlement (UE) 2024/1624**
  (applicable le 10 juillet 2027 ; ongoing monitoring art. 26).
- **RGPD (UE) 2016/679** ; **AI Act (UE) 2024/1689** (risque limité art. 50) ;
  **eIDAS** (horodatage qualifié).

## 6. Caveats / points d'incertitude

- Les **métriques F1** reposent en partie sur du synthétique + « 6 cas
  confirmés » : à présenter explicitement comme **indicatives**, non comme une
  validation production.
- Le statut **« live »** des connecteurs Sirene/DECP/RBE doit être **vérifié
  écran par écran** avant toute démo à un acheteur sérieux (S0.4).
- **OpenSanctions** : logiciel Yente MIT, mais usage commercial des **données**
  = licence à budgéter.
- L'accès **BE déclaré** (RBE) reste fermé à un RegTech privé non-assujetti
  depuis *Sovim* (CJUE C-37/20, 31 juillet 2024) ; si l'on opère pour un client
  assujetti, l'accès redevient possible via **intérêt légitime** (Directive
  2024/1640 art. 12).
- Classification **AI Act « risque limité » (art. 50)** défendable pour une aide
  à la décision avec validation humaine ; un **blocage automatisé** de paiement
  sans intervention humaine pourrait basculer en « haut risque ».
- **Pappers free** (~100 req/j) ne tient pas un pilote ETI : prévoir une offre
  payante ; **tarifs Pappers / éléments financiers Ellisphere** à reconfirmer
  par devis au moment de l'engagement.

---

*Plan dérivé de l'audit `P2P_Fraud_Detective_FR_audit.md`. Couvre les 9 gaps
G1–G9 + l'evidence pack signé. La décision finale (entrée en relation, DS
Tracfin) reste humaine.*
