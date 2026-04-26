"""Détecteur Loi de Newcomb-Benford.

Référence : Nigrini, *Benford's Law: Applications for Forensic Accounting,
Auditing, and Fraud Detection* (Wiley, 2012).

Trois tests :
- Premier chiffre (F1D) — détection grossière
- Deux premiers chiffres (F2D) — test le plus diagnostique en audit (Nigrini)
- Dernier chiffre (LD) — uniformément distribué dans le monde réel

Interprétation MAD (Mean Absolute Deviation) — seuils Nigrini :
| Test | Conforme | Acceptable | Marginalement | Non-conforme |
|------|----------|------------|---------------|--------------|
| F1D  | < 0.006  | 0.006-0.012| 0.012-0.015   | > 0.015      |
| F2D  | < 0.0012 | 0.0012-0.0018 | 0.0018-0.0022 | > 0.0022 |
| LD   | < 0.0008 | 0.0008-0.0012 | 0.0012-0.0016 | > 0.0016 |
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats

from p2p_fraud.schema import Finding, Severity


@dataclass(frozen=True)
class BenfordTest:
    name: Literal["F1D", "F2D", "LD"]
    digits_observed: dict[int, float]  # frequence relative observée
    digits_expected: dict[int, float]
    chi2: float
    chi2_p_value: float
    mad: float  # Mean Absolute Deviation
    n: int  # taille de l'échantillon utilisé
    interpretation: Literal["conforming", "acceptable", "marginal", "non_conforming"]


# Seuils Nigrini sur le MAD
_MAD_THRESHOLDS: dict[str, tuple[float, float, float]] = {
    "F1D": (0.006, 0.012, 0.015),
    "F2D": (0.0012, 0.0018, 0.0022),
    "LD": (0.0008, 0.0012, 0.0016),
}


def _expected_first_digit() -> dict[int, float]:
    return {d: math.log10(1 + 1 / d) for d in range(1, 10)}


def _expected_first_two_digits() -> dict[int, float]:
    return {d: math.log10(1 + 1 / d) for d in range(10, 100)}


def _expected_last_digit() -> dict[int, float]:
    return {d: 1 / 10 for d in range(0, 10)}


def _interpret_mad(test: str, mad: float) -> str:
    low, mid, high = _MAD_THRESHOLDS[test]
    if mad < low:
        return "conforming"
    if mad < mid:
        return "acceptable"
    if mad < high:
        return "marginal"
    return "non_conforming"


def _first_digit(amount: float) -> int | None:
    if amount <= 0:
        return None
    s = f"{amount:.10f}".lstrip("0").lstrip(".")
    for c in s:
        if c.isdigit() and c != "0":
            return int(c)
    return None


def _first_two_digits(amount: float) -> int | None:
    if amount < 10:
        return None
    digits = "".join(c for c in f"{amount:.0f}" if c.isdigit())
    digits = digits.lstrip("0")
    if len(digits) < 2:
        return None
    return int(digits[:2])


def _last_digit(amount: float) -> int | None:
    """Dernier chiffre significatif (avant le séparateur décimal — partie entière en centimes)."""
    cents = round(amount * 100)
    if cents <= 0:
        return None
    return cents % 10


def _run_test(
    digits_obs: list[int],
    expected: dict[int, float],
    test_name: Literal["F1D", "F2D", "LD"],
) -> BenfordTest:
    n = len(digits_obs)
    if n == 0:
        return BenfordTest(test_name, {}, expected, 0.0, 1.0, 0.0, 0, "conforming")

    counts = pd.Series(digits_obs).value_counts()
    observed_freq: dict[int, float] = {d: counts.get(d, 0) / n for d in expected}

    observed_counts = np.array([counts.get(d, 0) for d in sorted(expected)], dtype=float)
    expected_counts = np.array([expected[d] for d in sorted(expected)], dtype=float)
    # Renormalise pour que sum(expected) == sum(observed) à epsilon machine près
    # (scipy.stats.chisquare exige cette égalité stricte).
    expected_counts = expected_counts / expected_counts.sum() * observed_counts.sum()

    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)

    mad = float(np.mean([abs(observed_freq[d] - expected[d]) for d in expected]))
    interpretation = _interpret_mad(test_name, mad)

    return BenfordTest(
        name=test_name,
        digits_observed=observed_freq,
        digits_expected=expected,
        chi2=float(chi2_stat),
        chi2_p_value=float(p_value),
        mad=mad,
        n=n,
        interpretation=interpretation,  # type: ignore[arg-type]
    )


def run_benford_tests(amounts: pd.Series) -> dict[str, BenfordTest]:
    """Exécute les 3 tests sur une série de montants."""
    f1 = [d for d in amounts.map(_first_digit).tolist() if d is not None]
    f2 = [d for d in amounts.map(_first_two_digits).tolist() if d is not None]
    ld = [d for d in amounts.map(_last_digit).tolist() if d is not None]
    return {
        "F1D": _run_test(f1, _expected_first_digit(), "F1D"),
        "F2D": _run_test(f2, _expected_first_two_digits(), "F2D"),
        "LD": _run_test(ld, _expected_last_digit(), "LD"),
    }


# Sévérité d'une déviation Benford par interprétation
_SEVERITY_FROM_INTERP: dict[str, Severity] = {
    "conforming": Severity.LOW,
    "acceptable": Severity.LOW,
    "marginal": Severity.MEDIUM,
    "non_conforming": Severity.HIGH,
}


def detect_outlier_invoices(
    df: pd.DataFrame,
    *,
    test_name: Literal["F1D", "F2D"] = "F2D",
    top_pct: float = 0.01,
    min_amount: float = 10.0,
) -> list[Finding]:
    """Identifie les factures dont le premier ou les 2 premiers chiffres sont les plus
    sur-représentés dans le dataset par rapport à Benford.

    Stratégie : pour chaque chiffre suspect (observed >> expected), on flagge les factures
    portant ce chiffre, en proportion `top_pct` du dataset (priorité aux montants élevés).
    """
    if "amount" not in df.columns:
        return []
    amounts = df["amount"].astype(float)
    valid = amounts >= min_amount
    if not valid.any():
        return []
    test_results = run_benford_tests(amounts[valid])
    test = test_results[test_name]

    deviations = {
        d: test.digits_observed.get(d, 0) - test.digits_expected[d] for d in test.digits_expected
    }
    suspicious_digits = [d for d, dev in deviations.items() if dev > 0]
    if not suspicious_digits:
        return []

    extractor = _first_digit if test_name == "F1D" else _first_two_digits
    digit_col = df["amount"].map(extractor)

    target = max(1, int(len(df) * top_pct))
    candidates = df.loc[digit_col.isin(suspicious_digits) & valid].copy()
    if candidates.empty:
        return []
    candidates = candidates.sort_values("amount", ascending=False).head(target)

    severity = _SEVERITY_FROM_INTERP[test.interpretation]
    findings: list[Finding] = []
    for _, row in candidates.iterrows():
        digit_value = extractor(float(row["amount"]))
        findings.append(
            Finding(
                invoice_id=str(row["invoice_id"]),
                detector="benford",
                signal=f"benford_anomaly_{test_name.lower()}",
                severity=severity,
                rule_id=f"BENFORD_{test_name}",
                evidence={
                    "test": test_name,
                    "digit_value": digit_value,
                    "observed_freq": round(test.digits_observed.get(digit_value, 0), 5)
                    if digit_value
                    else None,
                    "expected_freq": round(test.digits_expected.get(digit_value, 0), 5)
                    if digit_value
                    else None,
                    "mad": round(test.mad, 5),
                    "interpretation": test.interpretation,
                },
            )
        )
    return findings
