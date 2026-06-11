"use client";

import { useMutation } from "@tanstack/react-query";
import { generateScenarioNarrative } from "@/lib/api-client";
import type { ScenarioNarrativeResult } from "@/lib/api-client";
import { ClaimList } from "@/components/grounded-claims";
import { useLocale } from "@/components/locale-provider";

/**
 * Narratif IA d'un scénario synthétique (Phase 6, ADR-0007).
 *
 * Le générateur déterministe reste seul responsable des données et labels —
 * le LLM ne produit que l'habillage pédagogique, sourcé sur les métadonnées.
 */
export function ScenarioNarrativePanel({ scenarioId }: { scenarioId: string }) {
  const { t } = useLocale();
  const mutation = useMutation({
    mutationFn: () => generateScenarioNarrative(scenarioId),
  });

  return (
    <div data-testid="scenario-narrative-panel">
      <button
        className="fx-btn-ghost sm"
        data-testid="scenario-narrative-button"
        type="button"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? t("ai.generating") : t("scenario_ai.generate")}
      </button>

      {mutation.error ? (
        <p className="fx-mono" style={{ marginTop: 8, fontSize: 11, color: "var(--muted)" }}>
          {t("scenario_ai.unavailable")}
        </p>
      ) : null}

      {mutation.data ? <NarrativeView result={mutation.data} /> : null}
    </div>
  );
}

function NarrativeView({ result }: { result: ScenarioNarrativeResult }) {
  const { t } = useLocale();
  const narrative = result.narrative;
  return (
    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 12 }}>
      <div
        style={{
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderLeft: "3px solid var(--warn)",
          padding: "12px 14px",
        }}
      >
        <p style={{ margin: 0, fontSize: 13, lineHeight: 1.65, color: "var(--fg)" }}>
          {narrative.pitch}
        </p>
      </div>

      <div>
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>{t("scenario_ai.modus")}</div>
        <ClaimList claims={narrative.fraud_story} />
      </div>

      {narrative.false_positive_traps.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8, color: "var(--warn)" }}>
            {t("scenario_ai.fp_traps")}
          </div>
          <ul style={{ margin: 0, paddingLeft: 18 }} className="space-y-1">
            {narrative.false_positive_traps.map((trap) => (
              <li key={trap} style={{ fontSize: 13, lineHeight: 1.6, color: "var(--fg-2)" }}>
                {trap}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="fx-mono" style={{ fontSize: 10, color: "var(--dim)" }}>
        {t("scenario_ai.footer", { model: result.model, promptVersion: result.prompt_version })}
      </div>
    </div>
  );
}
