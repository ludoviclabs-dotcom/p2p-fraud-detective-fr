"use client";

import type { SpotlightPreset } from "./p2p-demo-data";

export function P2PFocusSpotlight({ spotlight }: { spotlight?: SpotlightPreset }) {
  if (!spotlight) return null;

  return (
    <div
      className="p2p-demo-spotlight"
      aria-hidden
      style={{
        left: `${spotlight.x}%`,
        top: `${spotlight.y}%`,
        width: `${spotlight.width}%`,
        height: `${spotlight.height}%`,
      }}
    />
  );
}
