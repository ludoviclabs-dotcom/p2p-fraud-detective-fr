"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { generateReplay } from "@/lib/api-client";
import type { ReplayResult } from "@/lib/api-client";
import { ClaimList } from "@/components/grounded-claims";
import { SeverityBadge } from "@/components/ui/badge";

/**
 * Risk Replay (Phase 6, ADR-0007) — rejoue un cas en séquence d'enquête.
 *
 * Navigation pas-à-pas sur les étapes générées (chaque étape est sourcée
 * sur la timeline réelle du cas — aucune conclusion nouvelle).
 */
export function RiskReplayPanel({ caseId }: { caseId: string | null }) {
  const [stepIndex, setStepIndex] = useState(0);

  const mutation = useMutation({
    mutationFn: (id: string) => generateReplay(id),
    onSuccess: () => setStepIndex(0),
  });

  const replay = mutation.data?.replay ?? null;

  return (
    <div className="fx-panel" style={{ marginTop: 16 }} data-testid="risk-replay-panel">
      <div className="fx-panel-head">
        <div>
          <h2>Risk Replay</h2>
          <div className="sub">
            La fraude rejouée comme une séquence d&apos;enquête — étapes
            sourcées sur la timeline du cas
          </div>
        </div>
        <span className="glyph">▸</span>
      </div>
      <div className="fx-panel-body space-y-4">
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <button
            className="fx-btn"
            data-testid="replay-generate-button"
            type="button"
            disabled={!caseId || mutation.isPending}
            onClick={() => caseId && mutation.mutate(caseId)}
          >
            {mutation.isPending ? "◷ Génération…" : "▸ Rejouer le cas"}
          </button>
          <span className="fx-mono" style={{ fontSize: 11, color: "var(--muted)" }}>
            {caseId ? `Cas : ${caseId}` : "Sélectionnez exactement un cas."}
          </span>
        </div>

        {mutation.error ? (
          <div className="fx-notice">
            <span className="glyph">⚠</span>
            <div>
              <div className="nt">Replay indisponible</div>
              <p className="nb">
                Le backend FastAPI (et sa clé ANTHROPIC_API_KEY) doit être
                configuré pour générer la séquence.
              </p>
            </div>
          </div>
        ) : null}

        {replay && mutation.data ? (
          <ReplayView
            result={mutation.data}
            stepIndex={Math.min(stepIndex, replay.steps.length - 1)}
            setStepIndex={setStepIndex}
          />
        ) : null}
      </div>
    </div>
  );
}

function ReplayView({
  result,
  stepIndex,
  setStepIndex,
}: {
  result: ReplayResult;
  stepIndex: number;
  setStepIndex: (i: number) => void;
}) {
  const replay = result.replay;
  const step = replay.steps[stepIndex];
  if (!step) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <p className="fx-mono" style={{ margin: 0, fontSize: 12, color: "var(--muted)" }}>
        {replay.case_summary}
      </p>

      {/* Frise des étapes */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {replay.steps.map((s, i) => (
          <button
            key={s.title}
            type="button"
            onClick={() => setStepIndex(i)}
            className="fx-mono"
            style={{
              height: 28,
              padding: "0 10px",
              fontSize: 11,
              cursor: "pointer",
              background: i === stepIndex ? "var(--panel-2)" : "var(--bg)",
              border: `1px solid ${i === stepIndex ? "var(--border-strong)" : "var(--border)"}`,
              borderBottom:
                i === stepIndex ? "2px solid var(--risk)" : "1px solid var(--border)",
              color: i <= stepIndex ? "var(--fg)" : "var(--muted)",
            }}
          >
            {i + 1}
          </button>
        ))}
      </div>

      <div
        style={{
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderLeft: `3px solid ${step.risk_level === "critical" || step.risk_level === "high" ? "var(--risk)" : step.risk_level === "info" ? "var(--info)" : "var(--warn)"}`,
          padding: "14px 16px",
        }}
      >
        <div className="flex items-center justify-between gap-3" style={{ flexWrap: "wrap" }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: "var(--fg)" }}>
            Étape {stepIndex + 1}/{replay.steps.length} — {step.title}
          </div>
          {step.risk_level !== "info" ? <SeverityBadge value={step.risk_level} /> : null}
        </div>
        <p style={{ margin: "8px 0 0", fontSize: 13, lineHeight: 1.65, color: "var(--fg-2)" }}>
          {step.business_explanation}
        </p>
        <div style={{ marginTop: 12 }}>
          <div className="fx-eyebrow" style={{ marginBottom: 6 }}>Preuves</div>
          <ClaimList claims={step.evidence} />
        </div>
        <div
          className="fx-mono"
          style={{
            marginTop: 12,
            background: "var(--bg)",
            border: "1px solid var(--border-strong)",
            padding: "10px 12px",
            fontSize: 12,
            lineHeight: 1.6,
            color: "var(--fg)",
          }}
        >
          ¿ Question au reviewer : {step.reviewer_question}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button
          className="fx-btn-ghost sm"
          type="button"
          disabled={stepIndex === 0}
          onClick={() => setStepIndex(stepIndex - 1)}
        >
          ← Précédente
        </button>
        <button
          className="fx-btn-ghost sm"
          type="button"
          disabled={stepIndex >= replay.steps.length - 1}
          onClick={() => setStepIndex(stepIndex + 1)}
        >
          Suivante →
        </button>
        <span className="fx-mono" style={{ marginLeft: "auto", fontSize: 10, color: "var(--dim)" }}>
          Généré par {result.model} · prompt {result.prompt_version}
        </span>
      </div>
    </div>
  );
}
