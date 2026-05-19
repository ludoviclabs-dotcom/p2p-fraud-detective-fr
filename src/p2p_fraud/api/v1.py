"""API v1 — endpoints REST pour le frontend Next.js (Migration v2 Phase 0).

Router séparé du `app` principal pour clarté + versionning. Tous les endpoints
sont préfixés `/api/v1/` et retournent du JSON typé Pydantic (compatible
`openapi-typescript` côté SDK).

Conventions :
- Lecture : GET + query params optionnels (pagination, filtres).
- Mutation : POST + body Pydantic strict.
- Streaming : Server-Sent Events (`text/event-stream`) ou `StreamingResponse`.
- Auth : `Depends(_require_auth)` réutilise le bearer existant.

Le router est monté sur l'app principal dans `api/main.py`.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import (
    ALLOWED_CASE_DECISIONS,
    CaseClosedError,
    CaseNotFoundError,
    CaseService,
)
from p2p_fraud.schema import Finding, Severity

router = APIRouter(prefix="/api/v1", tags=["v1 (Next.js)"])


# ─── Auth dépendance partagée (re-importée depuis main pour éviter cycle) ───


def _require_auth_v1() -> str:
    """Stub : la vraie auth est injectée par `main.py` via `app.dependency_overrides`."""
    return "anonymous"


def _get_service() -> CaseService:
    """Stub : l'instance CaseService réelle est injectée par `main.py`."""
    raise NotImplementedError("Override via main.app.dependency_overrides")


# ─── Modèles Pydantic typés ─────────────────────────────────────────────────


class DailyPoint(BaseModel):
    date: str  # ISO YYYY-MM-DD
    value: float


class CockpitKPIs(BaseModel):
    exposure_total_eur: float = Field(..., description="Exposition totale (€)")
    exposure_critical_eur: float = Field(..., description="Exposition CRITICAL (€)")
    n_cases_open: int
    n_cases_overdue: int
    n_cases_unassigned_critical: int
    trend_cases_created: list[DailyPoint] = Field(default_factory=list)
    trend_cases_closed: list[DailyPoint] = Field(default_factory=list)
    trend_critical_alerts: list[DailyPoint] = Field(default_factory=list)
    trend_audit_activity: list[DailyPoint] = Field(default_factory=list)


class TopVendor(BaseModel):
    vendor_id: str
    vendor_name: str | None = None
    exposure_eur: float
    n_findings: int
    max_severity: str


class FindingOut(BaseModel):
    invoice_id: str
    rule_id: str
    severity: str
    signal: str
    detector: str
    detected_at: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class VendorSummary(BaseModel):
    vendor_id: str
    vendor_name: str | None = None
    siren: str | None = None
    total_paid_eur: float | None = None
    n_invoices: int = 0
    is_sanctioned: bool = False
    is_pep: bool = False


class TimelineEvent(BaseModel):
    at: str
    kind: str  # "invoice" | "master_change" | "finding"
    label: str
    amount_eur: float | None = None
    severity: str | None = None


class CommentBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    actor: str = Field(..., min_length=1, max_length=128)


class StatusBody(BaseModel):
    status: str = Field(
        ...,
        description='"new" | "triaged" | "in_progress" | "escalated"',
    )
    actor: str = Field(..., min_length=1, max_length=128)
    reason: str | None = Field(default=None, max_length=2000)
    channel: str | None = Field(default=None, max_length=128)


class DecisionBody(BaseModel):
    decision: str = Field(..., min_length=1, max_length=64)
    actor: str = Field(..., min_length=1, max_length=128)


class CaseBootstrapBody(BaseModel):
    finding_id: str = Field(..., min_length=1, max_length=128)
    invoice_id: str = Field(..., min_length=1, max_length=128)
    vendor_id: str = Field(..., min_length=1, max_length=128)
    vendor_name: str = Field(..., min_length=1, max_length=256)
    rule_id: str = Field(..., min_length=1, max_length=128)
    signal: str = Field(..., min_length=1, max_length=256)
    severity: str = Field(..., description='"low" | "medium" | "high" | "critical"')
    exposure_eur: float = Field(default=0, ge=0)
    risk_score: float = Field(default=0, ge=0, le=100)
    actor: str = Field(..., min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=256)


