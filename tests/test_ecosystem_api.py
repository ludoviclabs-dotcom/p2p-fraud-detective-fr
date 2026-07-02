"""Tests section 7 API v1 — connecteurs, alertes push, conflits, VoP."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from p2p_fraud.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ───────────────────────── Connecteurs ───────────────────────────────────────


def test_connectors_registry_shape(client: TestClient) -> None:
    r = client.get("/api/v1/connectors")
    assert r.status_code == 200
    rows = r.json()
    ids = {c["id"] for c in rows}
    assert {"sirene", "bodacc", "fnc_rf", "vop", "chorus_pro", "slack"} <= ids
    for c in rows:
        assert c["status"] in {"actif", "disponible", "config_requise", "en_attente_api", "roadmap"}
        assert isinstance(c["env_vars"], list)


def test_fnc_rf_pending_without_env(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("FNC_RF_API_URL", raising=False)
    r = client.get("/api/v1/connectors")
    fnc = next(c for c in r.json() if c["id"] == "fnc_rf")
    assert fnc["status"] == "en_attente_api"
    assert "FNC_RF_API_URL" in fnc["env_vars"]


def test_fnc_rf_active_with_env(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("FNC_RF_API_URL", "https://fnc-rf.example.fr/api")
    r = client.get("/api/v1/connectors")
    fnc = next(c for c in r.json() if c["id"] == "fnc_rf")
    assert fnc["status"] == "actif"


# ───────────────────────── Canaux d'alerte ────────────────────────────────────


def test_alert_channels_unconfigured(client: TestClient, monkeypatch) -> None:
    for var in ("SLACK_WEBHOOK_URL", "TEAMS_WEBHOOK_URL", "SMTP_HOST"):
        monkeypatch.delenv(var, raising=False)
    r = client.get("/api/v1/alerts/channels")
    assert r.status_code == 200
    rows = {c["name"]: c for c in r.json()}
    assert set(rows) == {"slack", "teams", "smtp"}
    assert not rows["slack"]["configured"]
    # Jamais de secret/URL complète exposée
    assert all("hooks.slack.com" not in str(c) or "://" not in c["target"] for c in r.json())


def test_alert_channels_masked_target(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/T000/B000/xyz")
    r = client.get("/api/v1/alerts/channels")
    slack = next(c for c in r.json() if c["name"] == "slack")
    assert slack["configured"]
    assert slack["target"] == "hooks.slack.com"
    assert "xyz" not in slack["target"]


def test_alert_test_without_channels(client: TestClient, monkeypatch) -> None:
    for var in ("SLACK_WEBHOOK_URL", "TEAMS_WEBHOOK_URL", "SMTP_HOST"):
        monkeypatch.delenv(var, raising=False)
    r = client.post("/api/v1/alerts/test")
    assert r.status_code == 200
    payload = r.json()
    assert payload["sent"] == []
    assert "SLACK_WEBHOOK_URL" in payload["message"]


# ───────────────────────── Conflits d'intérêts ────────────────────────────────


def test_conflicts_scan_shared_iban(client: TestClient) -> None:
    body = {
        "employees": [
            {
                "employee_id": "EMP-204",
                "full_name": "Marc Dupont",
                "iban": "FR76 1027 8060 4100 0204 2240 133",
                "can_approve_payments": True,
            }
        ],
        "vendors": [
            {
                "siren": "489330715",
                "name": "Prestaconseil RH",
                "iban_list": ["FR7610278060410002042240133"],
            }
        ],
    }
    r = client.post("/api/v1/conflicts/scan", json=body)
    assert r.status_code == 200
    rows = r.json()
    rule_ids = {f["rule_id"] for f in rows}
    assert "COI_SHARED_IBAN" in rule_ids
    assert "COI_APPROVER_LINK" in rule_ids
    iban_hit = next(f for f in rows if f["rule_id"] == "COI_SHARED_IBAN")
    assert iban_hit["severity"] == "critical"
    assert iban_hit["employee_id"] == "EMP-204"


def test_conflicts_scan_clean(client: TestClient) -> None:
    body = {
        "employees": [{"employee_id": "EMP-1", "full_name": "Julie Martin"}],
        "vendors": [{"siren": "812446901", "name": "Aciers Nord-Est SAS"}],
    }
    r = client.post("/api/v1/conflicts/scan", json=body)
    assert r.status_code == 200
    assert r.json() == []


# ───────────────────────── VoP precheck ──────────────────────────────────────


def test_vop_precheck_match(client: TestClient) -> None:
    r = client.post(
        "/api/v1/vop/precheck",
        json={
            "beneficiary_name": "Aciers Nord-Est SAS",
            "iban": "FR7630006000011234567890189",
            "expected_name": "ACIERS NORD-EST",
        },
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["verdict"] == "match"
    assert payload["provider"] == "simulation"


def test_vop_precheck_no_match(client: TestClient) -> None:
    r = client.post(
        "/api/v1/vop/precheck",
        json={
            "beneficiary_name": "Global Intermediary Ltd",
            "iban": "CY17002001280000001200527600",
            "expected_name": "Aciers Nord-Est SAS",
        },
    )
    assert r.json()["verdict"] == "no_match"


def test_vop_precheck_without_expected_name(client: TestClient) -> None:
    r = client.post(
        "/api/v1/vop/precheck",
        json={"beneficiary_name": "X", "iban": "FR76…"},
    )
    assert r.json()["verdict"] == "not_available"
