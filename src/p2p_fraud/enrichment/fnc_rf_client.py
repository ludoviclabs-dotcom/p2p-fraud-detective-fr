"""Connecteur FNC-RF — Fichier National Commun de la Relation Frauduleuse.

Lancé par la Banque de France le 7 mai 2026, le FNC-RF est le fichier partagé
entre PSP recensant les IBAN frauduleux connus. Il agit *côté bancaire, au
moment du virement* — P2P Fraud Detective agit *en amont*, au moment où le
master data fournisseur change. Les deux couches sont complémentaires.

ÉTAT : l'API n'est pas encore ouverte aux entreprises (réservée aux PSP).
Ce module est l'EMPLACEMENT réservé du connecteur :

- l'interface (`check_iban`) est figée dès maintenant pour que le pipeline
  puisse l'appeler sans refactor le jour de l'ouverture ;
- tant que ``Settings.fnc_rf_api_url`` est vide, `status()` renvoie
  ``pending_api`` et `check_iban` renvoie un résultat « non vérifiable »
  (jamais d'échec silencieux : le statut est explicite dans l'évidence).

Référence : communiqué Banque de France, « Lancement de la plateforme des
IBAN suspects », mai 2026.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import requests

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (5, 10)

FncRfStatus = Literal["configured", "pending_api"]
FncRfVerdict = Literal["listed", "not_listed", "not_available"]


@dataclass(frozen=True)
class FncRfResult:
    """Résultat d'une interrogation FNC-RF pour un IBAN."""

    iban_masked: str
    verdict: FncRfVerdict
    detail: str
    source: str = "fnc-rf"


def _mask_iban(iban: str) -> str:
    v = "".join(iban.split()).upper()
    if len(v) <= 8:
        return v
    return f"{v[:4]}…{v[-4:]}"


class FncRfClient:
    """Client FNC-RF — emplacement réservé tant que l'API n'est pas ouverte.

    Args:
        api_url: URL de l'API FNC-RF (``Settings.fnc_rf_api_url``). Vide tant
            que la Banque de France n'a pas ouvert l'accès aux entreprises.
        api_key: credential d'accès (``Settings.fnc_rf_api_key``).
    """

    def __init__(
        self,
        *,
        api_url: str = "",
        api_key: str = "",
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_url = api_url.rstrip("/") if api_url else ""
        self.api_key = api_key
        self.timeout = timeout

    def status(self) -> FncRfStatus:
        return "configured" if self.api_url else "pending_api"

    def check_iban(self, iban: str) -> FncRfResult:
        """Interroge le FNC-RF pour un IBAN — verdict explicite, jamais silencieux."""
        masked = _mask_iban(iban)
        if not self.api_url:
            return FncRfResult(
                iban_masked=masked,
                verdict="not_available",
                detail=(
                    "API FNC-RF non ouverte aux entreprises — connecteur en attente "
                    "(Banque de France, accès PSP uniquement à ce jour). "
                    "Le contrôle interne pré-paiement reste la couche active."
                ),
            )
        try:
            resp = requests.get(
                f"{self.api_url}/iban-check",
                params={"iban": "".join(iban.split()).upper()},
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("FNC-RF lookup failed: %s", exc)
            return FncRfResult(
                iban_masked=masked,
                verdict="not_available",
                detail=f"Interrogation FNC-RF en échec ({exc.__class__.__name__}).",
            )
        listed = bool(payload.get("listed"))
        return FncRfResult(
            iban_masked=masked,
            verdict="listed" if listed else "not_listed",
            detail=str(
                payload.get("detail")
                or ("IBAN présent au FNC-RF" if listed else "Aucune inscription connue")
            ),
        )
