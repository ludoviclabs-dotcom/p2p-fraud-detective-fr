# Comparatif SOTA — P2P Fraud Detective FR vs solutions du marché

> Tableau fonctionnel comparatif (mai 2026). Sources : sites éditeurs officiels, plaquettes commerciales publiques, retours utilisateurs anonymisés (G2, Capterra, podcasts AML).
> **Aucun lien commercial avec les éditeurs cités**. Comparatif strictement déclaratif à visée pédagogique.

## Positionnement

| Solution | Cible | Pricing indicatif | Modèle |
|---|---|---|---|
| **P2P Fraud Detective FR** | ETI 500 M€ - 2 Md€ + cabinets audit + secteur public | Open source MIT (déploiement support payant) | Self-hosted / SaaS / Cloud |
| **MindBridge AI Auditor** | Cabinets BIG4 + ETI | 30k - 150k €/an | SaaS |
| **PwC Halo** | Clients Audit PwC exclusifs | Inclus dans la mission PwC | SaaS interne |
| **KPMG Clara** | Clients Audit KPMG exclusifs | Inclus dans la mission KPMG | SaaS interne |
| **Deloitte Argus** | Clients Audit Deloitte exclusifs | Inclus dans la mission Deloitte | SaaS interne |
| **Forvis Mazars FraudSense** | Cabinets mid-tier + ETI | 15k - 60k €/an | SaaS |
| **SAS Anti-Money Laundering** | Banques + assurances | 200k+ €/an | On-premise / Cloud |
| **NICE Actimize IFM-X** | Banques tier 1 | 500k+ €/an | On-premise |
| **Quantexa** | Banques + ETI | 100k - 300k €/an | Cloud |

## Comparatif fonctionnel détaillé

### Détecteurs statistiques

| Critère | P2P FD FR | MindBridge | PwC Halo | KPMG Clara | Deloitte Argus | Forvis FraudSense | SAS AML | NICE Actimize | Quantexa |
|---|---|---|---|---|---|---|---|---|---|
| Loi de Benford | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Doublons fuzzy | ✅ RapidFuzz | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Fractionnement sous-seuils | ✅ COSI calibré | ⚠️ générique | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| Anomalies Isolation Forest | ✅ scikit-learn | ✅ propriétaire | ✅ | ✅ | ✅ | ⚠️ | ✅ XGBoost | ✅ | ✅ deep |
| Anneaux de fraude (graphe) | ✅ NetworkX | ⚠️ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ | ✅ entity resolution |
| Détecteur BEC (master data) | ✅ 4-eyes + corrélation | ❌ | ⚠️ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Score composite + waterfall | ✅ YAML éditable live | ⚠️ figé | ⚠️ figé | ⚠️ figé | ⚠️ figé | ⚠️ | ⚠️ | ✅ | ✅ |
| Explicabilité SHAP | ✅ | ⚠️ propriétaire | ❌ | ❌ | ⚠️ | ❌ | ✅ | ✅ | ✅ |

### Enrichissement réglementaire

| Critère | P2P FD FR | MindBridge | PwC Halo | KPMG Clara | Deloitte Argus | Forvis | SAS | NICE | Quantexa |
|---|---|---|---|---|---|---|---|---|---|
| Sirene (INSEE) v3 | ✅ live + cache | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ | ⚠️ |
| DECP marchés publics | ✅ live ODbL | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| RBE INPI (BO) | ✅ via Pappers | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ | ✅ | ✅ | ✅ |
| Sanctions UE + OFAC | ✅ via OpenSanctions | ✅ snapshot | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PEP open-source | ✅ OpenSanctions | ⚠️ propriétaire | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ Dow Jones | ✅ Refinitiv | ⚠️ |
| Mode démo offline | ✅ par défaut | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Conformité française

| Critère | P2P FD FR | MindBridge | PwC Halo | KPMG Clara | Deloitte Argus | Forvis | SAS | NICE | Quantexa |
|---|---|---|---|---|---|---|---|---|---|
| Audit trail SHA-256 chaîné | ✅ (P3) | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| RGPD art. 17 (purge user) | ✅ (P4-5) | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| Articles CMF référencés inline | ✅ (L. 561-x) | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ |
| AMLR / AMLD6 mapping | ✅ doc | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Format COSI (D. 561-31-1 CMF) | ✅ seuils calibrés | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ⚠️ | ⚠️ |
| Déclaration de soupçon stylisée | 🟡 v0.6 | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |

### Architecture et intégration

