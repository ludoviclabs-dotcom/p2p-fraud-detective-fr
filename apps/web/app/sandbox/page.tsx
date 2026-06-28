"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { Schemas } from "@p2pfd/shared-types";
import { SeverityBadge } from "@/components/ui/badge";
import { ForensicPage } from "@/components/forensic-page";
import { ScenarioNarrativePanel } from "@/components/scenario-narrative-panel";
import {
  getSandboxNarrative,
  mergeSandboxScenarios,
} from "@/data/sandbox-scenarios";

type ScenarioMeta = Schemas["ScenarioMeta"];

const DETECTOR_TO_PAGE: Record<string, string> = {
  master_data_changes: "/master-history",
  under_thresholds: "/structuring",
  duplicates: "/duplicates",
  network_rings: "/rings",
  shell_companies: "/rings",
  sanctions: "/sanctions",
  pep: "/sanctions",
  benford: "/benford",
  score_explorer: "/score",
};

export default function SandboxPage() {
  const [selected, setSelected] = useState<string | null>(null);

  // Catalogue local pré-chargé (offline) fusionné avec d'éventuels scénarios
  // backend. Le local est toujours présent → la sandbox fonctionne sans backend.
  const query = useQuery({
    queryKey: ["scenarios"],
    queryFn: () => api.get<ScenarioMeta[]>("/api/v1/scenarios"),
    retry: false,
  });

  const scenarios = mergeSandboxScenarios(query.data);
  const current = scenarios.find((s) => s.name === selected) ?? scenarios[0];

  return (
    <ForensicPage>
      <div className="fx-head">
        <div>
          <div className="fx-eyebrow">Sandbox · démo interactive</div>
          <h1 style={{ marginTop: 9 }}>
            Fraude en <span className="italic">60 secondes</span>
          </h1>
          <p className="sub">
            Choisissez une typologie synthétique et suivez le parcours jusqu&apos;au cockpit,
            au fournisseur 360 et aux contrôles associés, sans uploader de fichier client.
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <div>
          <div className="space-y-3">
            {[
              ["1", "Scénario", "Sélectionnez un risque préchargé."],
              ["2", "Investigation", "Ouvrez les détecteurs déclenchés."],
              ["3", "Preuve", "Exportez une piste d'audit signée."],
            ].map(([step, title, body]) => (
              <div key={step} className="fx-step">
                <div className="n">{step}</div>
                <div>
                  <div className="t">{title}</div>
                  <div className="d">{body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="fx-panel">
          <div className="fx-panel-head">
            <h2>Scénarios préchargés</h2>
            <span className="glyph">▣</span>
          </div>
          <div className="fx-panel-body">
            <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
              <div className="space-y-2">
                {scenarios.map((s) => {
                  const isActive = current?.name === s.name;
                  return (
                    <button
                      key={s.name}
                      type="button"
                      onClick={() => setSelected(s.name)}
                      style={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        background: isActive ? "var(--panel-2)" : "var(--panel)",
                        border: `1px solid ${isActive ? "var(--risk)" : "var(--border)"}`,
                        borderLeft: isActive ? "2px solid var(--risk)" : "2px solid transparent",
                        padding: "12px 14px",
                        cursor: "pointer",
                        transition: "all .15s",
                      }}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", fontWeight: 500 }}>
                            {s.title}
                          </div>
                          <div className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", marginTop: 3, lineHeight: 1.5 }}>
                            {s.short}
                          </div>
                        </div>
                        <SeverityBadge value={s.severity} />
                      </div>
                      <div className="fx-eyebrow" style={{ marginTop: 8 }}>
                        {s.pillar}
                      </div>
                    </button>
                  );
                })}
              </div>

              {current ? (
                <ScenarioDetail scenario={current} />
              ) : (
                <div className="fx-card">
                  <span className="fx-mono" style={{ fontSize: 12, color: "var(--muted)" }}>
                    Sélectionnez un scénario à gauche.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ForensicPage>
  );
}

const DETECTOR_HINT: Record<string, string> = {
  master_data_changes: "Modifications de coordonnées bancaires",
  under_thresholds: "Factures sous seuils de délégation",
  duplicates: "Doublons par raison sociale / IBAN",
  network_rings: "Graphe de fournisseurs liés",
  shell_companies: "Entités sans substance vérifiable",
  sanctions: "Screening listes sanctions OFAC / Trésor",
  pep: "Exposition personne politiquement exposée",
  benford: "Distribution Benford sur montants",
  score_explorer: "Score de risque consolidé",
};

function ScenarioDetail({ scenario }: { scenario: ScenarioMeta }) {
  const detectorPages = Array.from(
    new Set(
      scenario.detectors
        .map((d) => DETECTOR_TO_PAGE[d])
        .filter((p): p is string => Boolean(p)),
    ),
  );

  const vendorHref = scenario.target_vendor
    ? `/vendors/${encodeURIComponent(scenario.target_vendor)}`
    : "/vendors";

  const scoreMatch = scenario.storyline.match(/score\s+(\d+)\/100/i);
  const score = scoreMatch ? `${scoreMatch[1]}/100` : null;
  const demo = `?demo=${encodeURIComponent(scenario.name)}`;

  const conversionSteps = [
    {
      label: "Voir le cockpit",
      href: `/dashboard${demo}`,
      hint: score ? `Score ${score} · ${scenario.severity}` : scenario.severity,
    },
    {
      label: "Ouvrir le vendor 360",
      href: `${vendorHref}${demo}`,
      hint: scenario.target_vendor ? `Fournisseur ${scenario.target_vendor}` : "Vue multi-fournisseur",
    },
    {
      label: "Exporter la preuve",
      href: `/exports${demo}`,
      hint: "Piste d'audit signée",
    },
  ];

  return (
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div>
          <div className="fx-eyebrow">§ Scénario préchargé</div>
          <h2 style={{ marginTop: 4 }}>{scenario.title}</h2>
        </div>
        <SeverityBadge value={scenario.severity} />
      </div>
      <div className="fx-panel-body space-y-4">
        <div className="grid gap-3 sm:grid-cols-4">
          <FactBox label="Pilier" value={scenario.pillar} />
          <FactBox label="Cible" value={scenario.target_vendor ?? "Multi-vendor"} />
          <FactBox label="Détecteurs" value={String(scenario.detectors.length)} />
          {score ? <FactBox label="Score" value={score} /> : null}
        </div>

        <div className="fx-card">
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Storyline audit</div>
          <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)", whiteSpace: "pre-wrap" }}>
            {scenario.storyline}
          </p>
        </div>

        <ScenarioNarrativePanel
          key={scenario.name}
          scenarioId={scenario.name}
          staticNarrative={getSandboxNarrative(scenario.name)}
        />

        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Contrôles déclenchés</div>
          <div className="flex flex-wrap gap-2">
            {scenario.detectors.map((d) => (
              <span
                key={d}
                title={DETECTOR_HINT[d]}
                className="fx-mono"
                style={{
                  fontSize: 11,
                  padding: "3px 8px",
                  background: "var(--panel-2)",
                  border: "1px solid var(--border-strong)",
                  color: "var(--info)",
                  cursor: "help",
                }}
              >
                {d}
              </span>
            ))}
          </div>
        </div>

        <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "14px 16px" }}>
          <div className="fx-eyebrow" style={{ marginBottom: 10 }}>◷ Parcours de conversion · simulation</div>
          <div className="grid gap-2 sm:grid-cols-3">
            {conversionSteps.map((step) => (
              <Link
                key={step.label}
                href={step.href}
                className="fx-mono"
                style={{
                  fontSize: 11,
                  padding: "8px 10px",
                  background: "var(--panel)",
                  border: "1px solid var(--border)",
                  color: "var(--fg-2)",
                  textDecoration: "none",
                  display: "block",
                }}
              >
                <span style={{ color: "var(--fg)", display: "block", marginBottom: 3 }}>
                  {step.label} →
                </span>
                <span style={{ color: "var(--muted)", fontSize: 10 }}>
                  {step.hint}
                </span>
              </Link>
            ))}
          </div>
        </div>

        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Détecteurs à investiguer</div>
          <div className="flex flex-col gap-2">
            {detectorPages.map((p) => (
              <Link
                key={p}
                href={`${p}${demo}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 12px",
                  background: "var(--panel)",
                  border: "1px solid var(--border)",
                  textDecoration: "none",
                  fontSize: 12,
                }}
              >
                <span className="fx-mono" style={{ color: "var(--info)" }}>Explorer {p}</span>
                <span style={{ color: "var(--muted)", fontSize: 10 }}>
                  {scenario.detectors
                    .filter((d) => DETECTOR_TO_PAGE[d] === p)
                    .map((d) => DETECTOR_HINT[d] ?? d)
                    .join(" · ")}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function FactBox({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "10px 12px" }}>
      <div className="fx-eyebrow">{label}</div>
      <div className="fx-mono" style={{ fontSize: 13, color: "var(--fg)", marginTop: 4, fontWeight: 500 }}>
        {value}
      </div>
    </div>
  );
}
