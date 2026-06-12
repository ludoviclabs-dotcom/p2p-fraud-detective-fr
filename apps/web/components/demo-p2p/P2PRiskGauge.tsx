"use client";

import { useEffect, useRef, useState } from "react";

export interface P2PRiskGaugeProps {
  /** Cible 0..100. */
  target: number;
  label: string;
  size?: number;
  strokeWidth?: number;
  duration?: number;
  active: boolean;
}

/**
 * Jauge de risque SVG radiale. Arc + valeur pilotés ensemble par RAF
 * (stroke-dashoffset). `role="progressbar"` + `aria-valuenow` mis à jour.
 * Respecte `prefers-reduced-motion`.
 */
export function P2PRiskGauge({
  target,
  label,
  size = 168,
  strokeWidth = 12,
  duration = 1000,
  active,
}: P2PRiskGaugeProps) {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setValue(target);
      return;
    }
    const start = performance.now();
    const tick = (now: number) => {
      const k = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - k, 4);
      setValue(Math.round(target * eased));
      if (k < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [active, target, duration]);

  const r = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - value / 100);

  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value}
      aria-label={label}
      style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 8 }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
        <circle
          className="p2p-demo-gauge-track"
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          strokeWidth={strokeWidth}
        />
        <circle
          className="p2p-demo-gauge-fill"
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          strokeWidth={strokeWidth}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${cx} ${cy})`}
        />
        <text
          x={cx}
          y={cy}
          textAnchor="middle"
          dominantBaseline="central"
          style={{ fontFamily: "var(--font-display)", fontSize: size * 0.32, fill: "var(--fg)" }}
        >
          {value}
        </text>
      </svg>
      <div className="p2p-demo-eyebrow">{label}</div>
    </div>
  );
}
