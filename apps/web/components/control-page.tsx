"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { listCases, type CaseOutV1 } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";

export type ControlPageConfig = {
  surtitle: string; // "Contrôles statistiques" | "Données" | ...
  title: string;
  kicker: string;
  description: string; // markdown-like (paragraphes)
  ruleIdMatchers: string[]; // ex. ["BENFORD", "F1D", "F2D"]
  titleMatchers?: string[]; // fallback : keywords dans c.title si rule_id manque
  regulations: { label: string; ref: string }[];
  sources?: { name: string; url: string; license: string }[];
};

export function ControlPage({ config }: { config: ControlPageConfig }) {
  const query = useQuery({
    queryKey: ["control-cases", config.title],
    queryFn: () => listCases({ limit: 1000 }),
  });

  const filteredCases = useMemo(() => {
    return (query.data ?? []).filter((c) =>
      caseMatchesRule(c, config.ruleIdMatchers, config.titleMatchers ?? []),
    );
  }, [query.data, config]);

  const stats = useMemo(() => {
    return {
      total: filteredCases.length,
      critical: filteredCases.filter((c) => c.severity === "critical").length,
      high: filteredCases.filter((c) => c.severity === "high").length,
      exposure: filteredCases.reduce((s, c) => s + (c.exposure_eur ?? 0), 0),
    };
  }, [filteredCases]);

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        {config.surtitle}
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        {config.title}
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">{config.kicker}</p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Description du contrôle</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-[#1a1f2c]">
            {config.description}
          </p>
          {config.regulations.length > 0 ? (
            <div className="mt-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-[#5a6478]">
                Références réglementaires
              </div>
              <ul className="mt-1 space-y-1 text-sm">
                {config.regulations.map((r) => (
                  <li key={r.ref}>
                    <span className="font-medium text-[#0f1b33]">{r.label}</span>
                    <span className="text-[#5a6478]"> · {r.ref}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <KpiBox label="Cas flagués" value={String(stats.total)} />
        <KpiBox
          label="CRITICAL"
          value={String(stats.critical)}
          color="#a23e48"
        />
        <KpiBox label="HIGH" value={String(stats.high)} color="#c97b1f" />
        <KpiBox label="Exposition" value={formatEur(stats.exposure)} />
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>🚨 Cases flagués par ce contrôle</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          {query.isLoading ? (
            <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
          ) : !filteredCases.length ? (
            <div className="p-4 text-sm text-[#5a6478]">
              Aucun case flagué par ce contrôle. Lancer le détecteur côté
              Streamlit (legacy) pour générer des findings.
            </div>
          ) : (
            <CasesTable rows={filteredCases} />
          )}
        </div>
      </Card>

      {config.sources?.length ? (
        <Card>
          <CardHeader>
            <CardTitle>📡 Sources de données</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#e1e5ee] text-left text-xs text-[#5a6478]">
                  <th className="py-2">Source</th>
                  <th className="py-2">URL</th>
                  <th className="py-2">Licence</th>
                </tr>
              </thead>
              <tbody>
                {config.sources.map((s) => (
                  <tr key={s.name} className="border-b border-[#e1e5ee]">
                    <td className="py-2 font-medium">{s.name}</td>
                    <td className="py-2 font-mono text-xs">{s.url}</td>
                    <td className="py-2 text-xs">{s.license}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function KpiBox({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <Card>
      <CardContent>
        <div className="text-xs uppercase tracking-wider text-[#5a6478]">
          {label}
        </div>
        <div
          className="mt-1 text-2xl font-semibold"
          style={{ color: color ?? "#0f1b33" }}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  );
}

function CasesTable({ rows }: { rows: CaseOutV1[] }) {
  const sorted = [...rows].sort(
    (a, b) => (b.exposure_eur ?? 0) - (a.exposure_eur ?? 0),
  );
  return (
    <table className="w-full text-sm">
      <thead className="bg-[#f4f6fa] text-[#5a6478]">
        <tr>
          <th className="px-3 py-2 text-left">Case ID</th>
          <th className="px-3 py-2 text-left">Titre</th>
          <th className="px-3 py-2 text-left">Vendor</th>
          <th className="px-3 py-2 text-left">Sévérité</th>
          <th className="px-3 py-2 text-right">Exposition</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((c) => (
          <tr key={c.case_id} className="border-t border-[#e1e5ee]">
            <td className="px-3 py-2 font-mono text-xs">
              {c.case_id.slice(0, 16)}
            </td>
            <td className="px-3 py-2">{c.title}</td>
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

function caseMatchesRule(
  c: CaseOutV1,
  ruleMatchers: string[],
  titleMatchers: string[],
): boolean {
  const title = (c.title || "").toLowerCase();
  return (
    ruleMatchers.some((m) => title.includes(m.toLowerCase())) ||
    titleMatchers.some((m) => title.includes(m.toLowerCase()))
  );
}
