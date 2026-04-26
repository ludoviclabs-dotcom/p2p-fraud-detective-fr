"""Tests du client Sirene v3 — mock HTTP via responses, pas d'appel réseau."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
import requests
import responses

from p2p_fraud.enrichment.sirene_client import (
    SIRENE_API_BASE,
    SireneClient,
    cross_check_invoices,
)


def _siren_payload(
    *, is_active: bool = True, creation_date: str = "2010-01-01", ape: str = "6201Z"
) -> dict:
    return {
        "header": {"statut": 200, "message": "OK"},
        "uniteLegale": {
            "siren": "111111111",
            "dateCreationUniteLegale": creation_date,
            "dateDernierTraitementUniteLegale": "2025-01-01",
            "periodesUniteLegale": [
                {
                    "dateFin": None,
                    "dateDebut": creation_date,
                    "etatAdministratifUniteLegale": "A" if is_active else "C",
                    "denominationUniteLegale": "ACME SARL",
                    "activitePrincipaleUniteLegale": ape,
                }
            ],
        },
    }


@pytest.fixture(autouse=True)
def _no_real_http(monkeypatch, tmp_path):
    """Cache HTTP en mémoire pour ne rien persister entre tests."""
    monkeypatch.setenv("SIRENE_API_TOKEN", "test-token")
    yield


def _client_with_plain_session() -> SireneClient:
    # responses ne s'attache pas aux CachedSession ; on utilise une plain Session.
    return SireneClient(session=requests.Session(), rate_limit_qps=1000)


@responses.activate
def test_lookup_active_siren():
    responses.add(
        responses.GET,
        f"{SIRENE_API_BASE}/123456789",
        json=_siren_payload(is_active=True, creation_date="2010-05-15"),
        status=200,
    )
    client = _client_with_plain_session()
    record = client.lookup_siren("123456789")
    assert record is not None
    assert record.is_active is True
    assert record.creation_date == date(2010, 5, 15)
    assert record.ape_code == "6201Z"


@responses.activate
def test_lookup_404_returns_inactive_record():
    responses.add(
        responses.GET,
        f"{SIRENE_API_BASE}/999999999",
        status=404,
    )
    client = _client_with_plain_session()
    record = client.lookup_siren("999999999")
    assert record is not None
    assert record.is_active is False
    assert record.name is None


@responses.activate
def test_lookup_normalizes_siren_input():
    responses.add(
        responses.GET,
        f"{SIRENE_API_BASE}/123456789",
        json=_siren_payload(),
        status=200,
    )
    client = _client_with_plain_session()
    record = client.lookup_siren(" 123 456 789 ")
    assert record is not None
    assert record.siren == "123456789"


def test_lookup_invalid_siren_skipped(monkeypatch):
    client = _client_with_plain_session()
    assert client.lookup_siren("ABC") is None
    assert client.lookup_siren(None) is None
    assert client.lookup_siren("12345") is None  # < 9 chiffres


def test_disabled_when_no_token(monkeypatch):
    monkeypatch.delenv("SIRENE_API_TOKEN", raising=False)
    client = SireneClient(session=requests.Session())
    assert client.enabled is False
    assert client.lookup_siren("123456789") is None


@responses.activate
def test_cross_check_flags_404():
    responses.add(
        responses.GET,
        f"{SIRENE_API_BASE}/000000000",
        status=404,
    )
    df = pd.DataFrame(
        {
            "invoice_id": ["A", "B"],
            "vendor_name": ["Shell SARL", "Shell SARL"],
            "siren": ["000000000", "000000000"],
            "amount": [1000.0, 2000.0],
            "invoice_date": [date(2025, 1, 1), date(2025, 2, 1)],
        }
    )
    client = _client_with_plain_session()
    findings = cross_check_invoices(df, client=client)
    flagged = {f.signal for f in findings}
    assert "vendor_siren_not_found" in flagged
    assert len(findings) == 2  # une par facture


@responses.activate
def test_cross_check_flags_recent_creation():
    responses.add(
        responses.GET,
        f"{SIRENE_API_BASE}/123456789",
        json=_siren_payload(is_active=True, creation_date="2024-12-01"),
        status=200,
    )
    df = pd.DataFrame(
        {
            "invoice_id": ["A"],
            "vendor_name": ["Recent SARL"],
            "siren": ["123456789"],
            "amount": [10000.0],
            "invoice_date": [date(2025, 1, 15)],  # 45 jours après création
        }
    )
    client = _client_with_plain_session()
    findings = cross_check_invoices(df, client=client, new_vendor_grace_days=90)
    signals = {f.signal for f in findings}
    assert "vendor_recently_created" in signals
