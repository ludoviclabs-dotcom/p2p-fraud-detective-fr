"""Fiche fournisseur 360° — agrège profil, paiements, master data, findings, sanctions."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

from p2p_fraud.i18n import _, init_locale_from_session
from p2p_fraud.llm.narrative_generator import (
    generate_vendor_narrative,
    generate_vendor_narrative_stream,
)
from p2p_fraud.scoring.reason_codes import render_reason
from p2p_fraud.services.vendor_360 import get_vendor_summary
from p2p_fraud.streamlit_theme import init_page

init_locale_from_session()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_vendor_summary(vendor_id, invoices, vendors, master_events, findings_tuple):
    return get_vendor_summary(
        vendor_id,
        invoices=invoices,
        vendors=vendors,
        master_events=master_events,
        findings=list(findings_tuple),
    )


init_page(
    title="Fiche fournisseur 360°",
    surtitle="Investigation",
    kicker=("Profil · paiements · master data · findings"),
)
st.caption(
    "Vue consolidée par fournisseur : profil, paiements, historique master data, "
    "findings, sanctions/PEP. Aucun appel réseau — uniquement les données chargées en session."
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


def _aggrid_simple(df: pd.DataFrame, height: int = 240) -> None:
    """AgGrid en lecture seule, tri/filtre activés, format € sur colonnes numériques."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filter=True, resizable=True)
    for col in df.select_dtypes("number").columns:
        if "amount" in col or "eur" in col or "paid" in col:
            gb.configure_column(
                col,
                type=["numericColumn"],
                valueFormatter="value != null ? value.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' €' : '—'",
            )
    AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.NO_UPDATE,
        data_return_mode=DataReturnMode.AS_INPUT,
        height=height,
        use_container_width=True,
        allow_unsafe_jscode=True,
    )


vendors = st.session_state.get("df_vendors")
invoices = st.session_state.get("df_invoices_with_vid") or st.session_state.get("df_invoices")
master_events = st.session_state.get("df_master_events")
findings = _collect_session_findings()

if vendors is None or invoices is None:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

vendor_options = vendors["vendor_id"].tolist() if "vendor_id" in vendors.columns else []
if not vendor_options:
    st.error("La table fournisseurs ne contient pas de colonne `vendor_id`.")
    st.stop()

default_idx = 0
preselect = st.query_params.get("vendor_id")
if preselect and preselect in vendor_options:
    default_idx = vendor_options.index(preselect)

vendor_id = st.selectbox("Fournisseur", vendor_options, index=default_idx)
if vendor_id and vendor_id != st.query_params.get("vendor_id"):
    st.query_params["vendor_id"] = vendor_id

summary = _cached_vendor_summary(
    vendor_id,
    invoices=invoices,
    vendors=vendors,
    master_events=master_events,
    findings_tuple=tuple(findings),
)


def _fmt_eur(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f} €".replace(",", " ")


col1, col2, col3, col4 = st.columns(4)
col1.metric("Nom", summary.vendor_name or "—")
col2.metric("SIREN", summary.siren or "—")
col3.metric("Paiements (€)", _fmt_eur(summary.total_paid_eur))
col4.metric("Factures", summary.n_invoices)

