"use client";

import { DEMO_RAIL_STEPS, PHASE_TO_RAIL, type P2PDemoPhase } from "./p2p-demo-data";

/** Rail de progression : reflète l'étape active selon la phase courante. */
export function P2PTimelineRail({
  phase,
  labels,
}: {
  phase: P2PDemoPhase;
  labels: Record<string, string>;
}) {
  const activeStep = PHASE_TO_RAIL[phase];
  const activeIndex = DEMO_RAIL_STEPS.indexOf(activeStep);

  return (
    <div className="p2p-demo-rail" aria-hidden>
      {DEMO_RAIL_STEPS.map((step, i) => {
        const state = i < activeIndex ? "done" : i === activeIndex ? "active" : "";
        return (
          <span key={step} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            {i > 0 ? <span className="p2p-demo-rail-sep">→</span> : null}
            <span className={`p2p-demo-rail-step ${state}`}>{labels[step] ?? step}</span>
          </span>
        );
      })}
    </div>
  );
}