class BulkAssignBody(BaseModel):
    case_ids: list[str] = Field(..., min_length=1, max_length=500)
    assignee: str = Field(..., min_length=1, max_length=128)
    actor: str = Field(..., min_length=1, max_length=128)


class BulkCloseBody(BaseModel):
    case_ids: list[str] = Field(..., min_length=1, max_length=500)
    status: str = Field(..., description='"confirmed" | "rejected" | "false_positive"')
    reason: str = Field(..., min_length=3, max_length=2000)
    actor: str = Field(..., min_length=1, max_length=128)


class BulkResult(BaseModel):
    n_ok: int
    n_errors: int
    error_case_ids: list[str] = Field(default_factory=list)


class AuditEntryOut(BaseModel):
    seq: int
    at: str
    actor: str
    kind: str
    payload: dict[str, Any]
    prev_hash: str
    hash: str
    signature: str = ""


class AuditPage(BaseModel):
    entries: list[AuditEntryOut]
    total: int
    cursor_next: int | None = None


class AuditVerifyResult(BaseModel):
    valid: bool
    invalid_seqs: list[int] = Field(default_factory=list)
    n_total: int
    n_signed: int
    public_key_b64: str = ""


class NarrativeBody(BaseModel):
    vendor_id: str
    vendor_name: str | None = None
    siren: str | None = None
    total_paid_eur: float | None = None
    n_invoices: int = 0
    is_sanctioned: bool = False
    is_pep: bool = False
    findings: list[dict[str, Any]] = Field(default_factory=list)
    api_key: str | None = None  # override env var (rarement utilisé)


class P2PGraphNode(BaseModel):
    id: str
    kind: str
    label: str
    severity: str
    riskScore: float
    exposureEur: float
    maskedValue: str | None = None


class P2PGraphEdge(BaseModel):
    source: str
    target: str
    kind: str
    weight: float
    findingIds: list[str] = Field(default_factory=list)


class P2PFindingSummary(BaseModel):
    id: str
    invoiceId: str
    vendorName: str
    vendorId: str
    ruleId: str
    severity: str
    signal: str
    exposureEur: float
    riskScore: float
    evidence: dict[str, Any] = Field(default_factory=dict)


class P2PVendorSummary(BaseModel):
    id: str
    vendorId: str
    name: str
    siren: str | None = None
    apeCode: str | None = None
    severity: str
    riskScore: float
    exposureEur: float
    findingIds: list[str] = Field(default_factory=list)


class P2PGraphMetrics(BaseModel):
    invoiceCount: int
    findingCount: int
    vendorCount: int
    ibanNodeCount: int
    edgeCount: int
    sharedIbanRings: int
    vendorClusters: int
    largestClusterSize: int
    criticalFindings: int
    highFindings: int
    mediumFindings: int
    signalCounts: dict[str, int] = Field(default_factory=dict)
    exposureEur: float


class P2PDemoDataset(BaseModel):
    generatedAt: str
    nodes: list[P2PGraphNode]
    edges: list[P2PGraphEdge]
    findings: list[P2PFindingSummary]
    vendors: list[P2PVendorSummary]
    metrics: P2PGraphMetrics


# ─── 1. Cockpit ──────────────────────────────────────────────────────────────


def _daily_series(events: list[str], days: int = 30) -> list[DailyPoint]:
    today = datetime.now(UTC).date()
    idx = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    counts = Counter(events)
    return [DailyPoint(date=d.isoformat(), value=float(counts.get(d, 0))) for d in idx]


