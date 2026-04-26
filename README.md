# P2P Fraud Detective FR

> Mini-MindBridge open-source pour les ETI françaises — détection de fraude Procure-to-Pay sur exports comptables (factures fournisseurs), exploitant les sources publiques **Sirene v3** et **DECP** que les outils anglo-saxons (DataSnipper, MindBridge, Trustpair, Tipalti) ignorent.

🇫🇷 **FR** · [🇬🇧 EN below](#english)

---

## Pourquoi cet outil

La fraude P2P (factures fictives, doublons, fournisseurs fantômes, détournement d'IBAN, montants juste sous seuil de validation) reste le scénario le plus coûteux en contrôle interne. Les outils du marché (DataSnipper, MindBridge, Trustpair) sont chers et anglo-saxons ; aucun n'exploite nativement les sources publiques françaises (Sirene, DECP, Annuaire des entreprises).

Cet outil comble le manque pour **auditeurs internes, RCSI, contrôleurs de gestion et CAC** d'ETI françaises.

## Ce qu'il fait

À partir d'un export Excel/CSV de factures fournisseurs (champs `LFA1`/`RBKP` style SAP : SIREN, fournisseur, IBAN, montant, date, PO), l'outil exécute en cascade :

| # | Détecteur | Méthode | Référentiel |
|---|---|---|---|
| 1 | **Loi de Benford** | 1er chiffre, 2 premiers, dernier. Chi² + MAD (Nigrini) | ISA 240 — fraude écritures comptables |
| 2 | **Doublons fuzzy** | Bucket montant ± 0,01 € + date ± 2 j + RapidFuzz nom | AICPA Audit Data Standards |
| 3 | **Sous seuils** | Détection fenêtre `[seuil − ε, seuil[` paramétrable | Contrôle interne, séparation des tâches |
| 4 | **Cross-check Sirene** | API Sirene v3, statut, date création, code APE | INSEE — référentiel officiel |
| 5 | **Isolation Forest** | Pipeline scikit-learn sur features comportementales | ML anomaly detection |
| 6 | **Anneaux de fraude** | Graphe NetworkX `(employees ⟷ vendors)` | Forensic accounting |
| 7 | **Risk score consolidé** | Combinaison pondérée (YAML éditable) | Continuous auditing |

**Sortie** : tableau de findings classés par risk score, exportable en `.xlsx` avec hyperliens, et fichier Parquet alimentant un dashboard **Power BI** (`powerbi/p2p-fraud-dashboard.pbix`).

## Démo en ligne

🚀 **[Lien Streamlit Cloud — à venir]**

📽️ **[Vidéo Loom 5 min — à venir]**

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
├── schema.py          # Pydantic : Invoice, Vendor, Finding
├── ingestion/         # Parser Excel/CSV + mapping LFA1/RBKP/BSEG
├── detectors/         # Benford, doublons, seuils, IForest, graphe
├── enrichment/        # Sirene v3, DECP DuckDB
├── scoring/           # Risk engine + weights.yaml
├── synthetic/         # Générateur dataset étiqueté
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

> Open-source mini-MindBridge for French SMEs — Procure-to-Pay fraud detection on accounting exports, leveraging public **Sirene v3** and **DECP** sources that Anglo-Saxon tools (DataSnipper, MindBridge, Trustpair) overlook.

### What it does

Ingest Excel/CSV vendor invoice exports (SAP-style `LFA1`/`RBKP` fields), then run a 7-stage cascade: **Benford's law**, **fuzzy duplicates**, **just-under-threshold detection**, **Sirene v3 cross-check**, **Isolation Forest**, **NetworkX fraud rings**, **consolidated risk score**. Output: ranked findings as `.xlsx` with hyperlinks and a Parquet feed for the bundled Power BI dashboard.

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
