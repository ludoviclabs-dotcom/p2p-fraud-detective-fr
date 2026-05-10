"""Règles d'alerte — évaluation des findings vs seuils configurés.

Une `AlertRule` décrit la condition de déclenchement (sévérité min, exposition,
filtre détecteurs). `evaluate_rules` retourne la liste d'`Alert` correspondantes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from p2p_fraud.schema import Finding

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass
class AlertRule:
    """Règle de déclenchement d'alerte.

    Un finding déclenche cette règle si :
    - sa sévérité est ≥ `severity_threshold` ;
    - son exposition est ≥ `exposure_min_eur` (si défini) ;
    - son détecteur est dans `detector_filter` (si défini).
    """

    name: str
    severity_threshold: str = "high"
    exposure_min_eur: float | None = None
    detector_filter: list[str] | None = None
    channels: list[str] = field(default_factory=list)
    enabled: bool = True

    def matches(self, finding: Finding) -> bool:
        if not self.enabled:
            return False
        rank = _SEVERITY_RANK.get(finding.severity.value, 0)
        threshold = _SEVERITY_RANK.get(self.severity_threshold, 2)
        if rank < threshold:
            return False
        if self.detector_filter and finding.detector not in self.detector_filter:
            return False
        if self.exposure_min_eur is not None:
            exposure = float(finding.evidence.get("exposure_eur") or 0)
            if exposure < self.exposure_min_eur:
                return False
        return True


@dataclass
class Alert:
    """Alerte produite par l'évaluation des règles."""

    rule_name: str
    severity: str
    title: str
    body: str
    metadata: dict = field(default_factory=dict)
    triggered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finding_invoice_id: str = ""
    finding_rule_id: str = ""


def evaluate_rules(findings: list[Finding], rules: list[AlertRule]) -> list[Alert]:
    """Évalue toutes les règles vs tous les findings — retourne les alertes déclenchées.

    Une alerte par (règle × finding) qui matche.
    """
    alerts: list[Alert] = []
    for rule in rules:
        for f in findings:
            if not rule.matches(f):
                continue
            vendor_name = f.evidence.get("vendor_name", "—")
            exposure = f.evidence.get("exposure_eur")
            exposure_str = f"{float(exposure):,.0f} €".replace(",", " ") if exposure else "—"
            title = f"[{f.severity.value.upper()}] {f.rule_id} — {vendor_name}"
            body = (
                f"**Règle déclenchée** : {rule.name}\n\n"
                f"**Détecteur** : {f.detector}\n"
                f"**Signal** : {f.signal}\n"
                f"**Facture** : {f.invoice_id}\n"
                f"**Exposition** : {exposure_str}\n\n"
                f"**Détails** : {f.evidence.get('reason', '—')}"
            )
            alerts.append(
                Alert(
                    rule_name=rule.name,
                    severity=f.severity.value,
                    title=title,
                    body=body,
                    metadata={
                        "vendor_name": vendor_name,
                        "siren": f.evidence.get("siren") or "—",
                        "rule_id": f.rule_id,
                        "exposure_eur": exposure_str,
                        "detector": f.detector,
                    },
                    finding_invoice_id=f.invoice_id,
                    finding_rule_id=f.rule_id,
                )
            )
    return alerts
