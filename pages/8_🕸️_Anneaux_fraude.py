"""Page Anneaux de fraude — ego-network NetworkX + streamlit-agraph.

Approche ego-network : sélection d'un nœud central, sous-graphe à distance ≤ 2,
plafond 200 nœuds. Coloration : alert pour suspects (composante ≥ cluster_min),
gold pour nœud central, navy pour les autres.
Drill-down : lien vers Fiche fournisseur 360° via ?vendor_id.
"""

from __future__ import annotations

import networkx as nx
import pandas as pd
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

from p2p_fraud.detectors.graph import detect_fraud_rings
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Anneaux de fraude",
    surtitle="Détection ML",
    kicker=("Ego-network NetworkX · drill-down Fiche 360°"),
)
st.caption(
    "Graphe biparti `vendors ⟷ IBAN`. Détection : IBAN partagé entre fournisseurs (CRITICAL) "
    "+ clusters fournisseurs liés par attributs (HIGH). "
    "Ego-network à distance ≤ 2, plafonné à 200 nœuds."
)

if "df_invoices" not in st.session_state:
    st.warning("Aucun dataset chargé. Direction la page **📤 Upload**.")
    st.stop()

df: pd.DataFrame = st.session_state["df_invoices"]

cluster_min_size = st.slider("Taille minimale d'un cluster fournisseurs", 2, 10, 3)

if st.button("🔍 Lancer l'analyse de graphe", type="primary"):
    with st.spinner("Construction du graphe + détection des composantes…"):
        findings, analysis = detect_fraud_rings(df, cluster_min_size=cluster_min_size)
    st.session_state["findings_graph"] = findings
    st.session_state["_graph_analysis"] = analysis
    st.session_state["_graph_cluster_min"] = cluster_min_size

analysis = st.session_state.get("_graph_analysis")
findings = st.session_state.get("findings_graph", [])
cluster_min = st.session_state.get("_graph_cluster_min", cluster_min_size)

if analysis is None:
    st.info("Cliquez sur **Lancer l'analyse** pour construire le graphe.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Anneaux IBAN partagés", analysis.n_shared_iban_rings)
c2.metric("Clusters fournisseurs", analysis.n_vendor_clusters)
c3.metric("Plus gros cluster", analysis.largest_cluster_size)

if not findings:
    st.success("✅ Aucun anneau ni cluster détecté.")
else:
    rows = [
        {
            "invoice_id": f.invoice_id,
            "signal": f.signal,
            "severity": f.severity.value,
            **f.evidence,
        }
        for f in findings
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=240)

st.divider()
st.subheader("🌐 Ego-network interactif")

G: nx.Graph = analysis.graph
all_nodes = list(G.nodes())
if not all_nodes:
    st.info("Graphe vide — aucun lien détecté.")
    st.stop()

# Identifier les composantes suspectes pour coloration
suspicious_nodes: set = set()
for comp in nx.connected_components(G):
    if len(comp) >= max(2, cluster_min):
        suspicious_nodes.update(comp)

# Sélection du nœud central pour l'ego-network
node_labels = [f"{n[0]}: {n[1][:40]}" if isinstance(n, tuple) else str(n) for n in all_nodes]
node_map = {lbl: n for lbl, n in zip(node_labels, all_nodes, strict=True)}

default_central_label = node_labels[0]
if all_nodes:
    # Prioriser un nœud suspect s'il y en a un
    for lbl, n in node_map.items():
        if n in suspicious_nodes:
            default_central_label = lbl
            break

central_label = st.selectbox(
    "Nœud central (ego-network)",
    node_labels,
    index=node_labels.index(default_central_label),
)
central_node = node_map[central_label]

# Extraire l'ego-graph à distance ≤ 2
ego = nx.ego_graph(G, central_node, radius=2)

NODE_CAP = 200
if len(ego.nodes()) > NODE_CAP:
    st.warning(
        f"Le sous-graphe dépasse {NODE_CAP} nœuds ({len(ego.nodes())}). "
        "Augmentez la taille minimale du cluster pour réduire le graphe."
    )
    # Garder les nœuds les plus proches
    ego = nx.ego_graph(G, central_node, radius=1)

# Construire les objets agraph
COLORS = {
    "central": "#E5A93A",   # gold
    "suspect": "#A23E48",   # alert
    "vendor": "#1F3A6E",    # navy
    "iban": "#3E7CB1",      # navy-500
}


def _node_color(n: object) -> str:
    if n == central_node:
        return COLORS["central"]
    if n in suspicious_nodes:
        return COLORS["suspect"]
    if isinstance(n, tuple) and n[0] == "vendor":
        return COLORS["vendor"]
    return COLORS["iban"]


def _node_label(n: object) -> str:
    if isinstance(n, tuple):
        return str(n[1])[:25]
    return str(n)[:25]


agraph_nodes = [
    Node(
        id=str(n),
        label=_node_label(n),
        color=_node_color(n),
        size=20 if n == central_node else 14,
        font={"color": "#FFFFFF", "size": 11},
    )
    for n in ego.nodes()
]
agraph_edges = [
    Edge(source=str(u), target=str(v), color="#9AA3B2", width=1)
    for u, v in ego.edges()
]

config = Config(
    width="100%",
    height=520,
    directed=False,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#E5A93A",
    collapsible=False,
    node={"labelProperty": "label"},
)

if agraph_nodes:
    st.markdown(
        f"**{len(agraph_nodes)} nœuds** · **{len(agraph_edges)} liens** "
        f"· Rayon 2 depuis `{_node_label(central_node)}`"
    )
    clicked = agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)

    # Drill-down : si un nœud vendor est cliqué → lien Fiche 360°
    if clicked:
        # Retrouver le nœud original depuis l'ID stringifié
        id_to_node = {str(n): n for n in ego.nodes()}
        clicked_node = id_to_node.get(clicked)
        if clicked_node and isinstance(clicked_node, tuple) and clicked_node[0] == "vendor":
            vendor_id = clicked_node[1]
            st.info(f"Fournisseur sélectionné : **{vendor_id}**")
            st.page_link(
                "pages/15_🪪_Fiche_fournisseur_360.py",
                label=f"→ Ouvrir la fiche 360° de {vendor_id}",
                icon=":material/account_circle:",
            )
            st.query_params["vendor_id"] = vendor_id

st.divider()
st.caption(
    "🟡 Or = nœud central · 🔴 Rouge = suspect (composante ≥ seuil) · "
    "🔵 Navy = fournisseur non suspect · 🩵 Bleu = IBAN"
)
