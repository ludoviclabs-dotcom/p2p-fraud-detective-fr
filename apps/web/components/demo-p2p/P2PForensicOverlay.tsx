"use client";

import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { useTheme } from "next-themes";
import type { P2PDemoScene } from "./p2p-demo-data";
import type { DemoContent } from "./p2p-demo-content";
import { P2PTimelineRail } from "./P2PTimelineRail";
import "./p2p-demo-motion.css";

/**
 * Overlay plein écran de la démo (portal vers `document.body`).
 *
 * Le conteneur racine porte `className="forensic"` + `data-theme` synchronisé
 * (next-themes) pour que les variables CSS et le thème se résolvent hors de
 * l'AppShell. z-index 70 (au-dessus de tout le chrome existant). Le scrim fixe
 * capture les clics et bloque la page sous-jacente ; seuls les boutons restent
 * interactifs.
 */
export function P2PForensicOverlay({
  scene,
  sceneIndex,
  sceneCount,
  content,
  onSkip,
  isFinal,
  children,
}: {
  scene: P2PDemoScene;
  sceneIndex: number;
  sceneCount: number;
  content: DemoContent;
  onSkip: () => void;
  isFinal: boolean;
  children: ReactNode;
}) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Verrouille le scroll de la page sous l'overlay.
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  if (!mounted) return null;
  const theme = resolvedTheme === "light" ? "light" : "dark";

  return createPortal(
    <div
      className="p2p-demo-root forensic"
      data-theme={theme}
      data-grain="off"
      role="dialog"
      aria-modal="true"
      aria-label={content.brief.kicker}
    >
      <div className="p2p-demo-scrim">
        <div className="p2p-demo-top">
          <P2PTimelineRail
            scene={scene}
            sceneIndex={sceneIndex}
            sceneCount={sceneCount}
            content={content}
          />
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
            <span className="p2p-demo-notice">{content.controls.demoBadge}</span>
            <button
              type="button"
              className="p2p-demo-skip"
              onClick={onSkip}
              aria-label={isFinal ? content.controls.skip : content.controls.skipAria}
            >
              {isFinal ? "✕" : content.controls.skip}
            </button>
          </div>
        </div>
        <div className="p2p-demo-stage">
          <div className="p2p-demo-stage-inner">{children}</div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
