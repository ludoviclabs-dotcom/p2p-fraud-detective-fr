"""Générateur de dataset synthétique de factures avec patterns de fraude étiquetés.

Le ground truth (`is_fraud`, `fraud_type`) permet d'évaluer F1 par détecteur.

Ajout Sprint 1 : `generate_master_data_events()` produit un journal d'événements
master data avec scénarios étiquetés (`bec_iban_swap`, `dormant_reactivation`).
La fonction est *additive* — elle peut être appelée séparément sans impacter
les générations existantes.
"""

from __future__ import annotations

import argparse
import math
import random
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
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
    BEC_IBAN_SWAP = "bec_iban_swap"
    DORMANT_REACTIVATION = "dormant_reactivation"
    NAME_IBAN_SAME_DAY = "name_iban_same_day"


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


def attach_vendor_ids(invoices: pd.DataFrame, vendors: pd.DataFrame) -> pd.DataFrame:
    """Joint la colonne `vendor_id` à un DataFrame de factures.

    Sortie utilisée par le détecteur master_data_changes (qui a besoin du lien
    facture ↔ fournisseur). La colonne `vendor_id` n'est PAS ajoutée par
    `generate_dataset` afin de préserver la compatibilité avec le schéma Pydantic
    `Invoice` (extra="forbid"). Appelez `attach_vendor_ids` uniquement quand vous
    travaillez sur un DataFrame brut (pas après un parse Pydantic).
    """
    if invoices.empty:
        return invoices.copy()
    name_to_vid = dict(zip(vendors["vendor_name"], vendors["vendor_id"], strict=False))
    out = invoices.copy()
    out["vendor_id"] = out["vendor_name"].map(name_to_vid).fillna("UNKNOWN")
    return out


@dataclass
class MasterDataEventsConfig:
    """Configuration de la génération synthétique d'événements master data."""

    n_bec_swaps: int = 30
    n_dormant_reactivations: int = 15
    n_name_iban_same_day: int = 10
    n_legitimate_changes: int = 200
    dormant_days: int = 200
    seed: int = 42


def _new_event(
    vendor_id: str,
    field_name: str,
    old: str | None,
    new: str | None,
    when: datetime,
    changed_by: str,
    approved_by: str | None,
    source: str = "erp",
) -> dict:
    return {
        "event_id": f"E-{uuid.uuid4().hex[:12]}",
        "vendor_id": vendor_id,
        "field": field_name,
        "old_value": old,
        "new_value": new,
        "changed_at": when,
        "changed_by": changed_by,
        "approved_by": approved_by,
        "source": source,
        "is_fraud": False,
        "fraud_type": "none",
    }


