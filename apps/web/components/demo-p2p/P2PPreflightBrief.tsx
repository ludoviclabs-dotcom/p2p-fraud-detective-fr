"use client";

import type { DemoContent } from "./p2p-demo-content";

/** Carte de mission affichée avant l'entrée dans le cockpit. */
export function P2PPreflightBrief({ content }: { content: DemoContent }) {
  const b = content.brief;
  return (
    <div
      className="p2p-demo-panel p2p-demo-spring"
      style={{ maxWidth: 560, margin: "auto", borderTop: "3px solid var(--risk)" }}
    >
      <div className="p2p-demo-eyebrow" style={{ color: "var(--risk)" }}>
        {b.kicker}
      </div>
      <BriefRow label={b.objectiveLabel} value={b.objective} />
      <BriefRow label={b.signalsLabel} value={b.signals} />
      <BriefRow label={b.outputLabel} value={b.output} />
    </div>
  );
}

function BriefRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ marginTop: 14 }}>
      <div className="p2p-demo-eyebrow">{label}</div>
      <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--fg)", margin: "5px 0 0" }}>{value}</p>
    </div>
  );
}
