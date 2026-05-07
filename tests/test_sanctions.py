"""Tests détecteur sanctions / PEP — Sprint 2."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from p2p_fraud.detectors.sanctions import detect_sanctioned_vendors
from p2p_fraud.enrichment.sanctions_client import SanctionsClient, _normalize
from p2p_fraud.schema import Severity

FIXTURE = Path(__file__).parent / "fixtures" / "sanctions_test.csv"


@pytest.fixture(scope="module")
def client() -> SanctionsClient:
    return SanctionsClient(snapshot_path=FIXTURE, min_score=85)


def test_normalize_handles_accents_and_punctuation():
    assert _normalize("Société Aigle Noir S.A.R.L.") == "societe aigle noir s a r l"
    assert _normalize("DUPONT, Marie") == "dupont  marie"
    assert _normalize("") == ""


def test_client_loads_fixture(client: SanctionsClient):
    assert client.n_records == 3


def test_search_exact_name_returns_match(client: SanctionsClient):
    matches = client.search("Acme Test Corp")
    assert any(m.entity_id == "TEST-EU-001" for m in matches)
    assert matches[0].score >= 90


def test_search_via_alias(client: SanctionsClient):
    matches = client.search("Shadow Industries Ltd")
    assert any(m.entity_id == "TEST-OFAC-001" for m in matches)


def test_search_with_typo_below_threshold_returns_empty(client: SanctionsClient):
    # Très loin de toute entrée
    matches = client.search("Banque de Pierre Dupuis Holdings")
    assert matches == []


def test_pep_flag_distinguishes_pep_from_sanction(client: SanctionsClient):
    matches_pep = client.search("Marie Dupont")
    assert matches_pep
    pep_match = matches_pep[0]
    assert pep_match.is_pep
    assert not pep_match.is_sanction

    matches_sanction = client.search("Acme Test Corp")
    assert matches_sanction[0].is_sanction
    assert not matches_sanction[0].is_pep


def test_detect_sanctioned_vendors_emits_critical_finding(client: SanctionsClient):
    invoices = pd.DataFrame(
        [
            {"invoice_id": "INV1", "vendor_name": "Acme Test Corp", "amount": 12_000.0},
            {"invoice_id": "INV2", "vendor_name": "Acme Test Corp", "amount": 5_000.0},
            {"invoice_id": "INV3", "vendor_name": "Boulangerie Locale", "amount": 250.0},
        ]
    )
    findings = detect_sanctioned_vendors(invoices, client=client)
    assert len(findings) == 2  # 2 factures pour Acme Test Corp
    assert all(f.severity == Severity.CRITICAL for f in findings)
    assert all(f.rule_id == "SANCTIONS_VENDOR_HIT" for f in findings)
    assert findings[0].evidence["exposure_eur"] == pytest.approx(17_000.0)


def test_detect_pep_emits_high_finding(client: SanctionsClient):
    invoices = pd.DataFrame(
        [
            {"invoice_id": "INV10", "vendor_name": "Marie Dupont", "amount": 3_500.0},
        ]
    )
    findings = detect_sanctioned_vendors(invoices, client=client)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HIGH
    assert findings[0].rule_id == "SANCTIONS_VENDOR_PEP"


def test_detect_returns_empty_for_no_match(client: SanctionsClient):
    invoices = pd.DataFrame(
        [
            {"invoice_id": "INV1", "vendor_name": "Boulangerie du Coin SARL", "amount": 250.0},
        ]
    )
    assert detect_sanctioned_vendors(invoices, client=client) == []


def test_detect_handles_empty_or_missing_columns():
    assert detect_sanctioned_vendors(pd.DataFrame(), client=None) == []
    df_missing = pd.DataFrame([{"invoice_id": "X", "amount": 10.0}])
    assert detect_sanctioned_vendors(df_missing, client=None) == []
