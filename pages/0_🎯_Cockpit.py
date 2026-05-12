"""Page Cockpit — vue CFO / responsable contrôle interne.

Page d'accueil du démonstrateur (`default=True` dans `st.navigation`).

Triée par € exposition financière (pas par score brut). Sections :
1. Mission + positionnement (visible immédiatement, même sans données chargées)
2. 4 KPI principaux (exposition totale, critique, cases ouverts, en retard SLA)
3. 6 raccourcis vers les pages-piliers (st.page_link)
4. Top 10 fournisseurs par exposition € (si findings disponibles)
5. Cases ouverts (toujours visibles grâce au seed démo)
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from p2p_fraud.services.exposure import (
    aggregate_exposure_by_vendor,
    cases_to_dataframe,
    cockpit_summary,
)
from p2p_fraud.streamlit_theme import init_page
from pages._helpers import get_case_service

init_page(
    title="Cockpit",
    surtitle="Pilotage",
    kicker="Vue consolidée des risques P2P — exposition financière prioritaire",
)


# ─── 1. Mission + positionnement ─────────────────────────────────────────────

st.markdown(
    """
    **P2P Fraud Detective FR** est un démonstrateur d'audit du cycle Procure-to-Pay
    orienté détection de fraude (sous-seuils, doublons, BEC, sanctions, anneaux),
    aligné sur les méthodologies AML/CFT et les contrôles attendus en audit P2P
    public (ISA 240, AS 2401, Sapin 2, LCB-FT, DORA art. 28).

    *Pertinent pour ETI, cabinets d'audit, fonctions publiques et organismes de contrôle
    (DGFiP, Tracfin, IGF, Cour des comptes, CRC).*

    **Données** : fictives ou issues de sources ouvertes (Sirene, sanctions consolidées
    UE, listes PEP). Outil de démonstration, hors production.
    """
)

st.divider()


# ─── 2. KPI ──────────────────────────────────────────────────────────────────

service = get_case_service()


def _collect_session_findings() -> list:
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


def _fmt_eur(value: float) -> str:
    return f"{value:,.0f} €".replace(",", " ")


findings = _collect_session_findings()
invoices = st.session_state.get("df_invoices_with_vid") or st.session_state.get("df_invoices")
cases = service.list_cases()

# Si aucun finding en session, on prend une exposition "démo" depuis les cases seedés.
if findings:
    summary = cockpit_summary(findings, cases=cases, invoices=invoices)
    exposure_total = summary.exposure_eur_total
    exposure_critical = summary.exposure_eur_critical
    n_critical = summary.n_critical
    n_findings = summary.n_findings
    n_high = summary.n_high
    n_cases_open = summary.n_cases_open
    n_cases_overdue = summary.n_cases_overdue
    n_cases_unassigned_critical = summary.n_cases_unassigned_critical
else:
    summary = None
    exposure_total = sum((c.exposure_eur or 0) for c in cases)
    exposure_critical = sum((c.exposure_eur or 0) for c in cases if c.severity == "critical")
    n_critical = sum(1 for c in cases if c.severity == "critical")
    n_findings = 0
    n_high = sum(1 for c in cases if c.severity == "high")
    n_cases_open = sum(1 for c in cases if not c.status.is_closed)
    n_cases_overdue = 0
    n_cases_unassigned_critical = sum(
        1 for c in cases if c.severity == "critical" and not c.assignee and not c.status.is_closed
    )

col1, col2, col3, col4 = st.columns(4)
col1.metric("💸 Exposition totale", _fmt_eur(exposure_total))
col2.metric(
    "🔴 Exposition CRITICAL",
    _fmt_eur(exposure_critical),
    delta=f"{n_critical} alertes" if n_critical else None,
    delta_color="inverse",
)
col3.metric("📂 Cases ouverts", n_cases_open)
col4.metric(
    "⏰ Cases en retard SLA",
    n_cases_overdue,
    delta=f"{n_cases_unassigned_critical} non assignés" if n_cases_unassigned_critical else None,
    delta_color="inverse",
)


# ─── 2bis. Sparklines tendances 30 jours ─────────────────────────────────────


def _daily_series(events: list, days: int = 30) -> pd.Series:
    """Renvoie une Series indexée jour → count sur les `days` derniers jours.

    Bornes inclusives, jours sans événement = 0 (sparkline continue).
    """
    today = datetime.now(UTC).date()
    idx = pd.date_range(end=today, periods=days, freq="D")
    counts = Counter(events)
    series = pd.Series([counts.get(d.date(), 0) for d in idx], index=idx)
    return series


def _sparkline(series: pd.Series, color: str) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=series.index,
            y=series.values,
            mode="lines",
            line={"color": color, "width": 2},
            fill="tozeroy",
            fillcolor=color + "33",
            hovertemplate="%{x|%d %b}<br>%{y:d}<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=False,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=60,
        xaxis={"visible": False},
        yaxis={"visible": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# Agrégation des événements audit_log + cases sur 30 jours
audit_log = service.audit_log.all()
since = (datetime.now(UTC) - timedelta(days=30)).date()


def _parse_iso(s: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (TypeError, ValueError):
        return None


cases_created_dates = [
    c.created_at.astimezone(UTC).date()
    if hasattr(c.created_at, "astimezone")
    else _parse_iso(str(c.created_at)).date()
    for c in cases
    if hasattr(c.created_at, "astimezone") or _parse_iso(str(c.created_at))
]
cases_created_dates = [d for d in cases_created_dates if d >= since]

cases_closed_dates = [
    c.closed_at.astimezone(UTC).date()
    if c.closed_at and hasattr(c.closed_at, "astimezone")
    else None
    for c in cases
    if c.closed_at
]
cases_closed_dates = [d for d in cases_closed_dates if d and d >= since]

critical_events_dates = [e.payload.get("severity") for e in audit_log if e.kind.startswith("case.")]
# Plutôt : les events case.created avec severity=critical
critical_events_dates = [
    _parse_iso(e.at).date()
    for e in audit_log
    if e.kind == "case.created"
    and e.payload.get("severity") == "critical"
    and _parse_iso(e.at)
    and _parse_iso(e.at).date() >= since
]

all_audit_dates = [_parse_iso(e.at).date() for e in audit_log if _parse_iso(e.at)]
all_audit_dates = [d for d in all_audit_dates if d >= since]

st.caption("📈 **Tendance sur 30 jours**")
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown("**Cases créés**")
    st.plotly_chart(
        _sparkline(_daily_series(cases_created_dates), "#1F3A6E"),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with s2:
    st.markdown("**Cases clôturés**")
    st.plotly_chart(
        _sparkline(_daily_series(cases_closed_dates), "#3E7C5A"),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with s3:
    st.markdown("**Alertes critiques**")
    st.plotly_chart(
        _sparkline(_daily_series(critical_events_dates), "#A23E48"),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with s4:
    st.markdown("**Activité audit trail**")
    st.plotly_chart(
        _sparkline(_daily_series(all_audit_dates), "#E5A93A"),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.divider()


# ─── 3. Raccourcis rapides ───────────────────────────────────────────────────

st.subheader("🚀 Accès rapide")

q1, q2, q3 = st.columns(3)
with q1:
    st.page_link(
        "pages/10_🗂️_File_d_investigation.py",
        label="🗂️ File d'investigation",
        help="Case management, statuts, clôture motivée",
    )
    st.page_link(
        "pages/15_🪪_Fiche_fournisseur_360.py",
        label="🪪 Fiche fournisseur 360°",
        help="Profil + paiements + master data + findings",
    )
with q2:
    st.page_link(
        "pages/14_💡_Score_explorer.py",
        label="💡 Explorateur de score",
        help="Waterfall + reason codes FR",
    )
    st.page_link(
        "pages/9_⚖️_Sanctions_PEP.py",
        label="⚖️ Sanctions & PEP",
        help="OFAC, Trésor FR, UE consolidée",
    )
with q3:
    st.page_link(
        "pages/13_📜_Audit_trail.py",
        label="📜 Piste d'audit",
        help="Journal hash-chaîné SHA-256",
    )
    st.page_link(
        "pages/12_📚_Méthodologie.py",
        label="📚 Méthodologie",
        help="Sources, seuils, métriques F1",
    )

st.divider()


# ─── 4. Top 10 fournisseurs ──────────────────────────────────────────────────

st.subheader("🏆 Top 10 fournisseurs par exposition financière")

if summary and summary.top_vendors:
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
    sel = st.dataframe(
        df_top,
        use_container_width=True,
        height=320,
        on_select="rerun",
        selection_mode="single-row",
        key="top10_sel",
    )
    selected_rows = sel.selection.rows if sel and sel.selection else []
    if selected_rows:
        row_idx = selected_rows[0]
        vid = df_top.iloc[row_idx]["vendor_id"]
        vname = df_top.iloc[row_idx].get("vendor_name", vid)
        if st.button(f"🪪 Ouvrir la fiche de {vname}", type="primary", key="drill_fiche"):
            st.query_params["vendor_id"] = str(vid)
            st.switch_page("pages/15_🪪_Fiche_fournisseur_360.py")
    else:
        st.caption("👆 Cliquez sur une ligne pour ouvrir la **🪪 Fiche fournisseur 360°**.")
elif cases:
    st.info(
        "Top 10 calculé sur les findings de la session. "
        "Aucun finding chargé pour le moment — ci-dessous : les cases de démo."
    )
else:
    st.info("Aucun finding ni case en session. Direction **📤 Import des données** pour démarrer.")

st.divider()


# ─── 5. Cases ouverts ────────────────────────────────────────────────────────

st.subheader("📂 Cases en cours")

if cases:
    df_cases = cases_to_dataframe(cases)
    st.dataframe(df_cases, use_container_width=True, height=320)
    st.caption(
        "👉 Direction **🗂️ File d'investigation** pour créer / muter / clôturer un case. "
        "Chaque action est journalisée dans la **📜 Piste d'audit**."
    )
else:
    st.write("Aucun case enregistré.")


# ─── 6. Détail fournisseurs flagués (si findings) ───────────────────────────

if findings:
    st.divider()
    st.subheader("📊 Détail des fournisseurs flagués (findings session)")

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