def generate_master_data_events(
    invoices: pd.DataFrame,
    vendors: pd.DataFrame,
    cfg: MasterDataEventsConfig | None = None,
) -> pd.DataFrame:
    """Génère un journal d'événements master data avec ground truth.

    Hypothèses :
    - Les invoices sont déjà générées (avec colonne `vendor_id`).
    - On garantit que les BEC swaps précèdent au moins une facture du fournisseur.
    """
    cfg = cfg or MasterDataEventsConfig()
    rng = random.Random(cfg.seed)
    faker = Faker("fr_FR")
    Faker.seed(cfg.seed)

    if "vendor_id" not in invoices.columns:
        raise ValueError(
            "invoices doit contenir une colonne vendor_id. "
            "Appelez `attach_vendor_ids(invoices, vendors)` avant de générer les events."
        )

    inv = invoices.copy()
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"], errors="coerce")
    inv = inv.dropna(subset=["invoice_date"])
    user_pool = [f"U{i:03d}" for i in range(50)]

    events: list[dict] = []

    # 1. BEC IBAN swaps : changement IBAN sans 4-eyes, suivi de paiements.
    eligible_vendors = (
        inv.groupby("vendor_id")
        .agg(invoice_count=("invoice_id", "size"), max_date=("invoice_date", "max"))
        .reset_index()
    )
    eligible_vendors = eligible_vendors[eligible_vendors["invoice_count"] >= 3]
    bec_targets = eligible_vendors.sample(
        n=min(cfg.n_bec_swaps, len(eligible_vendors)), random_state=cfg.seed
    )
    for _, row in bec_targets.iterrows():
        vendor_id = row["vendor_id"]
        vendor_invoices = inv[inv["vendor_id"] == vendor_id].sort_values("invoice_date")
        # On choisit une date entre la 1ère et la dernière facture, puis on
        # marque les factures *postérieures* comme impactées.
        if len(vendor_invoices) < 2:
            continue
        # Pick a swap date in the middle third
        idx = rng.randint(len(vendor_invoices) // 3, max(1, 2 * len(vendor_invoices) // 3))
        swap_date = vendor_invoices.iloc[idx]["invoice_date"] - pd.Timedelta(days=2)
        when = pd.Timestamp(swap_date).to_pydatetime().replace(tzinfo=UTC)
        old_iban = vendor_invoices.iloc[0]["iban"]
        new_iban = (
            faker.iban() if hasattr(faker, "iban") else f"FR76{rng.randint(10**20, 10**21 - 1)}"
        )
        user = rng.choice(user_pool)
        ev = _new_event(
            vendor_id=vendor_id,
            field_name="iban",
            old=old_iban,
            new=new_iban,
            when=when,
            changed_by=user,
            approved_by=None,  # pas de 4-eyes
            source="manual",
        )
        ev["is_fraud"] = True
        ev["fraud_type"] = FraudType.BEC_IBAN_SWAP.value
        events.append(ev)

    # 2. Dormant reactivation : on choisit un fournisseur avec un grand gap.
    vendor_first_last = (
        inv.groupby("vendor_id")
        .agg(first=("invoice_date", "min"), last=("invoice_date", "max"))
        .reset_index()
    )
    candidates = vendor_first_last[
        (vendor_first_last["last"] - vendor_first_last["first"]).dt.days > cfg.dormant_days * 1.2
    ]
    n_dormant = min(cfg.n_dormant_reactivations, len(candidates))
    if n_dormant > 0:
        targets = candidates.sample(n=n_dormant, random_state=cfg.seed + 1)
        for _, row in targets.iterrows():
            vendor_id = row["vendor_id"]
            # Place IBAN change at last - dormant_days, after a long inactivity from "first".
            when = pd.Timestamp(row["last"] - pd.Timedelta(days=10))
            when_dt = when.to_pydatetime().replace(tzinfo=UTC)
            new_iban = (
                faker.iban() if hasattr(faker, "iban") else f"FR76{rng.randint(10**20, 10**21 - 1)}"
            )
            user = rng.choice(user_pool)
            ev = _new_event(
                vendor_id=vendor_id,
                field_name="iban",
                old="FR76OLD",
                new=new_iban,
                when=when_dt,
                changed_by=user,
                approved_by=rng.choice([u for u in user_pool if u != user]),
                source="manual",
            )
            ev["is_fraud"] = True
            ev["fraud_type"] = FraudType.DORMANT_REACTIVATION.value
            events.append(ev)

    # 3. Name + IBAN même jour
    same_day_targets = eligible_vendors.sample(
        n=min(cfg.n_name_iban_same_day, len(eligible_vendors)),
        random_state=cfg.seed + 2,
    )
    for _, row in same_day_targets.iterrows():
        vendor_id = row["vendor_id"]
        vendor_invoices = inv[inv["vendor_id"] == vendor_id].sort_values("invoice_date")
        if vendor_invoices.empty:
            continue
        when = pd.Timestamp(vendor_invoices.iloc[len(vendor_invoices) // 2]["invoice_date"])
        when_dt = when.to_pydatetime().replace(tzinfo=UTC)
        user = rng.choice(user_pool)
        new_iban = (
            faker.iban() if hasattr(faker, "iban") else f"FR76{rng.randint(10**20, 10**21 - 1)}"
        )
        ev_iban = _new_event(vendor_id, "iban", "FR76OLD", new_iban, when_dt, user, None, "manual")
        ev_iban["is_fraud"] = True
        ev_iban["fraud_type"] = FraudType.NAME_IBAN_SAME_DAY.value
        events.append(ev_iban)
        ev_name = _new_event(
            vendor_id,
            "name",
            "OLD NAME SARL",
            faker.company() + " SARL",
            when_dt + timedelta(hours=1),
            user,
            None,
            "manual",
        )
        ev_name["is_fraud"] = True
        ev_name["fraud_type"] = FraudType.NAME_IBAN_SAME_DAY.value
        events.append(ev_name)

    # 4. Changements légitimes (bruit) — adresse, contact email, IBAN avec 4-eyes ok
    legit_pool = vendors.sample(
        n=min(cfg.n_legitimate_changes, len(vendors)), random_state=cfg.seed + 3
    )
    for _, vrow in legit_pool.iterrows():
        vendor_id = vrow["vendor_id"]
        when_dt = datetime(2024, rng.randint(1, 12), rng.randint(1, 28), tzinfo=UTC)
        field_choice = rng.choice(["address", "contact_email", "iban", "contact_phone"])
        user = rng.choice(user_pool)
        approver = rng.choice([u for u in user_pool if u != user])
        ev = _new_event(
            vendor_id=vendor_id,
            field_name=field_choice,
            old="OLD",
            new=faker.email()
            if "email" in field_choice
            else faker.address().replace("\n", ", ")[:80],
            when=when_dt,
            changed_by=user,
            approved_by=approver,
            source="erp",
        )
        events.append(ev)

    df = pd.DataFrame(events)
    return df.sort_values("changed_at").reset_index(drop=True)


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
