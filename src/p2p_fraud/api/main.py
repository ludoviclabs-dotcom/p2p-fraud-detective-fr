"""FastAPI application — P2P Fraud Detective FR REST API.

Endpoints :
- GET  /health          — liveness probe
- POST /detect          — exécute tous les détecteurs sur un dataset de factures
- POST /score           — calcule le score de risque consolidé par facture
- GET  /cases           — liste les cases depuis la base SQLite
- POST /cases/{case_id}/close — clôture motivée d'un case

Déploiement :
- Développement : `uvicorn p2p_fraud.api.main:app --reload`
- Production : `gunicorn -k uvicorn.workers.UvicornWorker p2p_fraud.api.main:app`
- Docker : voir `Dockerfile` + `docker-compose.yml` à la racine du projet.

Auth : bearer token statique via FRAUD_API_SECRET (à configurer en production).
"""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime
from typing import Annotated, Any

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from p2p_fraud.api.oidc_router import router as oidc_router
from p2p_fraud.cases.service import CaseService
from p2p_fraud.config import get_settings
from p2p_fraud.detectors.duplicates import detect_duplicates
from p2p_fraud.detectors.sanctions import detect_sanctioned_vendors
from p2p_fraud.detectors.thresholds import detect_under_threshold
from p2p_fraud.logging_setup import configure_logging
from p2p_fraud.schema import Finding
from p2p_fraud.scoring.risk_engine import aggregate_findings_with_explanations

configure_logging()

log = logging.getLogger(__name__)

_CASE_SERVICE: CaseService | None = None


def _init_sentry() -> None:
    """Active Sentry si `SENTRY_DSN` est défini. Idempotent et silencieux sinon."""
    dsn = get_settings().sentry_dsn
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        log.warning("sentry-sdk non installé — observability désactivée")
        return
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.0,
        send_default_pii=False,  # pas de PII (RGPD)
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
        ],
        release=f"p2p-fraud-detective-fr@{_VERSION}",
    )
    log.info("Sentry initialisé")


_VERSION = "0.4.0"

_init_sentry()

app = FastAPI(
    title="P2P Fraud Detective FR — API",
    description=(
        "API REST pour la détection de fraude dans les cycles Procure-to-Pay. "
        "Conforme ISA 240, Sapin 2, LCB-FT, DORA art. 28."
    ),
    version=_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


def _init_prometheus(application: FastAPI) -> None:
    """Expose `/metrics` (format Prometheus) si la lib est installée."""
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
    except ImportError:
        log.info("prometheus_fastapi_instrumentator absent — /metrics indisponible")
        return
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(application).expose(application, endpoint="/metrics", include_in_schema=False)
    log.info("Prometheus instrumentator monté sur /metrics")


_init_prometheus(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(oidc_router)

# Router v1 (Next.js Migration v2 Phase 0) — endpoints typés Pydantic
from p2p_fraud.api.v1 import (  # noqa: E402
    _get_service as _v1_get_service_stub,
)
from p2p_fraud.api.v1 import (  # noqa: E402
    _require_auth_v1,
)
from p2p_fraud.api.v1 import (  # noqa: E402
    router as v1_router,
)

app.include_router(v1_router)

_bearer = HTTPBearer(auto_error=False)


def _get_api_secret() -> str:
    return get_settings().fraud_api_secret


def _require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    secret = _get_api_secret()
    if not secret:
        return "anonymous"
    if credentials is None or credentials.credentials != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def _case_service() -> CaseService:
    global _CASE_SERVICE
    if _CASE_SERVICE is None:
        _CASE_SERVICE = CaseService(db_path=get_settings().fraud_cases_db)
    return _CASE_SERVICE


# ─── Injection des dépendances v1 ────────────────────────────────────────────
# Override les stubs `_require_auth_v1` et `_get_service` du router v1 avec
# les vraies implémentations du main app (auth bearer + CaseService).
app.dependency_overrides[_require_auth_v1] = _require_auth
app.dependency_overrides[_v1_get_service_stub] = _case_service


# ─── Request / Response models ────────────────────────────────────────────────


class InvoiceRow(BaseModel):
    invoice_id: str
    vendor_name: str
    amount: float = Field(..., gt=0)
    invoice_date: str
    siren: str | None = None
    iban: str | None = None
    po_number: str | None = None
    user_id: str | None = None
    gl_account: str | None = None
    cost_center: str | None = None
    currency: str = "EUR"


class DetectRequest(BaseModel):
    invoices: list[InvoiceRow]
    detectors: list[str] = Field(
        default_factory=lambda: ["duplicates", "thresholds", "sanctions"],
        description="Détecteurs à activer parmi : duplicates, thresholds, sanctions, decp_rbe",
    )


class FindingOut(BaseModel):
    invoice_id: str
    detector: str
    rule_id: str
    severity: str
    signal: str
    evidence: dict[str, Any]
    detected_at: str


class DetectResponse(BaseModel):
    n_invoices: int
    n_findings: int
    findings: list[FindingOut]
    run_at: str


class ScoreRequest(BaseModel):
    invoices: list[InvoiceRow]
    detector_weights: dict[str, float] | None = None


class ScoreRow(BaseModel):
    invoice_id: str
    score: float
    findings_count: int
    reason_codes_fr: list[str]


class ScoreResponse(BaseModel):
    n_invoices: int
    scores: list[ScoreRow]
    run_at: str


class CaseOut(BaseModel):
    case_id: str
    title: str
    severity: str
    status: str
    exposure_eur: float | None
    assignee: str | None
    created_at: str
    invoice_id: str | None
    vendor_id: str | None


class CloseRequest(BaseModel):
    reason: str = Field(..., min_length=10)
    actor: str = "api"


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _invoices_to_df(rows: list[InvoiceRow]) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in rows])


