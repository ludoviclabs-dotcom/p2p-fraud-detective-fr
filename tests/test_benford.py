"""Tests Benford — propriétés mathématiques + scoring sur ground truth."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from p2p_fraud.detectors.benford import (
    _expected_first_digit,
    _expected_first_two_digits,
    _first_digit,
    _first_two_digits,
    _last_digit,
    detect_outlier_invoices,
    run_benford_tests,
)


def test_expected_distributions_sum_to_one():
    assert math.isclose(sum(_expected_first_digit().values()), 1.0, abs_tol=1e-9)
    assert math.isclose(sum(_expected_first_two_digits().values()), 1.0, abs_tol=1e-9)


def test_first_digit_helpers():
    assert _first_digit(1234.56) == 1
    assert _first_digit(0.0078) == 7
    assert _first_digit(0) is None
    assert _first_two_digits(12345) == 12
    assert _first_two_digits(9.99) is None  # < 10
    assert _last_digit(1234.56) == 6
    assert _last_digit(1000.00) == 0


def test_run_benford_tests_on_lognormal():
    """Une distribution log-normale doit être largement Benford-conforme."""
    rng = np.random.default_rng(42)
    amounts = pd.Series(np.exp(rng.normal(7.0, 1.4, size=20_000)).round(2))
    results = run_benford_tests(amounts)
    assert results["F1D"].mad < 0.012  # acceptable ou mieux
    assert results["F1D"].n > 19_000


def test_uniform_amounts_flagged_non_conforming():
    """Une distribution uniforme [1, 1000] viole sévèrement Benford sur F1D."""
    rng = np.random.default_rng(42)
    amounts = pd.Series(rng.uniform(1, 1000, size=20_000).round(2))
    results = run_benford_tests(amounts)
    assert results["F1D"].mad > 0.015
    assert results["F1D"].interpretation == "non_conforming"


@pytest.fixture(scope="module")
def benford_friendly_df() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    n = 5_000
    return pd.DataFrame(
        {
            "invoice_id": [f"INV{i:06d}" for i in range(n)],
            "amount": np.exp(rng.normal(7.0, 1.4, size=n)).round(2),
            "vendor_name": ["ACME"] * n,
            "invoice_date": pd.Timestamp("2025-01-01").date(),
        }
    )


def test_outlier_detection_returns_top_pct(benford_friendly_df):
    findings = detect_outlier_invoices(benford_friendly_df, top_pct=0.01)
    # On peut avoir 0 si rien n'est sur-représenté, ou ≤ 1 % du dataset
    assert len(findings) <= int(len(benford_friendly_df) * 0.012)
