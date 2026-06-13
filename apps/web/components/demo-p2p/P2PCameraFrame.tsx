"use client";

import type { ReactNode } from "react";
import { CAMERA_PRESETS, type DemoCameraPreset, type P2PDemoScene } from "./p2p-demo-data";

export function P2PCameraFrame({
  preset,
  scene,
  children,
}: {
  preset: DemoCameraPreset;
  scene: P2PDemoScene;
  children: ReactNode;
}) {
  const camera = CAMERA_PRESETS[preset];

  return (
    <div className="p2p-demo-camera-viewport" data-scene={scene}>
      <div
        key={scene}
        className="p2p-demo-camera-frame"
        style={{
          transform: `translate3d(${camera.x}px, ${camera.y}px, 0) scale(${camera.scale})`,
        }}
      >
        {children}
      </div>
    </div>
  );
}
