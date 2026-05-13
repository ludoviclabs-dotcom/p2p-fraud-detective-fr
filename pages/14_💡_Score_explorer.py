"""Page Score Explorer — explique le score consolidé d'une facture.

Trois sous-vues :
1. Sélecteur de facture par invoice_id ou par score le plus élevé.
2. Waterfall Plotly des contributions par finding (avec reason codes FR).
3. Top features ML (perturbation Isolation Forest) si modèle dispo en session.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from p2p_fraud.i18n import _, init_locale_from_session
from p2p_fraud.scoring.explainer import (
    score_waterfall,
    top_contributions_summary,
    waterfall_to_dataframe,
)
from p2p_fraud.scoring.risk_engine import aggregate_findings_with_explanations
from p2p_fraud.streamlit_theme import init_page

init_locale_from_session()

init_page(
    title=_("nav.page_score_explorer"),
    surtitle=_("nav.surtitle_ml"),
    kicker=_("nav.kicker_score_explorer"),
)
st.caption(
    "Explication des scores consolidés en français : reason codes, waterfall des "
    "contributions par finding, et perturbation Isolation Forest pour le ML. "
    "Conforme à la transparence requise par l'AI Act art. 50."
)


def _collect_session_findings():
    keys = (
        "findings_master_data",
        "findings_sanctions",
        "findings_benford",
        "findings_duplicates",
        "findings_thresholds",
        "findings_sirene",
        "findings_isolation_forest",
        "findings_graph",
    )
    out = []
    for k in keys:
        v = st.session_state.get(k)
        if v:
            out.extend(v)
    return out


findings = _collect_session_findings()
if not findings:
    st.info(
        "Aucun finding en session. Lancez d'abord les détecteurs (master data, "
        "sanctions, doublons, etc.)."
    )
    st.stop()

scores = aggregate_findings_with_explanations(findings)
if not scores:
    st.warning("Tous les findings ont un poids 0 — aucun score à expliquer.")
    st.stop()

st.markdown(f"**{len(scores):,} factures scorées** depuis {len(findings):,} findings.")

# Tableau récapitulatif
recap = pd.DataFrame(
    [
        {
            "invoice_id": rs.invoice_id,
            "score": rs.score,
            "findings_count": rs.findings_count,
            "top_rule": rs.contributions[0].finding_rule_id if rs.contributions else "—",
            "summary_fr": top_contributions_summary(rs, n=3),
        }
        for rs in scores.values()
    ]
).sort_values("score", ascending=False)

st.dataframe(recap.head(50), use_container_width=True, height=320)

st.divider()
st.subheader("🔍 Décomposition d'un score")

invoice_ids_list = recap["invoice_id"].tolist()
qp_inv = st.query_params.get("invoice_id", "")
default_idx = invoice_ids_list.index(qp_inv) if qp_inv in invoice_ids_list else 0
invoice_id = st.selectbox("Facture", invoice_ids_list, index=default_idx)
if invoice_id and invoice_id != st.query_params.get("invoice_id"):
    st.query_params["invoice_id"] = invoice_id


@st.fragment
def _render_score_detail(inv_id: str) -> None:
    rs = scores[inv_id]

    col1, col2, col3 = st.columns(3)
    col1.metric("Score consolidé", f"{rs.score:.0f}/100")
    col2.metric("Nombre de findings", rs.findings_count)
    top_pct = rs.contributions[0].contribution_pct if rs.contributions else 0
    col3.metric("Part du top contributeur", f"{top_pct} %")

    steps = score_waterfall(rs)
    df_steps = waterfall_to_dataframe(steps)

    st.markdown("**Waterfall des contributions au score** :")
    fig = go.Figure(
        go.Waterfall(
            name="contributions",
            orientation="v",
            measure=["relative"] * len(df_steps),
            x=df_steps["label"],
            y=df_steps["delta"],
            text=[f"+{d:.1f}" for d in df_steps["delta"]],
            textposition="outside",
            connector={"line": {"color": "rgba(63, 63, 63, 0.4)"}},
        )
    )
    fig.update_layout(
        yaxis_title="Points (0–100)",
        height=420,
        margin={"t": 30, "b": 80, "l": 30, "r": 30},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("📝 Reason codes (français)")
    if rs.reason_codes_fr:
        for code in rs.reason_codes_fr:
            st.markdown(f"- {code}")
    else:
        st.caption("Aucun reason code disponible (legacy mode).")

    st.divider()
    st.subheader("🤖 Top features ML (Isolation Forest, si modèle dispo)")
    pipeline = st.session_state.get("iforest_pipeline")
    feature_row = st.session_state.get(f"iforest_features::{inv_id}")
    feature_columns = st.session_state.get("iforest_feature_columns")

    if pipeline is None or feature_row is None or feature_columns is None:
        st.caption(
            "Pour activer l'explication ML, lancez la page **🤖 Anomalies ML** sur ce dataset. "
            "Le pipeline et les features par facture seront alors disponibles ici."
        )
    else:
        from p2p_fraud.scoring.explainer import explain_isolation_forest_row

        contribs = explain_isolation_forest_row(pipeline, feature_row, feature_columns)
        df_features = pd.DataFrame(
            [{"feature": c.feature, "delta_anomaly_score": c.delta_anomaly_score} for c in contribs]
        )
        st.dataframe(df_features, use_container_width=True)


_render_score_detail(invoice_id)
