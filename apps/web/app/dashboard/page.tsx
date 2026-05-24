"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  getCockpitKpis,
  getDemoGraphMetrics,
  getTopVendors,
  type CockpitKPIs,
  type DemoGraphMetrics,
  type TopVendor,
} from "@/lib/api-client";
import { formatNumber } from "@/lib/p2p-demo-format";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";
import { useLocale } from "@/components/locale-provider";

type KpiTone = "info" | "risk" | "warn" | "ok";

function KPICard({
  label,
  value,
  delta,
  tone,
  glyph,
}: {
  label: string;
  value: string;
  delta?: string;
  tone: KpiTone;
  glyph: string;
}) {
  return (
    <div className={`fx-stat ${tone}`}>
      <div className="fx-stat-top">
        <span className="glyph">{glyph}</span>
        {delta ? <span className="pill">{delta}</span> : null}
      </div>
      <div className="lbl">{label}</div>
      <div className="val">{value}</div>
    </div>
  );
}

function Sparkline({
  points,
  color = "var(--risk)",
}: {
  points: { date: string; value: number }[];
  color?: string;
}) {
  if (!points.length) {
    return (
      <div
        className="mt-3 h-14"
        style={{ background: "var(--bg-2)", border: "1px solid var(--border)" }}
      />
    );
  }
  const max = Math.max(...points.map((p) => p.value), 1);
  const width = 200;
  const height = 44;
  const stepX = width / (points.length - 1 || 1);
  const path = points
    .map((p, i) => {
      const x = i * stepX;
      const y = height - (p.value / max) * height;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const area = `${path} L${width},${height} L0,${height} Z`;
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="mt-3 h-14 w-full"
      aria-hidden
    >
      <path d={area} fill={color} fillOpacity={0.14} />
      <path d={path} fill="none" stroke={color} strokeWidth={2.4} />
    </svg>
  );
}

export default function DashboardPage() {
  const { t } = useLocale();
  const kpisQuery = useQuery({
    queryKey: ["cockpit", "kpis"],
    queryFn: getCockpitKpis,
    retry: false,
  });
  const vendorsQuery = useQuery({
    queryKey: ["cockpit", "top-vendors"],
    queryFn: () => getTopVendors(10),
    retry: false,
  });
  const demoGraphQuery = useQuery({
    queryKey: ["p2p-demo", "graph-metrics"],
    queryFn: getDemoGraphMetrics,
    retry: false,
  });

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">{t("dashboard.kicker")}</div>
          <h1 style={{ marginTop: 9 }}>{t("dashboard.title")}</h1>
          <p className="sub">{t("dashboard.description")}</p>
        </div>
        <div className="fx-head-actions">
          <Link href="/sandbox" className="fx-btn">
            {t("dashboard.analyze_scenario")} <span>↗</span>
          </Link>
          <Link href="/exports" className="fx-btn-ghost">
            {t("dashboard.prepare_export")}
          </Link>
        </div>
      </div>

      <section className="grid gap-4 lg:grid-cols-[1fr_0.42fr]">
        <div>
          {kpisQuery.isLoading ? (
            <KpiSkeleton />
          ) : kpisQuery.error ? (
            <ActionState
              title={t("dashboard.backend_unavailable_title")}
              body={t("dashboard.backend_unavailable_body")}
              actionHref="/sandbox"
              actionLabel={t("dashboard.launch_sandbox")}
            />
          ) : (
            <KpiGrid data={kpisQuery.data!} />
          )}
        </div>

        <PriorityPanel />
      </section>

      <section className="mt-8 grid gap-4 xl:grid-cols-[1fr_0.42fr]">
        <div className="fx-panel">
          <div className="fx-panel-head">
            <div>
              <h2>{t("dashboard.top_vendors_title")}</h2>
              <div className="sub">{t("dashboard.top_vendors_subtitle")}</div>
            </div>
            <span className="glyph">◫</span>
          </div>
          {vendorsQuery.isLoading ? (
            <TableSkeleton />
          ) : vendorsQuery.error ? (
            <div className="fx-panel-body">
              <ActionState
                title={t("dashboard.vendors_unloaded_title")}
                body={t("dashboard.vendors_unloaded_body")}
                actionHref="/sandbox"
                actionLabel={t("dashboard.view_scenarios")}
              />
            </div>
          ) : (
            <TopVendorsTable rows={vendorsQuery.data ?? []} />
          )}
        </div>

        <div className="flex flex-col gap-4">
          <SignalBreakdownCard
            data={demoGraphQuery.data}
            isLoading={demoGraphQuery.isLoading}
            isError={demoGraphQuery.isError}
          />
          <RecommendedPath />
        </div>
      </section>
    </ForensicPage>
  );
}

