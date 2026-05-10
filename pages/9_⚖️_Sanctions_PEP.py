"""Page sanctions / PEP — détection des fournisseurs listés (LCB-FT, Sapin 2 art. 17)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from p2p_fraud.detectors.sanctions import detect_sanctioned_vendors
from p2p_fraud.enrichment.sanctions_client import DEFAULT_SNAPSHOT, SanctionsClient
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Sanctions & PEP",
    surtitle="Contrôles statistiques",
    kicker=("OFAC, Trésor FR, UE consolidée"),
)
st.caption(
    "Cross-check fournisseurs vs OFAC SDN, listes consolidées UE, Trésor FR et "
    "listes PEP (personnes politiquement exposées)."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

invoices: pd.DataFrame = st.session_state["df_invoices"]

_snap_name = DEFAULT_SNAPSHOT.name
_snap_date = (
    _snap_name.replace("snapshot_", "").replace(".csv", "")
    if "snapshot_" in _snap_name
    else "inconnue"
)
st.caption(f"Snapshot embarqué : **{_snap_name}** — date de mise à jour : **{_snap_date}**")

with st.expander("ℹ️ Sources et méthodologie"):
    st.markdown(
        """
        **Source par défaut** : snapshot CSV embarqué (`data/sanctions/snapshot_*.csv`)
        — déterministe, déployable on-prem, sans appel réseau.

        **Sources réelles attendues en production** :
        - OFAC SDN (Trésor US) — JSON officiel,
        - Liste consolidée UE,
        - Trésor FR — gel des avoirs,
        - PEP UE / FR (sources OpenSanctions, Refinitiv, Dow Jones).

        Le matching utilise une normalisation Unicode + lower + RapidFuzz `WRatio`,
        avec un seuil minimal de 90 par défaut (réglable).

        **Réglementations couvertes** : LCB-FT, Sapin 2 art. 17 (due diligence
        tiers), DORA art. 28 (risque de concentration sur prestataires sanctionnés).
        """
    )

threshold = st.slider("Seuil minimal de matching (RapidFuzz WRatio)", 70, 99, 90, 1)
client = SanctionsClient(min_score=threshold)
st.caption(f"Snapshot : `{client.snapshot_path.name}` ({client.n_records} entités)")

with st.spinner("Cross-check sanctions / PEP…"):
    findings = detect_sanctioned_vendors(invoices, client=client)

c1, c2, c3 = st.columns(3)
n_critical = sum(1 for f in findings if f.severity.value == "critical")
n_high = sum(1 for f in findings if f.severity.value == "high")
exposure_total = sum(float(f.evidence.get("exposure_eur") or 0) for f in findings)
c1.metric("Findings sanctions (CRITICAL)", n_critical)
c2.metric("Findings PEP (HIGH)", n_high)
c3.metric("Exposition totale (€)", f"{exposure_total:,.0f}".replace(",", " "))

st.divider()
st.subheader("🚨 Fournisseurs flagués")
if not findings:
    st.success("Aucun fournisseur sanctionné ou PEP identifié dans ce dataset.")
else:
    rows = [
        {
            "invoice_id": f.invoice_id,
            "rule_id": f.rule_id,
            "severity": f.severity.value,
            "vendor_name": f.evidence.get("vendor_name"),
            "matched_name": f.evidence.get("matched_name"),
            "list_source": f.evidence.get("list_source"),
            "score": f.evidence.get("score"),
            "country": f.evidence.get("country"),
            "exposure_eur": f.evidence.get("exposure_eur"),
            "reason": f.evidence.get("reason"),
        }
        for f in findings
    ]
    df = pd.DataFrame(rows).sort_values("exposure_eur", ascending=False, na_position="last")
    st.dataframe(df, use_container_width=True, height=420)
    st.session_state["findings_sanctions"] = findings
