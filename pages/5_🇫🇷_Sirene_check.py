"""Page Sirene — cross-check API INSEE v3 (statut, date création, code APE)."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from p2p_fraud.enrichment.sirene_client import SireneClient, cross_check_invoices

load_dotenv()

st.set_page_config(page_title="Sirene check — P2P Fraud Detective", page_icon="🇫🇷", layout="wide")
st.title("🇫🇷 Cross-check API Sirene v3")
st.caption(
    "Vérifie chaque SIREN contre le référentiel INSEE : existence, statut administratif, "
    "date de création vs 1ère facture."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

df: pd.DataFrame = st.session_state["df_invoices"]

token_set = bool(os.environ.get("SIRENE_API_TOKEN", "").strip())
client = SireneClient()

if not token_set:
    st.warning(
        "🔑 `SIRENE_API_TOKEN` n'est pas défini dans l'environnement. "
        "Le cross-check est sauté. Obtenez un token gratuit sur "
        "[api.insee.fr](https://api.insee.fr/catalogue/) puis renseignez `.env`."
    )
    st.code("SIRENE_API_TOKEN=votre_token", language="bash")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    new_vendor_grace = st.slider(
        "Délai création-facture suspect (jours)", min_value=30, max_value=365, value=90, step=15
    )
with c2:
    n_unique = df["siren"].dropna().nunique() if "siren" in df.columns else 0
    st.metric("SIREN uniques à vérifier", f"{n_unique:,}")

if st.button("🔍 Lancer le cross-check Sirene", type="primary"):
    with st.spinner(f"Vérification de {n_unique:,} SIREN auprès de l'INSEE…"):
        findings = cross_check_invoices(df, client=client, new_vendor_grace_days=new_vendor_grace)
    st.session_state["findings_sirene"] = findings

    if not findings:
        st.success("✅ Aucune anomalie Sirene détectée.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "SIREN inexistants", sum(1 for f in findings if f.signal == "vendor_siren_not_found")
        )
        c2.metric("Fournisseurs radiés", sum(1 for f in findings if f.signal == "vendor_ceased"))
        c3.metric(
            "Créations récentes", sum(1 for f in findings if f.signal == "vendor_recently_created")
        )

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
