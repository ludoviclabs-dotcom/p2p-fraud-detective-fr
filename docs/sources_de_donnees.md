# Sources de données — référentiel public

> **PR P5-1** — adapters live DECP / Pappers / OpenSanctions Yente.
> Document mis à jour mai 2026.

## Vue d'ensemble

P2P Fraud Detective FR fonctionne en **deux modes** sélectionnables par variable d'environnement `ENRICHMENT_MODE` :

| Mode | Comportement | Usage typique |
|---|---|---|
| `demo` (défaut) | Adapters synthétiques embarqués, aucun appel réseau | Streamlit Cloud public, tests, démos offline |
| `live` | Appels HTTP réels aux sources ouvertes, cache `requests-cache` 24 h - 7 j | Pilote ETI, démos régaliennes, audit DGFiP |

**Fallback graceful** : en mode live, tout échec réseau (timeout, 5xx, JSON malformé) est intercepté par le client correspondant qui retombe transparently sur le snapshot démo embarqué. **Aucune exception** n'est remontée à l'UI Streamlit ni à l'API REST. Un `log.warning` structuré est émis pour diagnostic.

## Activation du mode live

```bash
# Mode live complet (sans Pappers — RBE en démo)
export ENRICHMENT_MODE=live

# Mode live avec RBE Pappers
export ENRICHMENT_MODE=live
export PAPPERS_API_KEY=pk_live_xxxxxxxxxxxxxxxxxxxxxxxx

# Yente self-hosted (recommandé en pilote prod)
export YENTE_BASE_URL=https://yente.votre-domaine.fr
```

Tous les paramètres ont des valeurs par défaut dans `Settings` (`src/p2p_fraud/config.py`).

## Sources couvertes par les adapters live

### 1. DECP — Données Essentielles de la Commande Publique

| Item | Détail |
|---|---|
| **URL adapter** | `src/p2p_fraud/enrichment/decp_live.py` |
| **Endpoint** | `https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/decp-v3/records` |
| **Producteur** | DAJ (Direction des Affaires Juridiques) / DINUM |
| **Licence** | ODbL (Open Database License) 1.0 |
| **Volumétrie** | ≈ 5 millions de contrats, mise à jour quotidienne |
| **Authentification** | Aucune (API publique) |
| **Quotas** | Pas de quota officiel, rate-limit raisonnable côté OpenDataSoft |
| **Cache local** | `requests-cache` SQLite, TTL **7 jours** |
| **Variable env** | `DECP_LIVE_BASE_URL` (défaut : `https://data.economie.gouv.fr/api/explore/v2.1`) |
| **Méthodes** | `lookup_by_siren(siren)`, `lookup_by_name(name)` |

**Format de retour** : `list[DECPContract]` (dataclass interne avec `siret_titulaire`, `nom_titulaire`, `acheteur`, `montant_eur`, `date_notification`, `objet`).

**Pertinence métier** : croisement fournisseurs ETI × marchés publics → détection conflit d'intérêts Sapin 2 art. 17 (un fournisseur P2P privé qui est aussi attributaire d'un marché auprès de l'acheteur audité).

### 2. Pappers — Bénéficiaires effectifs (RBE)

| Item | Détail |
|---|---|
| **URL adapter** | `src/p2p_fraud/enrichment/pappers_live.py` |
| **Endpoint** | `https://api.pappers.fr/v2/entreprise?siren=...&api_token=...` |
| **Producteur** | Pappers (agrégateur officiel RNE/Sirene/INPI) |
| **Licence** | Commerciale, free tier limité |
| **Authentification** | Clé API (`PAPPERS_API_KEY`) — sinon adapter désactivé (fallback démo) |
| **Source amont** | RNE (Registre National des Entreprises) — Sirene + INPI RBE consolidés depuis 2023 |
| **Cache local** | `requests-cache` SQLite, TTL **7 jours** |
| **Variable env** | `PAPPERS_BASE_URL` (défaut : `https://api.pappers.fr/v2`), `PAPPERS_API_KEY` |
| **Méthodes** | `lookup_by_siren(siren)` |

**Format de retour** : `list[BeneficialOwner]` (dataclass interne avec `owner_first_name`, `owner_last_name`, `ownership_pct`, `nationality`, `is_pep`).

**Pertinence métier** : due diligence tiers Sapin 2 art. 17 + AMLD6 art. 30 → identification BO ≥ 25 % + détection PEP bénéficiaires + structures opaques.

**Alternative gratuite** : `data.inpi.fr/rne/rbe` (Etalab) — non implémenté en V5 (parsing XML moins stable, pas de free tier en lookup unitaire). Reporté à V6 si demande pilote.

### 3. OpenSanctions Yente — sanctions consolidées + PEP

