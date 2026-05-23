"""Adapters `RiskRule` pour le détecteur master_data (P2P historique).

Démontre que l'interface Risk Core wrappe les détecteurs existants sans
modification de leur code source. Ces règles seront utilisables côté SEPA
comme côté P2P dès que `Mandate` / `BeneficiaryProfile` seront en base
(Sprint 2). Pour l'instant, elles vivent sur le contexte P2P historique :
DataFrame de factures + flux d'événements master data.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Final

import pandas as pd

from p2p_fraud.detectors.master_data_changes import (
    DEFAULT_DORMANT_DAYS,
    DEFAULT_EXPOSURE_WINDOW_DAYS,
    detect_dormant_reactivation,
    detect_iban_change_without_4eyes,
)
from p2p_fraud.risk_core.adapters.finding_bridge import finding_to_signal
from p2p_fraud.risk_core.types import RiskDomain, RiskSignal
from p2p_fraud.schema import VendorMasterEvent


@dataclass(frozen=True)
class SupplierPaymentContext:
    """Contexte d'évaluation des règles P2P historiques (master_data, etc.).

    Volontairement minimal : DataFrame factures + événements master data.
    Au fur et à mesure que d'autres détecteurs P2P sont adaptés, ce contexte
    s'enrichira (DECP, Sirene, sanctions, etc.).
    """

    invoices: pd.DataFrame
    master_data_events: tuple[VendorMasterEvent, ...] = field(default_factory=tuple)
    exposure_window_days: int = DEFAULT_EXPOSURE_WINDOW_DAYS
    dormant_days: int = DEFAULT_DORMANT_DAYS


class IbanChangeWithoutFourEyesRule:
    """Wrapper RiskRule de `detect_iban_change_without_4eyes`."""

    id: Final[str] = "MD_IBAN_NO_4EYES"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SUPPLIER_PAYMENT

    def evaluate(self, ctx: SupplierPaymentContext) -> list[RiskSignal]:
        findings = detect_iban_change_without_4eyes(
            ctx.master_data_events,
            ctx.invoices,
            exposure_window_days=ctx.exposure_window_days,
        )
        return [finding_to_signal(f) for f in findings]


class DormantVendorReactivationRule:
    """Wrapper RiskRule de `detect_dormant_reactivation`."""

    id: Final[str] = "MD_DORMANT_REACTIVATED"
    version: Final[str] = "1.0.0"
    domain: Final[RiskDomain] = RiskDomain.SUPPLIER_PAYMENT

    def evaluate(self, ctx: SupplierPaymentContext) -> list[RiskSignal]:
        findings = detect_dormant_reactivation(
            ctx.master_data_events,
            ctx.invoices,
            dormant_days=ctx.dormant_days,
            exposure_window_days=ctx.exposure_window_days,
        )
        return [finding_to_signal(f) for f in findings]


def build_supplier_payment_rules() -> Iterable[object]:
    """Factory utilisée par `RiskEngine` pour assembler les règles P2P v0."""
    return (
        IbanChangeWithoutFourEyesRule(),
        DormantVendorReactivationRule(),
    )
