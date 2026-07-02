"""Détecteur 10 — Conflits d'intérêts employé ↔ fournisseur.

Croise le référentiel RH (``EmployeeRecord``) avec le référentiel fournisseurs
pour détecter les liens non déclarés : IBAN de salaire identique à un IBAN
fournisseur, adresse commune, homonymie forte. La rupture de séparation des
tâches (l'employé lié peut approuver des paiements) escalade le faisceau.

Signaux (rule_ids) :
- ``COI_SHARED_IBAN``    — IBAN employé présent sur une fiche fournisseur (CRITICAL)
- ``COI_SHARED_ADDRESS`` — adresse normalisée identique (HIGH)
- ``COI_NAME_MATCH``     — similarité de nom ≥ seuil RapidFuzz (MEDIUM)
- ``COI_APPROVER_LINK``  — l'employé matché peut approuver des paiements → rupture
  de séparation des tâches (HIGH, en plus du signal source)

Références : ISA 240 (management override), Sapin 2 art. 17 (cartographie des
risques de corruption), ACFE Fraud Tree (Corruption → Conflicts of interest).

Conception : calcul local pur — le référentiel RH ne quitte jamais le SI
(RGPD : minimisation, finalité détection fraude interne).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from rapidfuzz import fuzz

from p2p_fraud.schema import EmployeeRecord, Finding, Severity, Vendor

DEFAULT_NAME_SIMILARITY = 90.0

_DETECTOR = "conflicts_of_interest"


def _normalize_address(value: str | None) -> str | None:
    if not value:
        return None
    v = value.lower()
    v = re.sub(r"[.,;]", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v or None


def _normalize_iban(value: str | None) -> str | None:
    if not value:
        return None
    v = re.sub(r"\s", "", value).upper()
    return v or None


def _new_finding(
    vendor: Vendor,
    employee: EmployeeRecord,
    rule_id: str,
    signal: str,
    severity: Severity,
    extra: dict,
) -> Finding:
    evidence = {
        "vendor_name": vendor.name,
        "siren": vendor.siren,
        "employee_id": employee.employee_id,
        "employee_department": employee.department,
        "can_approve_payments": employee.can_approve_payments,
        **extra,
    }
    return Finding(
        # Finding hors facture : la clé porte le fournisseur concerné.
        invoice_id=f"VENDOR::{vendor.siren}",
        detector=_DETECTOR,
        signal=signal,
        severity=severity,
        rule_id=rule_id,
        evidence=evidence,
    )


def detect_conflicts_of_interest(
    employees: Iterable[EmployeeRecord],
    vendors: Iterable[Vendor],
    *,
    name_similarity_threshold: float = DEFAULT_NAME_SIMILARITY,
) -> list[Finding]:
    """Croise employés × fournisseurs et retourne les liens non déclarés.

    Le produit cartésien est acceptable aux volumétries cibles (référentiel RH
    d'une ETI × fournisseurs actifs) ; pour de plus gros volumes, indexer les
    IBAN/adresses au préalable.
    """
    employees = list(employees)
    vendors = list(vendors)
    findings: list[Finding] = []

    for emp in employees:
        emp_iban = _normalize_iban(emp.iban)
        emp_addr = _normalize_address(emp.address)

        for vendor in vendors:
            matched: list[Finding] = []

            if emp_iban and emp_iban in {_normalize_iban(i) for i in vendor.iban_list}:
                matched.append(
                    _new_finding(
                        vendor,
                        emp,
                        "COI_SHARED_IBAN",
                        "IBAN employé identique à un IBAN fournisseur",
                        Severity.CRITICAL,
                        {
                            "reason": (
                                "L'IBAN de versement de salaire de l'employé "
                                f"{emp.employee_id} est référencé sur la fiche fournisseur."
                            ),
                        },
                    )
                )

            vendor_addr = _normalize_address(vendor.address)
            if emp_addr and vendor_addr and emp_addr == vendor_addr:
                matched.append(
                    _new_finding(
                        vendor,
                        emp,
                        "COI_SHARED_ADDRESS",
                        "Adresse commune employé / fournisseur",
                        Severity.HIGH,
                        {
                            "address": vendor.address,
                            "reason": "Adresse déclarée identique après normalisation.",
                        },
                    )
                )

            score = fuzz.token_set_ratio(emp.full_name, vendor.name)
            if score >= name_similarity_threshold:
                matched.append(
                    _new_finding(
                        vendor,
                        emp,
                        "COI_NAME_MATCH",
                        "Homonymie forte employé / fournisseur",
                        Severity.MEDIUM,
                        {
                            "similarity": round(float(score), 1),
                            "employee_name": emp.full_name,
                            "reason": (
                                f"Similarité RapidFuzz {score:.0f} ≥ {name_similarity_threshold:.0f}."
                            ),
                        },
                    )
                )

            if matched and emp.can_approve_payments:
                matched.append(
                    _new_finding(
                        vendor,
                        emp,
                        "COI_APPROVER_LINK",
                        "Séparation des tâches rompue",
                        Severity.HIGH,
                        {
                            "linked_rules": [f.rule_id for f in matched],
                            "reason": (
                                "L'employé lié à ce fournisseur dispose du droit "
                                "d'approbation des paiements (rupture 4-eyes)."
                            ),
                        },
                    )
                )

            findings.extend(matched)

    return findings