def _finding_to_out(f: Finding) -> FindingOut:
    return FindingOut(
        invoice_id=f.invoice_id,
        detector=f.detector,
        rule_id=f.rule_id,
        severity=f.severity.value,
        signal=f.signal,
        evidence=f.evidence,
        detected_at=f.detected_at.isoformat(),
    )


def _run_detectors(df: pd.DataFrame, detectors: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    if "duplicates" in detectors:
        findings.extend(detect_duplicates(df))
    if "thresholds" in detectors:
        findings.extend(detect_under_threshold(df))
    if "sanctions" in detectors:
        findings.extend(detect_sanctioned_vendors(df))
    if "decp_rbe" in detectors:
        from p2p_fraud.detectors.decp import detect_decp_rbe

        findings.extend(detect_decp_rbe(df))
    return findings


# ─── Routes ───────────────────────────────────────────────────────────────────


@app.get("/health", tags=["Ops"])
def health() -> dict[str, str]:
    """Liveness probe — retourne 200 si l'API est opérationnelle."""
    return {"status": "ok", "version": _VERSION, "at": datetime.now(UTC).isoformat()}


@app.get("/security/public-key", tags=["Ops"])
def security_public_key() -> dict[str, str]:
    """Publie la clé publique Ed25519 utilisée pour signer l'audit log (P5-5).

    Permet à un auditeur externe (CAC, ACPR, Cour des comptes) de vérifier
    indépendamment les signatures du journal d'audit sans accès au backend.

    En l'absence de clé privée configurée (mode démo), renvoie
    `{"public_key_b64": "", "enabled": false}`.
    """
    from p2p_fraud.security.signing import make_signer_from_settings

    signer = make_signer_from_settings()
    return {
        "public_key_b64": signer.public_key_b64,
        "enabled": "true" if signer.enabled else "false",
        "algorithm": "Ed25519" if signer.enabled else "",
    }


@app.post("/webhook/test", tags=["Ops"])
def webhook_test(_: Annotated[str, Depends(_require_auth)]) -> dict[str, object]:
    """Envoie un événement factice `webhook.test` vers `Settings.webhook_url`.

    Permet de valider la configuration côté pilote en bout-en-bout
    (signature HMAC, retry tenacity, format CloudEvents simplifié).
    Renvoie un objet `{ok, status, duration_ms, event_id, type}`.

    En l'absence de configuration (`webhook_url` vide), renvoie
    `{ok: false, skipped: true, reason: "disabled"}`.
    """
    from p2p_fraud.webhooks.dispatcher import (
        WebhookDeliveryError,
        make_dispatcher_from_settings,
    )
    from p2p_fraud.webhooks.events import build_test_event

    dispatcher = make_dispatcher_from_settings()
    evt = build_test_event(actor="api/webhook-test")
    try:
        return dispatcher.dispatch(evt)
    except WebhookDeliveryError as exc:
        return {"ok": False, "error": str(exc), "event_id": evt.id}


@app.post("/detect", response_model=DetectResponse, tags=["Détection"])
def detect(
    req: DetectRequest,
    _: Annotated[str, Depends(_require_auth)],
) -> DetectResponse:
    """Exécute les détecteurs sélectionnés sur le dataset de factures fourni.

    Retourne la liste complète des findings avec leur sévérité, signal et evidence.
    """
    if not req.invoices:
        raise HTTPException(status_code=422, detail="La liste de factures est vide.")

    df = _invoices_to_df(req.invoices)
    findings = _run_detectors(df, req.detectors)

    return DetectResponse(
        n_invoices=len(df),
        n_findings=len(findings),
        findings=[_finding_to_out(f) for f in findings],
        run_at=datetime.now(UTC).isoformat(),
    )


@app.post("/detect/csv", response_model=DetectResponse, tags=["Détection"])
async def detect_csv(
    file: UploadFile,
    _: Annotated[str, Depends(_require_auth)],
) -> DetectResponse:
    """Accepte un fichier CSV de factures et exécute les détecteurs par défaut."""
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Erreur de parsing CSV : {exc}") from exc

    if "invoice_id" not in df.columns or "vendor_name" not in df.columns:
        raise HTTPException(
            status_code=422,
            detail="Colonnes obligatoires manquantes : invoice_id, vendor_name.",
        )

    findings = _run_detectors(df, ["duplicates", "thresholds", "sanctions"])
    return DetectResponse(
        n_invoices=len(df),
        n_findings=len(findings),
        findings=[_finding_to_out(f) for f in findings],
        run_at=datetime.now(UTC).isoformat(),
    )


@app.post("/score", response_model=ScoreResponse, tags=["Scoring"])
def score(
    req: ScoreRequest,
    _: Annotated[str, Depends(_require_auth)],
) -> ScoreResponse:
    """Calcule le score de risque consolidé (0-100) par facture.

    Utilise les poids configurés dans `weights.yaml` par défaut.
    Passez `detector_weights` pour surcharger à la volée.
    """
    if not req.invoices:
        raise HTTPException(status_code=422, detail="La liste de factures est vide.")

    df = _invoices_to_df(req.invoices)
    findings = _run_detectors(df, ["duplicates", "thresholds", "sanctions"])

    scores = aggregate_findings_with_explanations(findings, weights=req.detector_weights)

    return ScoreResponse(
        n_invoices=len(df),
        scores=[
            ScoreRow(
                invoice_id=s.invoice_id,
                score=s.score,
                findings_count=s.findings_count,
                reason_codes_fr=s.reason_codes_fr,
            )
            for s in scores
        ],
        run_at=datetime.now(UTC).isoformat(),
    )


@app.get("/cases", response_model=list[CaseOut], tags=["Case management"])
def list_cases(
    _: Annotated[str, Depends(_require_auth)],
    status_filter: str | None = None,
    severity: str | None = None,
    limit: int = 100,
) -> list[CaseOut]:
    """Liste les cases depuis la base de données (SQLite persistante).

    Filtres optionnels : `status_filter` (open/closed) et `severity` (critical/high/medium/low).
    """
    service = _case_service()
    cases = service.list_cases()

    if status_filter:
        closed_flag = status_filter.lower() == "closed"
        cases = [c for c in cases if c.status.is_closed == closed_flag]
    if severity:
        cases = [c for c in cases if c.severity == severity.lower()]

    cases = cases[:limit]

    return [
        CaseOut(
            case_id=c.case_id,
            title=c.title,
            severity=c.severity,
            status=c.status.value,
            exposure_eur=c.exposure_eur,
            assignee=c.assignee,
            created_at=c.created_at.isoformat()
            if hasattr(c.created_at, "isoformat")
            else str(c.created_at),
            invoice_id=c.invoice_id,
            vendor_id=c.vendor_id,
        )
        for c in cases
    ]


@app.post("/cases/{case_id}/close", tags=["Case management"])
def close_case(
    case_id: str,
    req: CloseRequest,
    _: Annotated[str, Depends(_require_auth)],
) -> dict[str, str]:
    """Clôture motivée d'un case.

    La raison de clôture doit être non vide (≥ 10 caractères).
    L'événement est journalisé dans la piste d'audit SHA-256.
    """
    from p2p_fraud.cases.models import CaseStatus

    service = _case_service()
    try:
        service.close(
            case_id=case_id,
            status=CaseStatus.CLOSED_CONFIRMED,
            actor=req.actor,
            reason=req.reason,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "case_id": case_id,
        "status": "closed",
        "closed_at": datetime.now(UTC).isoformat(),
        "reason": req.reason,
    }
