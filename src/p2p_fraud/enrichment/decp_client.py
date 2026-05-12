"""Client DECP — Données Essentielles des Contrats de la Commande Publique.

Source : data.economie.gouv.fr/decp_augmente (ODbL).
Référentiel des marchés publics français : fournisseur × acheteur public × montant.

Modes de fonctionnement :
- Mode démo (par défaut) : données synthétiques générées localement.
- Mode live : appel à l'API data.economie.gouv.fr (nécessite accès réseau).

Usage principal : détecter si un fournisseur du cycle P2P est simultanément
titulaire d'un marché public auprès de l'acheteur audité (conflit d'intérêts,
risque de collusion Sapin 2 art. 17).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from unicodedata import normalize

log = logging.getLogger(__name__)

_DEMO_VENDORS = [
    ("ACME CONSULTING SAS", "123456789", "75001"),
    ("BTP NORD SARL", "234567890", "59000"),
    ("LOGICIELS PRO SA", "345678901", "69001"),
    ("MAINTENANCE SERVICES EURL", "456789012", "13001"),
    ("SECURITE GLOBAL SAS", "567890123", "44000"),
    ("FOURNITURES BUREAUTIQUES SA", "678901234", "31000"),
    ("TRANSPORT EXPRESS SARL", "789012345", "67000"),
    ("NETTOYAGE PREMIUM SAS", "890123456", "33000"),
]

_DEMO_BUYERS = [
    "Commune de Paris",
    "Département du Nord",
    "Région Île-de-France",
    "Centre Hospitalier Universitaire de Lille",
    "Université Lyon 1",
    "SNCF Réseau",
    "Caisse d'Allocations Familiales",
]


@dataclass
class DECPContract:
    """Contrat de marché public issu du DECP."""

    siret_titulaire: str
    nom_titulaire: str
    siren_titulaire: str
    acheteur: str
    montant_eur: float
    date_notification: str
    objet: str
    nature: str = "Marché"
    code_postal: str = ""

    @property
    def siren(self) -> str:
        return self.siren_titulaire[:9] if self.siren_titulaire else ""


@dataclass
class DECPClient:
    """Interroge le référentiel DECP pour un ensemble de fournisseurs.

    En mode "live" (`Settings.enrichment_mode == "live"`), un `DECPLiveClient`
    est branché et les `lookup_*` interrogent l'API `data.economie.gouv.fr`.
    En cas d'échec réseau, un `log.warning` est émis et la méthode retombe
    sur la base démo locale (graceful degradation, jamais d'exception remontée).
    """

    demo_mode: bool = True
    cache_path: Path | None = None
    live_client: object | None = None  # DECPLiveClient | None ; typed `object` pour éviter cycle d'import
    _contracts: list[DECPContract] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if self.demo_mode:
            self._contracts = self._generate_demo_contracts()
        elif self.cache_path and self.cache_path.exists():
            self._contracts = self._load_from_cache()

    @classmethod
    def from_settings(cls, settings=None) -> DECPClient:
        """Construit un client en respectant `Settings.enrichment_mode`."""
        from p2p_fraud.config import get_settings  # import local pour éviter cycles

        s = settings or get_settings()
        if s.enrichment_mode == "live":
            from p2p_fraud.enrichment.decp_live import DECPLiveClient

            live = DECPLiveClient(base_url=s.decp_live_base_url)
            # Le mode démo reste activé en repli (les `_contracts` synthétiques
            # restent disponibles si l'API live échoue).
            client = cls(demo_mode=True)
            client.live_client = live
            return client
        return cls(demo_mode=True)

    def _generate_demo_contracts(self) -> list[DECPContract]:
        import random

        rng = random.Random(42)
        contracts = []
        for name, siren, cp in _DEMO_VENDORS:
            n_contracts = rng.randint(0, 3)
            for i in range(n_contracts):
                contracts.append(
                    DECPContract(
                        siret_titulaire=siren + str(rng.randint(10000, 99999)),
                        nom_titulaire=name,
                        siren_titulaire=siren,
                        acheteur=rng.choice(_DEMO_BUYERS),
                        montant_eur=round(rng.uniform(10_000, 2_000_000), 2),
                        date_notification=f"202{rng.randint(0, 5)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
                        objet=f"Prestation {['informatique', 'travaux', 'fournitures', 'services'][i % 4]} n°{rng.randint(1000, 9999)}",
                        code_postal=cp,
                    )
                )
        return contracts

    def _load_from_cache(self) -> list[DECPContract]:
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))  # type: ignore[union-attr]
            return [DECPContract(**d) for d in data]
        except Exception as exc:
            log.warning("DECP cache unreadable: %s", exc)
            return []

    @staticmethod
    def _normalize(s: str) -> str:
        s = normalize("NFKD", s).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]", "", s.lower())

    def lookup_by_siren(self, siren: str) -> list[DECPContract]:
        """Retourne les contrats DECP pour un SIREN donné."""
        clean = siren.strip()[:9]
        if self.live_client is not None:
            try:
                live_hits = self.live_client.lookup_by_siren(clean)  # type: ignore[attr-defined]
                if live_hits:
                    return live_hits
            except Exception as exc:
                log.warning("DECP live failed, falling back to demo: %s", exc)
        return [c for c in self._contracts if c.siren == clean]

    def lookup_by_name(self, name: str, min_score: int = 80) -> list[DECPContract]:
        """Retourne les contrats DECP pour un nom de fournisseur (fuzzy match)."""
        if self.live_client is not None:
            try:
                live_hits = self.live_client.lookup_by_name(name)  # type: ignore[attr-defined]
                if live_hits:
                    return live_hits
            except Exception as exc:
                log.warning("DECP live search failed, falling back to demo: %s", exc)
        try:
            from rapidfuzz import fuzz
        except ImportError:
            return []

        norm = self._normalize(name)
        results = []
        seen: set[str] = set()
        for c in self._contracts:
            key = c.siren_titulaire
            if key in seen:
                continue
            score = fuzz.WRatio(norm, self._normalize(c.nom_titulaire))
            if score >= min_score:
                results.append(c)
                seen.add(key)
        return results

    @property
    def n_contracts(self) -> int:
        return len(self._contracts)

    @property
    def n_unique_vendors(self) -> int:
        return len({c.siren_titulaire for c in self._contracts})


def _fingerprint(contracts: list[DECPContract]) -> str:
    payload = json.dumps([c.__dict__ for c in contracts], sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]
