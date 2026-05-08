"""Données de démo pré-chargées pour la file d'investigation.

Pour la vitrine fonctionnelle (Streamlit Cloud free tier — filesystem éphémère),
les cases sont seedés au démarrage si la base est vide. Les visiteurs voient
immédiatement des dossiers réalistes sans devoir uploader un fichier.

Cinq cas couvrant les statuts NEW → CLOSED et les détecteurs principaux
(master_data, doublons, sous-seuils, sanctions).
"""

from __future__ import annotations

from p2p_fraud.cases.models import CaseStatus
from p2p_fraud.cases.service import CaseService
from p2p_fraud.schema import Finding, Severity


def _make_finding(
    *,
    detector: str,
    rule_id: str,
    invoice_id: str,
    severity: Severity,
    signal: str,
    evidence: dict,
) -> Finding:
    return Finding(
        detector=detector,
        rule_id=rule_id,
        invoice_id=invoice_id,
        severity=severity,
        signal=signal,
        evidence=evidence,
    )


def seed_demo_cases(service: CaseService) -> int:
    """Crée 5 cases de démo si aucun n'existe. Retourne le nombre créé."""
    if service.list_cases():
        return 0

    # Cas 1 — BEC IBAN swap (CRITICAL, NEW)
    f1 = _make_finding(
        detector="master_data_changes",
        rule_id="MD_IBAN_NO_4EYES",
        invoice_id="INV-2026-0142",
        severity=Severity.CRITICAL,
        signal="Changement IBAN sans approbation 4-eyes",
        evidence={
            "vendor_id": "V-FOURNISSEUR-789",
            "vendor_name": "Acme Industries SAS",
            "old_iban": "FR76 3000 1007 9412 3456 7890 185",
            "new_iban": "FR14 2004 1010 0505 0001 3M02 606",
            "exposure_eur": 184_500.0,
            "changed_by": "user.compromis@erp",
            "approved_by": None,
        },
    )
    service.create_case_from_finding(
        f1, actor="auditeur.demo", title="BEC suspecté — Acme Industries"
    )

    # Cas 2 — Doublon de facture (HIGH, TRIAGED après assignation)
    f2 = _make_finding(
        detector="duplicates",
        rule_id="DUP_FUZZY_NAME_AMOUNT",
        invoice_id="INV-2026-0234",
        severity=Severity.HIGH,
        signal="Doublon flou nom + montant (±2%)",
        evidence={
            "vendor_id": "V-PRESTA-456",
            "vendor_name": "Prestation Conseil SA",
            "matched_invoice": "INV-2026-0218",
            "score_similarity": 0.94,
            "amount_a": 12_400.0,
            "amount_b": 12_580.0,
            "exposure_eur": 12_580.0,
        },
    )
    case2 = service.create_case_from_finding(
        f2, actor="auditeur.demo", title="Doublon Prestation Conseil"
    )
    service.assign(case2.case_id, "alice.controleur", actor="auditeur.demo")

    # Cas 3 — Sous-seuil de validation (HIGH, IN_PROGRESS)
    f3 = _make_finding(
        detector="thresholds",
        rule_id="THRESHOLD_CLUSTER",
        invoice_id="INV-2026-0301",
        severity=Severity.HIGH,
        signal="3 factures de 4,8-4,9 k€ sur 30 j (seuil 5 k€)",
        evidence={
            "vendor_id": "V-SOUS-SEUIL-321",
            "vendor_name": "Maintenance Express SARL",
            "n_invoices_under": 3,
            "cumul_eur": 14_650.0,
            "exposure_eur": 14_650.0,
        },
    )
    case3 = service.create_case_from_finding(
        f3, actor="auditeur.demo", title="Fragmentation suspectée — Maintenance Express"
    )
    service.assign(case3.case_id, "bob.audit", actor="auditeur.demo")
    service.set_status(case3.case_id, CaseStatus.IN_PROGRESS, actor="bob.audit")
    service.comment(
        case3.case_id,
        actor="bob.audit",
        text="Demande de PV de réception envoyée au demandeur d'achat.",
    )

    # Cas 4 — Sanctions match (CRITICAL, ESCALATED)
    f4 = _make_finding(
        detector="sanctions",
        rule_id="SANCTIONS_VENDOR",
        invoice_id="VENDOR::V-SANC-007",
        severity=Severity.CRITICAL,
        signal="Match liste OFAC SDN (score 0,96)",
        evidence={
            "vendor_id": "V-SANC-007",
            "vendor_name": "Volkov Trading Ltd",
            "list": "OFAC SDN",
            "match_score": 0.96,
            "matched_name": "Volkov Trade Ltd.",
            "exposure_eur": 73_200.0,
        },
    )
    case4 = service.create_case_from_finding(
        f4, actor="auditeur.demo", title="Sanctions OFAC — Volkov Trading"
    )
    service.assign(case4.case_id, "claire.compliance", actor="auditeur.demo")
    service.escalate(
        case4.case_id,
        actor="claire.compliance",
        channel="legal",
        reason="Match OFAC à 0,96 — blocage paiements en attente confirmation",
    )

    # Cas 5 — Faux positif clôturé (illustre le motif obligatoire)
    f5 = _make_finding(
        detector="duplicates",
        rule_id="DUP_FUZZY_NAME_AMOUNT",
        invoice_id="INV-2026-0089",
        severity=Severity.MEDIUM,
        signal="Doublon flou nom (score 0,88)",
        evidence={
            "vendor_id": "V-LEGITIME-100",
            "vendor_name": "Société Générale Services",
            "matched_invoice": "INV-2026-0091",
            "score_similarity": 0.88,
            "exposure_eur": 4_200.0,
        },
    )
    case5 = service.create_case_from_finding(
        f5, actor="auditeur.demo", title="Doublon Société Générale Services"
    )
    service.close(
        case5.case_id,
        CaseStatus.CLOSED_FALSE_POSITIVE,
        actor="auditeur.demo",
        reason=(
            "Vérification ERP : factures distinctes (mois différents, BC différents). "
            "Faux positif lié à la similarité du nom court."
        ),
    )

    return 5
