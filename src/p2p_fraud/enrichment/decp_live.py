"""Adapter HTTP live pour DECP (Données Essentielles de la Commande Publique).

Source officielle : `data.economie.gouv.fr` — dataset `decp-v3` (ODbL).
API explore v2.1 (OpenDataSoft) : recherche par SIREN/SIRET via `where=` clause.

Documentation :
    https://data.economie.gouv.fr/explore/dataset/decp-v3/api/

Le cache HTTP `requests-cache` (TTL 7 j) absorbe les rafales et garantit la
reproductibilité de la démo en cas de coupure réseau.

Cet adapter est appelé par `DECPClient` quand `Settings.enrichment_mode == "live"`.
En cas d'échec (timeout, 5xx, JSON malformé), un `log.warning` est émis et
`DECPClient` retombe sur le mode démo (graceful degradation).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import requests

from p2p_fraud.enrichment.cache import get_cached_session
from p2p_fraud.enrichment.decp_client import DECPContract

log = logging.getLogger(__name__)

DEFAULT_DATASET = "decp-v3"
DEFAULT_TIMEOUT = (5, 15)  # connect, read
DEFAULT_LIMIT = 50  # marchés max par requête (assez pour une démo)


class DECPLiveError(RuntimeError):
    """L'API DECP a renvoyé un statut inattendu ou un payload illisible."""


class DECPLiveClient:
    """Client HTTP minimal pour l'API explore OpenDataSoft de data.economie.gouv.fr.

    Args:
        base_url: URL de base de l'API (par défaut `https://data.economie.gouv.fr/api/explore/v2.1`).
        dataset: identifiant du dataset (par défaut `decp-v3`).
        session: session `requests` (injecte un cache HTTP partagé en démo).
        timeout: tuple `(connect, read)` en secondes.
    """

    def __init__(
        self,
        *,
        base_url: str = "https://data.economie.gouv.fr/api/explore/v2.1",
        dataset: str = DEFAULT_DATASET,
        session: requests.Session | None = None,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.dataset = dataset
        self.timeout = timeout
        self._session = session or get_cached_session(
            cache_name="decp_live_cache",
            expire_after=timedelta(days=7),
        )

    def _records_url(self) -> str:
        return f"{self.base_url}/catalog/datasets/{self.dataset}/records"

    def lookup_by_siren(self, siren: str, *, limit: int = DEFAULT_LIMIT) -> list[DECPContract]:
        """Retourne les contrats DECP réels pour un SIREN donné."""
        siren = (siren or "").strip()
        if not siren or not siren.isdigit() or len(siren) != 9:
            return []
        params = {
            "where": f'titulaire_id="{siren}"',
            "limit": str(min(limit, 100)),
            "order_by": "datenotification DESC",
        }
        try:
            resp = self._session.get(self._records_url(), params=params, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("DECP live lookup failed for SIREN %s: %s", siren, exc)
            raise DECPLiveError(str(exc)) from exc
        return [_to_contract(rec) for rec in payload.get("results", [])]

    def lookup_by_name(self, name: str, *, limit: int = DEFAULT_LIMIT) -> list[DECPContract]:
        """Recherche full-text par nom de titulaire (fuzzy côté serveur OpenDataSoft)."""
        name = (name or "").strip()
        if not name:
            return []
        params = {
            "q": name,
            "where": "titulaire_id IS NOT NULL",
            "limit": str(min(limit, 100)),
            "order_by": "datenotification DESC",
        }
        try:
            resp = self._session.get(self._records_url(), params=params, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("DECP live name search failed for %r: %s", name, exc)
            raise DECPLiveError(str(exc)) from exc
        return [_to_contract(rec) for rec in payload.get("results", [])]


def _to_contract(record: dict[str, Any]) -> DECPContract:
    """Convertit un record OpenDataSoft en `DECPContract` interne."""
    siret = str(record.get("titulaire_id") or record.get("titulaireid") or "").strip()
    siren = siret[:9] if len(siret) >= 9 else siret
    try:
        montant = float(record.get("montant") or 0)
    except (TypeError, ValueError):
        montant = 0.0
    return DECPContract(
        siret_titulaire=siret,
        nom_titulaire=str(
            record.get("titulaire_denomination") or record.get("titulairedenomination") or ""
        ),
        siren_titulaire=siren,
        acheteur=str(record.get("acheteur_nom") or record.get("acheteurnom") or ""),
        montant_eur=montant,
        date_notification=str(
            record.get("datenotification") or record.get("date_notification") or ""
        ),
        objet=str(record.get("objet") or ""),
        nature=str(record.get("nature") or "Marché"),
        code_postal=str(record.get("lieuexecution_code") or record.get("code_postal") or "")[:5],
    )
