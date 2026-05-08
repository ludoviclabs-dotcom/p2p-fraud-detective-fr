"""Page Synthèse — risk score consolidé sur les 6 détecteurs + export Excel/Parquet."""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from p2p_fraud.export.excel_findings import build_workbook
from p2p_fraud.export.parquet_for_powerbi import export_to_parquet
from p2p_fraud.scoring.risk_engine import aggregate_findings, severity_band, to_dataframe
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Synthèse — export",
    surtitle="Investigation",
    kicker=("Risk score consolidé · Excel · Parquet"),
)
st.caption(
    "Combine les Findings produits par tous les détecteurs en un score unique par facture, "
    "via les pondérations de `weights.yaml`."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

df: pd.DataFrame = st.session_state["df_invoices"]

# Collecte les Findings depuis le session_state (peuplé par les pages détecteurs)
findings_keys = (
    "findings_benford",
    "findings_duplicates",
    "findings_thresholds",
    "findings_sirene",
    "findings_iforest",
    "findings_graph",
)
all_findings = []
breakdown_runs = {}
for key in findings_keys:
    f_list = st.session_state.get(key, [])
    breakdown_runs[key] = len(f_list)
    all_findings.extend(f_list)

c1, c2, c3 = st.columns(3)
c1.metric("Findings totaux", f"{len(all_findings):,}")
c2.metric("Détecteurs joués", sum(1 for v in breakdown_runs.values() if v > 0))
c3.metric("Factures analysées", f"{len(df):,}")

with st.expander("ℹ️ Détecteurs exécutés"):
    st.json({k: v for k, v in breakdown_runs.items()})

if not all_findings:
    st.info(
        "Aucun finding disponible. Lancez d'abord les détecteurs (Benford, Doublons, "
        "Sous-seuils, Sirene, Anomalies ML) dans les pages dédiées."
    )
    st.stop()

scores = aggregate_findings(all_findings)
st.session_state["risk_scores"] = scores
df_scores = to_dataframe(scores)

st.subheader("🏆 Top 50 factures à plus haut risque")
top_n = st.slider("N à afficher", min_value=10, max_value=200, value=50, step=10)
df_scores["band"] = df_scores["risk_score"].map(severity_band)
df_top = df_scores.head(top_n)

# Joindre les colonnes utiles de la facture
df_join = df_top.merge(
    df[["invoice_id", "vendor_name", "amount", "invoice_date", "siren"]],
    on="invoice_id",
    how="left",
)
display_cols = [
    "invoice_id",
    "band",
    "risk_score",
    "findings_count",
    "vendor_name",
    "amount",
    "invoice_date",
    "siren",
]
display_cols += [c for c in df_top.columns if c.startswith("score_")]
st.dataframe(df_join[display_cols], use_container_width=True, height=420)

st.subheader("📈 Distribution des scores")
fig = px.histogram(
    df_scores,
    x="risk_score",
    color="band",
    nbins=40,
    title="Risk score 0-100",
    color_discrete_map={
        "CRITIQUE": "#ef4444",
        "ÉLEVÉ": "#f97316",
        "MOYEN": "#eab308",
        "FAIBLE": "#10b981",
    },
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("📥 Export")
ec1, ec2, ec3 = st.columns(3)

with ec1:
    csv_buf = df_join.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 CSV (top N)",
        data=csv_buf,
        file_name="p2p_findings_topN.csv",
        mime="text/csv",
    )

with ec2:
    # Workbook Excel auditeur (Summary + Findings + Invoices + RiskScores)
    wb = build_workbook(invoices=df, findings=all_findings, risk_scores=scores)
    xlsx_buf = io.BytesIO()
    wb.save(xlsx_buf)
    st.download_button(
        "📊 Workbook Excel auditeur",
        data=xlsx_buf.getvalue(),
        file_name="p2p_findings.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="4 onglets : Summary, RiskScores, Findings (avec hyperliens), Invoices",
    )

with ec3:
    # Bundle Parquet pour Power BI
    with (
        tempfile.TemporaryDirectory() as tmp,
        zipfile.ZipFile((zip_buf := io.BytesIO()), "w", zipfile.ZIP_DEFLATED) as zf,
    ):
        tmp_path = Path(tmp)
        export_to_parquet(tmp_path, invoices=df, findings=all_findings, risk_scores=scores)
        for parquet_file in tmp_path.glob("*.parquet"):
            zf.write(parquet_file, arcname=parquet_file.name)
    st.download_button(
        "🪶 Bundle Parquet (Power BI)",
        data=zip_buf.getvalue(),
        file_name="p2p_powerbi_dataset.zip",
        mime="application/zip",
        help="invoices.parquet + findings.parquet + risk_scores.parquet — à connecter dans Power BI Desktop",
    )
