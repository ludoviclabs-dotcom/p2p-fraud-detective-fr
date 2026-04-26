"""Page Synthèse — risk score consolidé sur les 6 détecteurs + export Excel/Parquet."""

from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from p2p_fraud.scoring.risk_engine import aggregate_findings, severity_band, to_dataframe

st.set_page_config(page_title="Synthèse — P2P Fraud Detective", page_icon="📊", layout="wide")
st.title("📊 Synthèse consolidée — risk score 0-100")
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
    template="plotly_dark",
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
ec1, ec2 = st.columns(2)

with ec1:
    csv_buf = df_join.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 CSV (top N)",
        data=csv_buf,
        file_name="p2p_findings_topN.csv",
        mime="text/csv",
    )

with ec2:
    parquet_buf = io.BytesIO()
    df_scores.to_parquet(parquet_buf, index=False)
    st.download_button(
        "🪶 Parquet (tous les scores — pour Power BI)",
        data=parquet_buf.getvalue(),
        file_name="p2p_risk_scores.parquet",
        mime="application/octet-stream",
    )
