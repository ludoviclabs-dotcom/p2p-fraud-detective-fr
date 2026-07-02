"""Connecteur VoP — Verification of Payee (règlement IPR 2024/886).

Depuis le 9 octobre 2025, tous les PSP de la zone euro doivent vérifier la
concordance nom ↔ IBAN au moment du virement (VoP). Cette vérification agit
*au moment du paiement* ; P2P Fraud Detective agit *en amont*, à la saisie ou
modification du master data fournisseur. Le pré-check VoP à la saisie évite de
découvrir un ``no_match`` le jour du règlement.

Deux modes :
- **provider** — ``Settings.vop_provider_url`` configuré : POST HTTP vers le
  prestataire (SEPAmail Diamond, Swift PMPC, offre bancaire…), réponse au
  format EPC (match / close_match / no_match).
- **simulation** (défaut) — comparaison fuzzy locale du nom saisi vs nom
  attendu (registre interne) : reproduit la sémantique EPC pour la démo et le
  pré-check hors-ligne, sans appel réseau.

Référence : EPC Verification Of Payee scheme rulebook ; CFONB, brochure VoP.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

import requests
from rapidfuzz import fuzz

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (5, 10)

VopVerdict = Literal["match", "close_match", "no_match", "not_available"]

# Seuils de similarité alignés sur la pratique EPC (close match ≈ quasi-homonyme).
_MATCH_THRESHOLD = 95.0
_CLOSE_MATCH_THRESHOLD = 80.0


@dataclass(frozen=True)
class VopResult:
    """Résultat d'un pré-check VoP."""

    verdict: VopVerdict
    similarity: float | None
    detail: str
    provider: str  # "simulation" | hostname du prestataire


def _normalize_name(value: str) -> str:
    # Ponctuation → espace : « NORD-EST » et « NORD EST » doivent matcher.
    v = re.sub(r"[-.,·'’]", " ", value.upper())
    v = " ".join(v.split())
    for suffix in (" SAS", " SARL", " SA", " SASU", " EURL", " SCI", " LTD", " GMBH"):
        if v.endswith(suffix):
            v = v[: -len(suffix)]
    return v.strip()


class VopClient:
    """Pré-check VoP nom ↔ IBAN, prestataire ou simulation locale.

    Args:
        provider_url: URL du prestataire VoP (``Settings.vop_provider_url``).
        provider_key: credential prestataire (``Settings.vop_provider_key``).
    """

    def __init__(
        self,
        *,
        provider_url: str = "",
        provider_key: str = "",
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    ) -> None:
        self.provider_url = provider_url.rstrip("/") if provider_url else ""
        self.provider_key = provider_key
        self.timeout = timeout

    def precheck(
        self,
        *,
        beneficiary_name: str,
        iban: str,
        expected_name: str | None = None,
    ) -> VopResult:
        """Vérifie la concordance nom ↔ IBAN avant enregistrement du RIB.

        En mode simulation, ``expected_name`` (nom au registre interne /
        Sirene) est requis pour produire un verdict ; sans lui, le résultat
        est ``not_available`` avec explication.
        """
        if self.provider_url:
            return self._precheck_provider(beneficiary_name=beneficiary_name, iban=iban)

        if not expected_name:
            return VopResult(
                verdict="not_available",
                similarity=None,
                detail=(
                    "Simulation VoP : fournir le nom attendu (registre interne ou "
                    "Sirene) pour comparer — ou configurer un prestataire VoP "
                    "(VOP_PROVIDER_URL)."
                ),
                provider="simulation",
            )

        score = float(
            fuzz.token_sort_ratio(_normalize_name(beneficiary_name), _normalize_name(expected_name))
        )
        if score >= _MATCH_THRESHOLD:
            verdict: VopVerdict = "match"
            detail = "Concordance nom ↔ IBAN (équivalent EPC MATCH)."
        elif score >= _CLOSE_MATCH_THRESHOLD:
            verdict = "close_match"
            detail = (
                "Quasi-concordance (équivalent EPC CLOSE MATCH) — vérifier le nom "
                "exact auprès du fournisseur par canal vérifié avant d'enregistrer."
            )
        else:
            verdict = "no_match"
            detail = (
                "Divergence nom ↔ IBAN (équivalent EPC NO MATCH) — ne pas enregistrer "
                "le RIB sans vérification renforcée (rappel au numéro connu, e-mail "
                "du domaine vérifié)."
            )
        return VopResult(
            verdict=verdict, similarity=round(score, 1), detail=detail, provider="simulation"
        )

    def _precheck_provider(self, *, beneficiary_name: str, iban: str) -> VopResult:
        try:
            resp = requests.post(
                f"{self.provider_url}/verification-of-payee",
                json={"name": beneficiary_name, "iban": "".join(iban.split()).upper()},
                headers=(
                    {"Authorization": f"Bearer {self.provider_key}"} if self.provider_key else {}
                ),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("VoP provider call failed: %s", exc)
            return VopResult(
                verdict="not_available",
                similarity=None,
                detail=f"Prestataire VoP injoignable ({exc.__class__.__name__}).",
                provider=self.provider_url,
            )
        raw = str(payload.get("result") or payload.get("verdict") or "").lower().replace(" ", "_")
        verdict: VopVerdict = (
            raw if raw in ("match", "close_match", "no_match") else "not_available"
        )  # type: ignore[assignment]
        return VopResult(
            verdict=verdict,
            similarity=payload.get("similarity"),
            detail=str(payload.get("detail") or ""),
            provider=self.provider_url,
        )
