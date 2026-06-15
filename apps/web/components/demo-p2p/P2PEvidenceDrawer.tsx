"use client";

import { DEMO_EVIDENCE } from "./p2p-demo-data";
import type { DemoContent } from "./p2p-demo-content";

/** Panneau latéral de preuves — pièces scellées, hash fictif `ed25519`. */
export function P2PEvidenceDrawer({ content }: { content: DemoContent }) {
  const e = content.evidence;
  return (
    <div className="p2p-demo-drawer" data-demo-anchor="evidence-drawer">
      <div className="p2p-demo-eyebrow">{e.drawerTitle}</div>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)", margin: "4px 0 12px" }}>
        {e.drawerSub}
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {DEMO_EVIDENCE.map((ev, i) => {
          const item = e.items[ev.id];
          if (!item) return null;
          return (
            <div
              key={ev.id}
              className="p2p-demo-evidence-item"
              style={{
                animationDelay: `${i * 120}ms`,
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                padding: "10px 12px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--fg)" }}>{item.title}</span>
                <span
                  className="p2p-demo-audit-seal"
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 9,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    color: "var(--verified)",
                    border: "1px solid var(--verified)",
                    padding: "1px 6px",
                    whiteSpace: "nowrap",
                  }}
                >
                  ✓ {e.sealed}
                </span>
              </div>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)", margin: "5px 0 6px", lineHeight: 1.5 }}>
                {item.detail}
              </p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--dim)" }}>
                <span>{e.typeLabel}: {item.type}</span>
                <span aria-hidden>·</span>
                <span>{e.statusLabel}: {item.status}</span>
                <span aria-hidden>·</span>
                <code style={{ color: "var(--info)" }}>{ev.hash}</code>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
