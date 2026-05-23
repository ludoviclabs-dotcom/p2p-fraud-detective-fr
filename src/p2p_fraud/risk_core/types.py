"""Types canoniques du Risk Core — partagés SEPA + P2P + autres domaines.

Note de cohabitation : `Severity` est ré-exporté depuis `p2p_fraud.schema`
pour ne pas dupliquer l'enum. Les types ajoutés ici (RiskSignal, RiskDecision,
RiskAssessmentResult, RiskDomain, RiskLevel) sont neufs et propres au
Risk Core (le module existant `schema.Finding` reste utilisé tel quel par
les détecteurs P2P historiques — un adapter les convertit en `RiskSignal`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from p2p_fraud.schema import Severity  # ré-export volontaire

__all__ = [
    "RiskAssessmentResult",
    "RiskDecision",
    "RiskDomain",
    "RiskLevel",
    "RiskSignal",
    "Severity",
]


class RiskDomain(StrEnum):
    """Domaines de risque couverts par la plateforme (cf. spec MandateGuard §06)."""

    SEPA_DIRECT_DEBIT = "SEPA_DIRECT_DEBIT"
    SUPPLIER_PAYMENT = "SUPPLIER_PAYMENT"
    SEPA_CREDIT_TRANSFER = "SEPA_CREDIT_TRANSFER"
    P2P_TRANSFER = "P2P_TRANSFER"
    QR_PAYMENT = "QR_PAYMENT"
    MANDATE_EVENT = "MANDATE_EVENT"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskDecision(StrEnum):
    """Décision recommandée par le moteur — pas exécutoire seule (cf. ADR-0003)."""

    ALLOW = "ALLOW"
    ALLOW_MONITOR = "ALLOW_MONITOR"
    ALERT_USER = "ALERT_USER"
    REVIEW = "REVIEW"
    BLOCK_RECOMMENDED = "BLOCK_RECOMMENDED"
    DISPUTE_READY = "DISPUTE_READY"


class RiskSignal(BaseModel):
    """Signal produit par une `RiskRule`.

    Distinct de `schema.Finding` : un Signal est domain-agnostic (utilisable
    SEPA et P2P), porte un `title` court pour l'UI, et un `score` brut
    déjà calibré (0-100) plutôt qu'une seule severity. Le moteur les combine
    via `scoring.combine_signals`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(..., description="Reason code canonique, ex. NO_ACTIVE_MANDATE")
    title: str = Field(..., description="Titre court UI")
    message: str = Field(..., description="Phrase explicative (peut être FR)")
    severity: Severity
    score: int = Field(..., ge=0, le=100, description="Contribution brute au score")
    evidence: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RiskAssessmentResult(BaseModel):
    """Verdict final immuable, sérialisable, rejouable.

    `engine_version` est obligatoire pour que l'Evidence Pack puisse pointer
    sur une version précise du moteur — exigence d'auditabilité ISA 240 et
    de transparence AI Act art. 50.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    domain: RiskDomain
    score: int = Field(..., ge=0, le=100)
    level: RiskLevel
    decision: RiskDecision
    signals: list[RiskSignal] = Field(default_factory=list)
    engine_version: str
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
