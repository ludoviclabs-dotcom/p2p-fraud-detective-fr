# P2P Fraud Detective FR — Documentation technique

Détection de fraude Procure-to-Pay et monitoring du master data fournisseur,
avec piste d'audit signée. Conçu pour ETI françaises, cabinets d'audit, secteur
public et hospitalier.

## Sommaire

- [Architecture](architecture.md) — schéma global, flux de données, choix
  techniques.
- [Méthodologie d'audit](methodologie-audit.md) — mapping ISA 240, AS 2401,
  Sapin 2, DORA.
- [Benchmark F1](benchmark.md) — métriques reproductibles par détecteur,
  dataset synthétique, performance pipeline.
- **Conformité** — templates pré-remplis :
    - [DPIA (CNIL art. 35)](compliance/dpia_template.md)
    - [Registre AI Act (UE 2024/1689)](compliance/ai_act_register.md)
    - [Registre RGPD (art. 30)](compliance/data_processing_record.md)
- **Architecture Decision Records** — choix structurants et alternatives :
    - [ADR-0001 — Repositionnement produit](decisions/0001-repositionnement-produit.md)
    - [ADR-0002 — Benford rétrogradé](decisions/0002-benford-retrograde.md)
    - [ADR-0003 — Streamlit façade démo, FastAPI prévu en M3](decisions/0003-streamlit-facade-fastapi-future.md)
    - [ADR-0004 — Vectorisation des doublons fuzzy](decisions/0004-doublons-vectorises-rapidfuzz-cdist.md)
    - [ADR-0005 — Release engineering](decisions/0005-release-engineering-semver.md)

## Quickstart

```bash
git clone https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr.git
cd p2p-fraud-detective-fr
make install
make test
streamlit run streamlit_app.py
```

Voir le [README](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr#readme)
pour le détail.

## Modules principaux

| Module | Rôle |
|---|---|
| `src/p2p_fraud/schema.py` | Modèles Pydantic (`Invoice`, `Vendor`, `Finding`, `RiskScore`, `Contribution`, `VendorMasterEvent`) |
| `src/p2p_fraud/ingestion/` | Parser Excel/CSV + presets ERP (SAP, Cegid, Sage X3, Oracle AP) |
| `src/p2p_fraud/detectors/` | Règles : doublons, sous-seuils, master data, sanctions, Sirene, Isolation Forest, graphe |
| `src/p2p_fraud/scoring/` | Risk engine + reason codes FR + explainer (waterfall, perturbation IF) |
| `src/p2p_fraud/cases/` | Case management v0 + audit log immutable (hash-chaîné SHA-256) |
| `src/p2p_fraud/security/` | RBAC (4 rôles, PBKDF2-SHA256) + chiffrement IBAN (Fernet) |
| `src/p2p_fraud/services/` | Cockpit, exposition financière, vue 360° fournisseur |
| `src/p2p_fraud/synthetic/` | Générateur dataset étiqueté reproductible |

## Reproductibilité

```bash
make bench       # perf end-to-end
make bench-f1    # F1 par détecteur
make dataset-50k # dataset synthétique
make docs        # build de cette documentation
```
