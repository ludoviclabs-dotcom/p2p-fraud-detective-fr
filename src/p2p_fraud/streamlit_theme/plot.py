"""Template Plotly et palette dataviz unifiés (`p2pfd`).

Appel `register()` une fois par session — idempotent. Toutes les figures Plotly
créées ensuite hériteront du theme par défaut.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

PALETTE = [
    "#1F3A6E",  # navy 700
    "#E5A93A",  # gold
    "#3E7CB1",  # navy 500
    "#A23E48",  # alert
    "#5A6478",  # slate
    "#7BA17F",  # vert sobre
    "#B07FA3",  # mauve sobre
    "#C7C9D1",  # gris clair
]

SEMANTIC = {
    "alert": "#A23E48",
    "warn": "#E5A93A",
    "ok": "#3E7C5A",
    "info": "#3E7CB1",
    "muted": "#9AA3B2",
}


def register() -> None:
    """Enregistre le template Plotly `p2pfd` et le pose comme défaut."""
    pio.templates["p2pfd"] = go.layout.Template(
        layout=dict(
            font=dict(family="Inter, sans-serif", color="#1A1F2C"),
            colorway=PALETTE,
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(gridcolor="#E1E5EE", linecolor="#9AA3B2"),
            yaxis=dict(gridcolor="#E1E5EE", linecolor="#9AA3B2"),
            margin=dict(l=40, r=20, t=40, b=40),
        )
    )
    pio.templates.default = "p2pfd"