# Sparkline trend exposition 30 jours (P5-4)
if not summary.invoices.empty:
    from datetime import UTC, datetime, timedelta

    import plotly.graph_objects as go

    _sub = summary.invoices.copy()
    _sub["invoice_date"] = pd.to_datetime(_sub["invoice_date"], errors="coerce")
    _sub = _sub.dropna(subset=["invoice_date"])
    _since = pd.Timestamp(datetime.now(UTC).date() - timedelta(days=30), tz="UTC")
    _recent = _sub[_sub["invoice_date"] >= _since.tz_localize(None)]
    if not _recent.empty:
        _daily = _recent.groupby(_recent["invoice_date"].dt.date)["amount"].sum()
        _idx = pd.date_range(
            end=datetime.now(UTC).date(),
            periods=30,
            freq="D",
        )
        _series = pd.Series(
            [_daily.get(d.date(), 0.0) for d in _idx],
            index=_idx,
        )
        _exp_30d = float(_series.sum())
        st.caption(
            f"📈 **{_('vendor.exposure_30d')}** : {_fmt_eur(_exp_30d)} · "
            f"{_('vendor.exposure_trend')} sur 30 jours"
        )
        _fig_spark = go.Figure(
            go.Scatter(
                x=_series.index,
                y=_series.values,
                mode="lines",
                line={"color": "#1F3A6E", "width": 2},
                fill="tozeroy",
                fillcolor="rgba(31, 58, 110, 0.2)",
                hovertemplate="%{x|%d %b}<br>%{y:,.0f} €<extra></extra>",
            )
        )
        _fig_spark.update_layout(
            showlegend=False,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            height=60,
            xaxis={"visible": False},
            yaxis={"visible": False},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(_fig_spark, use_container_width=True)

if summary.is_sanctioned:
    st.error("🚨 Fournisseur SANCTIONNÉ — paiement à bloquer (LCB-FT).")
elif summary.is_pep:
    st.warning("⚠️ Lien PEP détecté — vigilance renforcée requise (Sapin 2).")

st.divider()

tabs = st.tabs(["Profil", "Paiements", "Master data", "Findings"])

with tabs[0]:
    st.markdown("### Profil")
    st.write(
        {
            "vendor_id": summary.vendor_id,
            "vendor_name": summary.vendor_name,
            "siren": summary.siren,
            "ape_code": summary.ape_code,
            "address": summary.address,
            "creation_date": summary.creation_date,
            "is_active": summary.is_active,
        }
    )

with tabs[1]:
    st.markdown("### Paiements")
    if summary.invoices.empty:
        st.write("Aucune facture pour ce fournisseur.")
    else:
        sub = summary.invoices.copy()
        sub["invoice_date"] = pd.to_datetime(sub["invoice_date"], errors="coerce")
        sub = sub.sort_values("invoice_date")
        display_cols = [
            c
            for c in [
                "invoice_id",
                "invoice_date",
                "amount",
                "currency",
                "po_number",
                "user_id",
                "gl_account",
            ]
            if c in sub.columns
        ]
        _aggrid_simple(sub[display_cols], height=240)
        try:
            fig = px.bar(sub, x="invoice_date", y="amount", title="Paiements dans le temps")
            st.plotly_chart(fig, use_container_width=True)
        except (ValueError, KeyError, TypeError):
            pass

with tabs[2]:
    st.markdown("### Historique master data")
    iban = pd.DataFrame(summary.iban_history)
    name_h = pd.DataFrame(summary.name_history)
    if iban.empty and name_h.empty:
        st.write("Aucun changement master data tracé.")
    else:
        if not iban.empty:
            st.markdown("#### Historique IBAN")
            _aggrid_simple(iban, height=200)
        if not name_h.empty:
            st.markdown("#### Historique nom")
            _aggrid_simple(name_h, height=200)

with tabs[3]:
    st.markdown("### Findings")
    if not summary.findings:
        st.success("Aucun finding pour ce fournisseur.")
    else:
        rows = [
            {
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "signal": f.signal,
                "invoice_id": f.invoice_id,
                "exposure_eur": f.evidence.get("exposure_eur"),
                "reason_fr": render_reason(f),
            }
            for f in summary.findings
        ]
        _aggrid_simple(pd.DataFrame(rows), height=320)

    st.divider()
    st.markdown("#### 📝 Narration d'audit automatique (Claude AI)")
    st.caption(
        "Génère un paragraphe de travail d'audit en français, structuré selon **ISA 240**, "
        "à partir des findings ci-dessus. Nécessite une clé API Anthropic."
    )

    api_key_input = st.text_input(
        "Clé API Anthropic (ANTHROPIC_API_KEY)",
        type="password",
        value=st.session_state.get("anthropic_api_key", ""),
        help="Configurez ANTHROPIC_API_KEY dans .env ou les secrets Streamlit Cloud pour éviter de saisir la clé manuellement.",
        key="anthropic_key_field",
    )
    if api_key_input:
        st.session_state["anthropic_api_key"] = api_key_input

    col_btn_stream, col_btn_block = st.columns(2)
    _stream_clicked = col_btn_stream.button(
        "📝 Générer narration (streaming)",
        type="primary",
        key="gen_narrative_stream",
        help="Affichage progressif via st.write_stream — UX type ChatGPT.",
    )
    _block_clicked = col_btn_block.button(
        "📝 Générer narration (bloquant)",
        key="gen_narrative_block",
        help="Variante bloquante avec métriques tokens en fin.",
    )

    if _stream_clicked or _block_clicked:
        _api_key = st.session_state.get("anthropic_api_key") or ""
        if not _api_key:
            st.error(_("llm.no_key"))
        else:
            _findings_dicts = [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity.value,
                    "signal": f.signal,
                    "exposure_eur": f.evidence.get("exposure_eur"),
                }
                for f in summary.findings
            ]
            _common_kwargs = dict(
                vendor_id=summary.vendor_id,
                vendor_name=summary.vendor_name,
                siren=summary.siren,
                total_paid_eur=summary.total_paid_eur,
                n_invoices=summary.n_invoices,
                is_sanctioned=summary.is_sanctioned,
                is_pep=summary.is_pep,
                findings=_findings_dicts,
                api_key=_api_key,
            )
            try:
                if _stream_clicked:
                    st.markdown("**Narration en cours…**")
                    streamed = st.write_stream(generate_vendor_narrative_stream(**_common_kwargs))
                    st.session_state[f"narrative_stream_{summary.vendor_id}"] = streamed
                else:
                    with st.spinner(_("llm.generating")):
                        result = generate_vendor_narrative(**_common_kwargs)
                    st.session_state[f"narrative_{summary.vendor_id}"] = result
            except (ImportError, ValueError) as exc:
                st.error(f"{_('llm.error_generic')} ({exc})")
            except Exception as exc:
                st.error(f"{_('llm.error_generic')} ({exc})")

    _cached_narrative = st.session_state.get(f"narrative_{summary.vendor_id}")
    if _cached_narrative:
        st.markdown("**Narration générée :**")
        st.markdown(_cached_narrative.narrative)
        st.caption(
            f"Modèle : `{_cached_narrative.model}` · "
            f"Tokens entrée : {_cached_narrative.input_tokens} "
            f"(dont {_cached_narrative.cached_tokens} en cache) · "
            f"Tokens sortie : {_cached_narrative.output_tokens}"
        )
        st.download_button(
            "⬇️ Télécharger la narration (.txt)",
            data=_cached_narrative.narrative,
            file_name=f"narration_audit_{summary.vendor_id}.txt",
            mime="text/plain",
        )
