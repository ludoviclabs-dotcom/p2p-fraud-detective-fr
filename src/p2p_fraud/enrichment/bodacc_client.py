"""Client Bodacc — procédures collectives par SIREN (annonces commerciales DILA).

Une procédure collective récente (sauvegarde, redressement, liquidation) sur un
fournisseur *actif* est un signal critique : risque de non-livraison, de
détournement d'acomptes, ou de fiche réactivée par un tiers.

Source : API opendatasoft DILA, dataset ``annonces-commerciales`` — open data,
aucune clé requise.
    https://bodacc-datadila.opendatasoft.com/explore/dataset/annonces-commerciales/

Mode ``demo`` (défaut) : échantillon déterministe embarqué, aucun appel réseau.
Mode ``live`` : GET HTTP réel, dégradation gracieuse vers ``[]`` + warning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

import requests

from p2p_fraud.enrichment.cache import get_cached_session

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (5, 15)
DEFAULT_BASE_URL = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1"

# Familles d'avis Bodacc considérées comme procédures collectives.
_PCL_FAMILLES = {"collective", "pcl", "procédure collective"}


@dataclass(frozen=True)
class BodaccAnnouncement:
    """Annonce Bodacc normalisée (sous-ensemble utile au scoring)."""

    siren: str
    publication_date: str  # ISO YYYY-MM-DD
    court: str
    family: str  # ex. "collective"
    nature: str  # ex. "jugement d'ouverture de liquidation judiciaire"
    announcement_id: str


# Échantillon démo — SIREN fictifs alignés sur les scénarios sandbox.
_DEMO_ANNOUNCEMENTS: dict[str, list[BodaccAnnouncement]] = {
    "451882330": [
        BodaccAnnouncement(
            siren="451882330",
            publication_date="2026-05-14",
            court="TC Lyon",
            family="collective",
            nature="Jugement d'ouverture d'une procédure de redressement judiciaire",
            announcement_id="BODACC-A-2026-0958-1204",
        )
    ],
}


class BodaccClient:
    """Procédures collectives Bodacc par SIREN, demo/live.

    Args:
        mode: ``"demo"`` (échantillon embarqué) ou ``"live"`` (HTTP réel).
        base_url: URL de base opendatasoft.
        session: session ``requests`` (cache HTTP partagé si omise).
    """

    def __init__(
        self,
        *,
        mode: str = "demo",
        base_url: str = DEFAULT_BASE_URL,
        session: requests.Session | None = None,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    ) -> None:
        self.mode = mode
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = get_cached_session(
                cache_name="bodacc_cache",
                expire_after=timedelta(days=1),
            )
        return self._session

    def collective_procedures(self, siren: str) -> list[BodaccAnnouncement]:
        """Annonces de procédures collectives pour un SIREN (récent d'abord)."""
        siren = (siren or "").strip()
        if not siren.isdigit() or len(siren) != 9:
            return []
        if self.mode != "live":
            return list(_DEMO_ANNOUNCEMENTS.get(siren, []))
        return self._fetch_live(siren)

    def _fetch_live(self, siren: str) -> list[BodaccAnnouncement]:
        url = f"{self.base_url}/catalog/datasets/annonces-commerciales/records"
        params = {
            "where": f'registre like "{siren}"',
            "order_by": "dateparution desc",
            "limit": 20,
        }
        try:
            resp = self._get_session().get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("Bodacc live lookup failed for SIREN %s: %s", siren, exc)
            return []

        results: list[BodaccAnnouncement] = []
        for rec in payload.get("results", []):
            family = str(rec.get("familleavis_lib") or rec.get("familleavis") or "").lower()
            if family and family not in _PCL_FAMILLES:
                continue
            results.append(
                BodaccAnnouncement(
                    siren=siren,
                    publication_date=str(rec.get("dateparution") or ""),
                    court=str(rec.get("tribunal") or ""),
                    family=family or "collective",
                    nature=str(rec.get("publicationavis_facette") or rec.get("nature") or ""),
                    announcement_id=str(rec.get("id") or ""),
                )
            )
        return results
