"use client";

import { DEMO_REASON_CODES, DEMO_SUPPLIER } from "./p2p-demo-data";
import type { DemoContent } from "./p2p-demo-content";
import { P2PRiskGauge } from "./P2PRiskGauge";
import { P2PSignalList } from "./P2PSignalList";

/** Dossier fournisseur 360 : jauge animée + reason codes sourcés. */
export function P2PCaseFile360({
  content,
  gaugeActive,
}: {
  content: DemoContent;
  gaugeActive: boolean;
}) {
  const c = content.case360;
  const signals = DEMO_REASON_CODES.map((rc) => ({
    code: rc.code,
    severity: rc.severity,
    label: content.reasonCodes[rc.code]?.label ?? rc.code,
    description: content.reasonCodes[rc.code]?.description,
  }));

  return (
    <div className="p2p-demo-panel p2p-demo-spring" style={{ borderLeft: "3px solid var(--risk)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div className="p2p-demo-eyebrow">{c.eyebrow}</div>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 24, color: "var(--fg)", margin: "6px 0 4px", fontWeight: 400 }}>
            {c.header}
          </h2>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted)" }}>{c.subheader}</p>
        </div>
        <span className="p2p-demo-notice">⚠ {content.demoNotice}</span>
      </div>

      <div
        style={{
          display: "grid",
          gap: 18,
          gridTemplateColumns: "auto minmax(0, 1fr)",
          alignItems: "center",
          marginTop: 16,
        }}
      >
        <P2PRiskGauge target={DEMO_SUPPLIER.score} label={c.gaugeLabel} active={gaugeActive} />
        <div>
          <div className="p2p-demo-eyebrow" style={{ marginBottom: 8 }}>{c.reasonCodesTitle}</div>
          <P2PSignalList items={signals} revealed={signals.length} />
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <button type="button" className="p2p-demo-cta" disabled style={{ opacity: 0.65, cursor: "default" }}>
          {c.prepareReview}
        </button>
      </div>
    </div>
  );
}
