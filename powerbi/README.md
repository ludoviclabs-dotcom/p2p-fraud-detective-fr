# Dashboard Power BI — P2P Fraud Detective FR

Le `.pbix` cible 5 pages connectées au bundle Parquet exporté par l'application
(`p2p_powerbi_dataset.zip` téléchargeable depuis la page Streamlit Synthèse).

## Sources de données attendues

Décompresser le bundle dans un dossier local puis dans Power BI Desktop :
**Accueil → Obtenir les données → Parquet** sur chacun des 3 fichiers.

| Fichier | Table cible | Clé |
|---|---|---|
| `invoices.parquet` | `Invoices` | `invoice_id` |
| `findings.parquet` | `Findings` (long) | `invoice_id`, `detector`, `signal` |
| `risk_scores.parquet` | `RiskScores` | `invoice_id` |

### Relations à créer dans le modèle

- `Invoices[invoice_id]` ↔ `RiskScores[invoice_id]` (1:1, bidirectionnelle filtrée)
- `Invoices[invoice_id]` ↔ `Findings[invoice_id]` (1:N)

## Mesures DAX recommandées

```dax
Total Factures = COUNTROWS(Invoices)
Factures Flaggées = DISTINCTCOUNT(Findings[invoice_id])
% Flaggées = DIVIDE([Factures Flaggées], [Total Factures])
Exposition € = CALCULATE(
    SUM(Invoices[amount]),
    Invoices[invoice_id] IN VALUES(Findings[invoice_id])
)
Score Risque Max = MAX(RiskScores[risk_score])
Score Risque Médian = MEDIAN(RiskScores[risk_score])
Bande Risque =
    SWITCH(TRUE(),
        RiskScores[risk_score] >= 80, "CRITIQUE",
        RiskScores[risk_score] >= 50, "ÉLEVÉ",
        RiskScores[risk_score] >= 25, "MOYEN",
        RiskScores[risk_score] > 0, "FAIBLE",
        "AUCUN"
    )
```

## Pages cibles

### 1. Overview
- Cartes KPI : Total Factures, % Flaggées, Exposition €, Score Risque Max, Médian.
- Histogramme `risk_score` par bande.
- Top 20 fournisseurs par exposition.

### 2. Benford
- Courbe observée vs attendue (1er chiffre, 2 premiers chiffres).
- Calcul DAX du MAD par sous-segment (à partir de `Findings` filtrés `detector=benford`).

### 3. Top fournisseurs à risque
- Tableau matriciel : vendor_name, n_findings, somme `risk_score`, exposition €.
- Filtres : bande, détecteur, période.

### 4. Heatmap utilisateurs × jours
- Matrice `user_id` (rows) × `weekday(invoice_date)` (cols).
- Valeur = count factures, mise en forme conditionnelle.

### 5. Graphe anneaux
- Visualiser les `Findings[detector="graph"]` avec `evidence_json` parsé.
- Power BI ne supporte pas nativement les graphes ; utiliser l'extension visuelle
  **« Network Navigator »** ou une capture du sous-graphe Streamlit (page 7).

## Création initiale

Le `.pbix` n'est pas versionné dans le repo (binaire). Pour le créer :

1. Ouvrir Power BI Desktop (Windows).
2. Importer les 3 Parquet via **Obtenir les données**.
3. Créer les relations.
4. Coller les mesures DAX ci-dessus.
5. Construire les 5 pages.
6. Sauvegarder en `powerbi/p2p-fraud-dashboard.pbix`.
7. Optionnel : publier sur Power BI Service pour démo en ligne.

## Rafraîchissement

Quand l'application Streamlit produit un nouveau bundle :
1. Décompresser dans le même dossier (écrase les `.parquet` précédents).
2. Power BI Desktop → **Accueil → Actualiser**.
3. Toutes les visualisations se mettent à jour automatiquement (le schéma est stable).
