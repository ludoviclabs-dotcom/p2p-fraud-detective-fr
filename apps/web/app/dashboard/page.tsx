"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getCockpitKpis,
  getTopVendors,
  type CockpitKPIs,
  type TopVendor,
} from "@/lib/api-client";
import { formatEur } from "@/lib/utils";

function KPICard({
  label,
  value,
  delta,
}: {
  label: string;
  value: string;
  delta?: string;
}) {
  return (
    <div className="rounded-md border border-l-4 border-[#e1e5ee] border-l-[#1f3a6e] bg-white p-4 dark:bg-[#162847] dark:border-[#1f3a6e]">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        {label}
      </div>
      <div className="text-2xl font-semibold text-[#0f1b33] dark:text-white">
        {value}
      </div>
      {delta ? (
        <div className="mt-1 text-xs text-[#a23e48]">{delta}</div>
      ) : null}
    </div>
  );
}

function Sparkline({
  points,
  color = "#1f3a6e",
}: {
  points: { date: string; value: number }[];
  color?: string;
}) {
  if (!points.length) return null;
  const max = Math.max(...points.map((p) => p.value), 1);
  const width = 200;
  const height = 40;
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
      className="w-full h-12"
      aria-hidden
    >
      <path d={area} fill={color} fillOpacity={0.2} />
      <path d={path} fill="none" stroke={color} strokeWidth={2} />
    </svg>
  );
}

export default function DashboardPage() {
  const kpisQuery = useQuery({
    queryKey: ["cockpit", "kpis"],
    queryFn: getCockpitKpis,
  });
  const vendorsQuery = useQuery({
    queryKey: ["cockpit", "top-vendors"],
    queryFn: () => getTopVendors(10),
  });

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Pilotage
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Cockpit
      </h1>
      <p className="mb-8 text-sm text-[#5a6478]">
        Vue consolidée des risques P2P — exposition financière prioritaire
      </p>

      {kpisQuery.isLoading ? (
        <KpiSkeleton />
      ) : kpisQuery.error ? (
        <div className="rounded border border-[#a23e48] bg-[#fdecee] p-4 text-sm text-[#a23e48]">
          ⚠️ API indisponible : vérifiez `NEXT_PUBLIC_API_URL` et que le backend
          FastAPI est lancé.
        </div>
      ) : (
        <KpiGrid data={kpisQuery.data!} />
      )}

      <div className="mt-10">
        <h2 className="mb-3 text-lg font-semibold text-[#0f1b33] dark:text-white">
          🏆 Top 10 fournisseurs par exposition financière
        </h2>
        {vendorsQuery.isLoading ? (
          <div className="text-sm text-[#5a6478]">Chargement…</div>
        ) : vendorsQuery.error ? (
          <div className="text-sm text-[#a23e48]">API indisponible.</div>
        ) : (
          <TopVendorsTable rows={vendorsQuery.data ?? []} />
        )}
      </div>
    </div>
  );
}

function KpiSkeleton() {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="h-24 animate-pulse rounded-md border border-[#e1e5ee] bg-white"
        />
      ))}
    </div>
  );
}

function KpiGrid({ data }: { data: CockpitKPIs }) {
  return (
    <>
      <div className="grid gap-3 md:grid-cols-4">
        <KPICard
          label="💸 Exposition totale"
          value={formatEur(data.exposure_total_eur)}
        />
        <KPICard
          label="🔴 Exposition CRITICAL"
          value={formatEur(data.exposure_critical_eur)}
        />
        <KPICard label="📂 Cases ouverts" value={String(data.n_cases_open)} />
        <KPICard
          label="⏰ Cases en retard SLA"
          value={String(data.n_cases_overdue)}
          delta={
            data.n_cases_unassigned_critical > 0
              ? `${data.n_cases_unassigned_critical} non assignés`
              : undefined
          }
        />
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-4">
        <div className="rounded-md border border-[#e1e5ee] bg-white p-3">
          <div className="text-xs text-[#5a6478]">Cases créés (30j)</div>
          <Sparkline points={data.trend_cases_created} color="#1f3a6e" />
        </div>
        <div className="rounded-md border border-[#e1e5ee] bg-white p-3">
          <div className="text-xs text-[#5a6478]">Cases clôturés (30j)</div>
          <Sparkline points={data.trend_cases_closed} color="#3e7c5a" />
        </div>
        <div className="rounded-md border border-[#e1e5ee] bg-white p-3">
          <div className="text-xs text-[#5a6478]">Alertes critiques (30j)</div>
          <Sparkline points={data.trend_critical_alerts} color="#a23e48" />
        </div>
        <div className="rounded-md border border-[#e1e5ee] bg-white p-3">
          <div className="text-xs text-[#5a6478]">Activité audit (30j)</div>
          <Sparkline points={data.trend_audit_activity} color="#e5a93a" />
        </div>
      </div>
    </>
  );
}

function TopVendorsTable({ rows }: { rows: TopVendor[] }) {
  if (!rows.length) {
    return (
      <div className="text-sm text-[#5a6478]">
        Top 10 calculé sur les findings de la session. Aucun finding chargé.
      </div>
    );
  }
  const severityColor: Record<string, string> = {
    critical: "bg-[#a23e48] text-white",
    high: "bg-[#c97b1f] text-white",
    medium: "bg-[#e5a93a] text-[#0f1b33]",
    low: "bg-[#3e7c5a] text-white",
  };
  return (
    <div className="overflow-hidden rounded-md border border-[#e1e5ee] bg-white">
      <table className="w-full text-sm">
        <thead className="bg-[#f4f6fa] text-[#5a6478]">
          <tr>
            <th className="px-4 py-2 text-left">Vendor ID</th>
            <th className="px-4 py-2 text-right">Exposition €</th>
            <th className="px-4 py-2 text-right">Findings</th>
            <th className="px-4 py-2 text-left">Sévérité max</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.vendor_id} className="border-t border-[#e1e5ee]">
              <td className="px-4 py-2 font-mono">{row.vendor_id}</td>
              <td className="px-4 py-2 text-right">
                {formatEur(row.exposure_eur)}
              </td>
              <td className="px-4 py-2 text-right">{row.n_findings}</td>
              <td className="px-4 py-2">
                <span
                  className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${severityColor[row.max_severity] ?? "bg-[#e1e5ee] text-[#0f1b33]"}`}
                >
                  {row.max_severity.toUpperCase()}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
