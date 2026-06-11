"""Tests du moteur de règles Detection Studio (Phase 4, ADR-0007) — 100 % déterministes."""

from __future__ import annotations

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.rules.backtest import backtest_rule
from p2p_fraud.rules.dsl import (
    RuleCondition,
    RuleParseError,
    RuleSpec,
    evaluate,
    parse_rule_yaml,
    rule_to_yaml,
    run_rule,
)
from p2p_fraud.rules.store import (
    FourEyesError,
    PromotionError,
    RuleNotFoundError,
    RuleStore,
)
from p2p_fraud.rules.testing import RuleTestCase, run_rule_tests

# ─── Règle de référence : facture juste sous le seuil de validation ─────────

SOUS_SEUIL = RuleSpec(
    rule_id="THR_JUST_UNDER_10K",
    name="Facture juste sous le seuil 10 000 €",
    description="Montant dans la fenêtre [9 000, 10 000[ — contournement de seuil possible.",
    severity="high",
    reason_code="THR_JUST_UNDER_10K",
    required_fields=["amount"],
    match_mode="all",
    conditions=[
        RuleCondition(field="amount", op="gte", value=9000),
        RuleCondition(field="amount", op="lt", value=10000),
    ],
)


# ─── DSL : évaluation ────────────────────────────────────────────────────────


def test_evaluate_all_mode():
    assert evaluate(SOUS_SEUIL, {"amount": 9500})
    assert not evaluate(SOUS_SEUIL, {"amount": 10000})
    assert not evaluate(SOUS_SEUIL, {"amount": 800})


def test_evaluate_numeric_string_coercion():
    assert evaluate(SOUS_SEUIL, {"amount": "9 500".replace(" ", "")})
    assert evaluate(SOUS_SEUIL, {"amount": "9500,50"})  # virgule française


def test_missing_required_field_never_matches():
    assert not evaluate(SOUS_SEUIL, {})
    assert not evaluate(SOUS_SEUIL, {"amount": None})


def test_any_mode_and_string_ops():
    rule = RuleSpec(
        rule_id="VENDOR_WATCHLIST",
        name="Fournisseur sous surveillance",
        description="Fournisseur listé ou libellé suspect — vigilance renforcée.",
        severity="medium",
        reason_code="VENDOR_WATCHLIST",
        required_fields=["vendor_name"],
        match_mode="any",
        conditions=[
            RuleCondition(field="vendor_name", op="in", values=["ALPHACOM", "BETACORP"]),
            RuleCondition(field="vendor_name", op="contains", value="offshore"),
        ],
    )
    assert evaluate(rule, {"vendor_name": "alphacom"})  # insensible à la casse
    assert evaluate(rule, {"vendor_name": "Trading Offshore Ltd"})
    assert not evaluate(rule, {"vendor_name": "Papeterie Durand"})


def test_exists_missing_ops():
    rule = RuleSpec(
        rule_id="NO_PO_REFERENCE",
        name="Facture sans bon de commande",
        description="Aucune référence PO sur la facture — contrôle interne contourné.",
        severity="medium",
        reason_code="NO_PO_REFERENCE",
        required_fields=["invoice_id"],
        conditions=[RuleCondition(field="po_number", op="missing")],
    )
    assert evaluate(rule, {"invoice_id": "INV1"})
    assert evaluate(rule, {"invoice_id": "INV1", "po_number": None})
    assert not evaluate(rule, {"invoice_id": "INV1", "po_number": "PO-7"})


def test_run_rule_returns_matched_ids():
    records = [
        {"invoice_id": "A", "amount": 9100},
        {"invoice_id": "B", "amount": 12000},
        {"invoice_id": "C", "amount": 9999},
    ]
    assert run_rule(SOUS_SEUIL, records) == ["A", "C"]


# ─── DSL : YAML aller-retour ─────────────────────────────────────────────────


def test_yaml_roundtrip():
    text = rule_to_yaml(SOUS_SEUIL)
    parsed = parse_rule_yaml(text)
    assert parsed == SOUS_SEUIL


