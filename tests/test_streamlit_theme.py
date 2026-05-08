"""Tests du module de theming Streamlit centralisé."""

from __future__ import annotations

import plotly.io as pio

from p2p_fraud.streamlit_theme.css import CSS, DEMO_VERSION
from p2p_fraud.streamlit_theme.plot import PALETTE, SEMANTIC, register


def test_css_contains_design_tokens() -> None:
    """Les tokens de palette doivent être présents dans le CSS injecté."""
    assert "--c-navy-900:#0F1B33" in CSS
    assert "--c-navy-700:#1F3A6E" in CSS
    assert "--c-gold:#E5A93A" in CSS
    assert "--c-charcoal:#1A1F2C" in CSS


def test_css_hides_streamlit_footer() -> None:
    """Le CSS doit masquer le footer 'Made with Streamlit'."""
    assert "footer" in CSS
    assert "visibility: hidden" in CSS


def test_css_includes_demo_ribbon() -> None:
    """Le ribbon DÉMONSTRATEUR doit être présent avec le numéro de version."""
    assert "ribbon-demo" in CSS
    assert "DÉMONSTRATEUR" in CSS
    assert f"v{DEMO_VERSION}" in CSS


def test_plotly_register_idempotent() -> None:
    """Appeler `register()` plusieurs fois doit rester sans effet de bord."""
    register()
    register()
    assert pio.templates.default == "p2pfd"
    template = pio.templates["p2pfd"]
    assert template.layout.font.family == "Inter, sans-serif"


def test_plotly_palette_navy_first() -> None:
    """La palette dataviz doit commencer par le navy primaire."""
    assert PALETTE[0] == "#1F3A6E"
    assert "#E5A93A" in PALETTE  # gold présent


def test_plotly_semantic_colors_complete() -> None:
    """Les couleurs sémantiques doivent couvrir alert/warn/ok/info/muted."""
    expected_keys = {"alert", "warn", "ok", "info", "muted"}
    assert set(SEMANTIC.keys()) >= expected_keys


def test_demo_version_format() -> None:
    """La version DEMO_VERSION doit suivre un format `<major>.<minor>` minimal."""
    parts = DEMO_VERSION.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts)
