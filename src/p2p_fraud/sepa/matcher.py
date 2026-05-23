"""Appariement déterministe d'un prélèvement à son mandat.

Produit un `MatchResult` qui documente :
- le mandat retenu (ou None) ;
- la liste des candidats (utile pour AMBIGUOUS_MANDATE_MATCH) ;
- les `MatchWarning` rencontrés (RUM manquante, plusieurs candidats, etc.).

Le matcher NE produit PAS de signal de risque — il fournit le contexte
qui sera consommé par les règles SEPA du Risk Core en Sprint 3
(NO_ACTIVE_MANDATE, MANDATE_REVOKED, RUM_MISMATCH, ICS_MISMATCH).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from p2p_fraud.sepa.debit_event import DebitEventRecord
from p2p_fraud.sepa.mandate import MandateRecord, MandateService


class MatchWarning(StrEnum):
    """Avertissements non bloquants détectés lors du matching."""

    RUM_MISSING = "RUM_MISSING"
    ICS_MISSING = "ICS_MISSING"
    IBAN_FP_MISSING = "IBAN_FP_MISSING"
    AMBIGUOUS_MANDATE_MATCH = "AMBIGUOUS_MANDATE_MATCH"


@dataclass(frozen=True)
class MatchResult:
    """Résultat du matching — porte le mandat retenu + le contexte de décision."""

    mandate: MandateRecord | None
    candidates: tuple[MandateRecord, ...] = ()
    warnings: tuple[MatchWarning, ...] = ()
    inactive_candidates: tuple[MandateRecord, ...] = ()

    @property
    def matched(self) -> bool:
        return self.mandate is not None

    @property
    def is_ambiguous(self) -> bool:
        return MatchWarning.AMBIGUOUS_MANDATE_MATCH in self.warnings


class MandateMatcher:
    """Stratégie d'appariement prélèvement → mandat."""

    def __init__(self, mandate_service: MandateService) -> None:
        self._mandates = mandate_service

    def match(
        self,
        event: DebitEventRecord,
        *,
        tenant_id: str | None = None,
    ) -> MatchResult:
        """Recherche un mandat actif compatible avec le prélèvement observé.

        Étapes :
        1. Si fingerprint IBAN ou ICS manquant → impossible de matcher.
        2. Recherche stricte avec RUM si fournie.
        3. Sinon recherche large (IBAN_fp + ICS), warning RUM_MISSING.
        4. >1 candidats → AMBIGUOUS_MANDATE_MATCH, prend le plus ancien.
        5. 0 candidat actif → mandate=None (la règle NO_ACTIVE_MANDATE prendra
           la suite).
        """
        warnings: list[MatchWarning] = []

        fp = event.debtor_iban_fingerprint
        ics = event.creditor_ics

        if not fp:
            warnings.append(MatchWarning.IBAN_FP_MISSING)
        if not ics:
            warnings.append(MatchWarning.ICS_MISSING)
        if not fp or not ics:
            return MatchResult(mandate=None, candidates=(), warnings=tuple(warnings))

        rum = event.rum
        if not rum:
            warnings.append(MatchWarning.RUM_MISSING)

        # Recherche stricte (avec RUM si fournie)
        candidates = self._mandates.find_active_candidates(
            tenant_id=tenant_id,
            debtor_iban_fingerprint=fp,
            creditor_ics=ics,
            rum=rum,
        )

        # Candidats inactifs (révoqués / expirés / suspendus / drafts) qui
        # matchent les axes — utilisé par les règles MANDATE_REVOKED, etc.
        all_status_candidates = self._mandates.find_candidates_any_status(
            tenant_id=tenant_id,
            debtor_iban_fingerprint=fp,
            creditor_ics=ics,
            rum=rum,
        )
        inactive_candidates = tuple(
            m for m in all_status_candidates if m.status.value != "ACTIVE"
        )

        # Si rien et qu'on avait une RUM, retenter sans RUM pour signaler
        # un éventuel mismatch RUM (converti en signal RUM_MISMATCH au Sprint 3).
        if not candidates and rum is not None:
            candidates_no_rum = self._mandates.find_active_candidates(
                tenant_id=tenant_id,
                debtor_iban_fingerprint=fp,
                creditor_ics=ics,
                rum=None,
            )
            if candidates_no_rum:
                return MatchResult(
                    mandate=None,
                    candidates=tuple(candidates_no_rum),
                    warnings=tuple(warnings),
                    inactive_candidates=inactive_candidates,
                )

        if len(candidates) > 1:
            warnings.append(MatchWarning.AMBIGUOUS_MANDATE_MATCH)

        mandate = candidates[0] if candidates else None
        return MatchResult(
            mandate=mandate,
            candidates=tuple(candidates),
            warnings=tuple(warnings),
            inactive_candidates=inactive_candidates,
        )
