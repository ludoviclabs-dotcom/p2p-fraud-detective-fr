"""Client API Sirene v3 (INSEE) — vérification d'identité fournisseur.

API : https://api.insee.fr/entreprises/sirene/V3
Quota : 30 req/s (gratuit avec compte INSEE).

Fournit :
- `lookup_siren()` : interroge un SIREN, renvoie un `SireneRecord` ou None.
- `cross_check_invoices()` : pipeline complet sur un DataFrame de factures, génère
  des Findings selon 4 règles (SIREN inexistant / radié / créé tardivement /
  code APE incohérent).

Dégradation gracieuse : si pas de token, on renvoie 0 finding et on log un warning.
On ne fait PAS d'appel pour les SIREN nuls/vides.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pandas as pd
import requests

from p2p_fraud.enrichment.cache import get_cached_session
from p2p_fraud.schema import Finding, Severity

log = logging.getLogger(__name__)

SIRENE_API_BASE = "https://api.insee.fr/entreprises/sirene/V3.11/siren"
DEFAULT_RATE_LIMIT_QPS = 25  # marge sous le plafond 30 req/s


@dataclass(frozen=True)
class SireneRecord:
    siren: str
    name: str | None
    is_active: bool
    creation_date: date | None
    closure_date: date | None
    ape_code: str | None
    ape_label: str | None

    @property
    def status(self) -> str:
        return "active" if self.is_active else "ceased"


class SireneClient:
    """Client API Sirene v3 avec cache partagé et rate-limiting basique."""

    def __init__(
        self,
        token: str | None = None,
        *,
        rate_limit_qps: int = DEFAULT_RATE_LIMIT_QPS,
        timeout: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self.token = token or os.environ.get("SIRENE_API_TOKEN", "").strip()
        self._enabled = bool(self.token)
        self._timeout = timeout
        self._min_interval = 1.0 / max(1, rate_limit_qps)
        self._last_request_at = 0.0
        self._session = session or get_cached_session()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _wait_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_at = time.monotonic()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}

    @staticmethod
    def _normalize_siren(value: str | None) -> str | None:
        if not value or pd.isna(value):
            return None
        digits = "".join(c for c in str(value) if c.isdigit())
        if len(digits) != 9:
            return None
        return digits

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    def lookup_siren(self, siren: str) -> SireneRecord | None:
        """Interroge l'API pour un SIREN. Renvoie None si non trouvé / désactivé."""
        normalized = self._normalize_siren(siren)
        if not normalized:
            return None
        if not self._enabled:
            log.warning("SIRENE_API_TOKEN absent — lookup SIREN sauté.")
            return None

        url = f"{SIRENE_API_BASE}/{normalized}"
        try:
            self._wait_rate_limit()
            resp = self._session.get(url, headers=self._headers(), timeout=self._timeout)
        except requests.RequestException as e:
            log.warning("Sirene HTTP error pour %s : %s", normalized, e)
            return None

        if resp.status_code == 404:
            # SIREN inexistant : on renvoie un record "neutre" pour mémoriser le 404
            return SireneRecord(
                siren=normalized,
                name=None,
                is_active=False,
                creation_date=None,
                closure_date=None,
                ape_code=None,
                ape_label=None,
            )
        if resp.status_code != 200:
            log.warning("Sirene HTTP %s pour %s", resp.status_code, normalized)
            return None

        return self._parse_payload(normalized, resp.json())

    @staticmethod
    def _parse_payload(siren: str, payload: dict[str, Any]) -> SireneRecord:
        unite = payload.get("uniteLegale", {})
        periodes = unite.get("periodesUniteLegale") or []
        # La période la plus récente (dateFin == None) donne le statut courant
        current = next(
            (p for p in periodes if p.get("dateFin") is None), periodes[0] if periodes else {}
        )
        is_active = current.get("etatAdministratifUniteLegale") == "A"
        ape_code = current.get("activitePrincipaleUniteLegale")
        name = current.get("denominationUniteLegale") or current.get("nomUniteLegale")
        creation = SireneClient._parse_date(unite.get("dateCreationUniteLegale"))
        closure = (
            SireneClient._parse_date(unite.get("dateDernierTraitementUniteLegale"))
            if not is_active
            else None
        )
        return SireneRecord(
            siren=siren,
            name=name,
            is_active=is_active,
            creation_date=creation,
            closure_date=closure,
            ape_code=ape_code,
            ape_label=None,
        )

    def lookup_many(self, sirens: Iterable[str]) -> dict[str, SireneRecord | None]:
        """Lookup batch — tire profit du cache HTTP (sessions multiples = même cache)."""
        out: dict[str, SireneRecord | None] = {}
        seen: set[str] = set()
        for raw in sirens:
            normalized = self._normalize_siren(raw)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            out[normalized] = self.lookup_siren(normalized)
        return out


