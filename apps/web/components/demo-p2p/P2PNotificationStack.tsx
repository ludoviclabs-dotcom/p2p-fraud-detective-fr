"use client";

import type { CSSProperties } from "react";
import type { DemoContent } from "./p2p-demo-content";
import {
  CALLOUT_SEVERITY,
  type P2PCalloutId,
  type P2PDemoScene,
  type P2PSeverity,
} from "./p2p-demo-data";

const SEVERITY_COLOR: Record<P2PSeverity, string> = {
  critical: "var(--risk)",
  high: "var(--warn)",
  medium: "var(--info)",
  low: "var(--verified)",
};

const SEVERITY_GLYPH: Record<P2PSeverity, string> = {
  critical: "●",
  high: "▲",
  medium: "◆",
  low: "✓",
};

/**
 * Flux de notifications « fraud-ops » : chaque signal de la scene (callout)
 * arrive en toast empile, glisse depuis la droite, code couleur par severite,
 * avec une barre de vie indexee sur la duree de la scene. Ancre dans un coin
 * du stage — donc jamais decale, contrairement aux anciennes cartes flottantes
 * qui tentaient de pointer un contenu transforme par la camera.
 */
export function P2PNotificationStack({
  scene,
  callouts,
  content,
  durationMs,
}: {
  scene: P2PDemoScene;
  callouts: P2PCalloutId[];
  content: DemoContent;
  durationMs: number;
}) {
  if (!callouts.length) return null;
  const n = content.notify;

  return (
    <div className="p2p-demo-notify" aria-hidden>
      {callouts.map((id, index) => {
        const copy = content.callouts[id];
        if (!copy) return null;
        const severity = CALLOUT_SEVERITY[id];
        const delay = index * 170;
        const style = {
          "--sev": SEVERITY_COLOR[severity],
          "--life": `${durationMs}ms`,
          animationDelay: `${delay}ms`,
        } as CSSProperties;

        return (
          <div key={`${scene}-${id}`} className="p2p-demo-toast" style={style}>
            <div className="p2p-demo-toast-head">
              <span className="p2p-demo-toast-dot" />
              <span>
                {n.label} · {n[severity]}
              </span>
              <span className="p2p-demo-toast-glyph" aria-hidden>
                {SEVERITY_GLYPH[severity]}
              </span>
            </div>
            <div className="p2p-demo-toast-title">{copy.title}</div>
            <div className="p2p-demo-toast-body">{copy.body}</div>
            <span
              className="p2p-demo-toast-bar"
              style={{ animationDelay: `${delay}ms` }}
            />
          </div>
        );
      })}
    </div>
  );
}
