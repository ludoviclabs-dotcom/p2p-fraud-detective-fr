"""Page Sandbox — 5 scénarios pré-chargés cliquables (P5-2).

Objectif commercial : permettre à un visiteur recruteur / pilote ETI / régalien
de voir la plateforme en action en 60 secondes sans avoir à uploader un CSV.

Chaque scénario :
1. Charge un dataset déterministe (~ 2 000 factures, 150 fournisseurs) ;
2. Pousse les données dans `st.session_state` (clés `df_invoices`, `df_vendors`,
   `df_master_events`) → les autres pages les consomment telles quelles ;
3. Affiche une storyline contextuelle (typologie Tracfin, doctrine ACPR) ;
4. Propose un raccourci direct vers la page la plus pertinente (Fiche 360°,
   Anneaux de fraude, Sous-seuils, etc.).
"""

from __future__ import annotations

import streamlit as st

from p2p_fraud.streamlit_theme import init_page
from p2p_fraud.synthetic.scenarios import (
    SCENARIOS,
    get_scenario_meta,
    list_scenarios,
    load_scenario,
)

init_page(
    title="Sandbox commerciale",
    surtitle="Pilotage",
    kicker="5 scénarios cliquables — démos institutionnelles en 60 secondes",
)

st.markdown(
    """
    Cette sandbox permet de **démontrer la plateforme en moins d'une minute**
    sans uploader de fichier. Chaque scénario amplifie un pattern de fraude
    pour que le détecteur correspondant remonte clairement.

    Les données sont synthétiques (Faker `fr_FR` + injections déterministes).
    Aucune PII réelle, conformité RGPD assurée. Reproductibles à seed fixé.
    """
)

st.divider()

# ── 1. Sélecteur de scénario ──────────────────────────────────────────────────
metas = list_scenarios()
labels = [f"🎯 {m.title}" for m in metas]
default_idx = 0
if "sandbox_selected" in st.session_state:
    try:
        default_idx = [m.name for m in metas].index(st.session_state["sandbox_selected"])
    except ValueError:
        default_idx = 0

choice = st.radio(
    "Scénario à charger",
    options=labels,
    index=default_idx,
    horizontal=False,
)
selected = metas[labels.index(choice)]
st.session_state["sandbox_selected"] = selected.name

# ── 2. Storyline et métadonnées ───────────────────────────────────────────────
col_meta, col_action = st.columns([3, 1])
with col_meta:
    severity_color = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(selected.severity, "🔵")
    st.markdown(
        f"### {severity_color} {selected.title}\n"
        f"**Pilier** : {selected.pillar} · **Sévérité attendue** : {selected.severity.upper()}\n\n"
        f"{selected.storyline}\n\n"
        f"**Détecteurs déclenchés** : {', '.join(f'`{d}`' for d in selected.detectors)}"
    )
    if selected.target_vendor:
        st.caption(f"Fournisseur cible : `{selected.target_vendor}`")

with col_action:
    if st.button("▶️ Charger le scénario", type="primary", use_container_width=True):
        with st.spinner("Génération en cours…"):
            invoices, vendors, events = load_scenario(selected.name)
        st.session_state["df_invoices"] = invoices
        st.session_state["df_vendors"] = vendors
        st.session_state["df_master_events"] = events
        st.session_state["sandbox_loaded"] = selected.name
        st.toast(
            f"Scénario « {selected.title} » chargé — {len(invoices)} factures",
            icon="🎮",
        )

# ── 3. Si scénario chargé, montrer les raccourcis vers les pages utiles ──────
if st.session_state.get("sandbox_loaded") == selected.name:
    st.success(
        f"✅ Scénario actif : **{selected.title}** "
        f"({len(st.session_state['df_invoices'])} factures, "
        f"{len(st.session_state['df_vendors'])} fournisseurs, "
        f"{len(st.session_state['df_master_events'])} événements master data)"
    )

    st.markdown("#### 🚀 Raccourcis vers les pages pertinentes")
    cols = st.columns(min(4, len(selected.detectors) + 2))

    page_map = {
        "master_data_changes": ("pages/3_🏦_Master_data_history.py", "🏦 Master data history"),
        "under_thresholds": ("pages/5_📏_Sous_seuils.py", "📏 Fractionnement"),
        "duplicates": ("pages/4_♊_Doublons.py", "♊ Doublons"),
        "network_rings": ("pages/8_🕸️_Anneaux_fraude.py", "🕸️ Anneaux de fraude"),
        "shell_companies": ("pages/8_🕸️_Anneaux_fraude.py", "🕸️ Anneaux de fraude"),
        "sanctions": ("pages/9_⚖️_Sanctions_PEP.py", "⚖️ Sanctions & PEP"),
        "pep": ("pages/9_⚖️_Sanctions_PEP.py", "⚖️ Sanctions & PEP"),
        "benford": ("pages/2_🔢_Benford.py", "🔢 Loi de Benford"),
        "score_explorer": ("pages/14_💡_Score_explorer.py", "💡 Score explorer"),
    }
    shown: set[str] = set()
    col_idx = 0
    for detector in selected.detectors:
        if detector not in page_map:
            continue
        page_path, label = page_map[detector]
        if page_path in shown:
            continue
        shown.add(page_path)
        with cols[col_idx % len(cols)]:
            st.page_link(page_path, label=label, icon="➡️")
        col_idx += 1
    with cols[col_idx % len(cols)]:
        st.page_link("pages/0_🎯_Cockpit.py", label="🎯 Cockpit", icon="🏠")
    if selected.target_vendor:
        with cols[(col_idx + 1) % len(cols)]:
            st.page_link(
                "pages/15_🪪_Fiche_fournisseur_360.py",
                label=f"🪪 Fiche {selected.target_vendor}",
                icon="🔍",
            )

st.divider()

# ── 4. Vue d'ensemble des scénarios disponibles ───────────────────────────────
with st.expander("📋 Vue d'ensemble des 5 scénarios"):
    rows = []
    for m in list_scenarios():
        rows.append(
            {
                "Scénario": m.title,
                "Pilier": m.pillar,
                "Sévérité": m.severity.upper(),
                "Cible": m.target_vendor or "—",
                "Détecteurs": ", ".join(m.detectors),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

st.caption(
    "💡 **Cas pédagogiques inspirés du rapport Tracfin 2024-2025 Tome III** — "
    "données 100 % synthétiques, non transmissibles à Tracfin. "
    "Pour activer les sources live (DECP / Pappers / OpenSanctions), définir "
    "`ENRICHMENT_MODE=live` — voir [`docs/sources_de_donnees.md`]"
    "(https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/docs/sources_de_donnees.md)."
)

# Garantit que SCENARIOS reste exporté (utile en tests d'intégration)
_ = get_scenario_meta(selected.name)
_ = SCENARIOS
