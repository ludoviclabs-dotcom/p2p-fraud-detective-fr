"""Page DECP / RBE — croisement fournisseurs × marchés publics × bénéficiaires effectifs."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from p2p_fraud.detectors.decp import detect_decp_rbe
from p2p_fraud.enrichment.decp_client import DECPClient
from p2p_fraud.enrichment.rbe_client import RBEClient
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="DECP & RBE INPI",
    surtitle="Contrôles réglementaires",
    kicker="Marchés publics (DECP) · Bénéficiaires effectifs (RBE/INPI) · Sapin 2 art. 17",
)
st.caption(
    "Croisement des fournisseurs avec le DECP (Données Essentielles des Contrats de la "
    "Commande Publique) et le RBE INPI (Registre des Bénéficiaires Effectifs). "
    "Détecte les conflits d'intérêts, structures opaques et PEP bénéficiaires (Sapin 2, AMLD6)."
)

with st.expander("ℹ️ Sources et réglementation"):
    st.markdown(
        """
        **Sources** :
        - **DECP** : `data.economie.gouv.fr/decp_augmente` — Données Essentielles des Contrats
          de la Commande Publique (ODbL). Référentiel de tous les marchés publics français > 25 k€.
        - **RBE INPI** : `data.inpi.fr/rne/rbe` — Registre National des Entreprises,
          liste des bénéficiaires effectifs (Etalab Open Licence).

        **Réglementations couvertes** :
        - **Sapin 2 art. 17** — due diligence tiers (identification des bénéficiaires effectifs,
          cartographie des risques de corruption et de trafic d'influence).
        - **AMLD6 / LCB-FT** — vérification des bénéficiaires effectifs et personnes politiquement
          exposées (PEP) dans la chaîne de propriété.
        - **Directive Marchés Publics 2014/24/UE** — conflits d'intérêts dans la commande publique.

        **Mode démo** : les données présentées sont synthétiques (aucun appel réseau).
        En production, connectez les API DECP et INPI via les variables d'environnement.

        **Règles de détection** :
        | Règle | Sévérité | Description |
        |---|---|---|
        | `RBE_BENEFICIAL_OWNER_MATCH` | 🔴 CRITICAL | Bénéficiaire effectif PEP identifié |
        | `DECP_VENDOR_IN_PUBLIC_MARKET` | 🟠 HIGH | Fournisseur titulaire d'un marché public |
        | `RBE_OPAQUE_STRUCTURE` | 🟠 HIGH | Structure de propriété opaque / nationalité haute risque |
        """
    )

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

invoices: pd.DataFrame = st.session_state["df_invoices"]

col_settings, col_info = st.columns([2, 1])
with col_settings:
    demo_mode = st.toggle(
        "Mode démo (données synthétiques)",
        value=True,
        help="En mode démo, les données DECP et RBE sont générées localement. "
        "Désactivez pour connecter les APIs réelles.",
    )
    min_score = st.slider("Seuil matching nom fournisseur (RapidFuzz)", 60, 99, 80, 1)

with col_info:
    decp_client = DECPClient(demo_mode=demo_mode)
    rbe_client = RBEClient(demo_mode=demo_mode)
    st.metric("Contrats DECP", f"{decp_client.n_contracts:,}")
    st.metric("Fournisseurs DECP uniques", f"{decp_client.n_unique_vendors:,}")
    st.metric("Bénéficiaires effectifs (RBE)", f"{rbe_client.n_records:,}")

if demo_mode:
    st.info(
        "🔬 **Mode démo actif** — données synthétiques. "
        "Le matching est réalisé sur un sous-ensemble de fournisseurs fictifs. "
        "Activez les APIs réelles pour un croisement sur vos données réelles."
    )

with st.spinner("Croisement DECP / RBE en cours…"):
    findings = detect_decp_rbe(
        invoices,
        decp_client=decp_client,
        rbe_client=rbe_client,
        min_name_score=min_score,
    )

n_critical = sum(1 for f in findings if f.severity.value == "critical")
n_high = sum(1 for f in findings if f.severity.value == "high")
n_decp = sum(1 for f in findings if f.rule_id == "DECP_VENDOR_IN_PUBLIC_MARKET")
n_rbe_pep = sum(1 for f in findings if f.rule_id == "RBE_BENEFICIAL_OWNER_MATCH")
n_rbe_opaque = sum(1 for f in findings if f.rule_id == "RBE_OPAQUE_STRUCTURE")
exposure_total = sum(float(f.evidence.get("exposure_eur") or 0) for f in findings)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Findings CRITICAL (PEP bénéficiaire)", n_critical)
c2.metric("Findings HIGH (marchés publics + opaques)", n_high)
c3.metric("Dont marchés publics DECP", n_decp)
c4.metric("Exposition totale (€)", f"{exposure_total:,.0f}".replace(",", " "))

st.divider()
st.subheader("🚨 Fournisseurs flagués")

if not findings:
    st.success("Aucun finding DECP / RBE pour ce dataset.")
else:
    rows = [
        {
            "invoice_id": f.invoice_id,
            "rule_id": f.rule_id,
            "severity": f.severity.value,
            "vendor_name": f.evidence.get("vendor_name"),
            "siren": f.evidence.get("siren"),
            "exposure_eur": f.evidence.get("exposure_eur"),
            "detail": f.evidence.get("acheteur") or f.evidence.get("pep_owners") or "—",
            "reason": f.evidence.get("reason"),
        }
        for f in findings
    ]
    df_findings = pd.DataFrame(rows).sort_values(
        "exposure_eur", ascending=False, na_position="last"
    )
    st.dataframe(df_findings, use_container_width=True, height=420)
    st.session_state["findings_decp_rbe"] = findings

st.divider()
st.subheader("🏛️ Contrats DECP (référentiel chargé)")
decp_contracts = decp_client._contracts
if decp_contracts:
    df_decp = pd.DataFrame(
        [
            {
                "nom_titulaire": c.nom_titulaire,
                "siren_titulaire": c.siren_titulaire,
                "acheteur": c.acheteur,
                "objet": c.objet,
                "montant_eur": c.montant_eur,
                "date_notification": c.date_notification,
            }
            for c in decp_contracts
        ]
    ).sort_values("montant_eur", ascending=False)
    st.dataframe(df_decp, use_container_width=True, height=320)
    st.caption(f"{len(df_decp):,} contrats DECP dans le référentiel actuel.")
