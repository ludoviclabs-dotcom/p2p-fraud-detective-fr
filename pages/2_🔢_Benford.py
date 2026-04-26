"""Page Benford — analyse des 3 tests (F1D, F2D, LD) avec graphiques Plotly."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from p2p_fraud.detectors.benford import detect_outlier_invoices, run_benford_tests

st.set_page_config(page_title="Benford — P2P Fraud Detective", page_icon="🔢", layout="wide")
st.title("🔢 Loi de Newcomb-Benford")
st.caption(
    "Tests F1D (1er chiffre), F2D (2 premiers chiffres) et LD (dernier chiffre) — chi² + MAD (Nigrini)."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

df: pd.DataFrame = st.session_state["df_invoices"]

with st.spinner("Calcul des distributions Benford…"):
    results = run_benford_tests(df["amount"].astype(float))


def _interpretation_label(interp: str) -> tuple[str, str]:
    return {
        "conforming": ("✅ Conforme", "green"),
        "acceptable": ("🟢 Acceptable", "green"),
        "marginal": ("🟠 Marginalement non-conforme", "orange"),
        "non_conforming": ("🔴 Non-conforme — anomalie", "red"),
    }.get(interp, ("?", "gray"))


tabs = st.tabs(["📊 1er chiffre (F1D)", "📊 2 premiers chiffres (F2D)", "📊 Dernier chiffre (LD)"])

for tab, key in zip(tabs, ("F1D", "F2D", "LD"), strict=True):
    with tab:
        test = results[key]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("n (montants utilisés)", f"{test.n:,}")
        c2.metric("MAD", f"{test.mad:.5f}")
        c3.metric("Chi²", f"{test.chi2:.2f}")
        c4.metric("p-value chi²", f"{test.chi2_p_value:.4f}")
        label, _ = _interpretation_label(test.interpretation)
        st.markdown(f"**Interprétation Nigrini** : {label}")

        digits = sorted(test.digits_expected.keys())
        observed = [test.digits_observed.get(d, 0) for d in digits]
        expected = [test.digits_expected[d] for d in digits]
        fig = go.Figure()
        fig.add_bar(x=digits, y=observed, name="Observé", marker_color="#7C3AED")
        fig.add_scatter(
            x=digits,
            y=expected,
            name="Benford attendu",
            mode="lines+markers",
            line={"color": "#10B981", "width": 3},
        )
        fig.update_layout(
            xaxis_title="Chiffre",
            yaxis_title="Fréquence relative",
            template="plotly_dark",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("🎯 Factures suspectes (top 1 % sur F2D)")
findings = detect_outlier_invoices(df, test_name="F2D", top_pct=0.01)
st.write(f"**{len(findings)}** facture(s) suspecte(s) identifiée(s).")
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
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=320)
    st.session_state["findings_benford"] = findings
