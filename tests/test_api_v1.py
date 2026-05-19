"""Tests Migration v2 Phase 0 — endpoints /api/v1/* pour le frontend Next.js.

Tous les tests utilisent `TestClient` (FastAPI) — pas d'HTTP réel. Le
`CaseService` partagé reçoit quelques cases seed pour avoir des données
significatives sur Cockpit, vendors, etc.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from p2p_fraud.api.main import _case_service, app
from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.schema import Finding, Severity


@pytest.fixture
def client(monkeypatch) -> TestClient:
    """TestClient avec un CaseService propre seedé."""
    # Force le CaseService global à un instance neuve in-memory
    fresh = CaseService(audit_log=AuditLog(":memory:"))
    monkeypatch.setattr("p2p_fraud.api.main._CASE_SERVICE", fresh)
    monkeypatch.setattr("p2p_fraud.api.main._case_service", lambda: fresh)
    # Re-écraser le dependency_override pour pointer sur l'instance fraîche
    from p2p_fraud.api.v1 import _get_service as v1_stub

    app.dependency_overrides[v1_stub] = lambda: fresh

    # Seed 3 cases
    finding_critical = Finding(
        invoice_id="INV-001",
        rule_id="SANCTION_MATCH",
        signal="OFAC SDN match",
        severity=Severity.CRITICAL,
        evidence={"vendor_id": "V001", "exposure_eur": 50000.0},
        detector="sanctions",
    )
    finding_high = Finding(
        invoice_id="INV-002",
        rule_id="DUPLICATE_FUZZY",
        signal="Doublons fuzzy",
        severity=Severity.HIGH,
        evidence={"vendor_id": "V002", "exposure_eur": 3000.0},
        detector="duplicates",
    )
    finding_med = Finding(
        invoice_id="INV-003",
        rule_id="UNDER_THRESHOLD",
        signal="Sous seuil COSI",
        severity=Severity.MEDIUM,
        evidence={"vendor_id": "V001", "exposure_eur": 950.0},
        detector="thresholds",
    )
    fresh.create_case_from_finding(finding_critical, actor="seed")
    fresh.create_case_from_finding(finding_high, actor="seed")
    fresh.create_case_from_finding(finding_med, actor="seed")

    yield TestClient(app)

    app.dependency_overrides.pop(v1_stub, None)


# ───────────────────────── Cockpit ───────────────────────────────────────────


def test_cockpit_kpis_returns_4_kpi_and_trends(client: TestClient) -> None:
    r = client.get("/api/v1/cockpit/kpis")
    assert r.status_code == 200
    body = r.json()
    assert body["exposure_total_eur"] > 0
    assert body["n_cases_open"] == 3
    assert len(body["trend_cases_created"]) == 30
    assert len(body["trend_audit_activity"]) == 30


def test_cockpit_top_vendors_sorts_by_exposure(client: TestClient) -> None:
    r = client.get("/api/v1/cockpit/top-vendors?limit=5")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    # V001 a deux cases → exposition cumulée 50950 > V002 (3000)
    assert rows[0]["vendor_id"] == "V001"
    assert rows[0]["exposure_eur"] >= 50000


# ───────────────────────── Findings ──────────────────────────────────────────


def test_findings_list_returns_all(client: TestClient) -> None:
    r = client.get("/api/v1/findings")
    assert r.status_code == 200
    assert len(r.json()) >= 3


def test_findings_filter_by_severity(client: TestClient) -> None:
    r = client.get("/api/v1/findings?severity=critical")
    assert r.status_code == 200
    body = r.json()
    assert all(f["severity"] == "critical" for f in body)
    assert len(body) >= 1


# ───────────────────────── Vendors ───────────────────────────────────────────


def test_vendor_summary_returns_aggregated(client: TestClient) -> None:
    r = client.get("/api/v1/vendors/V001")
    assert r.status_code == 200
    body = r.json()
    assert body["vendor_id"] == "V001"
    assert body["n_invoices"] >= 2  # V001 a deux cases


def test_vendor_summary_unknown_returns_empty(client: TestClient) -> None:
    r = client.get("/api/v1/vendors/V999")
    assert r.status_code == 200
    body = r.json()
    assert body["vendor_id"] == "V999"
    assert body["n_invoices"] == 0


def test_vendor_timeline_returns_recent_events(client: TestClient) -> None:
    r = client.get("/api/v1/vendors/V001/timeline")
    assert r.status_code == 200
    events = r.json()
    assert len(events) >= 1
    assert all(e["kind"] == "case" for e in events)


# ───────────────────────── Cases — comment + bulk ────────────────────────────


def test_case_comment_appends_to_audit(client: TestClient) -> None:
    # Récupère un case existant
    cases = _case_service().list_cases()
    cid = cases[0].case_id
    r = client.post(
        f"/api/v1/cases/{cid}/comment",
        json={"text": "Investigation en cours.", "actor": "auditeur1"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_case_comment_unknown_returns_404(client: TestClient) -> None:
    r = client.post(
        "/api/v1/cases/CASE-doesnotexist/comment",
        json={"text": "Test", "actor": "a"},
    )
    assert r.status_code == 404


def test_bulk_assign_succeeds(client: TestClient) -> None:
    cases = _case_service().list_cases()
    ids = [c.case_id for c in cases[:2]]
    r = client.post(
        "/api/v1/cases/bulk/assign",
        json={"case_ids": ids, "assignee": "alice", "actor": "manager"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["n_ok"] == 2
    assert body["n_errors"] == 0


def test_list_cases_filters_by_invoice_id(client: TestClient) -> None:
    cases = _case_service().list_cases()
    target = cases[0]
    r = client.get(f"/api/v1/cases?invoice_id={target.invoice_id}")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["case_id"] == target.case_id


def test_case_status_update_sets_in_progress(client: TestClient) -> None:
    case = _case_service().list_cases()[0]
    r = client.post(
        f"/api/v1/cases/{case.case_id}/status",
        json={"status": "in_progress", "actor": "auditeur.web"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["case_id"] == case.case_id
    assert body["status"] == "in_progress"


def test_case_status_update_escalates(client: TestClient) -> None:
    case = _case_service().list_cases()[1]
    r = client.post(
        f"/api/v1/cases/{case.case_id}/status",
        json={
            "status": "escalated",
            "actor": "auditeur.web",
            "reason": "Paiement a bloquer avant revue complementaire.",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "escalated"


def test_case_bootstrap_creates_new_case(client: TestClient) -> None:
    before = len(_case_service().list_cases())
    r = client.post(
        "/api/v1/cases/bootstrap",
        json={
            "finding_id": "finding-demo-001",
            "invoice_id": "INV-DEMO-100",
            "vendor_id": "VBOOT",
            "vendor_name": "Bootstrap Vendor",
            "rule_id": "SHARED_IBAN_RING",
            "signal": "shared_iban_ring",
            "severity": "high",
            "exposure_eur": 4200,
            "risk_score": 82,
            "actor": "auditeur.web",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["invoice_id"] == "INV-DEMO-100"
    assert body["vendor_id"] == "VBOOT"
    assert len(_case_service().list_cases()) == before + 1


def test_case_bootstrap_reuses_existing_case(client: TestClient) -> None:
    payload = {
        "finding_id": "finding-demo-002",
        "invoice_id": "INV-DEMO-101",
        "vendor_id": "VBOOT2",
        "vendor_name": "Bootstrap Vendor 2",
        "rule_id": "DUPLICATE_FUZZY",
        "signal": "duplicate_fuzzy",
        "severity": "medium",
        "exposure_eur": 900,
        "risk_score": 51,
        "actor": "auditeur.web",
    }
    first = client.post("/api/v1/cases/bootstrap", json=payload)
    second = client.post("/api/v1/cases/bootstrap", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["case_id"] == second.json()["case_id"]


def test_bulk_close_invalid_status_returns_400(client: TestClient) -> None:
    cases = _case_service().list_cases()
    r = client.post(
        "/api/v1/cases/bulk/close",
        json={
            "case_ids": [cases[0].case_id],
            "status": "not_a_status",
            "reason": "test",
            "actor": "a",
        },
    )
    assert r.status_code == 400


def test_bulk_close_succeeds(client: TestClient) -> None:
    cases = _case_service().list_cases()
    ids = [cases[0].case_id]
    r = client.post(
        "/api/v1/cases/bulk/close",
        json={
            "case_ids": ids,
            "status": "false_positive",
            "reason": "Investigué — non probant.",
            "actor": "alice",
        },
    )
    assert r.status_code == 200
    assert r.json()["n_ok"] == 1


# ───────────────────────── Audit ─────────────────────────────────────────────


def test_audit_list_paginated(client: TestClient) -> None:
    r = client.get("/api/v1/audit?limit=2")
    assert r.status_code == 200
    body = r.json()
    assert len(body["entries"]) <= 2
    assert body["total"] >= 3


def test_audit_verify_returns_valid(client: TestClient) -> None:
    r = client.get("/api/v1/audit/verify")
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["invalid_seqs"] == []
    assert body["n_total"] >= 3


# ───────────────────────── Exports PDF ───────────────────────────────────────


def test_export_dossier_pdf_returns_attachment(client: TestClient) -> None:
    cases = _case_service().list_cases()
    cid = cases[0].case_id
    r = client.get(f"/api/v1/exports/dossier.pdf?case_id={cid}")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("content-disposition", "")
    # weasyprint dispo → application/pdf ; sinon → text/plain (fallback)
    assert r.headers["content-type"] in ("application/pdf", "text/plain; charset=utf-8")


def test_export_dossier_pdf_unknown_case_returns_404(client: TestClient) -> None:
    r = client.get("/api/v1/exports/dossier.pdf?case_id=CASE-doesnotexist")
    assert r.status_code == 404
