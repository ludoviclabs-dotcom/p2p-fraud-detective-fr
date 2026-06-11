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
import time
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


def _get_rule_store() -> Any:
    """Stub : l'instance RuleStore réelle est injectée par `main.py`."""
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


def _to_audit_entry_out(entry: Any) -> AuditEntryOut:
    return AuditEntryOut(
        seq=entry.seq,
        at=entry.at,
        actor=entry.actor,
        kind=entry.kind,
        payload=entry.payload,
        prev_hash=entry.prev_hash,
        hash=entry.hash,
        signature=entry.signature,
    )


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


class AuditExplainResult(BaseModel):
    """Verdict technique (code) + explication audit (IA structurée, ADR-0007)."""

    chain_status: str  # "intact" | "broken" | "empty"
    n_total: int
    n_signed: int
    invalid_seqs: list[int] = Field(default_factory=list)
    signatures_checked: bool = False
    explanation: dict[str, Any]  # AuditExplanation sérialisé (llm/schemas.py)
    model: str
    prompt_version: str


class FeedbackRuleStats(BaseModel):
    """Verdicts de clôture agrégés par rule_id — boucle de feedback détection."""

    rule_id: str
    n_closed: int
    n_confirmed: int
    n_false_positive: int
    n_rejected: int
    false_positive_rate: float


class FeedbackStats(BaseModel):
    n_cases_closed: int
    rules: list[FeedbackRuleStats] = Field(default_factory=list)


class Case360Result(BaseModel):
    """Dossier d'enquête généré (FraudCase360, llm/schemas.py) + métadonnées IA."""

    case_id: str
    dossier: dict[str, Any]  # FraudCase360 sérialisé
    model: str
    prompt_version: str


class AIUsageBucketOut(BaseModel):
    """Agrégat d'usage IA (llm/ai_ledger.py) — dashboard de coût."""

    n_calls: int
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cost_usd: float
    n_calls_unpriced: int
    models: list[str] = Field(default_factory=list)


class AIUsageOut(BaseModel):
    total: AIUsageBucketOut
    by_feature: dict[str, AIUsageBucketOut] = Field(default_factory=dict)


class SourceFreshnessOut(BaseModel):
    """Fraîcheur d'une source externe (enrichment/freshness.py)."""

    source: str
    label: str
    configured: bool
    last_sync: str | None = None
    detail: str = ""


class CoverageItem(BaseModel):
    """Couverture d'un détecteur sur le dataset contrôlé (ISA 240)."""

    detector: str
    executed: bool
    n_findings: int = 0
    n_invoices_flagged: int = 0
    clean_rate: float | None = None  # part des factures sans alerte de ce détecteur
    reason: str = ""  # motif si non exécuté


class CoverageOut(BaseModel):
    scenario: str
    n_invoices: int
    n_detectors_executed: int
    overall_clean_rate: float  # part des factures sans aucune alerte
    items: list[CoverageItem] = Field(default_factory=list)


class CopilotQuestionOut(BaseModel):
    question_id: str
    label_fr: str


class CopilotAskBody(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=64)
    case_id: str = Field(..., min_length=1, max_length=128)
    actor: str = Field(default="api", max_length=128)


class CopilotResult(BaseModel):
    """Réponse du copilote (CopilotAnswer, llm/schemas.py) + métadonnées IA."""

    case_id: str
    question_id: str
    answer: dict[str, Any]
    model: str
    prompt_version: str


class ReplayResult(BaseModel):
    """Séquence Risk Replay (RiskReplay, llm/schemas.py) + métadonnées IA."""

    case_id: str
    replay: dict[str, Any]
    model: str
    prompt_version: str


class ScenarioNarrativeResult(BaseModel):
    """Habillage narratif d'un scénario (ScenarioNarrative) + métadonnées IA."""

    scenario_id: str
    narrative: dict[str, Any]
    model: str
    prompt_version: str


class RuleDraftBody(BaseModel):
    """Demande de draft d'une règle de détection depuis le français (Phase 4)."""

    description_fr: str = Field(..., min_length=20, max_length=4000)
    author: str = Field(..., min_length=1, max_length=128)


