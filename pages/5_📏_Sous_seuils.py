"""Page Sous-seuils — détection des montants juste sous seuil de validation."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from p2p_fraud.detectors.thresholds import _load_threshold_config, detect_under_threshold
from p2p_fraud.i18n import _, init_locale_from_session
from p2p_fraud.streamlit_theme import init_page

init_locale_from_session()

init_page(
    title=_("nav.page_sous_seuils"),
    surtitle=_("nav.surtitle_controles"),
    kicker=_("nav.kicker_sous_seuils"),
)
st.caption(
    "Fenêtre `[seuil − ε·seuil, seuil[` paramétrable. Sévérité aggravée par clustering fournisseur."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

df: pd.DataFrame = st.session_state["df_invoices"]
cfg = _load_threshold_config()

with st.expander("⚙️ Configuration des seuils (issue de `weights.yaml`)"):
    st.json(cfg)

with st.spinner("Détection en cours…"):
    findings = detect_under_threshold(df)
st.session_state["findings_thresholds"] = findings

c1, c2 = st.columns(2)
c1.metric("Findings", f"{len(findings):,}")
c2.metric("Factures uniques", f"{len({f.invoice_id for f in findings}):,}")

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
    df_findings = pd.DataFrame(rows)
    st.dataframe(df_findings, use_container_width=True, height=320)

    st.subheader("📊 Distribution autour des seuils")
    fig = px.histogram(
        df_findings,
        x="amount",
        color="severity",
        nbins=60,
        title="Concentration des montants flaggés",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("✅ Aucune facture juste sous seuil détectée.")
