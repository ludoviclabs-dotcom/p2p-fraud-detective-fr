"""Page Doublons — exact + fuzzy avec RapidFuzz et bucketing montant/date."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from p2p_fraud.detectors.duplicates import detect_duplicates

st.set_page_config(page_title="Doublons — P2P Fraud Detective", page_icon="♊", layout="wide")
st.title("♊ Doublons (exacts + fuzzy)")
st.caption("Bucketing montant ± 0,01 € + fenêtre date paramétrable + RapidFuzz `token_set_ratio`.")

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

df: pd.DataFrame = st.session_state["df_invoices"]

c1, c2, c3 = st.columns(3)
with c1:
    name_threshold = st.slider("Seuil RapidFuzz `token_set_ratio`", 70, 100, 90)
with c2:
    date_window = st.slider("Fenêtre date (jours)", 0, 14, 2)
with c3:
    st.metric("Factures à analyser", f"{len(df):,}")

if st.button("🔍 Lancer la détection", type="primary"):
    with st.spinner("Bucketing + comparaison fuzzy…"):
        findings = detect_duplicates(
            df, name_threshold=name_threshold, date_window_days=date_window
        )
    st.session_state["findings_duplicates"] = findings

    n_exact = sum(1 for f in findings if f.signal == "duplicate_exact")
    n_fuzzy = sum(1 for f in findings if f.signal == "duplicate_fuzzy")
    c1, c2, c3 = st.columns(3)
    c1.metric("Findings exact", f"{n_exact:,}")
    c2.metric("Findings fuzzy", f"{n_fuzzy:,}")
    c3.metric("Factures uniques flaggées", f"{len({f.invoice_id for f in findings}):,}")

    if findings:
        rows = [
            {
                "invoice_id": f.invoice_id,
                "signal": f.signal,
                "severity": f.severity.value,
                **f.evidence,
            }
            for f in findings
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)
    else:
        st.success("✅ Aucun doublon détecté.")