class RuleBacktestBody(BaseModel):
    """Backtest synthétique par défaut ; passer `records` pour des données réelles.

    `records` : factures labellisées fournies par le client (boucle de
    feedback : verdicts de clôture exportés, ou extraction comptable
    annotée). Champ `is_fraud` optionnel par record pour la précision.
    """

    n_invoices: int = Field(default=2000, ge=100, le=20000)
    seed: int = Field(default=42)
    actor: str = Field(default="api", max_length=128)
    records: list[dict[str, Any]] | None = Field(
        default=None,
        max_length=20000,
        description="Records labellisés réels ; si fourni, remplace le dataset synthétique.",
    )


class RuleActivateBody(BaseModel):
    approver: str = Field(..., min_length=1, max_length=128)


class RuleVersionOut(BaseModel):
    """Version de règle sérialisée (rules/store.py)."""

    rule_id: str
    version: int
    status: str
    yaml: str
    author: str
    created_at: str
    name: str
    severity: str
    reason_code: str
    tests: list[dict[str, Any]] = Field(default_factory=list)
    test_report: dict[str, Any] | None = None
    backtest: dict[str, Any] | None = None
    approved_by: str | None = None
    activated_at: str | None = None


def _to_rule_version_out(v: Any) -> RuleVersionOut:
    report = v.test_report
    backtest = v.backtest
    return RuleVersionOut(
        rule_id=v.rule_id,
        version=v.version,
        status=v.status,
        yaml=v.yaml,
        author=v.author,
        created_at=v.created_at,
        name=v.name,
        severity=v.severity,
        reason_code=v.reason_code,
        tests=[c.model_dump(mode="json") for c in v.test_cases],
        test_report=report.model_dump(mode="json") if report else None,
        backtest=backtest.model_dump(mode="json") if backtest else None,
        approved_by=v.approved_by,
        activated_at=v.activated_at,
    )


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
        entries=[_to_audit_entry_out(e) for e in filtered],
        total=len(entries),
        cursor_next=cursor_next,
    )


def _sse_event(event: str, payload: dict[str, Any], *, event_id: int | None = None) -> bytes:
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(payload, ensure_ascii=False, default=str)}")
    return ("\n".join(lines) + "\n\n").encode("utf-8")


@router.get(
    "/alerts/stream",
    responses={200: {"content": {"text/event-stream": {}}}},
)
def alerts_stream(
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
    cursor: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    poll_seconds: float = Query(5.0, ge=1.0, le=60.0),
    once: bool = Query(False),
) -> StreamingResponse:
    """Stream SSE des événements d'audit récents pour la page Alertes.

    Le flux émet les entrées `audit_log` sous forme d'événements `audit`.
    `once=true` sert aux tests et aux clients qui veulent une réponse finie.
    """

    def event_stream():
        last_seq = cursor
        while True:
            entries = [entry for entry in service.audit_log.all() if entry.seq > last_seq]
            for entry in entries[:limit]:
                last_seq = max(last_seq, entry.seq)
                yield _sse_event(
                    "audit",
                    _to_audit_entry_out(entry).model_dump(mode="json"),
                    event_id=entry.seq,
                )
            if once:
                break
            yield _sse_event(
                "heartbeat",
                {
                    "at": datetime.now(UTC).isoformat(),
                    "cursor": last_seq,
                },
            )
            time.sleep(poll_seconds)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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


