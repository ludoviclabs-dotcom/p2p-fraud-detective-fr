"use client";

import type { DemoContent } from "./p2p-demo-content";
import type { P2PCalloutId } from "./p2p-demo-data";

type CalloutPosition = {
  x: number;
  y: number;
  lineX: number;
  lineY: number;
  align?: "left" | "right";
};

const POSITIONS: Record<P2PCalloutId, CalloutPosition> = {
  "priority-score": { x: 72, y: 21, lineX: 62, lineY: 31, align: "right" },
  "global-search": { x: 10, y: 16, lineX: 28, lineY: 24 },
  "critical-kpi": { x: 42, y: 34, lineX: 48, lineY: 42 },
  "supplier-row": { x: 12, y: 56, lineX: 28, lineY: 64 },
  "data-lineage": { x: 63, y: 31, lineX: 55, lineY: 48, align: "right" },
  "case-score": { x: 66, y: 23, lineX: 53, lineY: 42, align: "right" },
  "iban-ring": { x: 8, y: 41, lineX: 24, lineY: 50 },
  "threshold-strip": { x: 58, y: 55, lineX: 53, lineY: 64, align: "right" },
  "rbe-mismatch": { x: 58, y: 28, lineX: 52, lineY: 38, align: "right" },
  "four-eyes": { x: 12, y: 64, lineX: 30, lineY: 70 },
  "evidence-seal": { x: 63, y: 70, lineX: 55, lineY: 70, align: "right" },
  "review-human": { x: 60, y: 42, lineX: 52, lineY: 50, align: "right" },
};

export function P2PCalloutLayer({
  ids,
  content,
}: {
  ids: P2PCalloutId[];
  content: DemoContent;
}) {
  if (!ids.length) return null;

  return (
    <div className="p2p-demo-callout-layer" aria-hidden>
      {ids.map((id, index) => {
        const copy = content.callouts[id];
        const position = POSITIONS[id];
        if (!copy || !position) return null;

        return (
          <div
            key={id}
            className={`p2p-demo-callout ${position.align === "right" ? "right" : ""}`}
            style={{
              left: `${position.x}%`,
              top: `${position.y}%`,
              animationDelay: `${index * 120}ms`,
            }}
          >
            <svg className="p2p-demo-callout-line" viewBox="0 0 120 64" focusable="false">
              <path
                d={
                  position.align === "right"
                    ? "M116 10 C80 10 66 38 8 56"
                    : "M4 10 C40 10 54 38 112 56"
                }
              />
            </svg>
            <div className="p2p-demo-callout-card">
              <div>{copy.title}</div>
              <p>{copy.body}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
