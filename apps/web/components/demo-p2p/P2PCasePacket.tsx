"use client";

import { CheckCircle2, Download, FileCheck2, ShieldCheck } from "lucide-react";
import { DEMO_ALERTS, DEMO_EVIDENCE, DEMO_SUPPLIER } from "./p2p-demo-data";
import type { DemoContent } from "./p2p-demo-content";
import { formatEuro } from "@/lib/p2p-demo-format";

const FEATURE_ICONS = [FileCheck2, ShieldCheck, CheckCircle2, Download] as const;

export function P2PCasePacket({
  content,
  onExplore,
  onScenarios,
  onExport,
  onReplay,
}: {
  content: DemoContent;
  onExplore: () => void;
  onScenarios: () => void;
  onExport: () => void;
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
        <div className="p2p-demo-export-inline">
          <FileCheck2 size={18} aria-hidden />
          <span>{c.exportTitle}</span>
          <small>{c.exportMeta}</small>
        </div>
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
          <button type="button" className="p2p-demo-cta" onClick={onExport}>
            {content.controls.exportAnalysis}
          </button>
          <button type="button" className="p2p-demo-cta" onClick={onReplay}>
            {content.controls.replay}
          </button>
        </div>
        <p>{content.final.disclaimer}</p>
      </div>
      <div className="p2p-demo-case-side">
        <div className="p2p-demo-audit-stamp" aria-hidden>
          <strong>{c.sealPrimary}</strong>
          <span>{c.sealSecondary}</span>
        </div>
        <div className="p2p-demo-export-summary">
          <div className="p2p-demo-export-summary-head">
            <FileCheck2 size={24} aria-hidden />
            <div>
              <strong>{c.exportTitle}</strong>
              <span>{c.exportMeta}</span>
            </div>
          </div>
          <ul>
            {c.exportFeatures.map((feature, index) => {
              const Icon = FEATURE_ICONS[index % FEATURE_ICONS.length]!;
              return (
                <li key={feature}>
                  <Icon size={14} aria-hidden />
                  <span>{feature}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}
