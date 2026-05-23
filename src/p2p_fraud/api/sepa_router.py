"""Endpoints FastAPI `/api/v1/mandates` + `/api/v1/debits` — Sprint 3 SEPA.

Router séparé pour clarté + versioning. Toutes les routes :
- valident l'entrée via Pydantic
- exigent `Depends(_require_auth_sepa)` (override depuis main.py)
- isolent par `tenant_id` quand fourni en header `X-Tenant-Id`
- créent un événement dans l'audit log Ed25519 existant via le service

Le service `SepaAnalyzer` est injecté via `Depends(_get_analyzer)` qui
est override depuis `main.py` (cf. dépendance `_case_service` historique).
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from p2p_fraud.api.webhook_security import (
    VerifiedWebhook,
    WebhookIdempotencyStore,
    verify_inbound_webhook,
)
from p2p_fraud.evidence.service import (
    EvidenceService,
    EvidenceSubjectNotFoundError,
    EvidenceSubjectNotSupported,
)
from p2p_fraud.evidence.types import EvidencePackInput
from p2p_fraud.sepa.analyzer import AnalyzedDebit, SepaAnalyzer
from p2p_fraud.sepa.debit_event import DebitEventInput
from p2p_fraud.sepa.mandate import (
    MandateInput,
    MandateNotFoundError,
    MandateRecord,
    MandateStateError,
)
from p2p_fraud.sepa.matcher import MatchResult
from p2p_fraud.sepa.types import MandateStatus

router = APIRouter(prefix="/api/v1", tags=["SEPA (MandateGuard)"])


# ─── Stubs de dépendances (override par main.py) ────────────────────────────


def _require_auth_sepa() -> str:
    """Stub : la vraie auth est injectée par `main.py`."""
    return "anonymous"


def _get_analyzer() -> SepaAnalyzer:
    """Stub : l'instance SepaAnalyzer réelle est injectée par `main.py`."""
    raise NotImplementedError("Override via main.app.dependency_overrides")


def _get_evidence_service() -> EvidenceService:
    """Stub : l'instance EvidenceService réelle est injectée par `main.py`."""
    raise NotImplementedError("Override via main.app.dependency_overrides")


def _get_webhook_idempotency_store() -> WebhookIdempotencyStore:
    """Stub : store d'idempotence webhook injecté par `main.py`."""
    raise NotImplementedError("Override via main.app.dependency_overrides")


# ─── Modèles I/O ─────────────────────────────────────────────────────────────


