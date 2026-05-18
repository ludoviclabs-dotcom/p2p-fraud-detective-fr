"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
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

type WaterfallRow = {
  rank: number;
  case_id: string;
  title: string;
  severity: string;
  value: number;
  cumul: number;
  start: number;
  invisible: number;
};

export default function ScorePage() {
  const [severity, setSeverity] = useState("");

  const query = useQuery({
    queryKey: ["score-cases", severity],
    queryFn: () =>
      listCases({
        severity: severity || undefined,
        limit: 30,
      }),
  });

  const sortedCases = useMemo(
    () =>
      (query.data ?? [])
        .filter((c) => (c.exposure_eur ?? 0) > 0)
        .sort((a, b) => (b.exposure_eur ?? 0) - (a.exposure_eur ?? 0))
        .slice(0, 15),
    [query.data],
  );

  const totalExposure = sortedCases.reduce(
    (s, c) => s + (c.exposure_eur ?? 0),
    0,
  );

  // Waterfall data : cumul progressif
  const waterfallData = useMemo(() => {
    return sortedCases.reduce<{ rows: WaterfallRow[]; cumul: number }>(
      (acc, c, i) => {
        const value = c.exposure_eur ?? 0;
        const start = acc.cumul;
        const cumul = start + value;
        return {
          rows: [
            ...acc.rows,
            {
              rank: i + 1,
              case_id: c.case_id.slice(0, 12),
              title: c.title,
              severity: c.severity,
              value,
              cumul,
              start,
              invisible: start, // bar invisible pour offset
            },
          ],
          cumul,
        };
      },
      { rows: [], cumul: 0 },
    ).rows;
  }, [sortedCases]);

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Détection ML
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Explorateur de score
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Waterfall des contributions à l'exposition cumulée. Top 15 cases triés
        par exposition financière.
      </p>

      <Card className="mb-4">
        <CardContent className="grid gap-3 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs text-[#5a6478]">Sévérité</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="h-10 w-full rounded-md border border-[#e1e5ee] bg-white px-3 text-sm"
            >
              <option value="">Toutes</option>
              <option value="critical">CRITICAL</option>
              <option value="high">HIGH</option>
              <option value="medium">MEDIUM</option>
              <option value="low">LOW</option>
            </select>
          </div>
          <div>
            <div className="text-xs text-[#5a6478]">Cases analysés</div>
            <div className="text-lg font-semibold text-[#0f1b33]">
              {sortedCases.length}
            </div>
          </div>
          <div>
            <div className="text-xs text-[#5a6478]">Exposition cumulée</div>
            <div className="text-lg font-semibold text-[#a23e48]">
              {formatEur(totalExposure)}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>
            💡 Waterfall — cumul progressif des expositions
          </CardTitle>
        </CardHeader>
        <CardContent className="h-96">
          {query.isLoading ? (
            <div className="text-sm text-[#5a6478]">Chargement…</div>
          ) : !sortedCases.length ? (
            <div className="text-sm text-[#5a6478]">
              Aucun case avec exposition à afficher. Lancez d'abord les
              détecteurs côté Streamlit (legacy).
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={waterfallData}
                stackOffset="sign"
                margin={{ top: 10, right: 20, bottom: 40, left: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e1e5ee" />
                <XAxis
                  dataKey="case_id"
                  tick={{ fontSize: 10, fill: "#5a6478" }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                  interval={0}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "#5a6478" }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k €`}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const p = payload[0].payload;
                    return (
                      <div className="rounded-md border border-[#e1e5ee] bg-white p-2 text-xs shadow">
                        <div className="font-mono text-[#5a6478]">
                          #{p.rank} · {p.case_id}
                        </div>
                        <div className="font-medium">{p.title}</div>
                        <div className="mt-1">
                          Contribution : {formatEur(p.value)}
                        </div>
                        <div>Cumul : {formatEur(p.cumul)}</div>
                      </div>
                    );
                  }}
                />
                {/* Spacer invisible pour offset (effet waterfall) */}
                <Bar dataKey="invisible" stackId="w" fill="transparent" />
                <Bar dataKey="value" stackId="w" radius={[2, 2, 0, 0]}>
                  {waterfallData.map((d, i) => (
                    <Cell
                      key={i}
                      fill={SEVERITY_COLORS[d.severity] ?? "#1f3a6e"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>📋 Détail des contributions</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <CasesTable rows={sortedCases} />
        </div>
      </Card>
    </div>
  );
}

function CasesTable({ rows }: { rows: CaseOutV1[] }) {
  if (!rows.length) return null;
  const rowsWithCumul = rows.reduce<
    { row: CaseOutV1; rank: number; cumul: number }[]
  >((acc, row, index) => {
    const previous = acc.at(-1)?.cumul ?? 0;
    return [
      ...acc,
      {
        row,
        rank: index + 1,
        cumul: previous + (row.exposure_eur ?? 0),
      },
    ];
  }, []);

  return (
    <table className="w-full text-sm">
      <thead className="bg-[#f4f6fa] text-[#5a6478]">
        <tr>
          <th className="px-3 py-2 text-left">#</th>
          <th className="px-3 py-2 text-left">Case ID</th>
          <th className="px-3 py-2 text-left">Titre</th>
          <th className="px-3 py-2 text-left">Sévérité</th>
          <th className="px-3 py-2 text-right">Contribution</th>
          <th className="px-3 py-2 text-right">Cumul</th>
        </tr>
      </thead>
      <tbody>
        {rowsWithCumul.map(({ row: c, rank, cumul }) => {
          return (
            <tr key={c.case_id} className="border-t border-[#e1e5ee]">
              <td className="px-3 py-2 font-mono text-xs">{rank}</td>
              <td className="px-3 py-2 font-mono text-xs">
                {c.case_id.slice(0, 16)}
              </td>
              <td className="px-3 py-2">{c.title}</td>
              <td className="px-3 py-2">
                <SeverityBadge value={c.severity} />
              </td>
              <td className="px-3 py-2 text-right font-mono">
                {formatEur(c.exposure_eur)}
              </td>
              <td className="px-3 py-2 text-right font-mono text-[#5a6478]">
                {formatEur(cumul)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