function PriorityPanel() {
  const { t } = useLocale();

  return (
    <div className="fx-card-accent">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="fx-eyebrow">{t("dashboard.priority_kicker")}</div>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 23,
              lineHeight: 1.1,
              color: "var(--fg)",
              marginTop: 8,
            }}
          >
            {t("dashboard.priority_title")}
          </div>
        </div>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: "var(--risk)" }}>▲</span>
      </div>
      <p
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          lineHeight: 1.65,
          color: "var(--muted)",
          marginTop: 14,
        }}
      >
        {t("dashboard.priority_body")}
      </p>
      <div className="mt-5 grid grid-cols-2 gap-3">
        {[
          [t("dashboard.next_action"), t("dashboard.assign_reviewer")],
          [t("dashboard.evidence"), t("dashboard.audit_trail")],
        ].map(([k, v]) => (
          <div
            key={k}
            style={{ background: "var(--panel)", border: "1px solid var(--border)", padding: "11px 13px" }}
          >
            <div className="fx-eyebrow">{k}</div>
            <div
              className="fx-mono"
              style={{ fontSize: 12, color: "var(--fg)", marginTop: 5 }}
            >
              {v}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function KpiSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {["a", "b", "c", "d"].map((k) => (
        <div key={k} className="fx-skel" style={{ height: 134 }} />
      ))}
    </div>
  );
}

function KpiGrid({ data }: { data: CockpitKPIs }) {
  const { t } = useLocale();

  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KPICard
          label={t("dashboard.kpi_total_exposure")}
          value={formatEur(data.exposure_total_eur)}
          tone="info"
          glyph="Σ"
        />
        <KPICard
          label={t("dashboard.kpi_critical_exposure")}
          value={formatEur(data.exposure_critical_eur)}
          tone="risk"
          glyph="▲"
        />
        <KPICard
          label={t("dashboard.kpi_open_cases")}
          value={String(data.n_cases_open)}
          tone="warn"
          glyph="▣"
        />
        <KPICard
          label={t("dashboard.kpi_sla_delays")}
          value={String(data.n_cases_overdue)}
          delta={
            data.n_cases_unassigned_critical > 0
              ? t("dashboard.kpi_unassigned", {
                  count: data.n_cases_unassigned_critical,
                })
              : undefined
          }
          tone="ok"
          glyph="◷"
        />
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <TrendCard title={t("dashboard.trend_created")} points={data.trend_cases_created ?? []} color="var(--info)" />
        <TrendCard
          title={t("dashboard.trend_closed")}
          points={data.trend_cases_closed ?? []}
          color="var(--verified)"
        />
        <TrendCard
          title={t("dashboard.trend_critical_alerts")}
          points={data.trend_critical_alerts ?? []}
          color="var(--risk)"
        />
        <TrendCard
          title={t("dashboard.trend_audit_activity")}
          points={data.trend_audit_activity ?? []}
          color="var(--warn)"
        />
      </div>
    </>
  );
}

function TrendCard({
  title,
  points,
  color,
}: {
  title: string;
  points: { date: string; value: number }[];
  color: string;
}) {
  const { t } = useLocale();

  return (
    <div className="fx-card">
      <div className="flex items-center justify-between gap-3">
        <span className="fx-mono" style={{ fontSize: 11, color: "var(--fg)", letterSpacing: "0.02em" }}>
          {title}
        </span>
        <span style={{ color }}>∿</span>
      </div>
      <Sparkline points={points} color={color} />
      <div className="fx-eyebrow" style={{ marginTop: 8 }}>
        {t("dashboard.trend_window")}
      </div>
    </div>
  );
}