| Critère | P2P FD FR | MindBridge | PwC Halo | KPMG Clara | Deloitte Argus | Forvis | SAS | NICE | Quantexa |
|---|---|---|---|---|---|---|---|---|---|
| Self-hosted possible | ✅ Docker | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ⚠️ |
| API REST OpenAPI publique | ✅ (P3-3) | ⚠️ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ |
| Webhook sortant SIEM | 🟡 v0.5 (P5-3) | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| SDK Python / TypeScript | 🟡 v0.5 (P5-3) | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ Java | ✅ | ✅ |
| OIDC fédéré (Entra/Auth0/Keycloak) | ✅ (P4-3) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Open source (code auditable) | ✅ MIT | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Démo & onboarding

| Critère | P2P FD FR | MindBridge | PwC Halo | KPMG Clara | Deloitte Argus | Forvis | SAS | NICE | Quantexa |
|---|---|---|---|---|---|---|---|---|---|
| Démo publique cliquable | ✅ Streamlit Cloud | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 5 scénarios pré-chargés | ✅ (P5-2) | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ |
| Code source consultable | ✅ GitHub | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Délai démo régalienne | < 1 jour | 2-3 sem. | sur mission | sur mission | sur mission | 1 sem. | 3-4 sem. | 4+ sem. | 2-3 sem. |

## Synthèse positionnement

| Dimension | P2P FD FR vs concurrence |
|---|---|
| **Coût** | 1 à 2 ordres de grandeur moins cher (MIT, self-hosted) |
| **Calibration FR-native** | Le seul outil avec seuils COSI calibrés, refs CMF inline, DECP live |
| **Démo accessible** | Le seul outil avec démo publique cliquable + 5 scénarios pré-chargés |
| **Open source** | Le seul outil dont le code est auditable (avantage AMF / ACPR / Cour des comptes) |
| **Maturité industrielle** | Moins mature que SAS / NICE Actimize / Quantexa pour banques tier 1 |
| **Volume** | Calibré ETI (< 500 k factures/an). Au-delà : Polars + AGE en roadmap |
| **Workflow case management** | Moins riche que Quantexa entity resolution + investigation workspace |

## Cible de pertinence

P2P Fraud Detective FR est **le bon outil pour** :

- ✅ **ETI 500 M€ - 2 Md€** avec 3 à 10 auditeurs internes (cibles : agroalimentaire, foncière, retail, industrie)
- ✅ **Cabinets d'audit mid-tier** (PME francophone) en complément ou alternative à MindBridge
- ✅ **Secteur public** : DGFiP audits internes, IGF, Cour des comptes, CRC régionales (cohérence open source obligatoire)
- ✅ **CAC commissaires aux comptes** missions Sapin 2 + LCB-FT chez des clients ETI
- ✅ **Formation continue** : universités, écoles d'audit (ESCP, IAE, Sciences Po Public Affairs)

P2P Fraud Detective FR n'est **pas le bon outil pour** :

- ❌ **Banques tier 1** (BNP Paribas, Crédit Agricole) : volume + criticité → SAS AML ou NICE Actimize
- ❌ **CASPs crypto** > 100 k transactions/jour : besoin GNN + Polars + GPU
- ❌ **Assureurs vie** avec besoin lourd de matching client : Quantexa entity resolution
- ❌ **Multinationales** avec besoin multi-juridictions complet : SAS / NICE Actimize

## Légende

- ✅ : fonctionnalité présente et mature
- 🟡 : fonctionnalité en cours de développement (roadmap publique 2026)
- ⚠️ : fonctionnalité partielle, propriétaire, ou non documentée publiquement
- ❌ : fonctionnalité absente

## Disclaimer

Ce comparatif est établi à partir de sources publiques (sites éditeurs, plaquettes commerciales, retours utilisateurs G2/Capterra, podcasts AML français). Les éditeurs cités peuvent avoir fait évoluer leurs produits depuis mai 2026. Les zones grisées (`⚠️`) signalent un manque d'information publique vérifiable au moment de la rédaction. Le présent document n'a aucun caractère commercial ni promotionnel. Toute correction ou mise à jour est bienvenue via PR GitHub.

**Sources principales** :
- MindBridge : mindbridge.ai/products
- PwC Halo : pwc.com/halo-financial-services
- KPMG Clara : kpmg.com/clara
- Deloitte Argus : deloitte.com/argus-financial-statement-fraud
- Forvis Mazars : forvismazars.com/services/fraudsense
- SAS AML : sas.com/en_us/software/anti-money-laundering.html
- NICE Actimize : niceactimize.com/financial-crime-risk-management
- Quantexa : quantexa.com/financial-crime
