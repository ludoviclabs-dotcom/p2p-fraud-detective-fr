"""Page Anneaux de fraude — graphe NetworkX (IBAN partagés, clusters fournisseurs)."""

from __future__ import annotations

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from p2p_fraud.detectors.graph import detect_fraud_rings
from p2p_fraud.streamlit_theme import init_page

init_page(
    title="Anneaux de fraude",
    surtitle="Détection ML",
    kicker=("Graphe NetworkX (employees ⟷ vendors)"),
)
st.caption(
    "Graphe biparti `vendors ⟷ IBAN`. Détection : IBAN partagé entre fournisseurs (CRITICAL) "
    "+ clusters fournisseurs liés par attributs (HIGH)."
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
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=320)

        # Visualisation : on extrait le sous-graphe des anneaux (composantes ≥ 2 vendors)
        st.subheader("🌐 Sous-graphe des composantes flaggées")
        suspicious_components = [
            c for c in nx.connected_components(analysis.graph) if len(c) >= max(2, cluster_min_size)
        ]
        if not suspicious_components:
            st.info("Pas de composante à visualiser.")
        else:
            sub_nodes: set = set()
            for comp in suspicious_components[:20]:  # cap visualisation
                sub_nodes.update(comp)
            subgraph = analysis.graph.subgraph(sub_nodes)
            pos = nx.spring_layout(subgraph, seed=42)

            edge_x: list = []
            edge_y: list = []
            for u, v in subgraph.edges():
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            node_x = [pos[n][0] for n in subgraph.nodes()]
            node_y = [pos[n][1] for n in subgraph.nodes()]
            node_text = [f"{n[0]}: {n[1][:30]}" for n in subgraph.nodes()]
            node_color = ["#7C3AED" if n[0] == "vendor" else "#10B981" for n in subgraph.nodes()]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode="lines",
                    line={"color": "#475569", "width": 1},
                    hoverinfo="none",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=node_x,
                    y=node_y,
                    mode="markers",
                    marker={
                        "color": node_color,
                        "size": 12,
                        "line": {"color": "white", "width": 1},
                    },
                    text=node_text,
                    hoverinfo="text",
                )
            )
            fig.update_layout(
                height=520,
                showlegend=False,
                xaxis={"visible": False},
                yaxis={"visible": False},
                title="Violet = fournisseurs · Vert = IBAN",
            )
            st.plotly_chart(fig, use_container_width=True)
