"use client";

import type { RefObject } from "react";
import type { DemoAnchorId } from "./p2p-demo-data";
import { useAnchoredRect } from "./useAnchoredRect";

/** Marge (px) ajoutee autour de l'element encadre par le reticule. */
const PAD = 12;

/**
 * Reticule d'analyse forensic : encadre l'element reel de la scene (mesure via
 * `useAnchoredRect`) avec des coins animes, une ligne de scan et un ping de
 * verrouillage. Remplace l'ancien carre positionne en pourcentage qui se
 * decalait des que la camera pannait ou zoomait.
 */
export function P2PFocusSpotlight({
  anchor,
  stageRef,
  token,
}: {
  anchor?: DemoAnchorId;
  stageRef: RefObject<HTMLElement | null>;
  token: unknown;
}) {
  const rect = useAnchoredRect(stageRef, anchor, token);
  if (!anchor || !rect) return null;

  return (
    <div
      className="p2p-demo-reticle"
      aria-hidden
      style={{
        left: rect.left - PAD,
        top: rect.top - PAD,
        width: rect.width + PAD * 2,
        height: rect.height + PAD * 2,
      }}
    >
      <span className="p2p-demo-reticle-corner tl" />
      <span className="p2p-demo-reticle-corner tr" />
      <span className="p2p-demo-reticle-corner bl" />
      <span className="p2p-demo-reticle-corner br" />
      <span className="p2p-demo-reticle-scan" />
      <span className="p2p-demo-reticle-ping" />
    </div>
  );
}
