"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { listCases, type CaseOutV1 } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#a23e48",
  high: "#c97b1f",
  medium: "#e5a93a",
  low: "#3e7c5a",
};

const SEVERITY_Y: Record<string, number> = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
};

export default function AnomaliesPage() {
  const query = useQuery({
    queryKey: ["all-cases-anomalies"],
    queryFn: () => listCases({ limit: 1000 }),
  });

  const scatterData = useMemo(() => {
    return (query.data ?? [])
      .filter((c) => (c.exposure_eur ?? 0) > 0)
      .map((c) => ({
        case_id: c.case_id,
        title: c.title,
        vendor_id: c.vendor_id,
        severity: c.severity,
        x: c.exposure_eur ?? 0,
        y: SEVERITY_Y[c.severity] ?? 0,
        z: 100,
        fill: SEVERITY_COLORS[c.severity] ?? "#1f3a6e",
      }));
  }, [query.data]);

  const grouped = useMemo(() => {
    const acc: Record<string, typeof scatterData> = {
      critical: [],
      high: [],
      medium: [],
      low: [],
    };
    for (const d of scatterData) {
      acc[d.severity]?.push(d);
    }
    return acc;
  }, [scatterData]);

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Détection ML
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Anomalies (ML)
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Dispersion des cases sur l'axe exposition (€) × sévérité. Chaque point
        est un case à investiguer. Approche Isolation Forest côté Streamlit
        (legacy) — le frontend Next.js v2 lit les findings agrégés et les
        affiche en scatter Recharts.
      </p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>📊 Dispersion exposition × sévérité</CardTitle>
        </CardHeader>
        <CardContent className="h-[500px]">
          {query.isLoading ? (
            <div className="text-sm text-[#5a6478]">Chargement…</div>
          ) : !scatterData.length ? (
            <div className="text-sm text-[#5a6478]">
              Aucun case avec exposition à afficher.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e1e5ee" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Exposition"
                  tick={{ fontSize: 10, fill: "#5a6478" }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k €`}
                  label={{
                    value: "Exposition (€)",
                    position: "insideBottom",
                    offset: -10,
                    fill: "#5a6478",
                    fontSize: 11,
                  }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Sévérité"
                  domain={[0, 5]}
                  ticks={[1, 2, 3, 4]}
                  tickFormatter={(v) =>
                    ({ 1: "Low", 2: "Medium", 3: "High", 4: "Critical" })[v as 1 | 2 | 3 | 4] ?? ""
                  }
                  tick={{ fontSize: 10, fill: "#5a6478" }}
                />
                <ZAxis dataKey="z" range={[60, 200]} />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const p = payload[0].payload;
                    return (
                      <div className="rounded-md border border-[#e1e5ee] bg-white p-2 text-xs shadow">
                        <div className="font-mono">{p.case_id?.slice(0, 16)}</div>
                        <div className="font-medium">{p.title}</div>
                        <div className="text-[#5a6478]">
                          Vendor : {p.vendor_id ?? "—"}
                        </div>
                        <div>Exposition : {formatEur(p.x)}</div>
                        <div>Sévérité : {p.severity}</div>
                      </div>
                    );
                  }}
                />
                {(["critical", "high", "medium", "low"] as const).map((sev) =>
                  grouped[sev]?.length ? (
                    <Scatter
                      key={sev}
                      name={sev}
                      data={grouped[sev]}
                      fill={SEVERITY_COLORS[sev]}
                    />
                  ) : null,
                )}
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            🚨 Outliers ({scatterData.length} cases avec exposition &gt; 0)
          </CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <CasesTable rows={query.data ?? []} />
        </div>
      </Card>
    </div>
  );
}

function CasesTable({ rows }: { rows: CaseOutV1[] }) {
  const top = rows
    .filter((c) => (c.exposure_eur ?? 0) > 0)
    .sort((a, b) => (b.exposure_eur ?? 0) - (a.exposure_eur ?? 0))
    .slice(0, 20);
  if (!top.length) {
    return <div className="p-4 text-sm text-[#5a6478]">Aucun outlier.</div>;
  }
  return (
    <table className="w-full text-sm">
      <thead className="bg-[#f4f6fa] text-[#5a6478]">
        <tr>
          <th className="px-3 py-2 text-left">Case ID</th>
          <th className="px-3 py-2 text-left">Vendor</th>
          <th className="px-3 py-2 text-left">Sévérité</th>
          <th className="px-3 py-2 text-right">Exposition</th>
        </tr>
      </thead>
      <tbody>
        {top.map((c) => (
          <tr key={c.case_id} className="border-t border-[#e1e5ee]">
            <td className="px-3 py-2 font-mono text-xs">
              {c.case_id.slice(0, 16)}
            </td>
            <td className="px-3 py-2">
              {c.vendor_id ? (
                <a
                  href={`/vendors/${encodeURIComponent(c.vendor_id)}`}
                  className="font-mono text-xs text-[#1f3a6e] hover:underline"
                >
                  {c.vendor_id}
                </a>
              ) : (
                <span className="text-xs text-[#9aa3b2]">—</span>
              )}
            </td>
            <td className="px-3 py-2">
              <SeverityBadge value={c.severity} />
            </td>
            <td className="px-3 py-2 text-right">{formatEur(c.exposure_eur)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
