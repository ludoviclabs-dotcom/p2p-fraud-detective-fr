"use client";

import type { P2PSeverity } from "./p2p-demo-data";

export interface P2PRegulatoryAlertProps {
  title: string;
  text: string;
  observation?: string;
  why?: string;
  proof?: string;
  action?: string;
  labels?: {
    observation: string;
    why: string;
    proof: string;
    action: string;
  };
  badges: string[];
  cta: string;
  severity: P2PSeverity;
  delayMs?: number;
}

/**
 * Carte d'alerte réglementaire PRUDENTE. Le libellé suggère une revue /
 * qualification, jamais une infraction établie. `role="alert"` + `aria-live`.
 */
export function P2PRegulatoryAlert({
  title,
  text,
  observation,
  why,
  proof,
  action,
  labels,
  badges,
  cta,
  severity,
  delayMs,
}: P2PRegulatoryAlertProps) {
  const accent =
    severity === "critical"
      ? "var(--risk)"
      : severity === "high"
        ? "var(--warn)"
        : "var(--info)";

  return (
    <div
      role="alert"
      aria-live="polite"
      className="p2p-demo-evidence-item"
      style={{
        animationDelay: delayMs ? `${delayMs}ms` : undefined,
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderLeft: `3px solid ${accent}`,
        padding: "14px 16px",
      }}
    >
      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--fg)" }}>{title}</div>
      <p style={{ margin: "6px 0 10px", fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
        {text}
      </p>
      {labels && observation && why && proof && action ? (
        <dl className="p2p-demo-finding-grid">
          <div>
            <dt>{labels.observation}</dt>
            <dd>{observation}</dd>
          </div>
          <div>
            <dt>{labels.why}</dt>
            <dd>{why}</dd>
          </div>
          <div>
            <dt>{labels.proof}</dt>
            <dd>{proof}</dd>
          </div>
          <div>
            <dt>{labels.action}</dt>
            <dd>{action}</dd>
          </div>
        </dl>
      ) : null}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
        {badges.map((b) => (
          <span
            key={b}
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              padding: "2px 7px",
              border: "1px solid var(--border-strong)",
              color: "var(--muted)",
            }}
          >
            {b}
          </span>
        ))}
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: accent,
          }}
        >
          {cta} →
        </span>
      </div>
    </div>
  );
}
