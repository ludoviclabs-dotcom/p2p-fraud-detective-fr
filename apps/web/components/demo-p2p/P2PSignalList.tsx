"use client";

import { Badge } from "@/components/ui/badge";
import type { P2PSeverity } from "./p2p-demo-data";

export interface P2PSignalItem {
  code: string;
  label: string;
  description?: string;
  severity: P2PSeverity;
}

/** Liste de signaux / reason codes, révélés un par un (`revealed`). */
export function P2PSignalList({
  items,
  revealed,
}: {
  items: P2PSignalItem[];
  revealed: number;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {items.slice(0, revealed).map((s, i) => (
        <div
          key={s.code}
          className="p2p-demo-reason-code"
          style={{
            animationDelay: `${i * 80}ms`,
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            padding: "10px 12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
            <code style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--info)" }}>
              {s.code}
            </code>
            <Badge severity={s.severity}>{s.severity.toUpperCase()}</Badge>
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--fg)", marginTop: 4 }}>
            {s.label}
          </div>
          {s.description ? (
            <p
              style={{
                margin: "4px 0 0",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                lineHeight: 1.55,
                color: "var(--muted)",
              }}
            >
              {s.description}
            </p>
          ) : null}
        </div>
      ))}
    </div>
  );
}