class MandateOut(BaseModel):
    """Vue publique d'un mandat — pas d'IBAN clair."""

    mandate_id: str
    tenant_id: str | None
    creditor_id: str
    creditor_ics: str
    creditor_name: str | None
    debtor_account_id: str
    debtor_iban_fingerprint: str
    rum: str
    scheme: str
    sequence_type: str
    status: str
    max_amount_cents: int | None
    currency: str
    frequency: str | None
    valid_from: str | None
    valid_to: str | None
    signed_at: str | None
    revoked_at: str | None
    commitment_hash: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_record(cls, m: MandateRecord) -> MandateOut:
        return cls(
            mandate_id=m.mandate_id,
            tenant_id=m.tenant_id,
            creditor_id=m.creditor_id,
            creditor_ics=m.creditor_ics,
            creditor_name=m.creditor_name,
            debtor_account_id=m.debtor_account_id,
            debtor_iban_fingerprint=m.debtor_iban_fingerprint,
            rum=m.rum,
            scheme=m.scheme.value,
            sequence_type=m.sequence_type.value,
            status=m.status.value,
            max_amount_cents=m.max_amount_cents,
            currency=m.currency,
            frequency=m.frequency,
            valid_from=m.valid_from,
            valid_to=m.valid_to,
            signed_at=m.signed_at,
            revoked_at=m.revoked_at,
            commitment_hash=m.commitment_hash,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class MandateActionRequest(BaseModel):
    actor: str = "api"
    reason: str | None = None
    signature_provider: str | None = None
    signature_evidence_key: str | None = None


class RevokeRequest(BaseModel):
    actor: str = "api"
    reason: str | None = None


class SignalOut(BaseModel):
    code: str
    title: str
    message: str
    severity: str
    score: int
    evidence: dict[str, Any]


class MatchOut(BaseModel):
    matched: bool
    mandate_id: str | None
    candidates_active: int
    candidates_inactive: int
    warnings: list[str]


class DebitAnalysisOut(BaseModel):
    event_id: str
    domain: str
    score: int
    level: str
    decision: str
    engine_version: str
    signals: list[SignalOut]
    match: MatchOut


def _analysis_to_out(result: AnalyzedDebit) -> DebitAnalysisOut:
    return DebitAnalysisOut(
        event_id=result.event.event_id,
        domain=result.assessment.domain.value,
        score=result.assessment.score,
        level=result.assessment.level.value,
        decision=result.assessment.decision.value,
        engine_version=result.assessment.engine_version,
        signals=[
            SignalOut(
                code=s.code,
                title=s.title,
                message=s.message,
                severity=s.severity.value,
                score=s.score,
                evidence=s.evidence,
            )
            for s in result.assessment.signals
        ],
        match=_match_to_out(result.match),
    )


def _match_to_out(match: MatchResult) -> MatchOut:
    return MatchOut(
        matched=match.matched,
        mandate_id=match.mandate.mandate_id if match.mandate else None,
        candidates_active=len(match.candidates),
        candidates_inactive=len(match.inactive_candidates),
        warnings=[w.value for w in match.warnings],
    )


# ─── Endpoints Mandats ───────────────────────────────────────────────────────


@router.post("/mandates", response_model=MandateOut, status_code=201)
def create_mandate(
    payload: MandateInput,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> MandateOut:
    """Crée un mandat SEPA en état DRAFT."""
    record = analyzer.mandates.create(payload, actor=actor, tenant_id=tenant_id)
    return MandateOut.from_record(record)


@router.get("/mandates", response_model=list[MandateOut])
def list_mandates(
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: int = 100,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> list[MandateOut]:
    """Liste les mandats du tenant (paginé simple)."""
    status_enum: MandateStatus | None = None
    if status_filter:
        try:
            status_enum = MandateStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"status invalide : {status_filter}") from exc
    records = analyzer.mandates.list(
        tenant_id=tenant_id, status=status_enum, limit=limit
    )
    return [MandateOut.from_record(r) for r in records]


@router.get("/mandates/{mandate_id}", response_model=MandateOut)
def get_mandate(
    mandate_id: str,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> MandateOut:
    record = analyzer.mandates.get(mandate_id, tenant_id=tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Mandat introuvable")
    return MandateOut.from_record(record)


@router.post("/mandates/{mandate_id}/sign", response_model=MandateOut)
def sign_mandate(
    mandate_id: str,
    request: MandateActionRequest,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> MandateOut:
    """Passe le mandat DRAFT → ACTIVE."""
    try:
        record = analyzer.mandates.sign(
            mandate_id,
            actor=request.actor or actor,
            tenant_id=tenant_id,
            signature_provider=request.signature_provider,
            signature_evidence_key=request.signature_evidence_key,
        )
    except MandateNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Mandat introuvable") from exc
    except MandateStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MandateOut.from_record(record)


@router.post("/mandates/{mandate_id}/revoke", response_model=MandateOut)
def revoke_mandate(
    mandate_id: str,
    request: RevokeRequest,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> MandateOut:
    """Révoque définitivement un mandat (état terminal)."""
    try:
        record = analyzer.mandates.revoke(
            mandate_id,
            actor=request.actor or actor,
            tenant_id=tenant_id,
            reason_text=request.reason,
        )
    except MandateNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Mandat introuvable") from exc
    except MandateStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MandateOut.from_record(record)


# ─── Endpoints Debit Events ──────────────────────────────────────────────────


@router.post("/debits/import")
def import_debit(
    payload: DebitEventInput,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> dict[str, Any]:
    """Ingestion idempotente d'un prélèvement (sans analyse)."""
    record = analyzer.debits.ingest(payload, actor=actor, tenant_id=tenant_id)
    return {
        "event_id": record.event_id,
        "idempotency_key": record.idempotency_key,
        "amount_cents": record.amount_cents,
        "currency": record.currency,
        "debtor_iban_fingerprint": record.debtor_iban_fingerprint,
        "matched_mandate_id": record.matched_mandate_id,
        "created_at": record.created_at,
    }


@router.post("/debits/analyze", response_model=DebitAnalysisOut)
def analyze_debit(
    payload: DebitEventInput,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> DebitAnalysisOut:
    """Pipeline complet ingest → match → assess SEPA + audit DEBIT_ANALYZED."""
    result = analyzer.analyze(payload, actor=actor, tenant_id=tenant_id)
    return _analysis_to_out(result)


# ─── Endpoint générique Risk Lab (SEPA scope v0) ─────────────────────────────


class RiskAssessRequest(BaseModel):
    """Payload générique d'évaluation — pour l'instant SEPA uniquement.

    Sprint 4+ : ajouter `risk_domain` discriminé pour SUPPLIER_PAYMENT.
    """

    risk_domain: str = Field(..., description="SEPA_DIRECT_DEBIT en v0")
    event: DebitEventInput


@router.post("/risk/assess", response_model=DebitAnalysisOut)
def risk_assess(
    payload: RiskAssessRequest,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> DebitAnalysisOut:
    """Endpoint Risk Lab — un seul appel pour analyser un événement synthétique."""
    if payload.risk_domain != "SEPA_DIRECT_DEBIT":
        raise HTTPException(
            status_code=400,
            detail=f"risk_domain non supporté en v0 : {payload.risk_domain}",
        )
    result = analyzer.analyze(payload.event, actor=actor, tenant_id=tenant_id)
    return _analysis_to_out(result)


# ─── Endpoints Evidence Pack ─────────────────────────────────────────────────


class EvidencePackOut(BaseModel):
    evidence_pack_id: str
    tenant_id: str | None
    subject_type: str
    subject_id: str
    domain: str
    engine_version: str
    pack_hash: str
    audit_anchor_hash: str | None
    audit_anchor_seq: int | None
    has_report: bool
    actor: str | None
    created_at: str
    payload: dict[str, Any]


class EvidenceVerifyOut(BaseModel):
    evidence_pack_id: str
    valid: bool
    hash_matches: bool
    audit_chain_valid: bool
    audit_anchor_present: bool
    checked_at: str
    errors: list[str]


@router.post("/evidence", response_model=EvidencePackOut, status_code=201)
def create_evidence_pack(
    payload: EvidencePackInput,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    evidence: Annotated[EvidenceService, Depends(_get_evidence_service)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> EvidencePackOut:
    """Crée un Evidence Pack pour un sujet (DEBIT_EVENT en v0)."""
    try:
        record = evidence.create(payload, actor=actor, tenant_id=tenant_id)
    except EvidenceSubjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Sujet introuvable : {exc}") from exc
    except EvidenceSubjectNotSupported as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _evidence_to_out(record)


@router.get("/evidence/{evidence_pack_id}", response_model=EvidencePackOut)
def get_evidence_pack(
    evidence_pack_id: str,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    evidence: Annotated[EvidenceService, Depends(_get_evidence_service)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> EvidencePackOut:
    record = evidence.get(evidence_pack_id, tenant_id=tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Evidence pack introuvable")
    return _evidence_to_out(record)


@router.get("/evidence/{evidence_pack_id}/report")
def get_evidence_report_html(
    evidence_pack_id: str,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    evidence: Annotated[EvidenceService, Depends(_get_evidence_service)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
):
    """Renvoie le rapport HTML rendu (sans déchiffrement d'IBAN)."""
    from fastapi.responses import HTMLResponse

    html = evidence.get_report_html(evidence_pack_id, tenant_id=tenant_id)
    if html is None:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    return HTMLResponse(content=html)


@router.post("/evidence/{evidence_pack_id}/verify", response_model=EvidenceVerifyOut)
def verify_evidence_pack(
    evidence_pack_id: str,
    actor: Annotated[str, Depends(_require_auth_sepa)],
    evidence: Annotated[EvidenceService, Depends(_get_evidence_service)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> EvidenceVerifyOut:
    result = evidence.verify(evidence_pack_id, tenant_id=tenant_id)
    return EvidenceVerifyOut(
        evidence_pack_id=result.evidence_pack_id,
        valid=result.valid,
        hash_matches=result.hash_matches,
        audit_chain_valid=result.audit_chain_valid,
        audit_anchor_present=result.audit_anchor_present,
        checked_at=result.checked_at,
        errors=list(result.errors),
    )


# ─── Webhook inbound : prélèvement signé PSP/banque ──────────────────────────


@router.post("/webhooks/debit", status_code=202)
async def webhook_inbound_debit(
    request: Request,
    analyzer: Annotated[SepaAnalyzer, Depends(_get_analyzer)],
    store: Annotated[WebhookIdempotencyStore, Depends(_get_webhook_idempotency_store)],
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> dict[str, Any]:
    """Reçoit un prélèvement signé HMAC d'un partenaire (PSP, banque).

    Headers requis :
    - X-MG-Timestamp     : ISO 8601 UTC, fenêtre +/- 5 min
    - X-MG-Signature     : sha256=<hex> sur le body brut
    - X-MG-Idempotency-Key : (recommandé) anti-replay applicatif

    Corps : `DebitEventInput` JSON. L'analyzer est invoqué et le verdict
    retourné de manière synchrone (le caller peut décider de bloquer).
    """
    verified: VerifiedWebhook = await verify_inbound_webhook(
        request, store=store, source="psp-inbound"
    )
    try:
        body_obj = json.loads(verified.body.decode("utf-8"))
        payload = DebitEventInput.model_validate(body_obj)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Body invalide : {exc}",
        ) from exc

    result = analyzer.analyze(payload, actor="webhook:psp", tenant_id=tenant_id)
    out = _analysis_to_out(result)
    return {
        "received_at": verified.timestamp.isoformat(),
        "idempotency_key": verified.idempotency_key,
        "analysis": out.model_dump(),
    }


def _evidence_to_out(record) -> EvidencePackOut:
    return EvidencePackOut(
        evidence_pack_id=record.evidence_pack_id,
        tenant_id=record.tenant_id,
        subject_type=record.subject_type,
        subject_id=record.subject_id,
        domain=record.domain,
        engine_version=record.engine_version,
        pack_hash=record.pack_hash,
        audit_anchor_hash=record.audit_anchor_hash,
        audit_anchor_seq=record.audit_anchor_seq,
        has_report=record.has_report,
        actor=record.actor,
        created_at=record.created_at,
        payload=record.payload,
    )
