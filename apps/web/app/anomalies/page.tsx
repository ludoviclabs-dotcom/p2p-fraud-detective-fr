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
import Link from "next/link";
import { listCases, type CaseOutV1 } from "@/lib/api-client";
import { SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#c8392c",
  high: "#c89b2c",
  medium: "#e5a93a",
  low: "#7fa37f",
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
        fill: SEVERITY_COLORS[c.severity] ?? "var(--info)",
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
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Détection ML</div>
          <h1 style={{ marginTop: 9 }}>
            Anomalies <span className="italic">ML</span>
          </h1>
          <p className="sub">
            Dispersion des cases sur l&apos;axe exposition (€) × sévérité. Chaque point est un
            case à investiguer. Approche Isolation Forest côté Streamlit (legacy) — le frontend
            Next.js v2 lit les findings agrégés et les affiche en scatter Recharts.
          </p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Dispersion exposition × sévérité</h2>
          <span className="glyph">∿</span>
        </div>
        <div className="fx-panel-body" style={{ height: 520 }}>
          {query.isLoading ? (
            <div className="fx-skel" style={{ height: 460 }} />
          ) : !scatterData.length ? (
            <div className="fx-notice">
              <span className="glyph">⚠</span>
              <div>
                <div className="nt">Aucun case avec exposition</div>
                <p className="nb">Aucun case avec exposition à afficher.</p>
              </div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Exposition"
                  tick={{ fontSize: 10, fill: "var(--muted)", fontFamily: "var(--font-mono)" }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k €`}
                  label={{
                    value: "Exposition (€)",
                    position: "insideBottom",
                    offset: -10,
                    fill: "var(--muted)",
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
                    ({ 1: "Low", 2: "Medium", 3: "High", 4: "Critical" })[
                      v as 1 | 2 | 3 | 4
                    ] ?? ""
                  }
                  tick={{ fontSize: 10, fill: "var(--muted)", fontFamily: "var(--font-mono)" }}
                />
                <ZAxis dataKey="z" range={[60, 200]} />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const p = payload[0].payload;
                    return (
                      <div
                        style={{
                          background: "var(--panel)",
                          border: "1px solid var(--border-strong)",
                          padding: "10px 14px",
                          fontFamily: "var(--font-mono)",
                          fontSize: 11,
                          color: "var(--fg-2)",
                        }}
                      >
                        <div style={{ color: "var(--fg)", marginBottom: 4 }}>
                          {p.case_id?.slice(0, 16)}
                        </div>
                        <div style={{ color: "var(--fg)", marginBottom: 4 }}>{p.title}</div>
                        <div>Vendor : {p.vendor_id ?? "—"}</div>
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
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">
          <div>
            <h2>Outliers</h2>
            <div className="sub">{scatterData.length} cases avec exposition &gt; 0</div>
          </div>
          <span className="glyph">▲</span>
        </div>
        <div className="fx-table-wrap">
          <CasesTable rows={query.data ?? []} />
        </div>
      </div>
    </ForensicPage>
  );
}

function CasesTable({ rows }: { rows: CaseOutV1[] }) {
  const top = rows
    .filter((c) => (c.exposure_eur ?? 0) > 0)
    .sort((a, b) => (b.exposure_eur ?? 0) - (a.exposure_eur ?? 0))
    .slice(0, 20);
  if (!top.length) {
    return (
      <div className="fx-panel-body">
        <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
          Aucun outlier.
        </span>
      </div>
    );
  }
  return (
    <table className="fx-table">
      <thead>
        <tr>
          <th>Case ID</th>
          <th>Vendor</th>
          <th>Sévérité</th>
          <th className="num">Exposition</th>
        </tr>
      </thead>
      <tbody>
        {top.map((c) => (
          <tr key={c.case_id}>
            <td className="key">{c.case_id.slice(0, 16)}</td>
            <td>
              {c.vendor_id ? (
                <Link
                  href={`/vendors/${encodeURIComponent(c.vendor_id)}`}
                  className="fx-link"
                >
                  {c.vendor_id}
                </Link>
              ) : (
                <span style={{ color: "var(--dim)" }}>—</span>
              )}
            </td>
            <td>
              <SeverityBadge value={c.severity} />
            </td>
            <td className="num">{formatEur(c.exposure_eur)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