| Item | Détail |
|---|---|
| **URL adapter** | `src/p2p_fraud/enrichment/yente_client.py` |
| **Endpoint** | `https://api.opensanctions.org/match/sanctions` (POST) |
| **Producteur** | OpenSanctions Foundation (Berlin) |
| **Licence** | CC-BY 4.0 |
| **Couverture** | ~ 250 listes officielles : UE consolidée, OFAC SDN, ONU, Trésor FR, ACPR FR, listes nationales 60+ pays + bases PEP |
| **Authentification** | Aucune sur le tier public (rate-limité), Pro avec clé |
| **Self-host** | `ghcr.io/opensanctions/yente` (recommandé en pilote prod) |
| **Cache local** | `requests-cache` SQLite, TTL **24 heures** |
| **Variable env** | `YENTE_BASE_URL` (défaut : `https://api.opensanctions.org`) |
| **Méthodes** | `match_entity(name)`, `match_person(name)` |

**Format de retour** : `list[SanctionMatch]` (dataclass interne avec `entity_id`, `name`, `kind`, `country`, `list_source` enum {`OFAC_SDN`, `EU_CONSOLIDATED`, `FR_TRESOR`, `PEP_EU`, ...}, `listed_at`, `reason`, `score` 0-100).

**Pertinence métier** : LCB-FT (AMLR + AMLD6) + obligations Tracfin sur déclaration de soupçon + screening fournisseurs avant règlement.

## Limites de couverture et biais identifiés

- **Délai de propagation Sirene** : 0-48 h. Une radiation très récente peut ne pas être reflétée → critère secondaire, jamais bloquant.
- **PEP open-source** : couverture des élus locaux français (maires, conseillers) estimée à 60-70 % seulement. Compléter par sources internes pour due diligence approfondie.
- **OFAC SDN** : pertinent pour entités américaines / dollar. Pour une ETI 100 % française, EU consolidée + Trésor FR sont plus discriminants.
- **DECP** : seuils minimaux légaux (25 k€ TTC pour les marchés, 90 k€ pour DSP) — les très petits marchés ne sont pas couverts.
- **Pappers** : free tier limité (~ 100 requêtes/jour). Pour un pilote ETI avec 10 000 fournisseurs uniques, prévoir un plan payant ou self-host RNE.

## Patterns d'utilisation

### Démo Streamlit Cloud publique

```bash
# .streamlit/secrets.toml ou env Streamlit Cloud
# (laisser ENRICHMENT_MODE non défini → mode demo par défaut)
```

Tous les enrichissements sont synthétiques. Aucune requête réseau sortante. Démo 100 % offline, reproductible, gratuite.

### Démo régalienne / pilote ETI

```bash
export ENRICHMENT_MODE=live
export PAPPERS_API_KEY=pk_live_xxx  # optionnel mais recommandé
export YENTE_BASE_URL=https://yente.votre-organisation.fr  # self-host
```

Les findings produits référencent des contrats / BO / sanctions **réels**. Le bandeau « 🟢 Mode LIVE actif » s'affiche sur les pages 12 (Méthodologie) et 17 (DECP_RBE).

### Tests CI

Les tests sont **toujours** en mode démo (jamais d'appel réseau réel en CI). Les adapters live sont testés via mocks `responses` (cf. `tests/test_enrichment_live.py` — 15 tests).

## Conformité juridique

- **RGPD** : aucune donnée personnelle persistée. Les seuls champs sensibles (BO, PEP) sont stockés en mémoire pour la durée de la session uniquement.
- **ODbL DECP** : attribution requise — la page Méthodologie cite explicitement `data.economie.gouv.fr` comme source.
- **CC-BY 4.0 OpenSanctions** : attribution requise — citée dans Méthodologie et footer.
- **Pappers ToS** : usage commercial autorisé sous réserve du plan tarifaire. Pas de stockage de masse, pas de revente.
- **Article 19 Loi Lemaire (2016)** : toutes les sources retenues sont des données publiques au sens du CRPA art. L. 312-1.

## Architecture de fallback

```
UI Streamlit / API REST
        ↓
DECPClient.lookup_by_siren("123456789")
        ↓
   ┌────┴────┐
   ▼         ▼
live_client (mode=live)   demo (_DEMO_VENDORS)
        ↓
   try:
     DECPLiveClient.lookup_by_siren(...)
     → return results (empty list possible)
   except DECPLiveError, Exception:
     log.warning("DECP live failed: ...")
     → fallback to _contracts (demo)
```

Cette architecture garantit que **la démo publique Streamlit Cloud ne casse jamais**, même si toutes les APIs externes tombent simultanément. La page reste fonctionnelle, seuls les warnings dans les logs signalent la dégradation.

## Roadmap

- **v0.5.0 (P5-1, actuel)** : adapters DECP + Pappers + Yente, fallback graceful
- **v0.6 (futur)** : adapter INPI RBE direct (gratuit, fallback Pappers)
- **v0.6 (futur)** : adapter `pansionsmap.eu` officiel UE (consolidation directe sans Yente)
- **v0.7 (futur)** : webhook live DECP → ingestion incrémentale quotidienne en base
- **v1.0 (production)** : abonnement ERMES / Tracfin (réservé aux personnes assujetties L. 561-2 CMF)
