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
          <div className="fx-eyebrow">Cockpit P2P · vue consolidée</div>
          <h1 style={{ marginTop: 9 }}>
            Cockpit risque <span className="italic">P2P</span>
          </h1>
          <p className="sub">
            Vue consolidée des risques fournisseurs, triée par exposition financière et prête
            pour la décision audit.
          </p>
        </div>
        <div className="fx-head-actions">
          <Link href="/sandbox" className="fx-btn">
            Analyser un scénario <span>↗</span>
          </Link>
          <Link href="/exports" className="fx-btn-ghost">
            Préparer l&apos;export
          </Link>
        </div>
      </div>

      <section className="grid gap-4 lg:grid-cols-[1fr_0.42fr]">
        <div>
          {kpisQuery.isLoading ? (
            <KpiSkeleton />
          ) : kpisQuery.error ? (
            <ActionState
              title="Backend indisponible"
              body="Les KPI live ne sont pas accessibles. Vous pouvez tout de même lancer une démo synthétique pour explorer le parcours."
              actionHref="/sandbox"
              actionLabel="Lancer la sandbox"
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
              <h2>Top fournisseurs par exposition</h2>
              <div className="sub">
                Le tri favorise l&apos;impact financier, pas seulement le score brut.
              </div>
            </div>
            <span className="glyph">◫</span>
          </div>
          {vendorsQuery.isLoading ? (
            <TableSkeleton />
          ) : vendorsQuery.error ? (
            <div className="fx-panel-body">
              <ActionState
                title="Fournisseurs non chargés"
                body="Vérifiez la variable NEXT_PUBLIC_API_URL ou explorez un scénario préchargé."
                actionHref="/sandbox"
                actionLabel="Voir les scénarios"
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
  return (
    <div className="fx-card-accent">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="fx-eyebrow">Priorité du jour</div>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 23,
              lineHeight: 1.1,
              color: "var(--fg)",
              marginTop: 8,
            }}
          >
            Réduire l&apos;exposition critique
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
        Traitez d&apos;abord les fournisseurs à criticité maximale avec retard SLA ou absence
        d&apos;assignation. Chaque case doit produire une preuve d&apos;audit exploitable.
      </p>
      <div className="mt-5 grid grid-cols-2 gap-3">
        {[
          ["Next action", "Assigner reviewer"],
          ["Preuve", "Audit trail"],
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
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KPICard
          label="Exposition totale"
          value={formatEur(data.exposure_total_eur)}
          tone="info"
          glyph="Σ"
        />
        <KPICard
          label="Exposition critique"
          value={formatEur(data.exposure_critical_eur)}
          tone="risk"
          glyph="▲"
        />
        <KPICard
          label="Cases ouverts"
          value={String(data.n_cases_open)}
          tone="warn"
          glyph="▣"
        />
        <KPICard
          label="Retards SLA"
          value={String(data.n_cases_overdue)}
          delta={
            data.n_cases_unassigned_critical > 0
              ? `${data.n_cases_unassigned_critical} non assignés`
              : undefined
          }
          tone="ok"
          glyph="◷"
        />
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <TrendCard title="Cases créés" points={data.trend_cases_created ?? []} color="var(--info)" />
        <TrendCard
          title="Cases clôturés"
          points={data.trend_cases_closed ?? []}
          color="var(--verified)"
        />
        <TrendCard
          title="Alertes critiques"
          points={data.trend_critical_alerts ?? []}
          color="var(--risk)"
        />
        <TrendCard
          title="Activité audit"
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
        Tendance 30 jours
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
  if (isLoading) {
    return <div className="fx-skel" style={{ height: 286 }} />;
  }

  if (isError || !data) {
    return (
      <ActionState
        title="Breakdown démo indisponible"
        body="Les métriques statiques du graphe ne sont pas accessibles pour le moment."
        actionHref="/rings"
        actionLabel="Ouvrir le graphe"
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
          <div className="fx-eyebrow">Démo Vercel</div>
          <h2 style={{ marginTop: 3 }}>Répartition des signaux</h2>
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
          Explorer le graphe →
        </Link>
      </div>
    </div>
  );
}

function RecommendedPath() {
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
          Parcours recommandé
        </span>
      </div>
      <div className="mt-5 space-y-4">
        {[
          ["1", "Qualifier la case", "Vérifier score, source et exposition."],
          ["2", "Ouvrir fournisseur 360", "Valider liens SIREN, IBAN et historique."],
          ["3", "Exporter la preuve", "Signer et archiver la piste d'audit."],
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
  if (!rows.length) {
    return (
      <div className="fx-panel-body">
        <ActionState
          title="Aucun finding chargé"
          body="Le Top 10 se calcule sur les findings de la session. Lancez un scénario synthétique pour voir le cockpit rempli."
          actionHref="/sandbox"
          actionLabel="Analyser un scénario"
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
            <th>Fournisseur</th>
            <th className="num">Exposition</th>
            <th className="num">Findings</th>
            <th>Sévérité</th>
            <th className="num">Action</th>
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
                  Ouvrir 360 →
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
            ↻ Réessayer
          </button>
        </div>
      </div>
    </div>
  );
}
