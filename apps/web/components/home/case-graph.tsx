"use client";

import { useEffect, useState } from "react";
import type { ScenarioGraph } from "./data";

// Frame-tick hook driving the graph's subtle node wobble.
function useTick(fps = 30) {
  const [t, setT] = useState(0);
  useEffect(() => {
    let raf = 0;
    let last = performance.now();
    const step = (now: number) => {
      if (now - last >= 1000 / fps) {
        setT((x) => x + 1);
        last = now;
      }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [fps]);
  return t;
}

interface NodeProps {
  cx: number;
  cy: number;
  r: number;
  label: string;
  fill?: string;
  critical?: boolean;
  risk?: boolean;
  muted?: boolean;
}

function Node({ cx, cy, r, fill, label, critical, risk, muted }: NodeProps) {
  let fillColor = fill ?? "var(--panel-2)";
  let stroke = "var(--border-strong)";
  if (critical) {
    stroke = "var(--risk)";
    fillColor = "var(--risk)";
  } else if (risk) {
    stroke = "var(--risk)";
  } else if (muted) {
    stroke = "var(--dim)";
  }
  return (
    <g>
      {critical && (
        <circle cx={cx} cy={cy} r={r + 6} fill="none" stroke="var(--risk)" strokeOpacity="0.4">
          <animate
            attributeName="r"
            values={`${r + 6};${r + 14};${r + 6}`}
            dur="2s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="stroke-opacity"
            values="0.5;0;0.5"
            dur="2s"
            repeatCount="indefinite"
          />
        </circle>
      )}
      <circle cx={cx} cy={cy} r={r} fill={fillColor} stroke={stroke} strokeWidth="1.5" />
      <text x={cx} y={cy + r + 14} textAnchor="middle" className="node-label">
        {label}
      </text>
    </g>
  );
}

export function CaseGraph({ kind }: { kind: ScenarioGraph }) {
  const t = useTick(60);
  const wob = Math.sin(t / 22) * 1.2;

  if (kind === "central-iban") {
    return (
      <svg viewBox="0 0 480 220" className="case-graph">
        <line x1="60" y1="60" x2="240" y2="110" stroke="var(--border-strong)" strokeWidth="1" />
        <line x1="420" y1="60" x2="240" y2="110" stroke="var(--border-strong)" strokeWidth="1" />
        <line x1="100" y1="180" x2="240" y2="110" stroke="var(--risk)" strokeWidth="1.5" />
        <line x1="380" y1="180" x2="240" y2="110" stroke="var(--risk)" strokeWidth="1.5" />
        <line
          x1="240"
          y1="40"
          x2="240"
          y2="110"
          stroke="var(--border-strong)"
          strokeWidth="1"
          strokeDasharray="3 3"
        />
        <Node cx={240} cy={110} r={22} fill="var(--risk)" label="IBAN-X" critical />
        <Node cx={60} cy={60} r={14} label="VND-0188" />
        <Node cx={420} cy={60} r={14} label="VND-0421" />
        <Node cx={100} cy={180 + wob} r={14} label="VND-0330" risk />
        <Node cx={380} cy={180 - wob} r={14} label="VND-0507" risk />
        <Node cx={240} cy={40 + wob * 0.5} r={11} label="USER-LDU" muted />
      </svg>
    );
  }

  if (kind === "duplicate") {
    return (
      <svg viewBox="0 0 480 220" className="case-graph">
        <line
          x1="150"
          y1="110"
          x2="330"
          y2="110"
          stroke="var(--risk)"
          strokeWidth="2"
          strokeDasharray="4 4"
        />
        <text x="240" y="100" textAnchor="middle" className="node-label" fill="var(--risk)">
          Δ ± 0.01€ / 31h
        </text>
        <Node cx={150} cy={110} r={26} label="F-04419" />
        <Node cx={330} cy={110} r={26} label="F-04428" />
        <Node cx={150 - 60} cy={60 + wob} r={11} label="BL-22841" muted />
        <Node cx={330 + 60} cy={60 - wob} r={11} label="BL-22841" muted />
        <Node cx={240} cy={180} r={14} label="OMÉGA" risk />
        <line x1="240" y1="180" x2="150" y2="110" stroke="var(--border-strong)" strokeWidth="1" />
        <line x1="240" y1="180" x2="330" y2="110" stroke="var(--border-strong)" strokeWidth="1" />
      </svg>
    );
  }

  if (kind === "structuring") {
    return (
      <svg viewBox="0 0 480 220" className="case-graph">
        {Array.from({ length: 14 }).map((_, i) => {
          const x = 40 + i * 30;
          const h = 30 + (i % 4) * 6 + Math.sin((t + i * 10) / 14) * 4;
          return (
            <g key={i}>
              <rect
                x={x}
                y={140 - h}
                width={16}
                height={h}
                fill={i < 12 ? "var(--risk)" : "var(--warn)"}
                opacity="0.85"
              />
              <text x={x + 8} y={158} textAnchor="middle" className="node-label">
                {4800 + (i % 6) * 30}
              </text>
            </g>
          );
        })}
        <line x1="20" y1="60" x2="460" y2="60" stroke="var(--risk)" strokeDasharray="4 4" strokeWidth="1" />
        <text x="466" y="56" textAnchor="end" className="node-label" fill="var(--risk)">
          SEUIL 5 000 €
        </text>
        <text x="20" y="200" className="node-label">
          14 factures / 14 jours
        </text>
      </svg>
    );
  }

  // sanction
  return (
    <svg viewBox="0 0 480 220" className="case-graph">
      <line x1="120" y1="110" x2="240" y2="110" stroke="var(--border-strong)" strokeWidth="1" />
      <line x1="240" y1="110" x2="360" y2="60" stroke="var(--risk)" strokeWidth="2" />
      <line
        x1="240"
        y1="110"
        x2="360"
        y2="160"
        stroke="var(--risk)"
        strokeWidth="1.5"
        strokeDasharray="3 3"
      />
      <Node cx={120} cy={110} r={18} label="INTL TRADE" risk />
      <Node cx={240} cy={110} r={14} label="BÉNÉF. EFF." muted />
      <Node cx={360 + wob} cy={60} r={22} fill="var(--risk)" label="OFAC SDN" critical />
      <Node cx={360 - wob * 0.5} cy={160} r={14} label="PEP-2°" risk />
      <text x="300" y="40" textAnchor="middle" className="node-label" fill="var(--risk)">
        match 97%
      </text>
    </svg>
  );
}
