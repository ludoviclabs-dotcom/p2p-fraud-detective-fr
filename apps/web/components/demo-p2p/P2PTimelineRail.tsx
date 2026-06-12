"use client";

import type { DemoContent } from "./p2p-demo-content";
import { DEMO_RAIL_STEPS, SCENE_TO_RAIL, type P2PDemoScene } from "./p2p-demo-data";

export function P2PTimelineRail({
  scene,
  sceneIndex,
  sceneCount,
  content,
}: {
  scene: P2PDemoScene;
  sceneIndex: number;
  sceneCount: number;
  content: DemoContent;
}) {
  const activeStep = SCENE_TO_RAIL[scene];
  const activeIndex = DEMO_RAIL_STEPS.indexOf(activeStep);
  const percent = ((sceneIndex + 1) / sceneCount) * 100;

  return (
    <div className="p2p-demo-rail-wrap" aria-hidden>
      <div className="p2p-demo-rail">
        {DEMO_RAIL_STEPS.map((step, index) => {
          const state = index < activeIndex ? "done" : index === activeIndex ? "active" : "";
          return (
            <span key={step} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              {index > 0 ? <span className="p2p-demo-rail-sep">-</span> : null}
              <span className={`p2p-demo-rail-step ${state}`}>{content.rail[step] ?? step}</span>
            </span>
          );
        })}
      </div>
      <div className="p2p-demo-rail-meta">
        <span>
          {content.labels.scene} {String(sceneIndex + 1).padStart(2, "0")} /{" "}
          {String(sceneCount).padStart(2, "0")}
        </span>
        <strong>{content.sceneLabels[scene]}</strong>
      </div>
      <div className="p2p-demo-rail-progress">
        <span style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
