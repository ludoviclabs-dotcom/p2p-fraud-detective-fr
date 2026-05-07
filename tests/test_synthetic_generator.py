import pytest

from p2p_fraud.synthetic.generator import (
    FraudType,
    MasterDataEventsConfig,
    attach_vendor_ids,
    generate_master_data_events,
)


def test_dataset_shape(small_dataset):
    invoices, vendors = small_dataset
    expected_min = 2_000
    assert len(invoices) >= expected_min  # +injections
    assert len(vendors) == 300


def test_ground_truth_columns(small_dataset):
    invoices, _ = small_dataset
    assert "is_fraud" in invoices.columns
    assert "fraud_type" in invoices.columns


def test_fraud_types_present(small_dataset):
    invoices, _ = small_dataset
    fraud_types = set(invoices.loc[invoices["is_fraud"], "fraud_type"].unique())
    expected = {
        FraudType.DUPLICATE_EXACT.value,
        FraudType.DUPLICATE_FUZZY.value,
        FraudType.UNDER_THRESHOLD.value,
        FraudType.SHELL_COMPANY.value,
        FraudType.SHARED_IBAN_RING.value,
        FraudType.AMOUNT_OUTLIER.value,
    }
    # Tolérance : weekend_unusual_user à 0.1 % peut tomber à 0 sur 2 000
    assert expected.issubset(fraud_types)


def test_unique_invoice_ids(small_dataset):
    invoices, _ = small_dataset
    assert invoices["invoice_id"].is_unique


def test_amount_positive(small_dataset):
    invoices, _ = small_dataset
    assert (invoices["amount"] > 0).all()


def test_seed_reproducibility():
    from p2p_fraud.synthetic.generator import GeneratorConfig, generate_dataset

    cfg_a = GeneratorConfig(n_invoices=500, n_vendors=50, seed=7)
    cfg_b = GeneratorConfig(n_invoices=500, n_vendors=50, seed=7)
    a, _ = generate_dataset(cfg_a)
    b, _ = generate_dataset(cfg_b)
    assert a.equals(b)


def test_attach_vendor_ids_adds_column(small_dataset):
    invoices, vendors = small_dataset
    enriched = attach_vendor_ids(invoices, vendors)
    assert "vendor_id" in enriched.columns
    assert (enriched["vendor_id"] != "UNKNOWN").mean() > 0.95  # quasi-tous résolus
    # L'original reste intact (immutabilité)
    assert "vendor_id" not in invoices.columns


def test_master_data_events_have_ground_truth(small_dataset):
    invoices, vendors = small_dataset
    invoices = attach_vendor_ids(invoices, vendors)
    events = generate_master_data_events(
        invoices,
        vendors,
        MasterDataEventsConfig(
            n_bec_swaps=5,
            n_dormant_reactivations=3,
            n_name_iban_same_day=2,
            n_legitimate_changes=20,
            seed=42,
        ),
    )
    assert "fraud_type" in events.columns
    assert (events["fraud_type"] == FraudType.BEC_IBAN_SWAP.value).sum() > 0
    # Au moins 1 dormant ou name_iban_same_day selon la disponibilité de candidates
    fraud_kinds = set(events.loc[events["is_fraud"], "fraud_type"].unique())
    assert FraudType.BEC_IBAN_SWAP.value in fraud_kinds


def test_master_data_events_require_vendor_id(small_dataset):
    invoices, vendors = small_dataset
    with pytest.raises(ValueError, match="vendor_id"):
        generate_master_data_events(invoices, vendors, MasterDataEventsConfig())
