"""Client RBE — Registre des Bénéficiaires Effectifs (INPI / RNE).

Source : data.inpi.fr/rne/rbe (Etalab Open Licence).
Référentiel légal des bénéficiaires effectifs des sociétés françaises
(personnes physiques détenant ≥ 25 % du capital ou des droits de vote).

Obligatoire pour la due diligence tiers Sapin 2 art. 17 et AMLD6 art. 30.

Modes de fonctionnement :
- Mode démo (par défaut) : données synthétiques générées localement.
- Mode live : appel à l'API INPI (nécessite accréditation).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from unicodedata import normalize

log = logging.getLogger(__name__)


@dataclass
class BeneficialOwner:
    """Bénéficiaire effectif d'une entreprise (art. R. 561-1 CMF)."""

    siren: str
    company_name: str
    owner_first_name: str
    owner_last_name: str
    ownership_pct: float
    nationality: str = "FR"
    is_pep: bool = False


_DEMO_OWNERS: list[dict] = [
    {
        "siren": "123456789",
        "company_name": "ACME CONSULTING SAS",
        "owner_first_name": "Jean",
        "owner_last_name": "Martin",
        "ownership_pct": 100.0,
        "nationality": "FR",
        "is_pep": False,
    },
    {
        "siren": "234567890",
        "company_name": "BTP NORD SARL",
        "owner_first_name": "Pierre",
        "owner_last_name": "Dupont",
        "ownership_pct": 51.0,
        "nationality": "FR",
        "is_pep": True,
    },
    {
        "siren": "345678901",
        "company_name": "LOGICIELS PRO SA",
        "owner_first_name": "Unknown",
        "owner_last_name": "Unknown",
        "ownership_pct": 0.0,
        "nationality": "XX",
        "is_pep": False,
    },
    {
        "siren": "456789012",
        "company_name": "MAINTENANCE SERVICES EURL",
        "owner_first_name": "Sophie",
        "owner_last_name": "Bernard",
        "ownership_pct": 100.0,
        "nationality": "FR",
        "is_pep": False,
    },
    {
        "siren": "567890123",
        "company_name": "SECURITE GLOBAL SAS",
        "owner_first_name": "Mohammed",
        "owner_last_name": "Al Rashid",
        "ownership_pct": 60.0,
        "nationality": "AE",
        "is_pep": False,
    },
]

_HIGH_RISK_NATIONALITIES = {"AE", "RU", "CN", "IR", "KP", "BY", "CU", "SY", "VE", "XX"}


@dataclass
class RBEClient:
    """Interroge le registre RBE pour un ensemble de fournisseurs."""

    demo_mode: bool = True
    _owners: list[BeneficialOwner] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if self.demo_mode:
            self._owners = [BeneficialOwner(**d) for d in _DEMO_OWNERS]

    @staticmethod
    def _normalize(s: str) -> str:
        s = normalize("NFKD", s).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]", "", s.lower())

    def lookup_by_siren(self, siren: str) -> list[BeneficialOwner]:
        """Retourne les bénéficiaires effectifs pour un SIREN donné."""
        clean = siren.strip()[:9]
        return [o for o in self._owners if o.siren == clean]

    def is_opaque_structure(self, siren: str) -> bool:
        """Retourne True si la structure de propriété est opaque.

        Critères : pas de bénéficiaire effectif renseigné,
        ou propriétaire inconnu, ou nationalité à haut risque.
        """
        owners = self.lookup_by_siren(siren)
        if not owners:
            return True
        for o in owners:
            if o.owner_last_name.upper() in ("UNKNOWN", "INCONNU", ""):
                return True
            if o.nationality.upper() in _HIGH_RISK_NATIONALITIES:
                return True
        return False

    def has_pep_beneficial_owner(self, siren: str) -> bool:
        """Retourne True si au moins un bénéficiaire effectif est PEP."""
        return any(o.is_pep for o in self.lookup_by_siren(siren))

    @property
    def n_records(self) -> int:
        return len(self._owners)
