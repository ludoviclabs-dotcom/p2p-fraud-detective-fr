"use client";

import type { DemoContent } from "./p2p-demo-content";

export function P2PDataLineageBeam({ content }: { content: DemoContent }) {
  return (
    <div className="p2p-demo-panel p2p-demo-lineage">
      <div className="p2p-demo-eyebrow">{content.dataLineage.title}</div>
      <p>{content.dataLineage.subtitle}</p>
      <div className="p2p-demo-lineage-chain" aria-label={content.labels.sources}>
        {content.dataLineage.sources.map((source, index) => (
          <div key={source} className="p2p-demo-lineage-step">
            <span className="p2p-demo-lineage-node" style={{ animationDelay: `${index * 130}ms` }} />
            <span>{source}</span>
            {index < content.dataLineage.sources.length - 1 ? (
              <span className="p2p-demo-lineage-beam" aria-hidden />
            ) : null}
          </div>
        ))}
      </div>
      <div className="p2p-demo-lineage-output">{content.dataLineage.output}</div>
    </div>
  );
}