def test_parse_rejects_invalid_yaml_and_schema():
    with pytest.raises(RuleParseError):
        parse_rule_yaml("rule_id: [non terminé")
    with pytest.raises(RuleParseError):
        parse_rule_yaml("- liste\n- pas un mapping\n")
    with pytest.raises(RuleParseError):
        parse_rule_yaml("rule_id: minuscules_interdites\nname: x\n")


# ─── Runner de tests ─────────────────────────────────────────────────────────


def _test_cases() -> list[RuleTestCase]:
    return [
        RuleTestCase(name="positif fenêtre", record={"amount": 9500}, expect_match=True),
        RuleTestCase(name="négatif au seuil", record={"amount": 10000}, expect_match=False),
        RuleTestCase(name="négatif bas", record={"amount": 500}, expect_match=False),
    ]


def test_run_rule_tests_all_green():
    report = run_rule_tests(SOUS_SEUIL, _test_cases())
    assert report.all_passed
    assert report.n_passed == report.n_total == 3


def test_run_rule_tests_detects_failure():
    bad_cases = [
        *_test_cases(),
        RuleTestCase(name="attente fausse", record={"amount": 9500}, expect_match=False),
    ]
    report = run_rule_tests(SOUS_SEUIL, bad_cases)
    assert not report.all_passed
    assert report.n_passed == 3
    failed = [r for r in report.results if not r.passed]
    assert failed[0].name == "attente fausse"


def test_empty_test_suite_never_passes():
    assert not run_rule_tests(SOUS_SEUIL, []).all_passed


# ─── Backtest ────────────────────────────────────────────────────────────────


def test_backtest_counts_fp_and_precision():
    records = [
        {"invoice_id": "A", "amount": 9100, "is_fraud": True},
        {"invoice_id": "B", "amount": 9200, "is_fraud": False},  # faux positif
        {"invoice_id": "C", "amount": 500, "is_fraud": False},
        {"invoice_id": "D", "amount": 9900, "is_fraud": True},
    ]
    summary = backtest_rule(SOUS_SEUIL, records)
    assert summary.n_records == 4
    assert summary.n_flagged == 3
    assert summary.n_true_positive == 2
    assert summary.n_false_positive == 1
    assert summary.precision == pytest.approx(2 / 3)
    assert summary.alert_rate == pytest.approx(0.75)
    assert summary.sample_flagged_ids == ["A", "B", "D"]


def test_backtest_without_labels():
    summary = backtest_rule(SOUS_SEUIL, [{"invoice_id": "A", "amount": 9100}])
    assert summary.n_flagged == 1
    assert summary.precision is None


# ─── Store : lifecycle + 4-eyes ──────────────────────────────────────────────


def _store() -> RuleStore:
    return RuleStore(":memory:", audit_log=AuditLog(":memory:"))


def test_store_draft_then_versions():
    store = _store()
    v1 = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())
    assert (v1.rule_id, v1.version, v1.status) == ("THR_JUST_UNDER_10K", 1, "draft")
    v2 = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())
    assert v2.version == 2
    assert len(store.list_versions("THR_JUST_UNDER_10K")) == 2
    # Le YAML stocké reste parsable et identique à la spec.
    assert v1.spec == SOUS_SEUIL


def test_activation_requires_green_tests_and_backtest_and_4eyes():
    store = _store()
    v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())

    # 1. Pas de rapport de tests → refus.
    with pytest.raises(PromotionError, match="tests"):
        store.activate(v.rule_id, v.version, approver="reviewer@test")

    # 2. Tests verts mais pas de backtest → refus.
    report = run_rule_tests(SOUS_SEUIL, _test_cases())
    store.record_test_report(v.rule_id, v.version, report, actor="auteur@test")
    with pytest.raises(PromotionError, match="backtest"):
        store.activate(v.rule_id, v.version, approver="reviewer@test")

    # 3. Backtest présent mais approbateur = auteur → refus 4-eyes.
    summary = backtest_rule(SOUS_SEUIL, [{"invoice_id": "A", "amount": 9100}])
    store.record_backtest(v.rule_id, v.version, summary, actor="auteur@test")
    with pytest.raises(FourEyesError):
        store.activate(v.rule_id, v.version, approver="AUTEUR@test")  # casse ≠ identité

    # 4. Approbateur distinct → activation.
    active = store.activate(v.rule_id, v.version, approver="reviewer@test")
    assert active.status == "active"
    assert active.approved_by == "reviewer@test"


