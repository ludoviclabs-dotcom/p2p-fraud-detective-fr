"""Modèles canoniques Pydantic v2 — contrats utilisés par tous les détecteurs."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.LOW: 10,
    Severity.MEDIUM: 30,
    Severity.HIGH: 60,
    Severity.CRITICAL: 100,
}


class Invoice(BaseModel):
    """Facture fournisseur après mapping vers le schéma canonique."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    invoice_id: str
    siren: str | None = None
    vendor_name: str
    iban: str | None = None
    amount: float = Field(..., gt=0)
    currency: str = "EUR"
    invoice_date: date
    posting_date: date | None = None
    po_number: str | None = None
    user_id: str | None = None
    cost_center: str | None = None
    gl_account: str | None = None

    @field_validator("siren")
    @classmethod
    def _validate_siren(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 9:
            return v
        return digits

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()


class Vendor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    siren: str
    name: str
    iban_list: list[str] = Field(default_factory=list)
    address: str | None = None
    ape_code: str | None = None
    creation_date: date | None = None
    is_active: bool = True


class Finding(BaseModel):
    """Résultat brut d'un détecteur — agrégé ensuite dans RiskScore."""

    model_config = ConfigDict(extra="forbid")

    invoice_id: str
    detector: str
    signal: str
    severity: Severity
    rule_id: str
    evidence: dict = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def severity_weight(self) -> int:
        return SEVERITY_WEIGHT[self.severity]


class RiskScore(BaseModel):
    """Score consolidé par facture (ou par fournisseur via vendor_id)."""

    model_config = ConfigDict(extra="forbid")

    invoice_id: str
    score: float = Field(..., ge=0, le=100)
    findings_count: int = 0
    breakdown: dict[str, float] = Field(default_factory=dict)

    @field_validator("score")
    @classmethod
    def _round_score(cls, v: float) -> float:
        return round(v, 2)
