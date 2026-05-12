"""Tests P5-1 — adapters live DECP / Pappers / Yente.

Couvre :
- Succès : payload officiel correctement mappé vers les modèles internes.
- Échec : timeout / 5xx / JSON malformé déclenchent un fallback graceful
  sans exception remontée (le client retombe sur les données démo).
- Validation entrée : SIREN invalide ignoré, nom vide ignoré.

Pas d'appel réseau réel : tous les endpoints sont mockés via `responses`.
"""

from __future__ import annotations

import pytest
import requests
import responses

from p2p_fraud.enrichment.decp_client import DECPClient
from p2p_fraud.enrichment.decp_live import DECPLiveClient, DECPLiveError
from p2p_fraud.enrichment.pappers_live import PappersLiveClient, PappersLiveError
from p2p_fraud.enrichment.rbe_client import RBEClient
from p2p_fraud.enrichment.sanctions_client import SanctionsClient
from p2p_fraud.enrichment.yente_client import YenteClient, YenteError

# ───────────────────────── DECP live ──────────────────────────────────────────


@responses.activate
def test_decp_live_lookup_by_siren_returns_contracts() -> None:
    siren = "552120222"
    responses.add(
        responses.GET,
        "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/decp-v3/records",
        json={
            "results": [
                {
                    "titulaire_id": siren + "00018",
                    "titulaire_denomination": "BNP PARIBAS SECURITIES SERVICES",
                    "acheteur_nom": "Caisse des Dépôts",
                    "montant": 124500.50,
                    "datenotification": "2025-09-12",
                    "objet": "Conservation de titres",
                    "nature": "Marché",
                    "lieuexecution_code": "75002",
                }
            ]
        },
        status=200,
    )
    client = DECPLiveClient(session=requests.Session())
    contracts = client.lookup_by_siren(siren)
    assert len(contracts) == 1
    assert contracts[0].siren_titulaire == siren
    assert contracts[0].montant_eur == 124500.50
    assert contracts[0].acheteur == "Caisse des Dépôts"


def test_decp_live_ignores_invalid_siren() -> None:
    client = DECPLiveClient(session=requests.Session())
    assert client.lookup_by_siren("") == []
    assert client.lookup_by_siren("ABC") == []
    assert client.lookup_by_siren("123") == []  # trop court


@responses.activate
def test_decp_live_5xx_raises_decp_live_error() -> None:
    responses.add(
        responses.GET,
        "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/decp-v3/records",
        status=503,
    )
    client = DECPLiveClient(session=requests.Session())
    with pytest.raises(DECPLiveError):
        client.lookup_by_siren("123456789")


@responses.activate
def test_decp_client_falls_back_to_demo_on_live_failure() -> None:
    """Quand le live échoue, DECPClient retombe silencieusement sur les données démo."""
    responses.add(
        responses.GET,
        "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/decp-v3/records",
        status=503,
    )
    decp = DECPClient(demo_mode=True)
    decp.live_client = DECPLiveClient(session=requests.Session())
    # Le SIREN "123456789" existe en démo (ACME CONSULTING SAS)
    result = decp.lookup_by_siren("123456789")
    assert isinstance(result, list)  # pas d'exception, fallback OK


# ───────────────────────── Pappers live ───────────────────────────────────────


@responses.activate
def test_pappers_live_lookup_by_siren_maps_owners() -> None:
    siren = "552120222"
    responses.add(
        responses.GET,
        "https://api.pappers.fr/v2/entreprise",
        json={
            "denomination": "BNP PARIBAS",
            "beneficiaires_effectifs": [
                {
                    "prenoms": "Jean-Laurent",
                    "nom": "BONNAFÉ",
                    "pourcentage_parts": 30.5,
                    "nationalite": "FR",
                    "politiquement_expose": True,
                }
            ],
        },
        status=200,
    )
    client = PappersLiveClient(api_key="test-key", session=requests.Session())
    owners = client.lookup_by_siren(siren)
    assert len(owners) == 1
    assert owners[0].owner_last_name == "BONNAFÉ"
    assert owners[0].ownership_pct == 30.5
    assert owners[0].is_pep is True


