"""Tests presets ERP — Sprint 6."""

from __future__ import annotations

import pandas as pd
import pytest

from p2p_fraud.ingestion.presets import (
    auto_detect_preset,
    list_presets,
    load_preset,
)


def test_list_presets_loads_all_yamls():
    presets = list_presets()
    names = {p.name for p in presets}
    assert {"sap_lfa1_rbkp", "cegid_loop", "sage_x3", "oracle_ap", "generic_csv"}.issubset(names)


def test_load_preset_by_name():
    preset = load_preset("sap_lfa1_rbkp")
    assert preset.name == "sap_lfa1_rbkp"
    assert "BELNR" in preset.signature_columns
    assert preset.mapping["invoice_id"] == "BELNR"


def test_load_preset_unknown_raises():
    with pytest.raises(FileNotFoundError):
        load_preset("does_not_exist")


def test_auto_detect_sap():
    headers = ["LIFNR", "BELNR", "BUKRS", "WRBTR", "BLDAT", "WAERS", "USNAM"]
    preset = auto_detect_preset(headers)
    assert preset is not None
    assert preset.name == "sap_lfa1_rbkp"


def test_auto_detect_cegid():
    headers = [
        "Numéro de facture",
        "Tiers",
        "Date de pièce",
        "Montant TTC",
        "Compte général",
        "Code journal",
    ]
    preset = auto_detect_preset(headers)
    assert preset is not None
    assert preset.name == "cegid_loop"


def test_auto_detect_oracle():
    headers = [
        "INVOICE_ID",
        "VENDOR_ID",
        "INVOICE_NUM",
        "INVOICE_AMOUNT",
        "INVOICE_DATE",
        "INVOICE_CURRENCY_CODE",
    ]
    preset = auto_detect_preset(headers)
    assert preset is not None
    assert preset.name == "oracle_ap"


def test_auto_detect_falls_back_to_generic():
    """Headers déjà au schéma canonique → preset generic_csv."""
    headers = ["invoice_id", "vendor_name", "amount", "invoice_date", "siren"]
    preset = auto_detect_preset(headers)
    assert preset is not None
    assert preset.name == "generic_csv"


def test_auto_detect_returns_none_when_unrecognized():
    headers = ["foo", "bar", "baz", "qux"]
    assert auto_detect_preset(headers) is None


def test_apply_renames_columns_to_canonical():
    preset = load_preset("oracle_ap")
    df = pd.DataFrame(
        [
            {
                "INVOICE_NUM": "INV-1",
                "VENDOR_NAME": "Acme Corp",
                "INVOICE_AMOUNT": "1,234.56",
                "INVOICE_DATE": "2025-06-01",
                "INVOICE_CURRENCY_CODE": "EUR",
            }
        ]
    )
    out = preset.apply(df)
    assert "invoice_id" in out.columns
    assert "vendor_name" in out.columns
    assert "amount" in out.columns
    assert out["invoice_id"].iloc[0] == "INV-1"
    assert out["amount"].iloc[0] == pytest.approx(1234.56)


def test_apply_handles_french_decimal_separator():
    preset = load_preset("cegid_loop")
    df = pd.DataFrame(
        [{"Numéro de facture": "F1", "Montant TTC": "1 234,56", "Date de pièce": "01/06/2025"}]
    )
    out = preset.apply(df)
    assert out["amount"].iloc[0] == pytest.approx(1234.56)


def test_apply_parses_sap_dates_yyyymmdd():
    preset = load_preset("sap_lfa1_rbkp")
    df = pd.DataFrame([{"BELNR": "100", "BLDAT": "20250601", "WRBTR": "1234.56"}])
    out = preset.apply(df)
    from datetime import date

    assert out["invoice_date"].iloc[0] == date(2025, 6, 1)


def test_apply_ignores_missing_source_columns_without_crashing():
    preset = load_preset("sap_lfa1_rbkp")
    df = pd.DataFrame([{"BELNR": "X", "WRBTR": 100.0}])  # tableau partiel
    out = preset.apply(df)
    assert "invoice_id" in out.columns
    assert "amount" in out.columns
    # Champs absents sont… absents (pas d'erreur)
    assert "iban" not in out.columns
    assert "siren" not in out.columns


def test_signature_match_score():
    preset = load_preset("sap_lfa1_rbkp")
    headers = ["LIFNR", "BELNR", "OTHER"]
    assert preset.signature_match_score(headers) == 2
