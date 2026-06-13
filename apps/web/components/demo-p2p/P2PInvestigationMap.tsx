"use client";

import type { DemoContent } from "./p2p-demo-content";

export function P2PInvestigationMap({
  content,
  activeIndex,
}: {
  content: DemoContent;
  activeIndex: number;
}) {
  return (
    <div className="p2p-demo-panel p2p-demo-investigation-map">
      <div className="p2p-demo-eyebrow">{content.investigationMap.title}</div>
      <ol>
        {content.investigationMap.steps.map((step, index) => (
          <li
            key={step}
            className={index < activeIndex ? "done" : index === activeIndex ? "active" : ""}
          >
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{step}</strong>
          </li>
        ))}
      </ol>
    </div>
  );
}
