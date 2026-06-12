"use client";

import { DEMO_ALERTS, DEMO_EVIDENCE, DEMO_SUPPLIER } from "./p2p-demo-data";
import type { DemoContent } from "./p2p-demo-content";
import { formatEuro } from "@/lib/p2p-demo-format";

export function P2PCasePacket({
  content,
  onExplore,
  onScenarios,
  onReplay,
}: {
  content: DemoContent;
  onExplore: () => void;
  onScenarios: () => void;
  onReplay: () => void;
}) {
  const c = content.casePacket;

  const rows = [
    [c.idLabel, "CASE-P2P-V00474"],
    [c.supplierLabel, DEMO_SUPPLIER.name],
    [c.scoreLabel, `${DEMO_SUPPLIER.score}/100`],
    [c.exposureLabel, formatEuro(DEMO_SUPPLIER.exposure)],
    [c.signalsLabel, String(DEMO_ALERTS.length)],
    [c.evidenceLabel, String(DEMO_EVIDENCE.length)],
    [c.statusLabel, c.statusValue],
    [c.fingerprintLabel, "ed25519:7f3a...91c2"],
  ];

  return (
    <div className="p2p-demo-case-packet p2p-demo-spring">
      <div className="p2p-demo-case-packet-main">
        <div className="p2p-demo-eyebrow">{c.title}</div>
        <h2>{c.subtitle}</h2>
        <dl>
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <div className="p2p-demo-case-actions">
          <button type="button" className="p2p-demo-cta primary" onClick={onExplore}>
            {content.controls.exploreCockpit}
          </button>
          <button type="button" className="p2p-demo-cta" onClick={onScenarios}>
            {content.controls.viewScenarios}
          </button>
          <button type="button" className="p2p-demo-cta" onClick={onReplay}>
            {content.controls.replay}
          </button>
        </div>
        <p>{content.final.disclaimer}</p>
      </div>
      <div className="p2p-demo-audit-stamp" aria-hidden>
        <strong>{c.sealPrimary}</strong>
        <span>{c.sealSecondary}</span>
      </div>
    </div>
  );
}