@router.post("/audit/explain", response_model=AuditExplainResult)
def audit_explain(
    _: Annotated[str, Depends(_require_auth_v1)],
    audit_or_service: Annotated[Any, Depends(_get_service)],
) -> AuditExplainResult:
    """Vérifie la chaîne (code déterministe) puis traduit le verdict en langage audit.

    Feature pilote du socle IA de confiance (ADR-0007) : le LLM n'effectue
    aucune vérification — il explique le verdict déjà calculé par
    `verify_chain()`. Sortie structurée, sourcée (provenance validée en code)
    et journalisée au ledger `ai.generation` du même audit log.
    """
    from p2p_fraud.llm.audit_explainer import compute_verdict, explain_verdict
    from p2p_fraud.security.signing import make_signer_from_settings

    audit: AuditLog = (
        audit_or_service.audit_log if hasattr(audit_or_service, "audit_log") else audit_or_service
    )
    signer = make_signer_from_settings()
    verdict = compute_verdict(audit, public_key_b64=signer.public_key_b64)
    try:
        result = explain_verdict(verdict, audit_log=audit, actor="api")
    except ValueError as exc:
        # Clé API absente ou sortie inexploitable → 503 explicite, pas de 500 opaque.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AuditExplainResult(
        chain_status=verdict.chain_status.value,
        n_total=verdict.n_total,
        n_signed=verdict.n_signed,
        invalid_seqs=verdict.invalid_seqs,
        signatures_checked=verdict.signatures_checked,
        explanation=result.output.model_dump(mode="json"),
        model=result.model,
        prompt_version=result.prompt_version,
    )


