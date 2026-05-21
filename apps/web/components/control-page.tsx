"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { listCases, type CaseOutV1 } from "@/lib/api-client";
import { formatEur } from "@/lib/utils";
import { ForensicPage } from "@/components/forensic-page";

export type ControlPageConfig = {
  surtitle: string;
  title: string;
  kicker: string;
  description: string;
  ruleIdMatchers: string[];
  titleMatchers?: string[];
  regulations: { label: string; ref: string }[];
  sources?: { name: string; url: string; license: string }[];
};

function sevClass(value: string): string {
  const n = value.toLowerCase();
  return n === "critical" || n === "high" || n === "medium" || n === "low" ? n : "";
}

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
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">{config.surtitle}</div>
          <h1 style={{ marginTop: 9 }}>{config.title}</h1>
          <p className="sub">{config.kicker}</p>
        </div>
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Description du contrôle</h2>
        </div>
        <div className="fx-panel-body">
          <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--fg-2)" }}>
            {config.description}
          </p>
          {config.regulations.length > 0 ? (
            <div style={{ marginTop: 16 }}>
              <div className="fx-eyebrow">Références réglementaires</div>
              <ul className="space-y-1" style={{ marginTop: 8, listStyle: "none", padding: 0 }}>
                {config.regulations.map((r) => (
                  <li key={r.ref} className="fx-mono" style={{ fontSize: 12 }}>
                    <span style={{ color: "var(--fg)" }}>{r.label}</span>
                    <span style={{ color: "var(--muted)" }}> · {r.ref}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-4" style={{ marginBottom: 16 }}>
        <KpiBox label="Cas flagués" value={String(stats.total)} tone="info" />
        <KpiBox label="Critical" value={String(stats.critical)} tone="risk" />
        <KpiBox label="High" value={String(stats.high)} tone="warn" />
        <KpiBox label="Exposition" value={formatEur(stats.exposure)} tone="ok" />
      </div>

      <div className="fx-panel" style={{ marginBottom: 16 }}>
        <div className="fx-panel-head">
          <h2>Cases flagués par ce contrôle</h2>
          <span className="glyph">▣</span>
        </div>
        {query.isLoading ? (
          <div className="fx-panel-body">
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
              Chargement…
            </span>
          </div>
        ) : !filteredCases.length ? (
          <div className="fx-panel-body">
            <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.6 }}>
              Aucun case flagué par ce contrôle. Lancer le détecteur côté Streamlit (legacy)
              pour générer des findings.
            </span>
          </div>
        ) : (
          <CasesTable rows={filteredCases} />
        )}
      </div>

      {config.sources?.length ? (
        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Sources de données</h2>
            <span className="glyph">✓</span>
          </div>
          <div className="fx-table-wrap">
            <table className="fx-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>URL</th>
                  <th>Licence</th>
                </tr>
              </thead>
              <tbody>
                {config.sources.map((s) => (
                  <tr key={s.name}>
                    <td className="key">{s.name}</td>
                    <td>{s.url}</td>
                    <td>{s.license}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </ForensicPage>
  );
}

function KpiBox({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className={`fx-stat ${tone}`}>
      <div className="lbl" style={{ marginTop: 0 }}>
        {label}
      </div>
      <div className="val">{value}</div>
    </div>
  );
}

function CasesTable({ rows }: { rows: CaseOutV1[] }) {
  const sorted = [...rows].sort(
    (a, b) => (b.exposure_eur ?? 0) - (a.exposure_eur ?? 0),
  );
  return (
    <div className="fx-table-wrap">
      <table className="fx-table">
        <thead>
          <tr>
            <th>Case ID</th>
            <th>Titre</th>
            <th>Vendor</th>
            <th>Sévérité</th>
            <th className="num">Exposition</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((c) => (
            <tr key={c.case_id}>
              <td className="key">{c.case_id.slice(0, 16)}</td>
              <td>{c.title}</td>
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
                <span className={`fx-tag ${sevClass(c.severity)}`}>
                  {c.severity.toUpperCase()}
                </span>
              </td>
              <td className="num">{formatEur(c.exposure_eur)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