@router.get("/cockpit/kpis", response_model=CockpitKPIs)
def cockpit_kpis(
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> CockpitKPIs:
    """4 KPI Cockpit + 4 séries 30 jours.

    Source : `CaseService.list_cases()` + `AuditLog`. Le frontend Next.js
    rend les sparklines via Recharts/visx en réutilisant ces séries.
    """
    cases = service.list_cases()
    exposure_total = sum((c.exposure_eur or 0) for c in cases)
    exposure_critical = sum((c.exposure_eur or 0) for c in cases if c.severity == "critical")
    n_cases_open = sum(1 for c in cases if not c.status.is_closed)
    now = datetime.now(UTC)
    n_cases_overdue = sum(
        1 for c in cases if not c.status.is_closed and c.sla_deadline and c.sla_deadline < now
    )
    n_cases_unassigned_critical = sum(
        1 for c in cases if c.severity == "critical" and not c.assignee and not c.status.is_closed
    )

    cases_created_dates = [c.created_at.astimezone(UTC).date() for c in cases if c.created_at]
    cases_closed_dates = [c.closed_at.astimezone(UTC).date() for c in cases if c.closed_at]

    audit = service.audit_log.all()
    audit_dates = []
    critical_dates = []
    for e in audit:
        try:
            d = datetime.fromisoformat(e.at).date()
        except ValueError:
            continue
        audit_dates.append(d)
        if e.kind == "case.created" and e.payload.get("severity") == "critical":
            critical_dates.append(d)

    return CockpitKPIs(
        exposure_total_eur=float(exposure_total),
        exposure_critical_eur=float(exposure_critical),
        n_cases_open=n_cases_open,
        n_cases_overdue=n_cases_overdue,
        n_cases_unassigned_critical=n_cases_unassigned_critical,
        trend_cases_created=_daily_series(cases_created_dates),
        trend_cases_closed=_daily_series(cases_closed_dates),
        trend_critical_alerts=_daily_series(critical_dates),
        trend_audit_activity=_daily_series(audit_dates),
    )


@router.get("/cockpit/top-vendors", response_model=list[TopVendor])
def cockpit_top_vendors(
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
    limit: int = Query(10, ge=1, le=100),
) -> list[TopVendor]:
    """Top N fournisseurs par exposition financière, agrégé depuis les cases."""
    cases = service.list_cases()
    agg: dict[str, dict[str, Any]] = {}
    for c in cases:
        if not c.vendor_id:
            continue
        a = agg.setdefault(
            c.vendor_id,
            {
                "vendor_id": c.vendor_id,
                "exposure_eur": 0.0,
                "n_findings": 0,
                "severities": set(),
            },
        )
        a["exposure_eur"] += float(c.exposure_eur or 0)
        a["n_findings"] += len(c.finding_ids or [])
        a["severities"].add(c.severity)
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    rows = [
        TopVendor(
            vendor_id=str(v["vendor_id"]),
            exposure_eur=v["exposure_eur"],
            n_findings=int(v["n_findings"]),
            max_severity=max(v["severities"], key=lambda s: severity_rank.get(s, 0)),
        )
        for v in agg.values()
    ]
    rows.sort(key=lambda r: r.exposure_eur, reverse=True)
    return rows[:limit]


# ─── 2. Findings + Vendors ──────────────────────────────────────────────────


@router.get("/findings", response_model=list[FindingOut])
def list_findings(
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
    rule_id: str | None = None,
    severity: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> list[FindingOut]:
    """Liste paginée des findings — source : cases enrichis par leurs events.

    Phase 0 — on agrège depuis `service.list_cases()` (qui porte `severity`,
    `invoice_id`, `vendor_id`) + `case_events` pour `signal` / `rule_id`.
    En Phase 5, une vraie table `findings` sera ajoutée.
    """
    rows: list[FindingOut] = []
    for c in service.list_cases():
        if severity and c.severity != severity:
            continue
        events = service.list_events(c.case_id)
        created = next((e for e in events if e.kind == "created"), None)
        c_rule = (created.payload.get("rule_id") if created else None) or "—"
        c_signal = (created.payload.get("signal") if created else None) or c.title or ""
        if rule_id and c_rule != rule_id:
            continue
        rows.append(
            FindingOut(
                invoice_id=c.invoice_id or c.case_id,
                rule_id=c_rule,
                severity=c.severity,
                signal=c_signal,
                detector="case",
                detected_at=c.created_at.isoformat() if c.created_at else "",
                evidence={
                    "case_id": c.case_id,
                    "vendor_id": c.vendor_id,
                    "exposure_eur": c.exposure_eur,
                },
            )
        )
        if len(rows) >= limit:
            break
    return rows


@router.get("/vendors/{vendor_id}", response_model=VendorSummary)
def vendor_summary(
    vendor_id: str,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> VendorSummary:
    """Fiche fournisseur 360° (version API — sans dataset session).

    En l'absence de données chargées (free-tier strict), renvoie au moins les
    cases agrégés par vendor_id pour calculer l'exposition.
    """
    cases = [c for c in service.list_cases() if c.vendor_id == vendor_id]
    if not cases:
        # Pas d'info — on renvoie au moins l'ID pour ne pas casser le front
        return VendorSummary(vendor_id=vendor_id, n_invoices=0)
    total = sum(float(c.exposure_eur or 0) for c in cases)
    return VendorSummary(
        vendor_id=vendor_id,
        total_paid_eur=total,
        n_invoices=len(cases),
        is_sanctioned=any("sanction" in (c.title or "").lower() for c in cases),
        is_pep=any("pep" in (c.title or "").lower() for c in cases),
    )


@router.get("/vendors/{vendor_id}/timeline", response_model=list[TimelineEvent])
def vendor_timeline(
    vendor_id: str,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
    days: int = Query(30, ge=1, le=365),
) -> list[TimelineEvent]:
    """Timeline événements 30 jours : cases + audit log pertinents."""
    since = datetime.now(UTC) - timedelta(days=days)
    events: list[TimelineEvent] = []
    for c in service.list_cases():
        if c.vendor_id != vendor_id:
            continue
        if c.created_at and c.created_at >= since:
            events.append(
                TimelineEvent(
                    at=c.created_at.isoformat(),
                    kind="case",
                    label=c.title or c.case_id,
                    amount_eur=c.exposure_eur,
                    severity=c.severity,
                )
            )
    events.sort(key=lambda e: e.at, reverse=True)
    return events


class CaseOutV1(BaseModel):
    case_id: str
    title: str
    severity: str
    status: str
    vendor_id: str | None = None
    invoice_id: str | None = None
    exposure_eur: float | None = None
    decision: str | None = None
    assignee: str | None = None
    created_at: str
    closed_at: str | None = None
    closure_reason: str | None = None


def _to_case_out_v1(case: Any) -> CaseOutV1:
    return CaseOutV1(
        case_id=case.case_id,
        title=case.title,
        severity=case.severity,
        status=case.status.value,
        vendor_id=case.vendor_id,
        invoice_id=case.invoice_id,
        exposure_eur=case.exposure_eur,
        decision=case.decision,
        assignee=case.assignee,
        created_at=case.created_at.isoformat() if case.created_at else "",
        closed_at=case.closed_at.isoformat() if case.closed_at else None,
        closure_reason=case.closure_reason,
    )


@router.get("/cases", response_model=list[CaseOutV1])
def list_cases_v1(
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
    case_id: str | None = None,
    invoice_id: str | None = None,
    vendor_id: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    assignee: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
) -> list[CaseOutV1]:
    """Liste paginée des cases avec filtres (status/severity/assignee)."""
    cases = service.list_cases()
    rows: list[CaseOutV1] = []
    for c in cases:
        if case_id and c.case_id != case_id:
            continue
        if invoice_id and c.invoice_id != invoice_id:
            continue
        if vendor_id and c.vendor_id != vendor_id:
            continue
        if status and c.status.value != status:
            continue
        if severity and c.severity != severity:
            continue
        if assignee and c.assignee != assignee:
            continue
        rows.append(_to_case_out_v1(c))
        if len(rows) >= limit:
            break
    return rows


# ─── 3. Cases — comment + bulk ──────────────────────────────────────────────


@router.post("/cases/{case_id}/comment", response_model=dict)
def case_comment(
    case_id: str,
    body: CommentBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> dict:
    try:
        service.comment(case_id, actor=body.actor, text=body.text)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "case_id": case_id}


@router.post("/cases/bootstrap", response_model=CaseOutV1)
def case_bootstrap(
    body: CaseBootstrapBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> CaseOutV1:
    token = f"{body.rule_id}::{body.invoice_id}"
    for case in service.list_cases():
        if token in (case.finding_ids or []):
            return _to_case_out_v1(case)
        if case.invoice_id == body.invoice_id and case.vendor_id == body.vendor_id:
            return _to_case_out_v1(case)

    try:
        severity = Severity(body.severity)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"severity invalide : {body.severity}. "
                'Choisir parmi ["low", "medium", "high", "critical"].'
            ),
        ) from exc

    finding = Finding(
        invoice_id=body.invoice_id,
        detector="workflow",
        signal=body.signal,
        severity=severity,
        rule_id=body.rule_id,
        evidence={
            "vendor_id": body.vendor_id,
            "vendor_name": body.vendor_name,
            "exposure_eur": body.exposure_eur,
            "risk_score": body.risk_score,
            "finding_id": body.finding_id,
        },
    )
    case = service.create_case_from_finding(
        finding,
        actor=body.actor,
        title=body.title or f"{body.rule_id} - {body.invoice_id}",
        vendor_id=body.vendor_id,
    )
    return _to_case_out_v1(case)


_STATUS_UPDATE_MAP = {
    "new": CaseStatus.NEW,
    "triaged": CaseStatus.TRIAGED,
    "in_progress": CaseStatus.IN_PROGRESS,
}


@router.post("/cases/{case_id}/status", response_model=CaseOutV1)
def case_status_update(
    case_id: str,
    body: StatusBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> CaseOutV1:
    try:
        if body.status == "escalated":
            case = service.escalate(
                case_id,
                actor=body.actor,
                channel=body.channel or "audit-workflow",
                reason=(body.reason or "Escalade depuis le workflow web.").strip(),
            )
        else:
            target = _STATUS_UPDATE_MAP.get(body.status)
            if target is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"status invalide : {body.status}. "
                        'Choisir parmi ["new", "triaged", "in_progress", "escalated"].'
                    ),
                )
            case = service.set_status(case_id, target, actor=body.actor)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (CaseClosedError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_case_out_v1(case)


@router.post("/cases/{case_id}/decision", response_model=CaseOutV1)
def case_decision_update(
    case_id: str,
    body: DecisionBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> CaseOutV1:
    try:
        case = service.set_decision(case_id, body.decision, actor=body.actor)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (CaseClosedError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                str(exc)
                if not isinstance(exc, ValueError)
                else f"{exc} Decisions valides: {sorted(ALLOWED_CASE_DECISIONS)}."
            ),
        ) from exc
    return _to_case_out_v1(case)


@router.post("/cases/bulk/assign", response_model=BulkResult)
def cases_bulk_assign(
    body: BulkAssignBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> BulkResult:
    n_ok = 0
    errors: list[str] = []
    for cid in body.case_ids:
        try:
            service.assign(cid, body.assignee, actor=body.actor)
            n_ok += 1
        except (CaseNotFoundError, CaseClosedError):
            errors.append(cid)
    return BulkResult(n_ok=n_ok, n_errors=len(errors), error_case_ids=errors)


_STATUS_MAP = {
    "confirmed": CaseStatus.CLOSED_CONFIRMED,
    "rejected": CaseStatus.CLOSED_REJECTED,
    "false_positive": CaseStatus.CLOSED_FALSE_POSITIVE,
}


@router.post("/cases/bulk/close", response_model=BulkResult)
def cases_bulk_close(
    body: BulkCloseBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> BulkResult:
    target = _STATUS_MAP.get(body.status)
    if target is None:
        raise HTTPException(
            status_code=400,
            detail=f"status invalide : {body.status}. Choisir parmi {list(_STATUS_MAP)}.",
        )
    n_ok = 0
    errors: list[str] = []
    for cid in body.case_ids:
        try:
            service.close(cid, target, actor=body.actor, reason=body.reason)
            n_ok += 1
        except (CaseNotFoundError, CaseClosedError, ValueError):
            errors.append(cid)
    return BulkResult(n_ok=n_ok, n_errors=len(errors), error_case_ids=errors)


@router.get("/graph", response_model=P2PDemoDataset)
def p2p_graph_dataset(
    _: Annotated[str, Depends(_require_auth_v1)],
    cluster_min_size: int = Query(3, ge=2, le=20),
    max_findings: int = Query(420, ge=1, le=1000),
) -> P2PDemoDataset:
    """Dataset graphe P2P public-safe, compatible avec la demo Vercel.

    Le frontend garde un JSON statique pour la demo publique, mais cet endpoint
    expose le meme contrat cote FastAPI pour preparer une passerelle quasi-live
    sans changer les composants sigma.js.
    """
    from p2p_fraud.services.p2p_graph_demo import load_default_dataset

    try:
        payload = load_default_dataset(
            cluster_min_size=cluster_min_size,
            max_findings=max_findings,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Dataset graphe indisponible: {exc}",
        ) from exc
    return P2PDemoDataset.model_validate(payload)


class GraphNode(BaseModel):
    id: str
    kind: str  # "vendor" | "iban"
    label: str


class GraphEdge(BaseModel):
    source: str
    target: str


class RingsGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    n_shared_iban_rings: int
    n_vendor_clusters: int
    largest_cluster_size: int
    scenario: str


@router.get("/rings", response_model=RingsGraph)
def rings_graph(
    _: Annotated[str, Depends(_require_auth_v1)],
    scenario: str = Query("anneau_fraude"),
) -> RingsGraph:
    """Charge un scénario synthétique et retourne le graphe vendor↔IBAN.

    Phase 3b — alimente la visualisation sigma.js côté Next.js sans nécessiter
    qu'un dataset soit uploadé en session. Réutilise les scénarios P5-2 +
    `detect_fraud_rings` (NetworkX).
    """
    from p2p_fraud.detectors.graph import detect_fraud_rings
    from p2p_fraud.synthetic.scenarios import SCENARIOS, load_scenario

    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scénario inconnu. Choix : {list(SCENARIOS)}.")

    invoices, _vendors, _events = load_scenario(scenario)  # type: ignore[arg-type]
    # Les invoices contiennent déjà vendor_name + iban (cf. generator.py)
    # — pas besoin de merge depuis vendors (qui causerait des suffixes _x/_y).
    _findings, analysis = detect_fraud_rings(invoices)

    # Sérialise le NetworkX graph : tuple (kind, value) → id string lisible
    def _node_id(node: object) -> str:
        if isinstance(node, tuple) and len(node) == 2:
            return f"{node[0]}::{node[1]}"
        return str(node)

    def _node_label(node: object) -> str:
        if isinstance(node, tuple) and len(node) == 2:
            value = str(node[1])
            return (value[:18] + "…") if len(value) > 20 else value
        return str(node)

    nodes: list[GraphNode] = []
    for n, data in analysis.graph.nodes(data=True):
        nodes.append(
            GraphNode(
                id=_node_id(n),
                kind=str(data.get("kind", "?")),
                label=_node_label(n),
            )
        )
    edges: list[GraphEdge] = [
        GraphEdge(source=_node_id(s), target=_node_id(t)) for s, t in analysis.graph.edges()
    ]

    return RingsGraph(
        nodes=nodes,
        edges=edges,
        n_shared_iban_rings=analysis.n_shared_iban_rings,
        n_vendor_clusters=analysis.n_vendor_clusters,
        largest_cluster_size=analysis.largest_cluster_size,
        scenario=scenario,
    )


class ScenarioMeta(BaseModel):
    name: str
    title: str
    pillar: str
    severity: str
    short: str
    detectors: list[str]
    target_vendor: str | None = None
    storyline: str


@router.get("/scenarios", response_model=list[ScenarioMeta])
def list_scenarios_endpoint(
    _: Annotated[str, Depends(_require_auth_v1)],
) -> list[ScenarioMeta]:
    """Liste les 5 scénarios pré-chargés disponibles (P5-2).

    Phase 7 — alimente la Sandbox commerciale Next.js. Les scénarios sont
    déterministes (seed fixé) et générables côté backend via
    `synthetic.scenarios.load_scenario(name)`.
    """
    from p2p_fraud.synthetic.scenarios import list_scenarios

    return [
        ScenarioMeta(
            name=m.name,
            title=m.title,
            pillar=m.pillar,
            severity=m.severity,
            short=m.short,
            detectors=list(m.detectors),
            target_vendor=m.target_vendor,
            storyline=m.storyline,
        )
        for m in list_scenarios()
    ]


# ─── 4. Audit log ────────────────────────────────────────────────────────────


@router.get("/audit", response_model=AuditPage)
def audit_list(
    _: Annotated[str, Depends(_require_auth_v1)],
    audit: Annotated[AuditLog, Depends(_get_service)],  # service.audit_log injecté
    cursor: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> AuditPage:
    """Audit log paginated. `cursor` = seq de départ (exclusif)."""
    if hasattr(audit, "audit_log"):
        audit = audit.audit_log  # type: ignore[assignment]
    entries = audit.all()
    filtered = [e for e in entries if e.seq > cursor][:limit]
    cursor_next = filtered[-1].seq if filtered and len(filtered) == limit else None
    return AuditPage(
        entries=[
            AuditEntryOut(
                seq=e.seq,
                at=e.at,
                actor=e.actor,
                kind=e.kind,
                payload=e.payload,
                prev_hash=e.prev_hash,
                hash=e.hash,
                signature=e.signature or "",
            )
            for e in filtered
        ],
        total=len(entries),
        cursor_next=cursor_next,
    )


@router.get("/audit/verify", response_model=AuditVerifyResult)
def audit_verify(
    _: Annotated[str, Depends(_require_auth_v1)],
    audit_or_service: Annotated[Any, Depends(_get_service)],
) -> AuditVerifyResult:
    """Recalcul du hash chain + validation des signatures Ed25519 (P5-5)."""
    from p2p_fraud.security.signing import make_signer_from_settings

    audit: AuditLog = (
        audit_or_service.audit_log if hasattr(audit_or_service, "audit_log") else audit_or_service
    )
    signer = make_signer_from_settings()
    valid, invalid = audit.verify_chain(public_key_b64=signer.public_key_b64)
    entries = audit.all()
    n_signed = sum(1 for e in entries if e.signature)
    return AuditVerifyResult(
        valid=valid,
        invalid_seqs=invalid,
        n_total=len(entries),
        n_signed=n_signed,
        public_key_b64=signer.public_key_b64,
    )


# ─── 5. Exports PDF ──────────────────────────────────────────────────────────


@router.get(
    "/exports/dossier.pdf",
    responses={200: {"content": {"application/pdf": {}}}},
)
def export_dossier_pdf(
    case_id: str,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> StreamingResponse:
    """Génère et streame un dossier PDF d'enquête (weasyprint si installé).

    Phase 0 — version minimale : renvoie un PDF placeholder via reportlab/
    weasyprint si disponibles, sinon un message en texte.
    """
    try:
        case = service.get(case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Tentative weasyprint (déjà en deps)
    try:
        from weasyprint import HTML

        html = (
            f"<h1>Dossier d'enquête — {case.case_id}</h1>"
            f"<p><strong>Vendor</strong> : {case.vendor_id or '—'}</p>"
            f"<p><strong>Sévérité</strong> : {case.severity}</p>"
            f"<p><strong>Exposition</strong> : {case.exposure_eur or 0:.2f} €</p>"
            f"<p><strong>Titre</strong> : {case.title}</p>"
            f"<p><strong>Statut</strong> : {case.status.value}</p>"
            f"<p><em>Généré le {datetime.now(UTC).isoformat()} — démonstration pédagogique.</em></p>"
        )
        pdf_bytes = HTML(string=html).write_pdf()
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="dossier_{case.case_id}.pdf"'},
        )
    except Exception as exc:
        body = (
            f"Dossier {case.case_id} — vendor {case.vendor_id} — "
            f"exposition {case.exposure_eur or 0:.2f} €. (weasyprint indisponible : {exc})"
        ).encode()
        return StreamingResponse(
            iter([body]),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="dossier_{case.case_id}.txt"'},
        )


# ─── 6. LLM narrative streaming ──────────────────────────────────────────────


@router.post(
    "/llm/narrative",
    responses={200: {"content": {"text/event-stream": {}}}},
)
def llm_narrative_stream(
    body: NarrativeBody,
    _: Annotated[str, Depends(_require_auth_v1)],
) -> StreamingResponse:
    """Génère la narration d'audit ISA 240 en streaming SSE.

    Format Server-Sent Events compatible Vercel AI SDK (`useChat`/`useCompletion`).
    Le front Next.js consomme via `EventSource` ou fetch streaming.
    """
    from p2p_fraud.llm.narrative_generator import generate_vendor_narrative_stream

    def _sse_iter():
        try:
            for chunk in generate_vendor_narrative_stream(
                vendor_id=body.vendor_id,
                vendor_name=body.vendor_name,
                siren=body.siren,
                total_paid_eur=body.total_paid_eur,
                n_invoices=body.n_invoices,
                is_sanctioned=body.is_sanctioned,
                is_pep=body.is_pep,
                findings=body.findings,
                api_key=body.api_key,
            ):
                # Format SSE : `data: <json>\n\n`
                yield f"data: {json.dumps({'text': chunk})}\n\n".encode()
            yield b"data: [DONE]\n\n"
        except Exception as exc:
            err = json.dumps({"error": str(exc)})
            yield f"data: {err}\n\n".encode()

    return StreamingResponse(
        _sse_iter(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # désactive buffering nginx/proxies
        },
    )
