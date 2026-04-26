# Architecture

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit multipage                          │
│  Upload → Benford → Doublons → Seuils → Sirene → IForest →      │
│  Anneaux → Synthèse / Export → Méthodologie                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      src/p2p_fraud/                              │
│                                                                   │
│   ingestion/  ──►  detectors/  ──►  scoring/  ──►  export/       │
│                       │                                           │
│                       ▼                                           │
│                 enrichment/  (Sirene v3, DECP DuckDB)            │
│                                                                   │
│   synthetic/  ── génère datasets étiquetés pour démo + tests     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │   schema.py (Pydantic)  │
                │   Invoice / Vendor /    │
                │   Finding / RiskScore   │
                └─────────────────────────┘
```

## Flux de données

1. **Upload** (Excel/CSV) → `ingestion.parsers.load_invoices()` → DataFrame canonique validé Pydantic
2. **Détecteurs** (parallèles) consomment ce DataFrame, produisent chacun une liste de `Finding`
3. **Enrichissement Sirene/DECP** ajoute `Finding` complémentaires (ex. SIREN inexistant)
4. **Risk engine** agrège tous les `Finding` par `invoice_id` → `RiskScore` 0-100
5. **Export** : `.xlsx` (auditeur) + `.parquet` (Power BI dashboard)

## Pourquoi pas de FastAPI séparé

- Streamlit Cloud comme cible recommandée par le brief portfolio
- Tout le code métier vit dans `src/p2p_fraud/`, importable par n'importe quelle façade ultérieure
- Une réécriture en service web serait un wrap autour du même package — pas une refonte

## Choix techniques structurants

| Décision | Raison |
|---|---|
| Pydantic v2 pour Invoice/Finding | Validation au boundary, contrats explicites, sérialisation JSON gratuite |
| pandas DataFrame côté détecteurs | Performance vectorisée, écosystème mature |
| `is_fraud` + `fraud_type` ground truth dans le générateur | Permet F1 par détecteur — argument CV différenciant |
| DuckDB pour DECP | Analytique OLAP locale, pas de serveur, lit Parquet natif |
| `requests-cache` SQLite pour Sirene | Respect quota 30 req/s + démo offline reproductible |
| Streamlit multipage (`pages/`) | 1 fichier = 1 vue, navigation auto, pas de routing à gérer |
| Persistence via `st.session_state` | Évite les recalculs lourds entre pages |

## Réutilisabilité par les projets ultérieurs

- `enrichment/sirene_client.py` → projet 4 (Sapin 2 due diligence) et 5 (DORA registre TIC)
- `scoring/risk_engine.py` → projet 4 (cartographie risques)
- `synthetic/generator.py` → projet 3 (JET) et 7 (SoD process mining)
- Pattern `detectors/ + Streamlit pages` → projets 3 et 7

L'investissement architectural de ce projet 2 sera amorti sur 4 projets futurs du portfolio.
