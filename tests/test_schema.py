from datetime import date

import pytest
from pydantic import ValidationError

from p2p_fraud.schema import SEVERITY_WEIGHT, Finding, Invoice, RiskScore, Severity


def test_invoice_minimal():
    inv = Invoice(
        invoice_id="INV1", vendor_name="ACME SARL", amount=100.0, invoice_date=date(2025, 1, 1)
    )
    assert inv.currency == "EUR"
    assert inv.siren is None


def test_invoice_amount_must_be_positive():
    with pytest.raises(ValidationError):
        Invoice(invoice_id="INV1", vendor_name="ACME", amount=0, invoice_date=date(2025, 1, 1))


def test_invoice_siren_normalized():
    inv = Invoice(
        invoice_id="INV1",
        vendor_name="ACME",
        amount=10,
        invoice_date=date(2025, 1, 1),
        siren=" 123 456 789 ",
    )
    assert inv.siren == "123456789"


def test_invoice_currency_uppercased():
    inv = Invoice(
        invoice_id="INV1",
        vendor_name="ACME",
        amount=10,
        invoice_date=date(2025, 1, 1),
        currency="eur",
    )
    assert inv.currency == "EUR"


def test_finding_severity_weight():
    f = Finding(
        invoice_id="X",
        detector="benford",
        signal="anomaly",
        severity=Severity.HIGH,
        rule_id="BENFORD_1ST",
    )
    assert f.severity_weight == SEVERITY_WEIGHT[Severity.HIGH] == 60


def test_risk_score_rounding():
    r = RiskScore(invoice_id="X", score=42.123456)
    assert r.score == 42.12


def test_risk_score_clamped():
    with pytest.raises(ValidationError):
        RiskScore(invoice_id="X", score=150.0)