def test_failed_tests_keep_status_draft():
    store = _store()
    v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())
    bad = run_rule_tests(
        SOUS_SEUIL,
        [RuleTestCase(name="faux", record={"amount": 9500}, expect_match=False)],
    )
    updated = store.record_test_report(v.rule_id, v.version, bad, actor="auteur@test")
    assert updated.status == "draft"
    with pytest.raises(PromotionError):
        store.activate(v.rule_id, v.version, approver="reviewer@test")


def test_new_activation_supersedes_previous():
    store = _store()
    report = run_rule_tests(SOUS_SEUIL, _test_cases())
    summary = backtest_rule(SOUS_SEUIL, [{"invoice_id": "A", "amount": 9100}])
    for _ in range(2):
        v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())
        store.record_test_report(v.rule_id, v.version, report, actor="auteur@test")
        store.record_backtest(v.rule_id, v.version, summary, actor="auteur@test")
        store.activate(v.rule_id, v.version, approver="reviewer@test")
    versions = store.list_versions("THR_JUST_UNDER_10K")
    statuses = {v.version: v.status for v in versions}
    assert statuses == {1: "superseded", 2: "active"}


def test_superseded_version_cannot_be_reactivated():
    """Régression (review Codex) : réactiver une version superseded serait un
    rollback silencieux vers une règle obsolète — refus, même avec tests verts,
    backtest présent et approbateur distinct."""
    store = _store()
    report = run_rule_tests(SOUS_SEUIL, _test_cases())
    summary = backtest_rule(SOUS_SEUIL, [{"invoice_id": "A", "amount": 9100}])
    for _ in range(2):
        v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())
        store.record_test_report(v.rule_id, v.version, report, actor="auteur@test")
        store.record_backtest(v.rule_id, v.version, summary, actor="auteur@test")
        store.activate(v.rule_id, v.version, approver="reviewer@test")

    with pytest.raises(PromotionError, match="superseded"):
        store.activate("THR_JUST_UNDER_10K", 1, approver="reviewer@test")
    # La version active n'a pas bougé.
    statuses = {v.version: v.status for v in store.list_versions("THR_JUST_UNDER_10K")}
    assert statuses == {1: "superseded", 2: "active"}


def test_active_version_is_frozen():
    store = _store()
    v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())
    store.record_test_report(
        v.rule_id, v.version, run_rule_tests(SOUS_SEUIL, _test_cases()), actor="a"
    )
    store.record_backtest(
        v.rule_id,
        v.version,
        backtest_rule(SOUS_SEUIL, [{"invoice_id": "A", "amount": 9100}]),
        actor="a",
    )
    store.activate(v.rule_id, v.version, approver="reviewer@test")
    with pytest.raises(PromotionError, match="figée"):
        store.record_test_report(
            v.rule_id, v.version, run_rule_tests(SOUS_SEUIL, _test_cases()), actor="a"
        )


def test_store_lifecycle_is_audit_logged():
    audit = AuditLog(":memory:")
    store = RuleStore(":memory:", audit_log=audit)
    v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_test_cases())
    store.record_test_report(
        v.rule_id, v.version, run_rule_tests(SOUS_SEUIL, _test_cases()), actor="auteur@test"
    )
    store.record_backtest(
        v.rule_id,
        v.version,
        backtest_rule(SOUS_SEUIL, [{"invoice_id": "A", "amount": 9100}]),
        actor="auteur@test",
    )
    store.activate(v.rule_id, v.version, approver="reviewer@test")
    kinds = [e.kind for e in audit.all()]
    assert kinds == ["rule.drafted", "rule.tested", "rule.backtested", "rule.activated"]
    valid, _ = audit.verify_chain()
    assert valid


def test_get_unknown_rule_raises():
    with pytest.raises(RuleNotFoundError):
        _store().get("INCONNUE", 1)
