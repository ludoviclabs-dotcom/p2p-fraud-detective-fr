"""Fixtures partagées pour les tests E2E Streamlit (P5-5)."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def small_invoices_df() -> pd.DataFrame:
    """Mini-dataset 30 factures pour smoke E2E rapide."""
    return pd.DataFrame(
        {
            "invoice_id": [f"INV-{i:03d}" for i in range(30)],
            "vendor_id": [f"V{i % 5:03d}" for i in range(30)],
            "vendor_name": [f"VENDOR {i % 5}" for i in range(30)],
            "amount": [1000.0 + i * 50 for i in range(30)],
            "currency": ["EUR"] * 30,
            "invoice_date": pd.date_range("2026-01-01", periods=30, freq="D"),
        }
    )
