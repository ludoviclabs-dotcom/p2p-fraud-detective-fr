"""Tests détecteur 10 — conflits d'intérêts employé ↔ fournisseur."""

from __future__ import annotations

from p2p_fraud.detectors.conflicts import detect_conflicts_of_interest
from p2p_fraud.schema import EmployeeRecord, Severity, Vendor


def _employee(**overrides) -> EmployeeRecord:
    base = {
        "employee_id": "EMP-001",
        "full_name": "Marc Dupont",
        "email": "marc.dupont@entreprise.fr",
        "address": "12 rue des Lilas, 75011 Paris",
        "iban": "FR76 1027 8060 4100 0204 2240 133",
        "department": "Comptabilité fournisseurs",
        "can_approve_payments": False,
    }
    base.update(overrides)
    return EmployeeRecord(**base)


def _vendor(**overrides) -> Vendor:
    base = {
        "siren": "489330715",
        "name": "Prestaconseil RH",
        "iban_list": ["FR7610278060410002042240133"],
        "address": "12 rue des lilas 75011 PARIS",
    }
    base.update(overrides)
    return Vendor(**base)


def test_shared_iban_critical() -> None:
    """IBAN salaire == IBAN fournisseur → CRITICAL, insensible aux espaces."""
    findings = detect_conflicts_of_interest([_employee()], [_vendor(address=None)])
    iban_hits = [f for f in findings if f.rule_id == "COI_SHARED_IBAN"]
    assert len(iban_hits) == 1
    assert iban_hits[0].severity == Severity.CRITICAL
    assert iban_hits[0].invoice_id == "VENDOR::489330715"


def test_shared_address_normalized() -> None:
    """Adresses équivalentes après normalisation (casse, ponctuation)."""
    findings = detect_conflicts_of_interest(
        [_employee(iban=None)],
        [_vendor(iban_list=[])],
    )
    assert [f.rule_id for f in findings] == ["COI_SHARED_ADDRESS"]
    assert findings[0].severity == Severity.HIGH


def test_name_match_fuzzy() -> None:
    """Homonymie forte employé / raison sociale."""
    findings = detect_conflicts_of_interest(
        [_employee(iban=None, address=None, full_name="Dupont Marc")],
        [_vendor(iban_list=[], address=None, name="SARL Marc Dupont")],
    )
    assert [f.rule_id for f in findings] == ["COI_NAME_MATCH"]
    assert findings[0].severity == Severity.MEDIUM
    assert findings[0].evidence["similarity"] >= 90


def test_approver_link_escalation() -> None:
    """Un match + droit d'approbation → finding COI_APPROVER_LINK en plus."""
    findings = detect_conflicts_of_interest(
        [_employee(can_approve_payments=True, address=None)],
        [_vendor(address=None)],
    )
    rule_ids = {f.rule_id for f in findings}
    assert "COI_SHARED_IBAN" in rule_ids
    assert "COI_APPROVER_LINK" in rule_ids
    link = next(f for f in findings if f.rule_id == "COI_APPROVER_LINK")
    assert link.evidence["linked_rules"] == ["COI_SHARED_IBAN"]


def test_no_link_no_findings() -> None:
    """Aucun attribut partagé → aucun finding."""
    findings = detect_conflicts_of_interest(
        [
            _employee(
                full_name="Julie Martin",
                iban="FR7630006000011234567890189",
                address="1 avenue Foch, Lyon",
            )
        ],
        [_vendor()],
    )
    assert findings == []
