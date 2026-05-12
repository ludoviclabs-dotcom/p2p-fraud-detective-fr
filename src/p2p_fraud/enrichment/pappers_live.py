"""Adapter HTTP live pour Pappers — bénéficiaires effectifs + dirigeants.

Source principale : `api.pappers.fr/v2/entreprise?api_token=...&siren=...`
Source de repli : `data.inpi.fr/rne/rbe` (Etalab) si pas de clé Pappers.

Pappers agrège le RNE (Registre National des Entreprises, qui consolide
Sirene + INPI RBE depuis 2023) avec une API stable, documentée et publique.

Documentation :
    https://www.pappers.fr/api/documentation

Cet adapter est appelé par `RBEClient` quand `Settings.enrichment_mode == "live"`.
En cas d'échec (timeout, 5xx, JSON malformé), un `log.warning` est émis et
`RBEClient` retombe sur le mode démo (graceful degradation).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import requests

from p2p_fraud.enrichment.cache import get_cached_session
from p2p_fraud.enrichment.rbe_client import BeneficialOwner

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (5, 15)


class PappersLiveError(RuntimeError):
    """L'API Pappers a renvoyé un statut inattendu ou un payload illisible."""


class PappersLiveClient:
    """Client HTTP Pappers v2 — bénéficiaires effectifs (RBE) + structure.

    Args:
        api_key: clé Pappers (env `P2PFD_PAPPERS_API_KEY`).
        base_url: URL de base (par défaut `https://api.pappers.fr/v2`).
        session: session `requests` (cache HTTP partagé).
        timeout: tuple `(connect, read)` en secondes.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.pappers.fr/v2",
        session: requests.Session | None = None,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("PappersLiveClient requires a non-empty api_key.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or get_cached_session(
            cache_name="pappers_live_cache",
            expire_after=timedelta(days=7),
        )

    def lookup_by_siren(self, siren: str) -> list[BeneficialOwner]:
        """Retourne les bénéficiaires effectifs Pappers pour un SIREN."""
        siren = (siren or "").strip()
        if not siren or not siren.isdigit() or len(siren) != 9:
            return []
        params = {
            "api_token": self.api_key,
            "siren": siren,
        }
        url = f"{self.base_url}/entreprise"
        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("Pappers live lookup failed for SIREN %s: %s", siren, exc)
            raise PappersLiveError(str(exc)) from exc
        return _extract_owners(payload, siren=siren)


def _extract_owners(payload: dict[str, Any], *, siren: str) -> list[BeneficialOwner]:
    """Mappe la réponse Pappers vers la liste `BeneficialOwner` interne."""
    company_name = str(payload.get("denomination") or payload.get("nom_entreprise") or "").upper()
    raw_owners = payload.get("beneficiaires_effectifs") or []
    owners: list[BeneficialOwner] = []
    for raw in raw_owners:
        if not isinstance(raw, dict):
            continue
        first = str(raw.get("prenoms") or raw.get("prenom") or "").split(" ")[0] or "Unknown"
        last = str(raw.get("nom") or "Unknown").upper()
        try:
            pct = float(raw.get("pourcentage_parts") or raw.get("pourcentage_votes") or 0)
        except (TypeError, ValueError):
            pct = 0.0
        nat = str(raw.get("nationalite") or "FR")[:2].upper()
        owners.append(
            BeneficialOwner(
                siren=siren,
                company_name=company_name,
                owner_first_name=first,
                owner_last_name=last,
                ownership_pct=pct,
                nationality=nat,
                is_pep=bool(raw.get("politiquement_expose") or raw.get("pep") or False),
            )
        )
    return owners
