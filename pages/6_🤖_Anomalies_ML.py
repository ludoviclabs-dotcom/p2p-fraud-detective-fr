"""Page Isolation Forest — anomalies ML sur features comportementales."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from p2p_fraud.detectors.isolation_forest import detect_anomalies

st.set_page_config(page_title="Anomalies ML — P2P Fraud Detective", page_icon="🤖", layout="wide")
st.title("🤖 Isolation Forest — anomalies ML")
st.caption(
    "Pipeline scikit-learn (StandardScaler → IsolationForest) sur features "
    "comportementales : log_amount, weekday, ratio vendor avg, écart depuis "
    "facture précédente, charge user/jour, présence PO."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

df: pd.DataFrame = st.session_state["df_invoices"]

c1, c2 = st.columns(2)
with c1:
    contamination = st.slider(
        "Contamination attendue (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5
    )
with c2:
    st.metric("Factures à scorer", f"{len(df):,}")

if st.button("🔍 Entraîner & scorer", type="primary"):
    with st.spinner("Entraînement Isolation Forest…"):
        findings, result = detect_anomalies(df, contamination=contamination / 100)
    st.session_state["findings_iforest"] = findings
    st.session_state["iforest_scores"] = result.scores

    c1, c2 = st.columns(2)
    c1.metric("Findings", f"{len(findings):,}")
    c2.metric(
        "Score max",
        f"{result.scores.max():.1f}" if not result.scores.empty else "n/a",
    )

    st.subheader("📈 Distribution des scores d'anomalie")
    fig = px.histogram(
        result.scores.rename("anomaly_score"),
        nbins=50,
        title="Distribution des scores (0 = normal, 100 = anomalie maximale)",
        template="plotly_dark",
    )
    st.plotly_chart(fig, use_container_width=True)

    if findings:
        rows = [
            {
                "invoice_id": f.invoice_id,
                "severity": f.severity.value,
                "anomaly_score": f.evidence.get("anomaly_score"),
                **f.evidence.get("features", {}),
            }
            for f in findings
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)
