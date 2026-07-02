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


class Contribution(BaseModel):
    """Contribution unitaire d'un détecteur au score consolidé d'une facture.

    Sert à construire les *waterfall* d'explication (Sprint 4) : chaque ligne
    est traçable à un Finding source (`finding_rule_id` + `signal`) et donne
    le poids appliqué + la valeur brute + la part du score finale.
    """

    model_config = ConfigDict(extra="forbid")

    detector: str
    finding_rule_id: str
    signal: str
    severity: str
    weight: float
    severity_multiplier: float
    contribution: float  # value en points sur 0..100
    contribution_pct: float = 0.0  # part dans le score final
    reason_fr: str | None = None


class RiskScore(BaseModel):
    """Score consolidé par facture (ou par fournisseur via vendor_id).

    Les champs `contributions` et `reason_codes_fr` sont optionnels et alimentés
    par `aggregate_findings_with_explanations` (Sprint 4). Les anciens appelants
    de `aggregate_findings` ne sont pas impactés (defaults vides).
    """

    model_config = ConfigDict(extra="forbid")

    invoice_id: str
    score: float = Field(..., ge=0, le=100)
    findings_count: int = 0
    breakdown: dict[str, float] = Field(default_factory=dict)
    contributions: list[Contribution] = Field(default_factory=list)
    reason_codes_fr: list[str] = Field(default_factory=list)

    @field_validator("score")
    @classmethod
    def _round_score(cls, v: float) -> float:
        return round(v, 2)


class EmployeeRecord(BaseModel):
    """Ligne du référentiel RH — croisée avec les fournisseurs (conflits d'intérêts).

    L'``iban`` est celui du versement de salaire : en production il doit être
    haché côté ingestion (``security.iban``), jamais stocké en clair.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    employee_id: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    iban: str | None = None
    department: str | None = None
    can_approve_payments: bool = False


class MasterDataField(StrEnum):
    """Champs sensibles d'un fournisseur dont les changements sont surveillés."""

    IBAN = "iban"
    BIC = "bic"
    NAME = "name"
    ADDRESS = "address"
    SIREN = "siren"
    CONTACT_EMAIL = "contact_email"
    CONTACT_PHONE = "contact_phone"
    STATUS = "status"  # active / blocked / dormant


class VendorMasterEvent(BaseModel):
    """Événement de modification du master data fournisseur.

    Chaque ligne est une *modification atomique d'un champ*. Pour un changement
    multi-champs (ex. nom + IBAN le même jour), produire plusieurs événements
    avec le même `changed_at`.

    Les valeurs `iban` ne sont jamais stockées en clair en production : utilisez
    le service `security.crypto` (à venir) ou hashez côté ingestion.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str
    vendor_id: str
    field: MasterDataField
    old_value: str | None = None
    new_value: str | None = None
    changed_at: datetime
    changed_by: str | None = None  # user_id ERP
    approved_by: str | None = None  # user_id approbateur si 4-eyes
    source: str = "erp"  # erp | manual | api | import

    @field_validator("changed_at")
    @classmethod
    def _aware_datetime(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v
