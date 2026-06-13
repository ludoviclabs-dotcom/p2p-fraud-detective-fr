"use client";

import { Badge, SeverityBadge } from "@/components/ui/badge";
import { formatEuro, formatNumber } from "@/lib/p2p-demo-format";
import { DEMO_KPIS, DEMO_SUPPLIER, DEMO_VENDORS, type P2PCockpitMode } from "./p2p-demo-data";
import type { DemoContent } from "./p2p-demo-content";
import { P2PKpiCounter } from "./P2PKpiCounter";

/** Rendu simulé du cockpit `/dashboard` (recherche, KPI, table, priorité). */
export function P2PCommandCockpit({
  content,
  phase,
  typed,
}: {
  content: DemoContent;
  phase: P2PCockpitMode;
  typed: string;
}) {
  const c = content.cockpit;
  const isSearch = phase === "search";
  const isLoading = phase === "loading";
  const showResults = phase === "results";

  return (
    <div style={{ display: "grid", gap: 16 }}>
      {/* Header + recherche simulée */}
      <div className="p2p-demo-panel">
        <div className="p2p-demo-eyebrow">{c.eyebrow}</div>
        <h2
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(22px, 2.4vw, 32px)",
            color: "var(--fg)",
            margin: "8px 0 6px",
            fontWeight: 400,
          }}
        >
          {c.title}
        </h2>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted)", lineHeight: 1.6, maxWidth: 640 }}>
          {c.subtitle}
        </p>
        <div className={`p2p-demo-search ${isSearch ? "p2p-demo-input-pulse" : ""}`} style={{ marginTop: 14 }}>
          <span aria-hidden style={{ color: "var(--muted)" }}>⌕</span>
          <span>
            {typed || (!isSearch ? c.searchPlaceholder : "")}
            {isSearch ? <span className="p2p-demo-caret" /> : null}
          </span>
        </div>
        {isSearch ? (
          <div style={{ marginTop: 8 }}>
            <div className="p2p-demo-eyebrow">{c.searchHint}</div>
            <div className="p2p-demo-suggestions" aria-label={c.suggestionsTitle}>
              {c.suggestions.map((suggestion, index) => (
                <div
                  key={suggestion}
                  className={`p2p-demo-suggestion ${index === 0 ? "active" : ""}`}
                >
                  {suggestion}
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {isLoading ? (
          <div className="p2p-demo-eyebrow" style={{ marginTop: 8, color: "var(--warn)" }}>{c.loadingStatus}</div>
        ) : null}
      </div>

      {/* KPI */}
      <div className="p2p-demo-kpis">
        <P2PKpiCounter label={c.kpiTotal} target={DEMO_KPIS.totalExposure} format={formatEuro} glyph="Σ" tone="neutral" active={showResults} />
        <P2PKpiCounter label={c.kpiCritical} target={DEMO_KPIS.criticalExposure} format={formatEuro} glyph="▲" tone="risk" active={showResults} />
        <P2PKpiCounter label={c.kpiOpen} target={DEMO_KPIS.openCases} format={formatNumber} glyph="▣" tone="neutral" active={showResults} />
        <P2PKpiCounter label={c.kpiSla} target={DEMO_KPIS.lateSla} format={formatNumber} glyph="◷" tone="warn" active={showResults} />
      </div>

      {/* Table fournisseurs + priorité */}
      <div className="p2p-demo-cockpit-lower" style={{ display: "grid", gap: 16, gridTemplateColumns: "minmax(0, 1.6fr) minmax(0, 1fr)" }}>
        <div className="p2p-demo-panel">
          <div className="p2p-demo-eyebrow">{c.tableTitle}</div>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)", margin: "4px 0 12px" }}>{c.tableSub}</p>
          <div className="p2p-demo-vendors-wrap">
            <table className="p2p-demo-vendors">
              <thead>
                <tr>
                  <th>{c.colVendor}</th>
                  <th className="num">{c.colExposure}</th>
                  <th className="num">{c.colFindings}</th>
                  <th>{c.colSeverity}</th>
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 4 }).map((_, i) => (
                      <tr key={i}>
                        <td colSpan={4}>
                          <div className="p2p-demo-skeleton" style={{ height: 18 }} />
                        </td>
                      </tr>
                    ))
                  : showResults
                    ? DEMO_VENDORS.map((v, i) => {
                        const heat = v.id === DEMO_SUPPLIER.id;
                        return (
                          <tr
                            key={v.id}
                            className={`p2p-demo-row ${heat ? "p2p-demo-risk-heat" : ""}`}
                            style={{ animationDelay: `${i * 90}ms` }}
                          >
                            <td style={{ fontFamily: "var(--font-mono)", color: heat ? "var(--risk)" : "var(--fg)", fontWeight: heat ? 700 : 400 }}>
                              {v.id}
                            </td>
                            <td className="num">{formatEuro(v.exposure)}</td>
                            <td className="num">{v.findings}</td>
                            <td>
                              <SeverityBadge value={v.severity} />
                            </td>
                          </tr>
                        );
                      })
                    : null}
              </tbody>
            </table>
          </div>
        </div>

        <div
          className={`p2p-demo-panel ${phase === "cockpit" ? "p2p-demo-critical-pulse" : ""}`}
          style={{ borderLeft: "3px solid var(--risk)" }}
        >
          <div className="p2p-demo-eyebrow">{c.priorityEyebrow}</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 8 }}>
            <span style={{ fontFamily: "var(--font-display)", fontSize: 40, color: "var(--risk)" }}>{DEMO_SUPPLIER.score}</span>
            <Badge severity="critical">CRIT</Badge>
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--fg)", marginTop: 4 }}>{DEMO_SUPPLIER.name}</div>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 18, color: "var(--fg)", margin: "12px 0 6px", fontWeight: 400 }}>{c.priorityTitle}</h3>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.6, color: "var(--muted)" }}>{c.priorityBody}</p>
        </div>
      </div>
    </div>
  );
}
