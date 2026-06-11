"""Client OpenSanctions Yente — sanctions consolidées + PEP.

OpenSanctions est un projet open source agrégeant ~250 listes officielles
(UE, OFAC, ONU, Trésor FR, listes nationales) + PEP. L'API Yente est l'API
de matching de référence — gratuite jusqu'à un quota raisonnable sur
`api.opensanctions.org`, self-hostable en Docker (`ghcr.io/opensanctions/yente`).

Documentation :
    https://www.opensanctions.org/docs/api/

Cet adapter est appelé par `SanctionsClient` quand `Settings.enrichment_mode == "live"`.
En cas d'échec, un `log.warning` est émis et l'appelant retombe sur le
snapshot CSV embarqué (graceful degradation).

Le matching côté Yente combine :
- normalisation et N-gram fuzzy matching côté serveur,
- threshold configurable via le param `?match_threshold=...`,
- support des alias (transparent).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import requests

from p2p_fraud.enrichment.cache import get_cached_session
from p2p_fraud.enrichment.sanctions_client import SanctionMatch

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (5, 15)
DEFAULT_DATASET = "sanctions"  # ou "default" pour incluer PEP
DEFAULT_THRESHOLD = 0.7


class YenteError(RuntimeError):
    """Yente a renvoyé un statut inattendu ou un payload illisible."""


class YenteClient:
    """Client HTTP Yente (`/match/<dataset>` endpoint).

    Args:
        base_url: URL de base (par défaut `https://api.opensanctions.org`).
        dataset: dataset Yente (`sanctions`, `peps`, `default`).
        session: session `requests` avec cache HTTP (TTL 24 h par défaut).
        timeout: tuple `(connect, read)`.
        threshold: score minimum côté Yente (0.0 - 1.0).
    """

    def __init__(
        self,
        *,
        base_url: str = "https://api.opensanctions.org",
        dataset: str = DEFAULT_DATASET,
        session: requests.Session | None = None,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.dataset = dataset
        self.timeout = timeout
        self.threshold = threshold
        self._session = session or get_cached_session(
            cache_name="yente_live_cache",
            expire_after=timedelta(hours=24),
        )

    def match_entity(self, name: str, *, schema: str = "LegalEntity") -> list[SanctionMatch]:
        """Cherche les matches Yente pour une entité (personne morale par défaut)."""
        return self._match(name=name, schema=schema)

    def match_person(self, name: str) -> list[SanctionMatch]:
        """Cherche les matches Yente pour une personne physique."""
        return self._match(name=name, schema="Person")

    def _match(self, *, name: str, schema: str) -> list[SanctionMatch]:
        name = (name or "").strip()
        if not name:
            return []
        url = f"{self.base_url}/match/{self.dataset}"
        body = {
            "queries": {
                "q1": {
                    "schema": schema,
                    "properties": {"name": [name]},
                }
            }
        }
        try:
            resp = self._session.post(
                url,
                json=body,
                params={"threshold": self.threshold},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("Yente match failed for %r: %s", name, exc)
            raise YenteError(str(exc)) from exc
        from p2p_fraud.enrichment.freshness import record_sync

        record_sync("sanctions", detail="match OpenSanctions")
        return _extract_matches(payload)


def _extract_matches(payload: dict[str, Any]) -> list[SanctionMatch]:
    """Mappe la réponse Yente vers la liste `SanctionMatch` interne."""
    out: list[SanctionMatch] = []
    responses = payload.get("responses") or {}
    for _qid, qbody in responses.items():
        if not isinstance(qbody, dict):
            continue
        for raw in qbody.get("results") or []:
            if not isinstance(raw, dict):
                continue
            props = raw.get("properties") or {}
            names = props.get("name") or []
            name = names[0] if names else str(raw.get("caption") or "")
            countries = props.get("country") or []
            datasets = raw.get("datasets") or []
            list_source = _resolve_list_source(datasets)
            listed = _parse_listed_at(props.get("createdAt") or props.get("modifiedAt"))
            try:
                score = round(float(raw.get("score") or 0) * 100)
            except (TypeError, ValueError):
                score = 0
            out.append(
                SanctionMatch(
                    entity_id=str(raw.get("id") or "")[:64],
                    name=name,
                    kind="person" if str(raw.get("schema")) == "Person" else "entity",
                    country=str(countries[0]).upper() if countries else None,
                    list_source=list_source,
                    listed_at=listed,
                    reason=", ".join(props.get("topics") or []) or None,
                    score=score,
                )
            )
    return out


def _resolve_list_source(datasets: list[str]) -> str:
    """Mappe les datasets Yente vers le vocabulaire interne (OFAC_SDN, EU_CONSOLIDATED, etc.)."""
    if not datasets:
        return "OS_UNKNOWN"
    joined = ",".join(datasets).lower()
    if "ofac" in joined:
        return "OFAC_SDN"
    if "eu_fsf" in joined or "eu_sanctions" in joined or "consolidated" in joined:
        return "EU_CONSOLIDATED"
    if "fr_tresor" in joined or "fr_dgt" in joined:
        return "FR_TRESOR"
    if "peps" in joined or "pep" in joined:
        return "PEP_EU"
    return f"OS_{datasets[0].upper()[:24]}"


def _parse_listed_at(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None
