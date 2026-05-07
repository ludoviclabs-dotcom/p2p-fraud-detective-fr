"""Fiche fournisseur 360° — agrège profil, paiements, master data, findings, sanctions."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from p2p_fraud.scoring.reason_codes import render_reason
from p2p_fraud.services.vendor_360 import get_vendor_summary

st.set_page_config(
    page_title="Fiche fournisseur 360° — P2P Fraud Detective",
    page_icon="🪪",
    layout="wide",
)
st.title("🪪 Fiche fournisseur 360°")
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


vendors = st.session_state.get("df_vendors")
invoices = st.session_state.get("df_invoices_with_vid") or st.session_state.get(
    "df_invoices"
)
master_events = st.session_state.get("df_master_events")
findings = _collect_session_findings()

if vendors is None or invoices is None:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

vendor_options = vendors["vendor_id"].tolist() if "vendor_id" in vendors.columns else []
if not vendor_options:
    st.error("La table fournisseurs ne contient pas de colonne `vendor_id`.")
    st.stop()

# Pré-sélection : si un vendor_id est passé en query param ou choisi avant
default_idx = 0
preselect = st.query_params.get("vendor_id")
if preselect and preselect in vendor_options:
    default_idx = vendor_options.index(preselect)

vendor_id = st.selectbox("Fournisseur", vendor_options, index=default_idx)

summary = get_vendor_summary(
    vendor_id,
    invoices=invoices,
    vendors=vendors,
    master_events=master_events,
    findings=findings,
)


def _fmt_eur(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f} €".replace(",", " ")


# --- Bandeau d'identification ---

col1, col2, col3, col4 = st.columns(4)
col1.metric("Nom", summary.vendor_name or "—")
col2.metric("SIREN", summary.siren or "—")
col3.metric("Paiements (€)", _fmt_eur(summary.total_paid_eur))
col4.metric("Factures", summary.n_invoices)

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
        st.dataframe(
            sub[
                [
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
            ],
            use_container_width=True,
            height=240,
        )
        # Timeline d'évolution des paiements
        try:
            fig = px.bar(
                sub,
                x="invoice_date",
                y="amount",
                template="plotly_dark",
                title="Paiements dans le temps",
            )
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
            st.dataframe(iban, use_container_width=True)
        if not name_h.empty:
            st.markdown("#### Historique nom")
            st.dataframe(name_h, use_container_width=True)

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
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=320)