@router.get("/cases/feedback-stats", response_model=FeedbackStats)
def cases_feedback_stats(
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> FeedbackStats:
    """Verdicts de clôture agrégés par rule_id — boucle de feedback détection.

    Les statuts CLOSED_CONFIRMED / CLOSED_FALSE_POSITIVE / CLOSED_REJECTED
    capturés à la clôture des cas sont agrégés par règle (le rule_id est
    encodé dans les finding_ids sous la forme "RULE::invoice"). C'est la
    matière première du backtest de règles du futur Detection Studio.
    """
    confirmed: Counter[str] = Counter()
    false_positive: Counter[str] = Counter()
    rejected: Counter[str] = Counter()
    n_closed = 0
    for case in service.list_cases():
        if not case.status.is_closed:
            continue
        n_closed += 1
        rule_ids = {fid.split("::", 1)[0] for fid in case.finding_ids if fid}
        for rule_id in rule_ids or {"unknown"}:
            if case.status == CaseStatus.CLOSED_CONFIRMED:
                confirmed[rule_id] += 1
            elif case.status == CaseStatus.CLOSED_FALSE_POSITIVE:
                false_positive[rule_id] += 1
            elif case.status == CaseStatus.CLOSED_REJECTED:
                rejected[rule_id] += 1
    rules = []
    for rule_id in sorted(set(confirmed) | set(false_positive) | set(rejected)):
        total = confirmed[rule_id] + false_positive[rule_id] + rejected[rule_id]
        rules.append(
            FeedbackRuleStats(
                rule_id=rule_id,
                n_closed=total,
                n_confirmed=confirmed[rule_id],
                n_false_positive=false_positive[rule_id],
                n_rejected=rejected[rule_id],
                false_positive_rate=(false_positive[rule_id] / total) if total else 0.0,
            )
        )
    return FeedbackStats(n_cases_closed=n_closed, rules=rules)


@router.post("/cases/{case_id}/case360", response_model=Case360Result)
def case_generate_case360(
    case_id: str,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> Case360Result:
    """Génère le dossier d'enquête FraudCase360 d'un cas (Phase 3, ADR-0007).

    Le source pack est construit depuis le cas et ses événements de workflow ;
    la provenance de chaque fait est validée en code ; `human_review_required`
    est forcé à true ; l'appel est journalisé au ledger ai.generation.
    """
    from p2p_fraud.llm.case360 import generate_case360

    try:
        case = service.get(case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    events = service.list_events(case_id)
    try:
        result = generate_case360(
            case,
            events=events,
            audit_log=service.audit_log,
            actor="api",
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Case360Result(
        case_id=case.case_id,
        dossier=result.output.model_dump(mode="json"),
        model=result.model,
        prompt_version=result.prompt_version,
    )


# ─── 4qua. Gouvernance : coût IA, fraîcheur des sources, couverture ─────────


@router.get("/ai/usage", response_model=AIUsageOut)
def ai_usage(
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> AIUsageOut:
    """Dashboard de coût IA — agrégation des entrées `ai.generation` du ledger.

    Chaque appel IA est déjà journalisé (modèle, tokens in/out/cachés) dans
    l'audit log signé ; on additionne et on valorise via la table de prix
    publique (ADR-0007 décision C). Modèle hors table → compté non valorisé.
    """
    from p2p_fraud.llm.ai_ledger import aggregate_ai_usage

    total, by_feature = aggregate_ai_usage(service.audit_log)

    def _out(bucket: Any) -> AIUsageBucketOut:
        return AIUsageBucketOut(
            n_calls=bucket.n_calls,
            input_tokens=bucket.input_tokens,
            output_tokens=bucket.output_tokens,
            cached_tokens=bucket.cached_tokens,
            cost_usd=round(bucket.cost_usd, 6),
            n_calls_unpriced=bucket.n_calls_unpriced,
            models=sorted(bucket.models),
        )

    return AIUsageOut(
        total=_out(total),
        by_feature={k: _out(v) for k, v in sorted(by_feature.items())},
    )


@router.get("/sources/freshness", response_model=list[SourceFreshnessOut])
def sources_freshness(
    _: Annotated[str, Depends(_require_auth_v1)],
) -> list[SourceFreshnessOut]:
    """Fraîcheur des sources externes (Sirene, DECP, sanctions, Pappers).

    `last_sync` = dernier appel réussi enregistré par le client de la source.
    Une source jamais synchronisée ou périmée est un risque d'audit à
    surfacer, pas à masquer.
    """
    from p2p_fraud.enrichment.freshness import get_freshness

    return [SourceFreshnessOut(**row) for row in get_freshness()]


@router.get("/coverage", response_model=CoverageOut)
def coverage(
    _: Annotated[str, Depends(_require_auth_v1)],
    store: Annotated[Any, Depends(_get_rule_store)],
    scenario: str = Query(default="bec_iban_swap"),
) -> CoverageOut:
    """Vue de couverture ISA 240 — ce qui a été contrôlé, pas seulement alerté.

    Exécute les détecteurs purs sur le dataset déterministe du scénario et
    rapporte, par détecteur : population contrôlée, factures signalées et
    part « propre ». Les détecteurs dépendant d'API externes sont déclarés
    non exécutés avec leur motif (la complétude se prouve, elle ne se
    suppose pas).
    """
    from p2p_fraud.detectors.duplicates import detect_duplicates
    from p2p_fraud.detectors.sanctions import detect_sanctioned_vendors
    from p2p_fraud.detectors.thresholds import detect_under_threshold
    from p2p_fraud.rules.runtime import dataframe_to_records, run_active_rules
    from p2p_fraud.synthetic.scenarios import SCENARIOS, load_scenario

    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scénario inconnu. Choix : {list(SCENARIOS)}.")
    invoices, _vendors, _events = load_scenario(scenario)
    n_invoices = len(invoices)
    records = dataframe_to_records(invoices)

    executed: list[tuple[str, list]] = [
        ("duplicates", detect_duplicates(invoices)),
        ("thresholds", detect_under_threshold(invoices)),
        ("sanctions", detect_sanctioned_vendors(invoices)),
        ("rule_studio", run_active_rules(records, store)),
    ]
    items: list[CoverageItem] = []
    flagged_any: set[str] = set()
    for name, findings in executed:
        flagged = {f.invoice_id for f in findings}
        flagged_any |= flagged
        items.append(
            CoverageItem(
                detector=name,
                executed=True,
                n_findings=len(findings),
                n_invoices_flagged=len(flagged),
                clean_rate=round(1 - len(flagged) / n_invoices, 4) if n_invoices else None,
            )
        )
    for name, reason in (
        ("sirene", "API INSEE externe — exécuté à la demande (page Sirene)"),
        ("decp_rbe", "API DECP/RBE externe — exécuté à la demande"),
        ("master_data", "nécessite l'historique master data de la session"),
        ("isolation_forest", "modèle ML — exécuté depuis la page Anomalies"),
        ("benford", "outil de scoping — hors périmètre alerte (ADR-0002)"),
    ):
        items.append(CoverageItem(detector=name, executed=False, reason=reason))

    return CoverageOut(
        scenario=scenario,
        n_invoices=n_invoices,
        n_detectors_executed=len(executed),
        overall_clean_rate=round(1 - len(flagged_any) / n_invoices, 4) if n_invoices else 0.0,
        items=items,
    )


# ─── 4ter. Copilote analyste + Risk Replay + narratif scénarios (P5-P6) ─────


@router.get("/copilot/questions", response_model=list[CopilotQuestionOut])
def copilot_questions(
    _: Annotated[str, Depends(_require_auth_v1)],
) -> list[CopilotQuestionOut]:
    """Catalogue des questions prédéfinies du copilote (pas de chat libre)."""
    from p2p_fraud.llm.copilot import QUESTIONS

    return [
        CopilotQuestionOut(question_id=q.question_id, label_fr=q.label_fr)
        for q in QUESTIONS.values()
    ]


@router.post("/copilot/ask", response_model=CopilotResult)
def copilot_ask(
    body: CopilotAskBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> CopilotResult:
    """Répond à une question prédéfinie sur un cas (Phase 5, ADR-0007).

    Le modèle ne voit que le source pack du cas (surface d'outils contrôlée
    en code) ; provenance validée ; revue humaine toujours requise.
    """
    from p2p_fraud.llm.copilot import ask_copilot

    try:
        case = service.get(body.case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    events = service.list_events(body.case_id)
    try:
        result = ask_copilot(
            body.question_id,
            case,
            events=events,
            audit_log=service.audit_log,
            actor=body.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CopilotResult(
        case_id=case.case_id,
        question_id=body.question_id,
        answer=result.output.model_dump(mode="json"),
        model=result.model,
        prompt_version=result.prompt_version,
    )


@router.post("/cases/{case_id}/replay", response_model=ReplayResult)
def case_generate_replay(
    case_id: str,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> ReplayResult:
    """Rejoue un cas en séquence narrative d'enquête (Phase 6, ADR-0007)."""
    from p2p_fraud.llm.replay import generate_replay

    try:
        case = service.get(case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    events = service.list_events(case_id)
    try:
        result = generate_replay(case, events=events, audit_log=service.audit_log, actor="api")
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ReplayResult(
        case_id=case.case_id,
        replay=result.output.model_dump(mode="json"),
        model=result.model,
        prompt_version=result.prompt_version,
    )


@router.post("/scenarios/{scenario_id}/narrative", response_model=ScenarioNarrativeResult)
def scenario_generate_narrative(
    scenario_id: str,
    _: Annotated[str, Depends(_require_auth_v1)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> ScenarioNarrativeResult:
    """Habillage narratif d'un scénario synthétique (Phase 6, ADR-0007).

    Les données et labels ground-truth restent générés par le code
    déterministe — le LLM ne produit que le récit pédagogique sourcé.
    """
    from p2p_fraud.llm.scenario_narrative import generate_scenario_narrative
    from p2p_fraud.synthetic.scenarios import SCENARIOS, get_scenario_meta

    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scénario inconnu. Choix : {list(SCENARIOS)}.")
    meta = get_scenario_meta(scenario_id)
    try:
        result = generate_scenario_narrative(meta, audit_log=service.audit_log, actor="api")
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ScenarioNarrativeResult(
        scenario_id=scenario_id,
        narrative=result.output.model_dump(mode="json"),
        model=result.model,
        prompt_version=result.prompt_version,
    )


# ─── 4bis. Detection Studio — règles (Phase 4, ADR-0007) ────────────────────


@router.post("/rules/draft", response_model=RuleVersionOut)
def rules_draft(
    body: RuleDraftBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    store: Annotated[Any, Depends(_get_rule_store)],
    service: Annotated[CaseService, Depends(_get_service)],
) -> RuleVersionOut:
    """Drafte une règle depuis le français (LLM), la valide et la teste en code.

    Le draft est sauvegardé en version `draft` ; ses tests générés sont
    immédiatement exécutés par le moteur déterministe (statut `tested` si
    tout est vert). L'activation reste soumise au backtest + 4-eyes.
    """
    from p2p_fraud.llm.rule_studio import draft_rule
    from p2p_fraud.rules.dsl import RuleParseError

    try:
        result = draft_rule(
            body.description_fr,
            audit_log=service.audit_log,
            actor=body.author,
        )
    except RuleParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    version = store.save_draft(result.spec, author=body.author, tests=result.test_cases)
    version = store.record_test_report(
        version.rule_id, version.version, result.test_report, actor=body.author
    )
    return _to_rule_version_out(version)


@router.get("/rules", response_model=list[RuleVersionOut])
def rules_list(
    _: Annotated[str, Depends(_require_auth_v1)],
    store: Annotated[Any, Depends(_get_rule_store)],
    rule_id: str | None = Query(default=None),
) -> list[RuleVersionOut]:
    """Liste les versions de règles (toutes, ou celles d'un rule_id)."""
    return [_to_rule_version_out(v) for v in store.list_versions(rule_id)]


@router.post("/rules/{rule_id}/versions/{version}/test", response_model=RuleVersionOut)
def rules_run_tests(
    rule_id: str,
    version: int,
    _: Annotated[str, Depends(_require_auth_v1)],
    store: Annotated[Any, Depends(_get_rule_store)],
) -> RuleVersionOut:
    """Ré-exécute les tests embarqués d'une version (moteur déterministe)."""
    from p2p_fraud.rules.store import PromotionError, RuleNotFoundError
    from p2p_fraud.rules.testing import run_rule_tests

    try:
        v = store.get(rule_id, version)
        report = run_rule_tests(v.spec, v.test_cases)
        v = store.record_test_report(rule_id, version, report, actor="api")
    except RuleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PromotionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _to_rule_version_out(v)


@router.post("/rules/{rule_id}/versions/{version}/backtest", response_model=RuleVersionOut)
def rules_backtest(
    rule_id: str,
    version: int,
    body: RuleBacktestBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    store: Annotated[Any, Depends(_get_rule_store)],
) -> RuleVersionOut:
    """Backtest sur données labellisées — réelles si `records` est fourni,
    sinon dataset synthétique (ground truth is_fraud)."""
    from p2p_fraud.rules.backtest import backtest_rule
    from p2p_fraud.rules.store import PromotionError, RuleNotFoundError

    try:
        v = store.get(rule_id, version)
    except RuleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if body.records is not None:
        if not body.records:
            raise HTTPException(status_code=422, detail="`records` fourni mais vide.")
        summary = backtest_rule(v.spec, body.records)
        try:
            v = store.record_backtest(rule_id, version, summary, actor=body.actor)
        except PromotionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _to_rule_version_out(v)

    from p2p_fraud.synthetic.generator import GeneratorConfig, generate_dataset

    invoices, _vendors = generate_dataset(
        GeneratorConfig(
            n_invoices=body.n_invoices,
            n_vendors=max(50, body.n_invoices // 10),
            seed=body.seed,
        )
    )
    records = [
        {k: (None if (isinstance(val, float) and val != val) else val) for k, val in row.items()}
        for row in invoices.to_dict("records")
    ]
    summary = backtest_rule(v.spec, records)
    try:
        v = store.record_backtest(rule_id, version, summary, actor=body.actor)
    except PromotionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _to_rule_version_out(v)


@router.post("/rules/{rule_id}/versions/{version}/activate", response_model=RuleVersionOut)
def rules_activate(
    rule_id: str,
    version: int,
    body: RuleActivateBody,
    _: Annotated[str, Depends(_require_auth_v1)],
    store: Annotated[Any, Depends(_get_rule_store)],
) -> RuleVersionOut:
    """Active une version — tests verts + backtest + 4-eyes (auteur ≠ approbateur)."""
    from p2p_fraud.rules.store import FourEyesError, PromotionError, RuleNotFoundError

    try:
        v = store.activate(rule_id, version, approver=body.approver)
    except RuleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FourEyesError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except PromotionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _to_rule_version_out(v)


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
