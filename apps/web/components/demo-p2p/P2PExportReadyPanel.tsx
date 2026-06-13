"use client";

import { CheckCircle2, Download, FileCheck2, ShieldCheck } from "lucide-react";
import type { DemoContent } from "./p2p-demo-content";

const FEATURE_ICONS = [CheckCircle2, ShieldCheck, FileCheck2, Download] as const;

export function P2PExportReadyPanel({ content }: { content: DemoContent }) {
  const packet = content.casePacket;

  return (
    <div className="p2p-demo-export-ready p2p-demo-spring">
      <div className="p2p-demo-export-document" aria-hidden>
        <FileCheck2 size={44} strokeWidth={1.5} />
        <div>
          <span />
          <span />
          <span />
        </div>
        <strong>READY</strong>
      </div>
      <div className="p2p-demo-export-copy">
        <div className="p2p-demo-eyebrow">{packet.exportTitle}</div>
        <h2>{packet.exportSubtitle}</h2>
        <p>{packet.exportMeta}</p>
        <ul>
          {packet.exportFeatures.map((feature, index) => {
            const Icon = FEATURE_ICONS[index % FEATURE_ICONS.length]!;
            return (
              <li key={feature}>
                <Icon size={15} aria-hidden />
                <span>{feature}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