function SignalBreakdownCard({
  data,
  isLoading,
  isError,
}: {
  data: DemoGraphMetrics | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const { t } = useLocale();

  if (isLoading) {
    return <div className="fx-skel" style={{ height: 286 }} />;
  }

  if (isError || !data) {
    return (
      <ActionState
        title={t("dashboard.breakdown_unavailable_title")}
        body={t("dashboard.breakdown_unavailable_body")}
        actionHref="/rings"
        actionLabel={t("dashboard.open_graph")}
      />
    );
  }

  const severityRows: [string, number, string][] = [
    ["Critical", data.metrics.criticalFindings, "var(--risk)"],
    ["High", data.metrics.highFindings, "var(--warn)"],
    ["Medium", data.metrics.mediumFindings, "var(--info)"],
  ];

  return (
    <div className="fx-panel" data-testid="dashboard-signal-breakdown">
      <div className="fx-panel-head">
        <div>
          <div className="fx-eyebrow">{t("dashboard.vercel_demo")}</div>
          <h2 style={{ marginTop: 3 }}>{t("dashboard.signal_breakdown")}</h2>
        </div>
        <span className="glyph">▦</span>
      </div>
      <div className="fx-panel-body">
        <div className="grid grid-cols-3 gap-2">
          {severityRows.map(([label, count, color]) => (
            <div
              key={label}
              style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}
            >
              <div className="fx-eyebrow">{label}</div>
              <div className="fx-mono" style={{ fontSize: 18, fontWeight: 700, color, marginTop: 5 }}>
                {formatNumber(Number(count))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 space-y-3">
          {data.signalBreakdown.map((item) => (
            <div key={item.signal}>
              <div className="flex items-center justify-between gap-3">
                <span className="fx-mono" style={{ fontSize: 12, color: "var(--fg)" }}>
                  {item.label}
                </span>
                <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                  {formatNumber(item.count)}
                </span>
              </div>
              <div className="fx-bar" style={{ marginTop: 6 }}>
                <i style={{ width: `${Math.max(item.share * 100, 2)}%` }} />
              </div>
            </div>
          ))}
        </div>

        <Link href="/rings" className="fx-link" style={{ marginTop: 18 }}>
          {t("dashboard.explore_graph")} →
        </Link>
      </div>
    </div>
  );
}

function RecommendedPath() {
  const { t } = useLocale();

  return (
    <div className="fx-card">
      <div className="flex items-center gap-2">
        <span style={{ fontFamily: "var(--font-mono)", color: "var(--risk)" }}>▣</span>
        <span
          className="fx-mono"
          style={{
            fontSize: 12,
            color: "var(--fg)",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
          }}
        >
          {t("dashboard.recommended_path")}
        </span>
      </div>
      <div className="mt-5 space-y-4">
        {[
          ["1", t("dashboard.step_qualify_title"), t("dashboard.step_qualify_body")],
          ["2", t("dashboard.step_vendor_title"), t("dashboard.step_vendor_body")],
          ["3", t("dashboard.step_export_title"), t("dashboard.step_export_body")],
        ].map(([step, title, body]) => (
          <div key={step} className="fx-step">
            <div className="n">{step}</div>
            <div>
              <div className="t">{title}</div>
              <div className="d">{body}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3 p-5">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="fx-skel" style={{ height: 44 }} />
      ))}
    </div>
  );
}

function TopVendorsTable({ rows }: { rows: TopVendor[] }) {
  const { t } = useLocale();

  if (!rows.length) {
    return (
      <div className="fx-panel-body">
        <ActionState
          title={t("dashboard.empty_findings_title")}
          body={t("dashboard.empty_findings_body")}
          actionHref="/sandbox"
          actionLabel={t("dashboard.analyze_scenario")}
        />
      </div>
    );
  }
  const severityClass: Record<string, string> = {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low",
  };
  return (
    <div className="fx-table-wrap">
      <table className="fx-table" data-testid="dashboard-top-vendors">
        <thead>
          <tr>
            <th>{t("dashboard.table_vendor")}</th>
            <th className="num">{t("dashboard.table_exposure")}</th>
            <th className="num">{t("dashboard.table_findings")}</th>
            <th>{t("dashboard.table_severity")}</th>
            <th className="num">{t("dashboard.table_action")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.vendor_id}>
              <td className="key">{row.vendor_id}</td>
              <td className="num">{formatEur(row.exposure_eur)}</td>
              <td className="num">{row.n_findings}</td>
              <td>
                <span className={`fx-tag ${severityClass[row.max_severity] ?? ""}`}>
                  {row.max_severity.toUpperCase()}
                </span>
              </td>
              <td className="num">
                <Link
                  href={`/vendors/${encodeURIComponent(row.vendor_id)}`}
                  className="fx-link"
                >
                  {t("dashboard.open_360")} →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ActionState({
  title,
  body,
  actionHref,
  actionLabel,
}: {
  title: string;
  body: string;
  actionHref: string;
  actionLabel: string;
}) {
  const { t } = useLocale();

  return (
    <div className="fx-notice">
      <span className="glyph">⚠</span>
      <div className="min-w-0 flex-1">
        <div className="nt">{title}</div>
        <p className="nb">{body}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href={actionHref} className="fx-btn">
            {actionLabel} <span>↗</span>
          </Link>
          <button
            type="button"
            className="fx-btn-ghost"
            onClick={() => window.location.reload()}
          >
            ↻ {t("dashboard.retry")}
          </button>
        </div>
      </div>
    </div>
  );
}
