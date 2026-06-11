"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getAIUsage, getCoverage, getSourcesFreshness } from "@/lib/api-client";
import { useLocale } from "@/components/locale-provider";

/**
 * Panneaux gouvernance branchés au backend : coût IA (agrégation du ledger
 * ai.generation), fraîcheur des sources externes et couverture ISA 240.
 * Fallback sobre si le backend est absent (mode démo statique, ADR-0006).
 */
export function GovernanceLivePanels() {
  return (
    <div className="grid gap-4 lg:grid-cols-2" style={{ marginBottom: 16 }}>
      <AIUsagePanel />
      <FreshnessPanel />
      <div className="lg:col-span-2">
        <CoveragePanel />
      </div>
    </div>
  );
}

function PanelShell({
  title,
  subtitle,
  glyph,
  children,
}: {
  title: string;
  subtitle: string;
  glyph: string;
  children: React.ReactNode;
}) {
  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div>
          <h2>{title}</h2>
          <div className="sub">{subtitle}</div>
        </div>
        <span className="glyph">{glyph}</span>
      </div>
      <div className="fx-panel-body">{children}</div>
    </div>
  );
}

function BackendNotice() {
  const { t } = useLocale();
  return (
    <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", margin: 0 }}>
      {t("gov.unavailable_body")}
    </p>
  );
}

function AIUsagePanel() {
  const { t } = useLocale();
  const query = useQuery({ queryKey: ["ai-usage"], queryFn: getAIUsage, retry: false });

  return (
    <PanelShell title={t("gov.ai_usage_title")} subtitle={t("gov.ai_usage_subtitle")} glyph="¤">
      {query.error ? (
        <BackendNotice />
      ) : !query.data ? null : query.data.total.n_calls === 0 ? (
        <p className="fx-mono" style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>
          {t("gov.ai_usage_empty")}
        </p>
      ) : (
        <div className="space-y-3">
          <div className="flex items-baseline gap-3" style={{ flexWrap: "wrap" }}>
            <span
              style={{ fontFamily: "var(--font-display)", fontSize: 32, color: "var(--fg)" }}
              data-testid="ai-usage-total-cost"
            >
              {query.data.total.cost_usd.toFixed(4)} $
            </span>
            <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
              {query.data.total.n_calls} {t("gov.calls")} ·{" "}
              {query.data.total.input_tokens + query.data.total.cached_tokens} in ·{" "}
              {query.data.total.output_tokens} out
            </span>
          </div>
          <div className="space-y-1">
            {Object.entries(query.data.by_feature).map(([feature, bucket]) => (
              <div
                key={feature}
                className="fx-mono"
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 8,
                  fontSize: 11,
                  color: "var(--fg-2)",
                  background: "var(--bg-2)",
                  border: "1px solid var(--border)",
                  padding: "6px 10px",
                }}
              >
                <span>{feature}</span>
                <span style={{ color: "var(--muted)" }}>
                  {bucket.n_calls} {t("gov.calls")} · {bucket.cost_usd.toFixed(4)} $
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </PanelShell>
  );
}

function FreshnessPanel() {
  const { t, locale } = useLocale();
  const query = useQuery({
    queryKey: ["sources-freshness"],
    queryFn: getSourcesFreshness,
    retry: false,
  });

  return (
    <PanelShell
      title={t("gov.freshness_title")}
      subtitle={t("gov.freshness_subtitle")}
      glyph="◷"
    >
      {query.error ? (
        <BackendNotice />
      ) : !query.data ? null : (
        <div className="space-y-1">
          {query.data.map((source) => {
            const synced = Boolean(source.last_sync);
            const tone = !source.configured
              ? "var(--dim)"
              : synced
                ? "var(--verified)"
                : "var(--warn)";
            return (
              <div
                key={source.source}
                className="fx-mono"
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 8,
                  fontSize: 11,
                  background: "var(--bg-2)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${tone}`,
                  padding: "6px 10px",
                }}
              >
                <span style={{ color: "var(--fg-2)" }}>{source.label}</span>
                <span style={{ color: tone }}>
                  {!source.configured
                    ? t("gov.not_configured")
                    : synced
                      ? new Date(source.last_sync as string).toLocaleString(
                          locale === "fr" ? "fr-FR" : "en-GB",
                        )
                      : t("gov.never_synced")}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </PanelShell>
  );
}

function CoveragePanel() {
  const { t } = useLocale();
  const [run, setRun] = useState(false);
  const mutation = useMutation({ mutationFn: () => getCoverage() });

  return (
    <PanelShell
      title={t("gov.coverage_title")}
      subtitle={t("gov.coverage_subtitle")}
      glyph="▣"
    >
      <div className="space-y-3">
        <button
          className="fx-btn"
          type="button"
          data-testid="coverage-run-button"
          disabled={mutation.isPending}
          onClick={() => {
            setRun(true);
            mutation.mutate();
          }}
        >
          {mutation.isPending ? t("gov.coverage_running") : t("gov.coverage_run")}
        </button>
        {run && mutation.error ? <BackendNotice /> : null}
        {mutation.data ? (
          <>
            <p className="fx-mono" style={{ fontSize: 12, color: "var(--fg)", margin: 0 }}>
              {t("gov.coverage_summary", {
                nInvoices: mutation.data.n_invoices,
                nDetectors: mutation.data.n_detectors_executed,
                cleanRate: (mutation.data.overall_clean_rate * 100).toFixed(1),
              })}
            </p>
            <div className="grid gap-1 sm:grid-cols-2">
              {mutation.data.items.map((item) => (
                <div
                  key={item.detector}
                  className="fx-mono"
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 8,
                    fontSize: 11,
                    background: "var(--bg-2)",
                    border: "1px solid var(--border)",
                    borderLeft: `3px solid ${item.executed ? "var(--verified)" : "var(--dim)"}`,
                    padding: "6px 10px",
                  }}
                >
                  <span style={{ color: "var(--fg-2)" }}>{item.detector}</span>
                  <span style={{ color: "var(--muted)", textAlign: "right" }}>
                    {item.executed
                      ? `${item.n_findings} findings · ${((item.clean_rate ?? 0) * 100).toFixed(1)} %`
                      : `${t("gov.coverage_not_executed")} — ${item.reason}`}
                  </span>
                </div>
              ))}
            </div>
          </>
        ) : null}
      </div>
    </PanelShell>
  );
}
