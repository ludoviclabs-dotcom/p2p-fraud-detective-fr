"""Tests des features de gouvernance : runtime des règles actives, coût IA,
fraîcheur des sources, backtest sur records réels. 100 % déterministes."""

from __future__ import annotations

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.enrichment.freshness import get_freshness, record_sync
from p2p_fraud.llm.ai_ledger import (
    AIUsageBucket,
    aggregate_ai_usage,
    estimate_cost_usd,
)
from p2p_fraud.rules.backtest import backtest_rule
from p2p_fraud.rules.dsl import RuleCondition, RuleSpec
from p2p_fraud.rules.runtime import DETECTOR_NAME, run_active_rules
from p2p_fraud.rules.store import RuleStore
from p2p_fraud.rules.testing import RuleTestCase, run_rule_tests

SOUS_SEUIL = RuleSpec(
    rule_id="THR_JUST_UNDER_10K",
    name="Facture juste sous le seuil 10 000 €",
    description="Montant dans la fenêtre [9 000, 10 000[ — contournement de seuil possible.",
    severity="high",
    reason_code="THR_JUST_UNDER_10K",
    required_fields=["amount"],
    conditions=[
        RuleCondition(field="amount", op="gte", value=9000),
        RuleCondition(field="amount", op="lt", value=10000),
    ],
)

_TESTS = [
    RuleTestCase(name="pos", record={"amount": 9500}, expect_match=True),
    RuleTestCase(name="neg", record={"amount": 100}, expect_match=False),
]


def _activated_store() -> RuleStore:
    store = RuleStore(":memory:")
    v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_TESTS)
    store.record_test_report(v.rule_id, v.version, run_rule_tests(SOUS_SEUIL, _TESTS), actor="a")
    store.record_backtest(
        v.rule_id,
        v.version,
        backtest_rule(SOUS_SEUIL, [{"invoice_id": "X", "amount": 9100}]),
        actor="a",
    )
    store.activate(v.rule_id, v.version, approver="reviewer@test")
    return store


# ─── Runtime des règles actives ──────────────────────────────────────────────


def test_run_active_rules_produces_findings():
    store = _activated_store()
    records = [
        {"invoice_id": "A", "amount": 9100},
        {"invoice_id": "B", "amount": 15000},
    ]
    findings = run_active_rules(records, store)
    assert len(findings) == 1
    f = findings[0]
    assert f.invoice_id == "A"
    assert f.detector == DETECTOR_NAME
    assert f.rule_id == "THR_JUST_UNDER_10K"
    assert f.severity.value == "high"
    assert f.evidence["reason_code"] == "THR_JUST_UNDER_10K"
    assert f.evidence["approved_by"] == "reviewer@test"


def test_run_active_rules_ignores_non_active_versions():
    store = RuleStore(":memory:")
    store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_TESTS)  # reste draft
    assert run_active_rules([{"invoice_id": "A", "amount": 9100}], store) == []


def test_detect_pipeline_includes_rule_studio(monkeypatch):
    """Le pipeline /detect exécute les règles actives via le détecteur rule_studio."""
    import pandas as pd

    from p2p_fraud.api import main as api_main

    store = _activated_store()
    monkeypatch.setattr(api_main, "_rule_store", lambda: store)
    df = pd.DataFrame([{"invoice_id": "A", "vendor_name": "V", "amount": 9100}])
    findings = api_main._run_detectors(df, ["rule_studio"])
    assert [f.rule_id for f in findings] == ["THR_JUST_UNDER_10K"]


# ─── Coût IA ─────────────────────────────────────────────────────────────────


def test_estimate_cost_known_and_unknown_model():
    cost = estimate_cost_usd(
        "claude-opus-4-8", input_tokens=1_000_000, output_tokens=1_000_000, cached_tokens=1_000_000
    )
    # 5 $ input + 0,5 $ cache (0,1×) + 25 $ output
    assert cost == pytest.approx(30.5)
    assert estimate_cost_usd("modele-inconnu", input_tokens=10, output_tokens=10) is None


def test_aggregate_ai_usage_by_feature():
    log = AuditLog(":memory:")
    log.append(actor="t", kind="case.created", payload={})  # bruit ignoré
    for feature, tokens in (("audit_explainer", 100), ("audit_explainer", 200), ("copilot", 50)):
        log.append(
            actor="t",
            kind="ai.generation",
            payload={
                "feature": feature,
                "model": "claude-sonnet-4-6",
                "input_tokens": tokens,
                "output_tokens": tokens,
                "cached_tokens": 0,
            },
        )
    total, by_feature = aggregate_ai_usage(log)
    assert total.n_calls == 3
    assert total.input_tokens == 350
    assert by_feature["audit_explainer"].n_calls == 2
    assert by_feature["copilot"].output_tokens == 50
    assert total.cost_usd > 0
    assert total.n_calls_unpriced == 0


def test_usage_bucket_counts_unpriced_models():
    bucket = AIUsageBucket()
    bucket.add({"feature": "x", "model": "gpt-mystere", "input_tokens": 10, "output_tokens": 10})
    assert bucket.n_calls_unpriced == 1
    assert bucket.cost_usd == 0.0


# ─── Fraîcheur des sources ───────────────────────────────────────────────────


def test_freshness_roundtrip(tmp_path):
    registry = tmp_path / "freshness.json"
    rows = {r["source"]: r for r in get_freshness(registry)}
    assert set(rows) == {"sirene", "decp", "sanctions", "pappers"}
    assert rows["sirene"]["last_sync"] is None

    record_sync("sirene", detail="lookup SIREN 123456789", path=registry)
    rows = {r["source"]: r for r in get_freshness(registry)}
    assert rows["sirene"]["last_sync"] is not None
    assert "123456789" in rows["sirene"]["detail"]
    assert rows["decp"]["last_sync"] is None  # les autres ne bougent pas


# ─── Backtest sur records réels ──────────────────────────────────────────────


def test_backtest_endpoint_accepts_real_records():
    from p2p_fraud.api.v1 import RuleBacktestBody, rules_backtest

    store = RuleStore(":memory:")
    v = store.save_draft(SOUS_SEUIL, author="auteur@test", tests=_TESTS)
    body = RuleBacktestBody(
        records=[
            {"invoice_id": "R1", "amount": 9200, "is_fraud": True},
            {"invoice_id": "R2", "amount": 9300, "is_fraud": False},
            {"invoice_id": "R3", "amount": 100, "is_fraud": False},
        ]
    )
    out = rules_backtest(v.rule_id, v.version, body, "anonymous", store)
    assert out.backtest is not None
    assert out.backtest["n_records"] == 3
    assert out.backtest["n_flagged"] == 2
    assert out.backtest["n_false_positive"] == 1
    assert out.backtest["precision"] == pytest.approx(0.5)
