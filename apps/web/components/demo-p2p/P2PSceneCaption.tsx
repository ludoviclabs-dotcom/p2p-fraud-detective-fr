"use client";

import type { DemoContent } from "./p2p-demo-content";
import type { P2PDemoScene } from "./p2p-demo-data";

export function P2PSceneCaption({
  scene,
  content,
}: {
  scene: P2PDemoScene;
  content: DemoContent;
}) {
  const caption = content.sceneCaptions[scene];

  return (
    <div className="p2p-demo-scene-caption" key={scene}>
      <div className="p2p-demo-eyebrow">{caption.label}</div>
      <h2>{caption.title}</h2>
      <p>{caption.body}</p>
    </div>
  );
}
