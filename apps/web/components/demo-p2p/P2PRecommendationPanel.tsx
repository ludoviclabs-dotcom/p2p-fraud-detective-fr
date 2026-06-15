"use client";

import type { DemoContent } from "./p2p-demo-content";

/** Synthèse finale : parcours recommandé + actions (escalade conformité). */
export function P2PRecommendationPanel({ content }: { content: DemoContent }) {
  const r = content.recommendations;
  return (
    <div className="p2p-demo-panel p2p-demo-spring" data-demo-anchor="review-panel">
      <div className="p2p-demo-eyebrow">{r.eyebrow}</div>
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: 22, color: "var(--fg)", margin: "6px 0 4px", fontWeight: 400 }}>
        {r.title}
      </h2>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted)" }}>{r.sub}</p>
      <ol style={{ listStyle: "none", margin: "16px 0 0", padding: 0, display: "flex", flexDirection: "column", gap: 8 }}>
        {r.actions.map((a, i) => (
          <li
            key={a}
            className="p2p-demo-evidence-item"
            style={{
              animationDelay: `${i * 140}ms`,
              display: "flex",
              alignItems: "center",
              gap: 10,
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              padding: "11px 13px",
            }}
          >
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--risk)" }}>
              {String(i + 1).padStart(2, "0")}
            </span>
            <span style={{ fontSize: 13, color: "var(--fg)" }}>{a}</span>
          </li>
        ))}
      </ol>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--dim)", marginTop: 14, lineHeight: 1.6 }}>
        {r.note}
      </p>
    </div>
  );
}
