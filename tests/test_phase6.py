"""Tests Phase 6 — Tour guidé + LLM streaming.

Pas d'appel réseau réel — la fonction streaming Anthropic est mockée
au niveau du SDK pour tester le yielding sans dépendre de la clé API.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from p2p_fraud.i18n import _, _load_catalog, missing_keys, set_locale
from p2p_fraud.llm.narrative_generator import generate_vendor_narrative_stream

# ───────────────────────── i18n tour + llm namespaces ─────────────────────────


def test_tour_namespace_present_in_both_locales() -> None:
    _load_catalog.cache_clear()
    assert missing_keys() == {}
    set_locale("fr")
    assert _("tour.title") == "Tour guidé — bienvenue"
    set_locale("en")
    assert _("tour.title") == "Guided tour — welcome"
    set_locale("fr")


def test_tour_progress_formatting() -> None:
    set_locale("fr")
    assert "2 sur 5" in _("tour.progress", current=2, total=5)
    set_locale("en")
    assert "2 of 5" in _("tour.progress", current=2, total=5)
    set_locale("fr")


def test_llm_namespace_has_required_keys() -> None:
    set_locale("fr")
    for key in ("llm.no_key", "llm.generating", "llm.error_generic"):
        assert _(key) != key, f"clé manquante : {key}"


def test_all_tour_steps_have_title_and_body() -> None:
    set_locale("fr")
    for step in range(1, 6):
        title = _(f"tour.step{step}_title")
        body = _(f"tour.step{step}_body")
        assert title != f"tour.step{step}_title"
        assert body != f"tour.step{step}_body"
        assert len(body) > 50  # non-vide significatif


# ───────────────────────── LLM streaming ──────────────────────────────────────


class _FakeStreamCtx:
    """Mocke `client.messages.stream(...)` qui retourne un context manager."""

    def __init__(self, chunks: list[str]) -> None:
        self.text_stream = iter(chunks)

    def __enter__(self) -> _FakeStreamCtx:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def test_generate_vendor_narrative_stream_yields_chunks(monkeypatch) -> None:
    """Le générateur doit yielder les chunks dans l'ordre du stream."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")

    fake_client = MagicMock()
    fake_client.messages.stream.return_value = _FakeStreamCtx(
        ["Narrative ", "ISA 240 ", "audit complete."]
    )

    with patch("anthropic.Anthropic", return_value=fake_client):
        chunks = list(
            generate_vendor_narrative_stream(
                vendor_id="V001",
                vendor_name="ACME SAS",
                siren="123456789",
                total_paid_eur=15000.0,
                n_invoices=12,
                is_sanctioned=False,
                is_pep=False,
                findings=[],
                api_key="sk-ant-fake",
            )
        )
    assert chunks == ["Narrative ", "ISA 240 ", "audit complete."]


def test_generate_vendor_narrative_stream_passes_correct_args(monkeypatch) -> None:
    """Vérifie que system prompt + user content sont bien construits."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")

    fake_client = MagicMock()
    fake_client.messages.stream.return_value = _FakeStreamCtx(["ok"])
    with patch("anthropic.Anthropic", return_value=fake_client):
        list(
            generate_vendor_narrative_stream(
                vendor_id="V042",
                vendor_name="BTP NORD SARL",
                siren="234567890",
                total_paid_eur=120_000.0,
                n_invoices=8,
                is_sanctioned=True,
                is_pep=True,
                findings=[
                    {
                        "rule_id": "SANCTION_MATCH",
                        "severity": "critical",
                        "signal": "Entité listée OFAC SDN",
                        "exposure_eur": 50_000,
                    }
                ],
                api_key="sk-ant-fake",
            )
        )

    call = fake_client.messages.stream.call_args
    # Vérifie l'enveloppe de l'appel
    assert call.kwargs["model"].startswith("claude-")
    assert call.kwargs["max_tokens"] == 1024
    # System prompt épinglé avec cache_control
    system = call.kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    # User content cite le vendor + les findings critiques
    user_content = call.kwargs["messages"][0]["content"]
    assert "BTP NORD" in user_content
    assert "V042" in user_content
    assert "SANCTION_MATCH" in user_content
    assert "OUI — CRITIQUE" in user_content  # sanctioned


def test_generate_vendor_narrative_stream_requires_api_key() -> None:
    """Sans clé API et sans env var, doit lever ValueError avant le SDK."""
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        # On consomme le générateur — l'erreur survient au premier next()
        list(
            generate_vendor_narrative_stream(
                vendor_id="V001",
                vendor_name="X",
                siren=None,
                total_paid_eur=None,
                n_invoices=0,
                is_sanctioned=False,
                is_pep=False,
                findings=[],
                api_key="",
            )
        )
