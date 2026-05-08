"""Page Cockpit — vue CFO / responsable contrôle interne.

Triée par € exposition financière (pas par score brut). KPIs :
- alertes critiques, total et en attente
- € exposition totale et critique
- cases ouverts, en retard SLA, critiques non assignés
- top 10 fournisseurs

Position 0 pour apparaître en tête de la nav Streamlit.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.services.exposure import (
    aggregate_exposure_by_vendor,
    cases_to_dataframe,
    cockpit_summary,
)
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Cockpit",
    surtitle="Pilotage",
    kicker=("Vue consolidée des risques P2P"),
)
st.caption(
    "Vue CFO / responsable contrôle interne. Tri par exposition financière, pas par score brut."
)


@st.cache_resource
def _service() -> CaseService:
    return CaseService(":memory:", AuditLog(":memory:"))


service = _service()


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
invoices = st.session_state.get("df_invoices_with_vid") or st.session_state.get("df_invoices")
cases = service.list_cases()

if not findings:
    st.info(
        "Aucun finding en session. Lancez d'abord les détecteurs (master data, "
        "sanctions, doublons, etc.) puis revenez ici. Les cases s'afficheront "
        "dès leur création depuis la page **🗂️ File d'investigation**."
    )
    st.stop()

summary = cockpit_summary(findings, cases=cases, invoices=invoices)


def _fmt_eur(value: float) -> str:
    return f"{value:,.0f} €".replace(",", " ")


col1, col2, col3, col4 = st.columns(4)
col1.metric("💸 Exposition totale", _fmt_eur(summary.exposure_eur_total))
col2.metric(
    "🔴 Exposition CRITICAL",
    _fmt_eur(summary.exposure_eur_critical),
    delta=f"{summary.n_critical} alertes",
    delta_color="inverse",
)
col3.metric("🚨 Findings", summary.n_findings)
col4.metric("📂 Cases ouverts", summary.n_cases_open)

st.divider()

col5, col6, col7 = st.columns(3)
col5.metric("⏰ Cases en retard SLA", summary.n_cases_overdue)
col6.metric("👤 Critiques non assignés", summary.n_cases_unassigned_critical)
col7.metric("🟠 Findings HIGH", summary.n_high)

st.divider()
st.subheader("🏆 Top 10 fournisseurs par exposition")

if summary.top_vendors:
    df_top = pd.DataFrame(
        [
            {
                "vendor_id": v.vendor_id,
                "vendor_name": v.vendor_name,
                "exposure_eur": v.exposure_eur,
                "n_findings": v.n_findings,
                "n_critical": v.n_critical,
                "rules": ", ".join(v.rules),
            }
            for v in summary.top_vendors
        ]
    )
    st.dataframe(df_top, use_container_width=True, height=320)
    st.caption("👉 Cliquez sur un vendor_id pour ouvrir sa fiche 360° (page suivante).")
else:
    st.write("Aucun fournisseur exposé.")

st.divider()
st.subheader("📂 Cases ouverts")

if cases:
    df_cases = cases_to_dataframe(cases)
    st.dataframe(df_cases, use_container_width=True, height=320)
else:
    st.write(
        "Aucun case enregistré. Direction la page **🗂️ File d'investigation** "
        "pour créer des cases depuis vos findings."
    )

st.divider()
st.subheader("📊 Détail des fournisseurs flagués")

vendor_table = aggregate_exposure_by_vendor(findings, invoices)
if vendor_table:
    df_all = pd.DataFrame(
        [
            {
                "vendor_id": v.vendor_id,
                "vendor_name": v.vendor_name,
                "exposure_eur": v.exposure_eur,
                "n_findings": v.n_findings,
                "n_critical": v.n_critical,
                "rules": ", ".join(v.rules),
            }
            for v in vendor_table
        ]
    )
    st.dataframe(df_all, use_container_width=True, height=320)
