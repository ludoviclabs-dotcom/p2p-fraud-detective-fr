"use client";

import { useEffect, useRef, useState } from "react";

export interface P2PKpiCounterProps {
  label: string;
  target: number;
  format: (n: number) => string;
  glyph?: string;
  tone?: "neutral" | "risk" | "warn";
  duration?: number;
  /** Démarre le count-up quand passe à true. */
  active: boolean;
  /** Ancre DOM optionnelle ciblée par le réticule d'analyse. */
  anchorId?: string;
}

/**
 * Compteur KPI animé (count-up) — réutilise le pattern RAF + easing
 * `1-(1-k)^4` du hero (`components/home/hero.tsx`). Respecte
 * `prefers-reduced-motion` (affiche directement la valeur cible).
 */
export function P2PKpiCounter({
  label,
  target,
  format,
  glyph,
  tone = "neutral",
  duration = 1100,
  active,
  anchorId,
}: P2PKpiCounterProps) {
  const [n, setN] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setN(target);
      return;
    }
    const start = performance.now();
    const tick = (now: number) => {
      const k = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - k, 4);
      setN(Math.round(target * eased));
      if (k < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [active, target, duration]);

  const color =
    tone === "risk" ? "var(--risk)" : tone === "warn" ? "var(--warn)" : "var(--info)";

  return (
    <div className="p2p-demo-kpi" data-demo-anchor={anchorId}>
      <span className="glyph" aria-hidden style={{ fontFamily: "var(--font-mono)", color }}>
        {glyph}
      </span>
      <div className="p2p-demo-eyebrow" style={{ marginTop: 10 }}>
        {label}
      </div>
      <div className="val" aria-live="polite">
        {active ? format(n) : "—"}
      </div>
    </div>
  );
}