def test_pappers_requires_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        PappersLiveClient(api_key="")


@responses.activate
def test_pappers_live_404_raises_error() -> None:
    responses.add(
        responses.GET,
        "https://api.pappers.fr/v2/entreprise",
        status=404,
    )
    client = PappersLiveClient(api_key="test", session=requests.Session())
    with pytest.raises(PappersLiveError):
        client.lookup_by_siren("123456789")


def test_rbe_client_with_live_falls_back_on_invalid_siren() -> None:
    """Un SIREN invalide ne déclenche pas d'appel live (court-circuit côté client)."""
    rbe = RBEClient(demo_mode=True)
    rbe.live_client = PappersLiveClient(api_key="dummy", session=requests.Session())
    assert rbe.lookup_by_siren("") == []


# ───────────────────────── Yente live ─────────────────────────────────────────


@responses.activate
def test_yente_match_entity_returns_sanctions() -> None:
    responses.add(
        responses.POST,
        "https://api.opensanctions.org/match/sanctions",
        json={
            "responses": {
                "q1": {
                    "results": [
                        {
                            "id": "ofac-12345",
                            "schema": "LegalEntity",
                            "caption": "ROSNEFT OIL COMPANY",
                            "score": 0.95,
                            "datasets": ["ofac_sdn"],
                            "properties": {
                                "name": ["ROSNEFT OIL COMPANY"],
                                "country": ["ru"],
                                "topics": ["sanction"],
                            },
                        }
                    ]
                }
            }
        },
        status=200,
    )
    client = YenteClient(session=requests.Session())
    matches = client.match_entity("Rosneft")
    assert len(matches) == 1
    assert matches[0].list_source == "OFAC_SDN"
    assert matches[0].country == "RU"
    assert matches[0].score == 95


def test_yente_empty_name_returns_empty_list() -> None:
    client = YenteClient(session=requests.Session())
    assert client.match_entity("") == []
    assert client.match_entity("   ") == []


@responses.activate
def test_yente_5xx_raises_error() -> None:
    responses.add(
        responses.POST,
        "https://api.opensanctions.org/match/sanctions",
        status=500,
    )
    client = YenteClient(session=requests.Session())
    with pytest.raises(YenteError):
        client.match_entity("Rosneft")


@responses.activate
def test_sanctions_client_falls_back_to_snapshot_on_yente_failure() -> None:
    responses.add(
        responses.POST,
        "https://api.opensanctions.org/match/sanctions",
        status=503,
    )
    client = SanctionsClient(live_client=YenteClient(session=requests.Session()))
    # Échec live → fallback CSV snapshot, jamais d'exception
    result = client.search("inexistant qz xz")
    assert isinstance(result, list)


# ───────────────────────── from_settings() ────────────────────────────────────


def test_from_settings_demo_mode_returns_pure_demo_clients(monkeypatch) -> None:
    monkeypatch.delenv("ENRICHMENT_MODE", raising=False)
    monkeypatch.delenv("PAPPERS_API_KEY", raising=False)
    decp = DECPClient.from_settings()
    rbe = RBEClient.from_settings()
    sanc = SanctionsClient.from_settings()
    assert decp.live_client is None
    assert rbe.live_client is None
    assert sanc.live_client is None


def test_from_settings_live_mode_attaches_live_clients(monkeypatch) -> None:
    monkeypatch.setenv("ENRICHMENT_MODE", "live")
    monkeypatch.setenv("PAPPERS_API_KEY", "fake-key")
    decp = DECPClient.from_settings()
    rbe = RBEClient.from_settings()
    sanc = SanctionsClient.from_settings()
    assert decp.live_client is not None
    assert rbe.live_client is not None
    assert sanc.live_client is not None


def test_from_settings_live_mode_without_pappers_key_skips_rbe_live(monkeypatch) -> None:
    monkeypatch.setenv("ENRICHMENT_MODE", "live")
    monkeypatch.delenv("PAPPERS_API_KEY", raising=False)
    rbe = RBEClient.from_settings()
    # Sans clé Pappers, le live RBE est désactivé (fallback démo).
    assert rbe.live_client is None
