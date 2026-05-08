# P2P Fraud Detective FR

> **Vendor & Payment Integrity FR-native** — détection de fraude Procure-to-Pay, monitoring du master data fournisseur, et piste d'audit signée pour ETI, cabinets d'audit et secteur public/hospitalier.

🇫🇷 **FR** · [🇬🇧 EN below](#english)

---

## Pourquoi cet outil

80 % de la fraude P2P passe par un changement d'IBAN ou un fournisseur fictif — pas par une anomalie statistique exotique. Cet outil regarde ce que personne ne regarde côté français : **l'historique du master data fournisseur**, croisé avec les sources publiques (Sirene, DECP, RBE, listes de sanctions) et une **piste d'audit que votre CAC peut signer**.

**Cibles** : ETI 200 M€ – 2 Md€ CA, cabinets d'audit mid-tier, hôpitaux / universités / établissements publics.

**Promesse** : détecter et documenter, en moins de 24 heures, 100 % des changements de coordonnées bancaires fournisseurs à risque, avec preuve auditable signée — sans envoyer une seule donnée hors de votre SI.

## Ce qu'il fait

À partir d'un export Excel/CSV de factures fournisseurs (champs `LFA1`/`RBKP` style SAP : SIREN, fournisseur, IBAN, montant, date, PO) + optionnellement l'historique des modifications master data, l'outil exécute en cascade :

| # | Détecteur | Méthode | Référentiel |
|---|---|---|---|
| 1 | **Master data history** | Diff IBAN / nom / SIREN / adresse / dormant + 4-eyes | AFP 2026, ISA 240 |
| 2 | **Doublons fuzzy** | Bucket montant ± 0,01 € + date ± 2 j + RapidFuzz nom | AICPA Audit Data Standards |
| 3 | **Sous seuils** | Détection fenêtre `[seuil − ε, seuil[` paramétrable | Contrôle interne, séparation des tâches |
| 4 | **Cross-check Sirene** | API Sirene v3, statut, date création, code APE | INSEE — référentiel officiel |
| 5 | **Sanctions / PEP** | OpenSanctions / Trésor FR / OFAC, matching RapidFuzz | LCB-FT, Sapin 2 art. 17 |
| 6 | **Isolation Forest** | Pipeline scikit-learn sur features comportementales | ML anomaly detection |
| 7 | **Anneaux de fraude** | Graphe NetworkX `(employees ⟷ vendors)` | Forensic accounting |
| 8 | **Risk score consolidé** | Combinaison pondérée (YAML éditable) + reason codes FR | Continuous auditing |
| ⓘ | *Benford (scoping)* | F1D / F2D / LD chi² + MAD — orientation d'échantillonnage | ISA 240 (outil ancillaire) |

**Sortie** : tableau de findings classés par risk score, exportable en `.xlsx` avec hyperliens, et fichier Parquet alimentant un dashboard **Power BI** (`powerbi/p2p-fraud-dashboard.pbix`).

## Démo en ligne

🚀 **[Lien Streamlit Cloud — à venir]**

📽️ **[Vidéo Loom 5 min — à venir]** ([script](docs/demo-script.md))

## Performance mesurée (ground truth synthétique 10k factures)

| Détecteur | Recall | Précision | F1 |
|---|---|---|---|
| Doublons (exact + fuzzy) | **1.000** | 0.30 | 0.47 |
| Sous-seuils | **1.000** | 0.46 | 0.63 |
| Anneaux IBAN (graph NetworkX) | **1.000** | élevée | élevé |
| Isolation Forest (sur outliers étiquetés) | 0.62 | — | — |

Reproductible : `pytest -s tests/`. Voir [docs/methodologie-audit.md](docs/methodologie-audit.md)
pour le mapping ISA 240 / AS 2401 / Sapin 2 / DORA.

## Quickstart

```bash
git clone https://github.com/ludoviclabeaut/p2p-fraud-detective-fr.git
cd p2p-fraud-detective-fr

python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env                # Renseigner SIRENE_API_TOKEN

# Générer un dataset synthétique de 50 000 factures avec fraudes étiquetées
python -m p2p_fraud.synthetic.generator --output data/synthetic/dataset_50k.csv --rows 50000

# Lancer l'application
streamlit run streamlit_app.py
```

## Tests et qualité

```bash
pytest -q --cov=src/p2p_fraud
ruff check .
ruff format --check .
```

Tests F1 par détecteur sur ground truth synthétique : objectif ≥ 0,85 pour les détecteurs déterministes, ≥ 0,7 pour Isolation Forest.

## Architecture

```
src/p2p_fraud/
├── schema.py          # Pydantic : Invoice, Vendor, Finding, VendorMasterEvent
├── ingestion/         # Parser Excel/CSV + mapping LFA1/RBKP/BSEG
├── detectors/         # Doublons, seuils, IForest, graphe, master_data_changes, sanctions, benford (scoping)
├── enrichment/        # Sirene v3, DECP DuckDB, sanctions client
├── scoring/           # Risk engine + weights.yaml
├── synthetic/         # Générateur dataset étiqueté (factures + master data events)
├── cases/             # Case management v0 + audit log immutable chaîné par hash
└── export/            # Excel hyperliens + Parquet pour Power BI
```

Voir [`docs/architecture.md`](docs/architecture.md) pour le détail.

## Mapping référentiels d'audit

- **ISA 240** — fraude dans l'audit des comptes : tests JET (journal entry testing), Benford
- **AS 2401** (PCAOB) — équivalent US, applicable à l'audit légal SEC
- **Sapin 2** — cartographie corruption (réutilise le risk engine, voir projet 4 du portfolio)
- **DORA** — registre prestataires TIC (réutilise sirene_client, voir projet 5)

Voir [`docs/methodologie-audit.md`](docs/methodologie-audit.md).

---

## English

> **Vendor & Payment Integrity, FR-native** — P2P fraud detection, vendor master data monitoring, and signed audit trail for mid-market companies, audit firms, and the public/healthcare sector.

### What it does

Ingest Excel/CSV vendor invoice exports (SAP-style `LFA1`/`RBKP` fields) plus optional master data change history, then run a layered pipeline: **master data history (IBAN/name/address swaps, dormant reactivation, 4-eyes breach)**, **fuzzy duplicates**, **just-under-threshold detection**, **Sirene v3 cross-check**, **OpenSanctions / PEP**, **Isolation Forest**, **NetworkX fraud rings**, **consolidated risk score with French reason codes**. Benford remains available as a *scoping* tool. Output: ranked findings as `.xlsx` with hyperlinks, a Parquet feed for the bundled Power BI dashboard, and an immutable hash-chained audit log.

### Quickstart

```bash
git clone https://github.com/ludoviclabeaut/p2p-fraud-detective-fr.git
cd p2p-fraud-detective-fr
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Fill in SIRENE_API_TOKEN
python -m p2p_fraud.synthetic.generator --rows 50000 --output data/synthetic/dataset_50k.csv
streamlit run streamlit_app.py
```

## License

MIT — see [LICENSE](LICENSE).
