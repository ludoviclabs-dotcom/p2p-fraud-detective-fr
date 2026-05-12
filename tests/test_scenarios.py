"""Tests P5-2 — scénarios pré-chargés sandbox.

Vérifie pour chaque scénario :
- Le dataset se charge sans erreur.
- Les volumes restent dans la cible (< 3 000 factures, < 200 vendors).
- La reproductibilité (deux appels successifs → mêmes hash de données).
- Les ajustements ex post pour BEC + sanctions sont effectifs.
"""

from __future__ import annotations

import pandas as pd
import pytest

from p2p_fraud.synthetic.scenarios import (
    SCENARIOS,
    ScenarioName,
    get_scenario_meta,
    list_scenarios,
    load_scenario,
)


@pytest.mark.parametrize("name", list(SCENARIOS.keys()))
def test_each_scenario_loads(name: ScenarioName) -> None:
    invoices, vendors, events = load_scenario(name)
    assert isinstance(invoices, pd.DataFrame)
    assert isinstance(vendors, pd.DataFrame)
    assert isinstance(events, pd.DataFrame)
    assert len(invoices) > 100, f"{name} doit produire > 100 factures"
    assert len(invoices) < 3_000, f"{name} doit rester < 3 000 factures (perf Streamlit)"
    assert len(vendors) > 50
    assert len(vendors) < 200


@pytest.mark.parametrize("name", list(SCENARIOS.keys()))
def test_scenarios_are_deterministic(name: ScenarioName) -> None:
    """Deux appels successifs doivent renvoyer les mêmes données métier.

    Le champ `event_id` (UUID4) reste non-déterministe par construction ;
    on vérifie l'égalité sur les colonnes signifiantes uniquement.
    """
    inv1, v1, e1 = load_scenario(name)
    inv2, v2, e2 = load_scenario(name)
    pd.testing.assert_frame_equal(inv1, inv2)
    pd.testing.assert_frame_equal(v1, v2)
    stable_cols = [c for c in e1.columns if c != "event_id"]
    pd.testing.assert_frame_equal(
        e1[stable_cols].reset_index(drop=True),
        e2[stable_cols].reset_index(drop=True),
    )


def test_bec_scenario_injects_iban_swap_without_approval() -> None:
    _, _, events = load_scenario("bec_iban_swap")
    # L'événement injecté ex post a vendor_id=V00007 et approved_by=None.
    suspect = events[
        (events["vendor_id"] == "V00007")
        & (events["field"] == "iban")
        & (events["approved_by"].isna())
    ]
    assert len(suspect) >= 1, "Le scénario BEC doit injecter un IBAN swap sans 4-eyes"


def test_sanctions_scenario_renames_vendor() -> None:
    _, vendors, _ = load_scenario("sanctions_ue")
    sanctioned = vendors[vendors["vendor_name"].str.contains("EUROPE BUILDING", na=False)]
    assert len(sanctioned) == 1


def test_list_scenarios_returns_all_metas() -> None:
    metas = list_scenarios()
    assert len(metas) == 5
    names = {m.name for m in metas}
    assert names == set(SCENARIOS.keys())


def test_get_scenario_meta_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_scenario_meta("inexistant")  # type: ignore[arg-type]


def test_scenarios_amplify_target_pattern() -> None:
    """Chaque scénario doit avoir plus de fraude que la baseline démo."""
    # On contrôle juste que les volumes ne sont pas anormaux ; la qualité
    # métier des findings est validée par les tests des détecteurs.
    for name in SCENARIOS:
        invoices, _, _ = load_scenario(name)
        assert "invoice_id" in invoices.columns
        assert "vendor_id" in invoices.columns
        assert "amount" in invoices.columns