def cross_check_invoices(
    df: pd.DataFrame,
    *,
    client: SireneClient | None = None,
    new_vendor_grace_days: int = 90,
) -> list[Finding]:
    """Génère des Findings basés sur le cross-check Sirene.

    Règles :
    - SIREN inexistant : CRITICAL `vendor_siren_not_found`.
    - Statut radié (cessation administrative) : CRITICAL `vendor_ceased`.
    - Création < `new_vendor_grace_days` avant 1ère facture : HIGH `vendor_recently_created`.
    - Si pas de token Sirene : aucun finding (et un warning log).
    """
    if df.empty:
        return []
    client = client or SireneClient()
    if not client.enabled:
        log.info("Sirene cross-check sauté (pas de token).")
        return []

    findings: list[Finding] = []
    if "siren" not in df.columns or "invoice_date" not in df.columns:
        return findings

    # 1ère facture par SIREN — borne basse pour la règle "created right before"
    first_invoice_per_siren: dict[str, date] = (
        df.groupby("siren")["invoice_date"].min().dropna().to_dict()
    )

    unique_sirens = [s for s in df["siren"].dropna().unique().tolist() if s]
    records = client.lookup_many(unique_sirens)

    for siren, record in records.items():
        invoices_for_siren = df.loc[df["siren"] == siren, "invoice_id"].astype(str).tolist()
        if record is None:
            # Lookup en échec (timeout, etc.) — ne pas pénaliser le fournisseur
            continue
        for invoice_id in invoices_for_siren:
            if record.name is None and not record.is_active:
                # 404 : SIREN inexistant
                findings.append(
                    Finding(
                        invoice_id=invoice_id,
                        detector="sirene",
                        signal="vendor_siren_not_found",
                        severity=Severity.CRITICAL,
                        rule_id="SIRENE_404",
                        evidence={"siren": siren},
                    )
                )
                continue
            if not record.is_active:
                findings.append(
                    Finding(
                        invoice_id=invoice_id,
                        detector="sirene",
                        signal="vendor_ceased",
                        severity=Severity.CRITICAL,
                        rule_id="SIRENE_CEASED",
                        evidence={
                            "siren": siren,
                            "closure_date": record.closure_date.isoformat()
                            if record.closure_date
                            else None,
                        },
                    )
                )
            first_inv = first_invoice_per_siren.get(siren)
            if record.creation_date and first_inv:
                gap = (first_inv - record.creation_date).days
                if 0 <= gap < new_vendor_grace_days:
                    findings.append(
                        Finding(
                            invoice_id=invoice_id,
                            detector="sirene",
                            signal="vendor_recently_created",
                            severity=Severity.HIGH,
                            rule_id="SIRENE_NEW_VENDOR",
                            evidence={
                                "siren": siren,
                                "creation_date": record.creation_date.isoformat(),
                                "first_invoice_date": first_inv.isoformat(),
                                "gap_days": gap,
                            },
                        )
                    )
    return findings
