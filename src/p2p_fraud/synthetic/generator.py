"""Générateur de dataset synthétique de factures avec patterns de fraude étiquetés.

Le ground truth (`is_fraud`, `fraud_type`) permet d'évaluer F1 par détecteur.
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker


class FraudType(StrEnum):
    NONE = "none"
    DUPLICATE_EXACT = "duplicate_exact"
    DUPLICATE_FUZZY = "duplicate_fuzzy"
    UNDER_THRESHOLD = "under_threshold"
    SHELL_COMPANY = "shell_company"
    SHARED_IBAN_RING = "shared_iban_ring"
    AMOUNT_OUTLIER = "amount_outlier"
    WEEKEND_UNUSUAL_USER = "weekend_unusual_user"


@dataclass
class GeneratorConfig:
    n_invoices: int = 50_000
    n_vendors: int = 5_000
    n_users: int = 100
    n_accountants: int = 30  # Sous-ensemble d'utilisateurs habilités à passer des écritures
    period_months: int = 24
    end_date: date = date(2025, 12, 31)
    seed: int = 42

    # Taux d'injection (proportions du dataset)
    rate_duplicate_exact: float = 0.003
    rate_duplicate_fuzzy: float = 0.005
    rate_under_threshold: float = 0.010
    rate_shell_company: float = 0.002
    rate_shared_iban_ring: float = 0.005
    rate_amount_outlier: float = 0.005
    rate_weekend_unusual_user: float = 0.001

    # Seuils de validation paramétrables
    thresholds: tuple[int, ...] = (1_000, 5_000, 10_000, 25_000, 50_000)


_LEGAL_FORMS = ["SARL", "SAS", "SA", "EURL", "SASU", "SCI"]


def _random_iban(faker: Faker, country: str = "FR") -> str:
    return (
        faker.iban()
        if hasattr(faker, "iban")
        else f"{country}76{faker.random_number(digits=21, fix_len=True)}"
    )


def _random_siren(rng: random.Random) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(9))


def _build_vendor_master(cfg: GeneratorConfig, rng: random.Random, faker: Faker) -> pd.DataFrame:
    rows = []
    earliest_creation = cfg.end_date - timedelta(days=365 * 30)
    for i in range(cfg.n_vendors):
        base = faker.company()
        legal = rng.choice(_LEGAL_FORMS)
        name = f"{base} {legal}"
        creation = faker.date_between(start_date=earliest_creation, end_date=cfg.end_date)
        rows.append(
            {
                "vendor_id": f"V{i:05d}",
                "siren": _random_siren(rng),
                "vendor_name": name,
                "iban": _random_iban(faker),
                "address": faker.address().replace("\n", ", "),
                "ape_code": rng.choice(["6201Z", "4669A", "4799B", "4321A", "5510Z", "8299Z"]),
                "creation_date": creation,
                "is_active": True,
            }
        )
    return pd.DataFrame(rows)


def _normal_amount(rng: random.Random) -> float:
    """Distribution log-normale grossièrement Benford-conforme."""
    return round(math.exp(rng.gauss(7.0, 1.4)), 2)


def _date_in_period(cfg: GeneratorConfig, faker: Faker) -> date:
    start = cfg.end_date - timedelta(days=30 * cfg.period_months)
    return faker.date_between(start_date=start, end_date=cfg.end_date)


def _generate_clean(
    cfg: GeneratorConfig,
    vendors: pd.DataFrame,
    accountant_ids: list[str],
    rng: random.Random,
    faker: Faker,
    n: int,
) -> list[dict]:
    rows = []
    vendor_arr = vendors.to_dict("records")
    for i in range(n):
        v = rng.choice(vendor_arr)
        d = _date_in_period(cfg, faker)
        rows.append(
            {
                "invoice_id": f"INV{i:08d}",
                "siren": v["siren"],
                "vendor_name": v["vendor_name"],
                "iban": v["iban"],
                "amount": _normal_amount(rng),
                "currency": "EUR",
                "invoice_date": d,
                "posting_date": d + timedelta(days=rng.randint(0, 7)),
                "po_number": f"PO{rng.randint(100000, 999999)}" if rng.random() > 0.1 else None,
                "user_id": rng.choice(accountant_ids),
                "cost_center": f"CC{rng.randint(100, 999)}",
                "gl_account": rng.choice(
                    ["6061", "6063", "6065", "6068", "6132", "6135", "6181", "6228"]
                ),
                "is_fraud": False,
                "fraud_type": FraudType.NONE.value,
            }
        )
    return rows


def _inject_duplicates_exact(
    rows: list[dict], n_pairs: int, next_id: int, rng: random.Random
) -> int:
    for _ in range(n_pairs):
        src = rng.choice(rows)
        clone = dict(src)
        clone["invoice_id"] = f"INV{next_id:08d}"
        next_id += 1
        clone["is_fraud"] = True
        clone["fraud_type"] = FraudType.DUPLICATE_EXACT.value
        rows.append(clone)
    return next_id


def _inject_duplicates_fuzzy(
    rows: list[dict], n_pairs: int, next_id: int, rng: random.Random
) -> int:
    """Doublon avec variations cosmétiques sur le nom du fournisseur."""
    for _ in range(n_pairs):
        src = rng.choice(rows)
        clone = dict(src)
        clone["invoice_id"] = f"INV{next_id:08d}"
        next_id += 1
        # Variation : remplacer "SARL" par "S.A.R.L." ou ajouter un espace
        original_name = clone["vendor_name"]
        for legal in _LEGAL_FORMS:
            if legal in original_name:
                varied = original_name.replace(legal, ".".join(legal) + ".")
                clone["vendor_name"] = varied
                break
        else:
            clone["vendor_name"] = original_name + " "
        clone["amount"] = round(clone["amount"] + rng.uniform(-0.5, 0.5), 2)
        clone["invoice_date"] = clone["invoice_date"] + timedelta(days=rng.randint(-2, 2))
        clone["is_fraud"] = True
        clone["fraud_type"] = FraudType.DUPLICATE_FUZZY.value
        rows.append(clone)
    return next_id


def _inject_under_threshold(
    rows: list[dict], n: int, thresholds: tuple[int, ...], next_id: int, rng: random.Random
) -> int:
    """Factures clusterisées juste sous un seuil de validation."""
    base_invoice = rng.choice(rows)
    for _ in range(n):
        threshold = rng.choice(thresholds)
        clone = dict(base_invoice)
        clone["invoice_id"] = f"INV{next_id:08d}"
        next_id += 1
        clone["amount"] = round(threshold - rng.uniform(1, threshold * 0.015), 2)
        clone["is_fraud"] = True
        clone["fraud_type"] = FraudType.UNDER_THRESHOLD.value
        rows.append(clone)
    return next_id


def _inject_shell_companies(
    rows: list[dict], n: int, vendors: pd.DataFrame, next_id: int, rng: random.Random, faker: Faker
) -> int:
    """Fournisseurs avec SIREN inexistant ou créés peu avant la 1ère facture."""
    for _ in range(n):
        clone = dict(rng.choice(rows))
        clone["invoice_id"] = f"INV{next_id:08d}"
        next_id += 1
        if rng.random() < 0.5:
            clone["siren"] = "000000000"  # SIREN inexistant
        else:
            clone["siren"] = _random_siren(rng)  # nouveau, pas dans master
        clone["vendor_name"] = faker.company() + " " + rng.choice(_LEGAL_FORMS)
        clone["amount"] = round(rng.uniform(800, 8000), 2)
        clone["is_fraud"] = True
        clone["fraud_type"] = FraudType.SHELL_COMPANY.value
        rows.append(clone)
    return next_id


def _inject_shared_iban_rings(
    rows: list[dict],
    n_rings: int,
    vendors: pd.DataFrame,
    next_id: int,
    rng: random.Random,
    faker: Faker,
) -> int:
    """Anneaux : 3-5 fournisseurs partageant le même IBAN."""
    for _ in range(n_rings):
        ring_size = rng.randint(3, 5)
        shared_iban = _random_iban(faker)
        for _ in range(ring_size):
            base = dict(rng.choice(rows))
            base["invoice_id"] = f"INV{next_id:08d}"
            next_id += 1
            base["siren"] = _random_siren(rng)
            base["vendor_name"] = faker.company() + " " + rng.choice(_LEGAL_FORMS)
            base["iban"] = shared_iban
            base["amount"] = round(rng.uniform(2000, 50000), 2)
            base["is_fraud"] = True
            base["fraud_type"] = FraudType.SHARED_IBAN_RING.value
            rows.append(base)
    return next_id


def _inject_amount_outliers(rows: list[dict], n: int, next_id: int, rng: random.Random) -> int:
    """Montants 50× supérieurs à la médiane du fournisseur."""
    by_vendor: dict[str, list[float]] = {}
    for r in rows:
        by_vendor.setdefault(r["vendor_name"], []).append(r["amount"])
    candidates = [(v, np.median(amts)) for v, amts in by_vendor.items() if len(amts) >= 3]
    if not candidates:
        return next_id
    for _ in range(n):
        vendor_name, median_amt = rng.choice(candidates)
        ref = next(r for r in rows if r["vendor_name"] == vendor_name)
        clone = dict(ref)
        clone["invoice_id"] = f"INV{next_id:08d}"
        next_id += 1
        clone["amount"] = round(float(median_amt) * rng.uniform(40, 80), 2)
        clone["is_fraud"] = True
        clone["fraud_type"] = FraudType.AMOUNT_OUTLIER.value
        rows.append(clone)
    return next_id


def _inject_weekend_unusual_user(
    rows: list[dict],
    n: int,
    all_user_ids: list[str],
    accountant_ids: set[str],
    next_id: int,
    rng: random.Random,
) -> int:
    """Écritures week-end passées par un utilisateur non-comptable."""
    non_accountants = [u for u in all_user_ids if u not in accountant_ids]
    if not non_accountants:
        return next_id
    for _ in range(n):
        clone = dict(rng.choice(rows))
        clone["invoice_id"] = f"INV{next_id:08d}"
        next_id += 1
        d: date = clone["invoice_date"]
        offset = (5 - d.weekday()) % 7  # 5 = samedi
        clone["invoice_date"] = d + timedelta(days=offset)
        clone["posting_date"] = clone["invoice_date"]
        clone["user_id"] = rng.choice(non_accountants)
        clone["amount"] = round(rng.uniform(10_000, 200_000), 2)
        clone["is_fraud"] = True
        clone["fraud_type"] = FraudType.WEEKEND_UNUSUAL_USER.value
        rows.append(clone)
    return next_id


def generate_dataset(cfg: GeneratorConfig | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Génère (invoices, vendors) avec ground truth de fraude."""
    cfg = cfg or GeneratorConfig()
    rng = random.Random(cfg.seed)
    np.random.seed(cfg.seed)
    faker = Faker("fr_FR")
    Faker.seed(cfg.seed)

    vendors = _build_vendor_master(cfg, rng, faker)

    all_user_ids = [f"U{i:03d}" for i in range(cfg.n_users)]
    accountant_ids = all_user_ids[: cfg.n_accountants]
    accountants_set = set(accountant_ids)

    n_clean = cfg.n_invoices
    rows = _generate_clean(cfg, vendors, accountant_ids, rng, faker, n_clean)
    next_id = n_clean

    next_id = _inject_duplicates_exact(
        rows, int(cfg.n_invoices * cfg.rate_duplicate_exact), next_id, rng
    )
    next_id = _inject_duplicates_fuzzy(
        rows, int(cfg.n_invoices * cfg.rate_duplicate_fuzzy), next_id, rng
    )
    next_id = _inject_under_threshold(
        rows, int(cfg.n_invoices * cfg.rate_under_threshold), cfg.thresholds, next_id, rng
    )
    next_id = _inject_shell_companies(
        rows, int(cfg.n_invoices * cfg.rate_shell_company), vendors, next_id, rng, faker
    )
    next_id = _inject_shared_iban_rings(
        rows,
        max(1, int(cfg.n_invoices * cfg.rate_shared_iban_ring / 4)),
        vendors,
        next_id,
        rng,
        faker,
    )
    next_id = _inject_amount_outliers(
        rows, int(cfg.n_invoices * cfg.rate_amount_outlier), next_id, rng
    )
    next_id = _inject_weekend_unusual_user(
        rows,
        int(cfg.n_invoices * cfg.rate_weekend_unusual_user),
        all_user_ids,
        accountants_set,
        next_id,
        rng,
    )

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=cfg.seed).reset_index(drop=True)
    return df, vendors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère un dataset synthétique de factures avec ground truth."
    )
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--vendors", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic/dataset_50k.csv"))
    parser.add_argument("--vendors-output", type=Path, default=None)
    parser.add_argument("--format", choices=["csv", "parquet"], default="csv")
    args = parser.parse_args()

    cfg = GeneratorConfig(n_invoices=args.rows, n_vendors=args.vendors, seed=args.seed)
    invoices, vendors = generate_dataset(cfg)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "csv":
        invoices.to_csv(args.output, index=False)
    else:
        invoices.to_parquet(args.output, index=False)

    vendors_path = args.vendors_output or args.output.with_name("vendors_" + args.output.name)
    if args.format == "csv":
        vendors.to_csv(vendors_path, index=False)
    else:
        vendors.to_parquet(vendors_path, index=False)

    fraud_stats = invoices["fraud_type"].value_counts().to_dict()
    total_fraud = int(invoices["is_fraud"].sum())
    print(f"[OK] {len(invoices):,} factures generees -> {args.output}")
    print(f"     Fournisseurs : {len(vendors):,} -> {vendors_path}")
    print(f"     Fraudes etiquetees : {total_fraud:,} ({total_fraud / len(invoices):.2%})")
    for k, v in fraud_stats.items():
        if k != FraudType.NONE.value:
            print(f"       - {k}: {v:,}")


if __name__ == "__main__":
    main()
