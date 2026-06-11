"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  activateRule,
  backtestRule,
  draftRule,
  listRules,
  runRuleTests,
} from "@/lib/api-client";
import type { RuleVersionOut } from "@/lib/api-client";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { useLocale } from "@/components/locale-provider";

/**
 * Studio de règles (Phase 4, ADR-0007) — authoring réel branché au backend.
 *
 * Français → draft LLM → YAML validé → tests exécutés par le moteur
 * déterministe → backtest sur dataset labellisé → activation 4-eyes
 * (approbateur ≠ auteur). Le LLM drafte ; le code engage.
 */
export function RuleStudioPanel() {
  const { t } = useLocale();
  const qc = useQueryClient();
  const [descriptionFr, setDescriptionFr] = useState("");
  const [author, setAuthor] = useState("analyste@p2pfd.local");

  const rulesQuery = useQuery({
    queryKey: ["rules"],
    queryFn: () => listRules(),
    retry: false,
  });

  const draftMutation = useMutation({
    mutationFn: () => draftRule({ description_fr: descriptionFr, author }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  const backendDown = Boolean(rulesQuery.error);

  return (
    <div className="fx-panel" style={{ marginBottom: 16 }} data-testid="rule-studio-panel">
      <div className="fx-panel-head">
        <div>
          <h2>{t("rules.title")}</h2>
          <div className="sub">{t("rules.subtitle")}</div>
        </div>
        <span className="glyph">⌬</span>
      </div>
      <div className="fx-panel-body space-y-4">
        <div>
          <label
            htmlFor="rule-studio-description"
            className="fx-eyebrow"
            style={{ display: "block", marginBottom: 6 }}
          >
            {t("rules.description_label")}
          </label>
          <textarea
            id="rule-studio-description"
            data-testid="rule-studio-description"
            value={descriptionFr}
            onChange={(e) => setDescriptionFr(e.target.value)}
            rows={3}
            placeholder="Ex. : alerter quand un changement d'IBAN fournisseur est enregistré sans validateur (4-eyes absent), sévérité critique…"
            style={{
              width: "100%",
              background: "var(--bg)",
              border: "1px solid var(--border)",
              padding: "10px 12px",
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              color: "var(--fg)",
              outline: "none",
              resize: "vertical",
            }}
          />
          <div style={{ display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap", alignItems: "center" }}>
            <input
              aria-label="Auteur de la règle"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              style={{
                height: 36,
                width: 260,
                background: "var(--bg)",
                border: "1px solid var(--border)",
                padding: "0 12px",
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                color: "var(--fg)",
                outline: "none",
              }}
            />
            <button
              className="fx-btn"
              data-testid="rule-studio-draft-button"
              type="button"
              disabled={descriptionFr.trim().length < 20 || draftMutation.isPending}
              onClick={() => draftMutation.mutate()}
            >
              {draftMutation.isPending ? t("rules.drafting") : t("rules.draft")}
            </button>
          </div>
        </div>

        {draftMutation.error || backendDown ? (
          <div className="fx-notice">
            <span className="glyph">⚠</span>
            <div>
              <div className="nt">{t("ai.unavailable_title")}</div>
              <p className="nb">{t("rules.unavailable_body")}</p>
            </div>
          </div>
        ) : null}

        {rulesQuery.data?.length ? (
          <div className="space-y-3">
            <div className="fx-eyebrow">
              {t("rules.versions", { count: rulesQuery.data.length })}
            </div>
            {rulesQuery.data.map((version) => (
              <RuleVersionCard
                key={`${version.rule_id}-${version.version}`}
                version={version}
              />
            ))}
          </div>
        ) : !backendDown && !rulesQuery.isLoading ? (
          <p className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
            {t("rules.none")}
          </p>
        ) : null}
      </div>
    </div>
  );
}

const STATUS_TONE: Record<string, "critical" | "high" | "medium" | "low"> = {
  draft: "medium",
  tested: "low",
  active: "low",
  superseded: "medium",
  rejected: "high",
};

function RuleVersionCard({ version }: { version: RuleVersionOut }) {
  const { t } = useLocale();
  const qc = useQueryClient();
  const [approver, setApprover] = useState("");
  const [showYaml, setShowYaml] = useState(false);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["rules"] });
  const testMutation = useMutation({
    mutationFn: () => runRuleTests(version.rule_id, version.version),
    onSuccess: invalidate,
  });
  const backtestMutation = useMutation({
    mutationFn: () => backtestRule(version.rule_id, version.version),
    onSuccess: invalidate,
  });
  const activateMutation = useMutation({
    mutationFn: () => activateRule(version.rule_id, version.version, { approver }),
    onSuccess: invalidate,
  });

  const report = version.test_report;
  const backtest = version.backtest;
  const frozen = version.status === "active" || version.status === "superseded";
  const canActivate =
    version.status === "tested" && Boolean(report?.all_passed) && backtest !== null;

  return (
    <div
      style={{
        background: "var(--bg-2)",
        border: "1px solid var(--border)",
        borderLeft: `3px solid ${version.status === "active" ? "var(--verified)" : "var(--border-strong)"}`,
        padding: "14px 16px",
      }}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2" style={{ flexWrap: "wrap" }}>
          <code className="fx-mono" style={{ fontSize: 12, color: "var(--fg)" }}>
            {version.rule_id} · v{version.version}
          </code>
          <Badge severity={STATUS_TONE[version.status] ?? "medium"}>{version.status}</Badge>
          <SeverityBadge value={version.severity} />
        </div>
        <span className="fx-mono" style={{ fontSize: 10, color: "var(--muted)" }}>
          par {version.author}
          {version.approved_by ? ` · approuvé par ${version.approved_by}` : ""}
        </span>
      </div>
      <p style={{ margin: "8px 0 0", fontSize: 13, color: "var(--fg-2)", lineHeight: 1.5 }}>
        {version.name}
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <span className="fx-mono" style={{ fontSize: 11, color: report?.all_passed ? "var(--verified)" : "var(--warn)" }}>
          {report
            ? `Tests : ${report.n_passed}/${report.n_total} ${report.all_passed ? "✓" : "✗"}`
            : t("rules.tests_not_run")}
        </span>
        <span className="fx-mono" style={{ fontSize: 11, color: backtest ? "var(--verified)" : "var(--muted)" }}>
          {backtest
            ? `Backtest : ${backtest.n_flagged} alertes / ${backtest.n_records} · ${backtest.n_false_positive} FP${backtest.precision !== null ? ` · précision ${(backtest.precision * 100).toFixed(0)} %` : ""}`
            : t("rules.backtest_not_run")}
        </span>
      </div>

      {report && !report.all_passed ? (
        <div className="mt-2 space-y-1">
          {report.results
            .filter((r) => !r.passed)
            .map((r) => (
              <div key={r.name} className="fx-mono" style={{ fontSize: 11, color: "var(--risk)" }}>
                ✗ {r.name} — attendu {String(r.expected)}, obtenu {String(r.actual)}
              </div>
            ))}
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          className="fx-btn-ghost sm"
          type="button"
          onClick={() => setShowYaml((s) => !s)}
        >
          {showYaml ? t("rules.hide_yaml") : t("rules.show_yaml")}
        </button>
        {!frozen ? (
          <>
            <button
              className="fx-btn-ghost sm"
              type="button"
              disabled={testMutation.isPending}
              onClick={() => testMutation.mutate()}
            >
              {t("rules.rerun_tests")}
            </button>
            <button
              className="fx-btn-ghost sm"
              type="button"
              disabled={backtestMutation.isPending}
              onClick={() => backtestMutation.mutate()}
            >
              {backtestMutation.isPending ? t("rules.backtesting") : t("rules.backtest")}
            </button>
          </>
        ) : null}
        {version.status === "tested" ? (
          <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
            <input
              aria-label={`Approbateur 4-eyes pour ${version.rule_id} v${version.version}`}
              placeholder={t("rules.approver_placeholder")}
              value={approver}
              onChange={(e) => setApprover(e.target.value)}
              style={{
                height: 30,
                width: 200,
                background: "var(--bg)",
                border: "1px solid var(--border)",
                padding: "0 10px",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--fg)",
                outline: "none",
              }}
            />
            <button
              className="fx-btn sm"
              type="button"
              disabled={!canActivate || !approver.trim() || activateMutation.isPending}
              onClick={() => activateMutation.mutate()}
            >
              {t("rules.activate")}
            </button>
          </span>
        ) : null}
      </div>

      {activateMutation.error ? (
        <div className="fx-mono" style={{ marginTop: 8, fontSize: 11, color: "var(--risk)" }}>
          {(activateMutation.error as Error).message}
        </div>
      ) : null}

      {showYaml ? (
        <pre
          style={{
            marginTop: 10,
            maxHeight: 320,
            overflowY: "auto",
            background: "var(--bg)",
            border: "1px solid var(--border-strong)",
            padding: "12px 14px",
            fontSize: 11,
            lineHeight: 1.6,
            color: "var(--fg-2)",
            fontFamily: "var(--font-mono)",
            whiteSpace: "pre-wrap",
          }}
        >
          {version.yaml}
        </pre>
      ) : null}
    </div>
  );
}
