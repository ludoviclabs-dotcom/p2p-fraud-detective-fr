"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { generateScenarioNarrative } from "@/lib/api-client";
import type { ScenarioNarrative } from "@/lib/api-client";
import { ClaimList } from "@/components/grounded-claims";
import { Badge } from "@/components/ui/badge";

/**
 * Narratif d'un scénario synthétique (Phase 6, ADR-0007).
 *
 * Deux sources possibles, transparentes via un badge :
 * - `staticNarrative` fourni (catalogue sandbox pré-chargé) → affichage 100 %
 *   déterministe, OFFLINE, aucun appel API (badge « DONNÉES PRÉ-CHARGÉES »).
 * - sinon → génération IA live via le backend (badge « IA LIVE »), Claude ne
 *   restant qu'un fallback. Le générateur déterministe reste seul responsable
 *   des données et labels ; le LLM ne produit que l'habillage pédagogique.
 */
export function ScenarioNarrativePanel({
  scenarioId,
  staticNarrative,
}: {
  scenarioId: string;
  staticNarrative?: ScenarioNarrative;
}) {
  const [revealed, setRevealed] = useState(false);
  const mutation = useMutation({
    mutationFn: () => generateScenarioNarrative(scenarioId),
  });

  // Source pré-chargée : narratif statique, aucun appel réseau.
  if (staticNarrative) {
    return (
      <div data-testid="scenario-narrative-panel">
        <button
          className="fx-btn-ghost sm"
          data-testid="scenario-narrative-button"
          type="button"
          onClick={() => setRevealed((v) => !v)}
        >
          {revealed ? "× Masquer le narratif" : "¶ Narratif du scénario"}
        </button>

        {revealed ? <NarrativeBody narrative={staticNarrative} source="static" /> : null}
      </div>
    );
  }

  // Sinon : génération IA live (fallback), comportement historique.
  return (
    <div data-testid="scenario-narrative-panel">
      <button
        className="fx-btn-ghost sm"
        data-testid="scenario-narrative-button"
        type="button"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "◷ Génération…" : "¶ Narratif IA du scénario"}
      </button>

      {mutation.error ? (
        <p className="fx-mono" style={{ marginTop: 8, fontSize: 11, color: "var(--muted)" }}>
          Narratif indisponible — backend FastAPI + clé ANTHROPIC_API_KEY requis. Le scénario reste
          jouable sans IA.
        </p>
      ) : null}

      {mutation.data ? (
        <NarrativeBody
          narrative={mutation.data.narrative}
          source="ia"
          model={mutation.data.model}
          promptVersion={mutation.data.prompt_version}
        />
      ) : null}
    </div>
  );
}

function NarrativeBody({
  narrative,
  source,
  model,
  promptVersion,
}: {
  narrative: ScenarioNarrative;
  source: "static" | "ia";
  model?: string;
  promptVersion?: string;
}) {
  return (
    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Badge severity={source === "static" ? "low" : "medium"}>
          {source === "static" ? "Données pré-chargées" : "IA live"}
        </Badge>
      </div>

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
        <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Mode opératoire</div>
        <ClaimList claims={narrative.fraud_story} />
      </div>

      {narrative.false_positive_traps.length ? (
        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8, color: "var(--warn)" }}>
            Pièges faux-positifs (à montrer en démo)
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
        {source === "static"
          ? "Données pré-chargées · scénario déterministe (offline, sans appel IA)"
          : `Généré par ${model} · prompt ${promptVersion} · les données et labels du scénario restent 100 % déterministes`}
      </div>
    </div>
  );
}
