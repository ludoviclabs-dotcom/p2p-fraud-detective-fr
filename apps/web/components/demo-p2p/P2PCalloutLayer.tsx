"use client";

import type { DemoContent } from "./p2p-demo-content";
import type { P2PCalloutId, P2PDemoScene } from "./p2p-demo-data";

type CalloutSlot =
  | "top-left"
  | "top-right"
  | "mid-left"
  | "mid-right"
  | "bottom-left"
  | "bottom-right";

const DEFAULT_SLOTS: Record<P2PCalloutId, CalloutSlot> = {
  "priority-score": "top-right",
  "global-search": "top-left",
  "critical-kpi": "mid-left",
  "supplier-row": "bottom-left",
  "data-lineage": "mid-right",
  "case-score": "top-right",
  "iban-ring": "mid-left",
  "threshold-strip": "bottom-right",
  "rbe-mismatch": "top-right",
  "four-eyes": "bottom-left",
  "evidence-seal": "bottom-right",
  "review-human": "mid-right",
  "export-ready": "top-right",
};

const SCENE_SLOTS: Partial<Record<P2PDemoScene, Partial<Record<P2PCalloutId, CalloutSlot>>>> = {
  "cold-open": { "priority-score": "top-right" },
  "cockpit-wide": { "global-search": "top-left", "critical-kpi": "mid-right" },
  "data-cascade": { "data-lineage": "top-right", "critical-kpi": "bottom-left" },
  "score-breakdown": {
    "case-score": "top-left",
    "iban-ring": "mid-right",
    "threshold-strip": "bottom-right",
  },
  "evidence-build": {
    "rbe-mismatch": "top-right",
    "four-eyes": "bottom-left",
    "evidence-seal": "bottom-right",
  },
  "alert-sequence": {
    "iban-ring": "top-left",
    "threshold-strip": "mid-right",
    "evidence-seal": "bottom-right",
  },
  "export-ready": { "export-ready": "top-left", "evidence-seal": "bottom-right" },
};

export function P2PCalloutLayer({
  scene,
  ids,
  content,
}: {
  scene: P2PDemoScene;
  ids: P2PCalloutId[];
  content: DemoContent;
}) {
  if (!ids.length) return null;

  return (
    <div className="p2p-demo-callout-layer" aria-hidden>
      {ids.map((id, index) => {
        const copy = content.callouts[id];
        const slot = SCENE_SLOTS[scene]?.[id] ?? DEFAULT_SLOTS[id];
        if (!copy || !slot) return null;

        return (
          <div
            key={id}
            className={`p2p-demo-callout slot-${slot}`}
            style={{ animationDelay: `${index * 120}ms` }}
          >
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
