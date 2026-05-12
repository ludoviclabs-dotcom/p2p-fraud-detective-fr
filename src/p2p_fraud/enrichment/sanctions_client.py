"""Client de vérification sanctions / PEP / OFAC / Trésor FR.

Conception offline-first :
- Le snapshot CSV embarqué (`data/sanctions/snapshot_*.csv`) est la source de
  vérité par défaut pour la démo, les tests et les déploiements on-prem.
- Une intégration OpenSanctions Yente (https://api.opensanctions.org/) est
  prévue mais non activée par défaut (sécurité + conformité).

Matching :
- Normalisation Unicode + minuscules + suppression ponctuation.
- Score RapidFuzz `WRatio` ≥ 90 par défaut (réglable).
- Toujours évaluer aussi les alias.

L'objectif est la précision (un faux positif coûte cher en investigation).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

log = logging.getLogger(__name__)

DEFAULT_SNAPSHOT = (
    Path(__file__).resolve().parents[3] / "data" / "sanctions" / "snapshot_2026-05-01.csv"
)
DEFAULT_MIN_SCORE = 90


@dataclass(frozen=True)
class SanctionMatch:
    entity_id: str
    name: str
    kind: str  # "entity" | "person"
    country: str | None
    list_source: str  # OFAC_SDN, EU_CONSOLIDATED, FR_TRESOR, PEP_FR, PEP_EU
    listed_at: date | None
    reason: str | None
    score: int  # 0–100

    @property
    def is_pep(self) -> bool:
        return self.list_source.startswith("PEP_")

    @property
    def is_sanction(self) -> bool:
        return not self.is_pep


def _normalize(text: str) -> str:
    """Normalisation pour matching : NFKD + ASCII + lower + alnum/space."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s]+", " ", ascii_only.lower()).strip()


def _parse_date(value: str | None) -> date | None:
    if not value or pd.isna(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


class SanctionsClient:
    """Client snapshot CSV — interface stable pour swap futur vers OpenSanctions."""

    def __init__(
        self,
        snapshot_path: Path | None = None,
        *,
        min_score: int = DEFAULT_MIN_SCORE,
        live_client: object | None = None,
    ) -> None:
        self._path = snapshot_path or DEFAULT_SNAPSHOT
        self._min_score = min_score
        self._df = self._load()
        # Quand `live_client` (YenteClient) est fourni, `search()` interroge
        # d'abord OpenSanctions Yente, puis retombe sur le snapshot CSV si
        # l'appel échoue (graceful degradation, jamais d'exception remontée).
        self.live_client = live_client

    @classmethod
    def from_settings(cls, settings=None) -> SanctionsClient:
        """Construit un client en respectant `Settings.enrichment_mode`."""
        from p2p_fraud.config import get_settings  # local pour éviter cycles

        s = settings or get_settings()
        live = None
        if s.enrichment_mode == "live":
            from p2p_fraud.enrichment.yente_client import YenteClient

            live = YenteClient(base_url=s.yente_base_url)
        return cls(live_client=live)

    def _load(self) -> pd.DataFrame:
        if not self._path.exists():
            log.warning("Snapshot sanctions absent : %s. Le client renverra 0 match.", self._path)
            return pd.DataFrame(
                columns=[
                    "entity_id",
                    "name",
                    "aliases",
                    "kind",
                    "country",
                    "list_source",
                    "listed_at",
                    "reason",
                ]
            )
        df = pd.read_csv(self._path)
        df["aliases"] = df["aliases"].fillna("")
        df["norm_name"] = df["name"].map(_normalize)
        df["norm_aliases"] = df["aliases"].map(
            lambda s: [_normalize(a) for a in str(s).split(";") if a]
        )
        return df

    @property
    def snapshot_path(self) -> Path:
        return self._path

    @property
    def n_records(self) -> int:
        return len(self._df)

    def search(self, query: str, *, country: str | None = None) -> list[SanctionMatch]:
        """Recherche un nom/raison sociale dans le snapshot. Retourne tous les matches >= min_score."""
        if not query:
            return []
        if self.live_client is not None:
            try:
                live_hits = self.live_client.match_entity(query)  # type: ignore[attr-defined]
                if live_hits:
                    threshold = self._min_score
                    return [m for m in live_hits if m.score >= threshold]
            except Exception as exc:
                log.warning("Yente live match failed, falling back to snapshot: %s", exc)
        if self._df.empty:
            return []
        norm_q = _normalize(query)
        if not norm_q:
            return []

        matches: list[SanctionMatch] = []
        for row in self._df.itertuples(index=False):
            candidates = [row.norm_name, *row.norm_aliases]
            best = max((fuzz.WRatio(norm_q, c) for c in candidates if c), default=0)
            if best < self._min_score:
                continue
            if country and isinstance(row.country, str) and row.country != country and row.country:
                # Filtre pays optionnel : on n'écarte que si pays explicite défini ET différent.
                # On garde quand même si pays absent (None) pour ne pas rater un match.
                pass
            matches.append(
                SanctionMatch(
                    entity_id=row.entity_id,
                    name=row.name,
                    kind=row.kind,
                    country=row.country if isinstance(row.country, str) else None,
                    list_source=row.list_source,
                    listed_at=_parse_date(
                        row.listed_at if isinstance(row.listed_at, str) else None
                    ),
                    reason=row.reason if isinstance(row.reason, str) else None,
                    score=int(best),
                )
            )
        return sorted(matches, key=lambda m: m.score, reverse=True)

    def search_many(self, queries: Iterable[str]) -> dict[str, list[SanctionMatch]]:
        return {q: self.search(q) for q in queries if q}
