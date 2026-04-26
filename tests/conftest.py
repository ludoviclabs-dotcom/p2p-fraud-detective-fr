"""Fixtures partagées — datasets synthétiques avec ground truth."""

from __future__ import annotations

import pandas as pd
import pytest

from p2p_fraud.synthetic.generator import GeneratorConfig, generate_dataset


@pytest.fixture(scope="session")
def small_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = GeneratorConfig(n_invoices=2_000, n_vendors=300, seed=123)
    return generate_dataset(cfg)


@pytest.fixture(scope="session")
def medium_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = GeneratorConfig(n_invoices=10_000, n_vendors=1_000, seed=42)
    return generate_dataset(cfg)
