"""Golden set du Rule Studio — les 3 règles MVP du brief (Phase 4, ADR-0007).

Appelle réellement l'API Anthropic — sauté sans `ANTHROPIC_API_KEY`.
Gate de non-régression du prompt `rule-studio/N`.

Invariants par cas :
- le draft se convertit en RuleSpec valide (aller-retour YAML stable —
  vérifié en code par draft_rule, le test échoue sinon) ;
- les tests générés par le modèle passent sur le moteur déterministe ;
- les règles à composante statistique (répétition, doublon inter-records)
  déclarent leurs limites dans known_limitations au lieu de prétendre
  les couvrir.
"""

from __future__ import annotations

import os

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.llm.rule_studio import draft_rule

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Éval LLM — nécessite ANTHROPIC_API_KEY",
)


def _draft(description: str):
    log = AuditLog(":memory:")
    result = draft_rule(description, audit_log=log, actor="eval")
    # Le draft est journalisé au ledger.
    assert any(e.kind == "ai.generation" for e in log.all())
    return result


def test_golden_iban_change_sans_4eyes():
    result = _draft(
        "Alerter quand un changement d'IBAN fournisseur est enregistré dans les "
        "données de base sans validateur (champ validated_by vide ou absent). "
        "Sévérité critique : c'est le mode opératoire classique de la fraude au RIB."
    )
    assert result.test_report.all_passed, result.test_report
    assert result.spec.severity in {"high", "critical"}
    assert any("iban" in f.lower() or "field" in f.lower() for f in result.spec.required_fields)


def test_golden_sous_seuil_declared_limitations():
    result = _draft(
        "Alerter sur toute facture dont le montant est juste sous un seuil de "
        "validation (entre 9 000 € inclus et 10 000 € exclus), surtout si le "
        "même fournisseur le fait de façon répétée dans le mois."
    )
    assert result.test_report.all_passed, result.test_report
    # La répétition mensuelle est statistique → doit être déclarée comme limite.
    assert result.spec.known_limitations, "limite statistique non déclarée"


def test_golden_doublon_declared_limitations():
    result = _draft(
        "Détecter les doublons de factures : même montant, même date et même "
        "fournisseur qu'une autre facture déjà comptabilisée."
    )
    assert result.test_report.all_passed, result.test_report
    # La comparaison inter-records n'est pas exprimable dans le DSL mono-record.
    assert result.spec.known_limitations, "limite inter-records non déclarée"
