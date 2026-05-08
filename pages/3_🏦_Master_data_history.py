"""Page master data history — détection IBAN swap / dormant / clone.

Dépend des invoices chargées dans `st.session_state["df_invoices"]` et,
optionnellement, d'un journal d'événements master data dans
`st.session_state["df_master_events"]`. Si ce dernier est absent, propose
de générer un journal synthétique pour la démo.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from p2p_fraud.detectors import master_data_changes as md
from p2p_fraud.schema import VendorMasterEvent
from p2p_fraud.streamlit_theme import init_page
from p2p_fraud.synthetic.generator import (
    MasterDataEventsConfig,
    attach_vendor_ids,
    generate_master_data_events,
)

init_page(
    title="Référentiel — historique",
    surtitle="Données",
    kicker=("Détection BEC + 4-eyes manquant"),
)
st.caption(
    "Le scénario fraude n°1 (AFP 2026) : changement d'IBAN sans 4-eyes, "
    "fournisseur dormant réactivé, clone vendor (nom + IBAN même jour)."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

invoices: pd.DataFrame = st.session_state["df_invoices"]
vendors: pd.DataFrame | None = st.session_state.get("df_vendors")

with st.expander("ℹ️ Fonctionnement"):
    st.markdown(
        """
        Cette page croise un **journal d'événements master data** (changements
        IBAN, nom, adresse, contact, statut) avec vos factures et vos paiements.

        Trois règles sont évaluées :

        1. **MD_IBAN_NO_4EYES** — IBAN modifié sans approbateur distinct
           (`approved_by` nul ou égal à `changed_by`).
        2. **MD_DORMANT_REACTIVATED** — fournisseur sans activité depuis > 180
           jours dont l'IBAN change avant un nouveau paiement.
        3. **MD_NAME_AND_IBAN_SAME_DAY** — clone vendor (typosquat + nouvel IBAN).

        L'exposition financière est calculée comme la somme des paiements dans
        les 90 jours suivant le changement.
        """
    )

events_df = st.session_state.get("df_master_events")
if events_df is None or events_df.empty:
    st.info(
        "Aucun journal d'événements master data chargé. "
        "Générez un journal synthétique pour explorer les détecteurs."
    )
    if st.button("🔧 Générer un journal synthétique de démo", type="primary"):
        if vendors is None:
            st.error(
                "Le générateur a besoin du master fournisseurs. "
                "Re-chargez le dataset via la page Upload."
            )
            st.stop()
        with st.spinner("Génération du journal master data…"):
            invoices_with_vid = attach_vendor_ids(invoices, vendors)
            events_df = generate_master_data_events(
                invoices_with_vid, vendors, MasterDataEventsConfig()
            )
            st.session_state["df_master_events"] = events_df
            st.session_state["df_invoices_with_vid"] = invoices_with_vid
        st.success(f"{len(events_df):,} événements master data générés.")
        st.rerun()
    st.stop()

invoices_with_vid = st.session_state.get("df_invoices_with_vid")
if invoices_with_vid is None and vendors is not None:
    invoices_with_vid = attach_vendor_ids(invoices, vendors)
    st.session_state["df_invoices_with_vid"] = invoices_with_vid
elif invoices_with_vid is None:
    invoices_with_vid = invoices

c1, c2, c3, c4 = st.columns(4)
c1.metric("Événements", f"{len(events_df):,}")
c2.metric("IBAN changes", int((events_df["field"] == "iban").sum()))
c3.metric("Sans 4-eyes", int(events_df["approved_by"].isna().sum()))
fraud_count = int(events_df["is_fraud"].sum()) if "is_fraud" in events_df.columns else 0
c4.metric("Étiquetés fraude (synthétique)", fraud_count)

st.divider()
st.subheader("📜 Timeline des changements")

display_df = events_df.copy()
display_df["changed_at"] = pd.to_datetime(display_df["changed_at"], utc=True)
fig = px.scatter(
    display_df,
    x="changed_at",
    y="field",
    color="field",
    hover_data=["vendor_id", "old_value", "new_value", "changed_by", "approved_by"],
    height=380,
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("🚨 Findings master data")

with st.spinner("Évaluation des règles…"):
    pydantic_events = []
    for _, row in events_df.iterrows():
        try:
            pydantic_events.append(
                VendorMasterEvent(
                    event_id=row["event_id"],
                    vendor_id=row["vendor_id"],
                    field=row["field"],
                    old_value=row.get("old_value"),
                    new_value=row.get("new_value"),
                    changed_at=row["changed_at"]
                    if isinstance(row["changed_at"], datetime)
                    else pd.Timestamp(row["changed_at"]).to_pydatetime().replace(tzinfo=UTC),
                    changed_by=row.get("changed_by"),
                    approved_by=row.get("approved_by")
                    if pd.notna(row.get("approved_by"))
                    else None,
                    source=row.get("source", "erp"),
                )
            )
        except (ValueError, KeyError, TypeError) as e:
            st.warning(f"Événement ignoré ({row.get('event_id')}): {e}")
    findings = md.run_all(pydantic_events, invoices_with_vid)

st.write(f"**{len(findings)}** findings détectés.")
if findings:
    rows = [
        {
            "invoice_id": f.invoice_id,
            "rule_id": f.rule_id,
            "signal": f.signal,
            "severity": f.severity.value,
            "vendor_id": f.evidence.get("vendor_id"),
            "exposure_eur": f.evidence.get("exposure_eur"),
            "changed_at": f.evidence.get("changed_at") or f.evidence.get("iban_changed_at"),
        }
        for f in findings
    ]
    df_findings = pd.DataFrame(rows).sort_values(
        "exposure_eur", ascending=False, na_position="last"
    )
    st.dataframe(df_findings, use_container_width=True, height=420)
    st.session_state["findings_master_data"] = findings
