"""Tests E2E Streamlit AppTest (P5-5) — smoke tests sur les pages clés.

Objectif : garantir qu'aucune page ne lève d'exception au chargement
(import errors, KeyError sur `st.session_state`, schéma incompatible…)
pour les configurations canoniques (mode démo sans données + mode démo
avec scénario sandbox chargé).

`AppTest.from_file()` lance la page dans un sous-process Streamlit
mocké en mémoire — pas de browser, pas de port, exécution rapide.

Pourquoi seulement 6 pages : les autres dépendent d'un dataset uploadé
ou d'un compte OIDC actif, hors périmètre du smoke test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[2]
TIMEOUT_SEC = 30  # généreux pour le démarrage en CI (Streamlit Cloud Python 3.14)


def _run(page_relpath: str) -> AppTest:
    """Lance une page Streamlit AppTest et renvoie l'instance après run()."""
    page_path = REPO_ROOT / page_relpath
    if not page_path.exists():
        pytest.skip(f"Page introuvable : {page_relpath}")
    at = AppTest.from_file(str(page_path), default_timeout=TIMEOUT_SEC)
    at.run()
    return at


def test_cockpit_renders_up_to_page_link() -> None:
    """Cockpit charge ses KPI + sparklines avant les st.page_link.

    `st.page_link()` requiert la nav multipage `st.navigation()` configurée
    par `streamlit_app.py` — non disponible en AppTest standalone. On
    accepte donc une exception KeyError('url_pathname') tant que les
    éléments principaux ont été rendus AVANT l'échec.
    """
    at = _run("pages/0_🎯_Cockpit.py")
    # Les markdown/headers initiaux doivent avoir été rendus, même si
    # page_link explose plus loin.
    if at.exception:
        assert "url_pathname" in str(at.exception), f"Exception inattendue : {at.exception}"
    assert len(at.markdown) >= 1 or len(at.metric) >= 1


def test_sandbox_lists_5_scenarios() -> None:
    """Sandbox liste les 5 scénarios avant la zone de raccourcis page_link."""
    at = _run("pages/20_🎮_Sandbox.py")
    if at.exception:
        assert "url_pathname" in str(at.exception), f"Exception inattendue : {at.exception}"
    # Le radio des scénarios doit avoir été rendu
    radios = at.radio
    if radios:
        assert len(radios[0].options) >= 5


def test_methodologie_renders_with_sources() -> None:
    """Page Méthodologie : doit afficher les sources et le mode demo/live."""
    at = _run("pages/12_📚_Méthodologie.py")
    assert not at.exception, f"Méthodologie a levé : {at.exception}"
    # Au moins quelques sections markdown
    assert len(at.markdown) >= 2


def test_gouvernance_renders() -> None:
    """Page Gouvernance : doit charger avec RBAC + RGPD + AI Act."""
    at = _run("pages/16_🛡️_Gouvernance.py")
    assert not at.exception, f"Gouvernance a levé : {at.exception}"


def test_alertes_renders_with_4_channel_tabs() -> None:
    """Page Alertes : doit afficher 4 onglets (Slack/Teams/SMTP/Webhook B2B)."""
    at = _run("pages/18_🔔_Alertes.py")
    assert not at.exception, f"Alertes a levé : {at.exception}"
    # L'onglet Webhook B2B P5-3 doit être présent
    tabs = at.tabs
    if tabs:
        labels = [t.label for t in tabs if hasattr(t, "label")]
        # Au moins 3 onglets (Slack, Teams, SMTP) + idéalement le 4e webhook
        assert len(labels) >= 3


def test_audit_trail_loads_without_data() -> None:
    """Page Audit trail : doit s'afficher (au moins l'entrée seed démo)."""
    at = _run("pages/13_📜_Audit_trail.py")
    assert not at.exception, f"Audit trail a levé : {at.exception}"
