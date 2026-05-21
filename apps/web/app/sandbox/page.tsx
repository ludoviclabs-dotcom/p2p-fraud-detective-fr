"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { Schemas } from "@p2pfd/shared-types";
import { SeverityBadge } from "@/components/ui/badge";
import { ForensicPage } from "@/components/forensic-page";

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

  const query = useQuery({
    queryKey: ["scenarios"],
    queryFn: () => api.get<ScenarioMeta[]>("/api/v1/scenarios"),
    retry: false,
  });

  const scenarios = query.data ?? [];
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
            {query.isLoading ? (
              <ScenarioSkeleton />
            ) : query.error ? (
              <ScenarioError />
            ) : (
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
            )}
          </div>
        </div>
      </div>
    </ForensicPage>
  );
}

function ScenarioDetail({ scenario }: { scenario: ScenarioMeta }) {
  const detectorPages = Array.from(
    new Set(
      scenario.detectors
        .map((d) => DETECTOR_TO_PAGE[d])
        .filter((p): p is string => Boolean(p)),
    ),
  );

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
        <div className="grid gap-3 sm:grid-cols-3">
          <FactBox label="Pilier" value={scenario.pillar} />
          <FactBox label="Cible" value={scenario.target_vendor ?? "Multi-vendor"} />
          <FactBox label="Détecteurs" value={String(scenario.detectors.length)} />
        </div>

        <div className="fx-card">
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Storyline audit</div>
          <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--fg-2)", whiteSpace: "pre-wrap" }}>
            {scenario.storyline}
          </p>
        </div>

        <div>
          <div className="fx-eyebrow" style={{ marginBottom: 8 }}>Contrôles déclenchés</div>
          <div className="flex flex-wrap gap-2">
            {scenario.detectors.map((d) => (
              <span
                key={d}
                className="fx-mono"
                style={{
                  fontSize: 11,
                  padding: "3px 8px",
                  background: "var(--panel-2)",
                  border: "1px solid var(--border-strong)",
                  color: "var(--info)",
                }}
              >
                {d}
              </span>
            ))}
          </div>
        </div>

        <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", padding: "14px 16px" }}>
          <div className="fx-eyebrow" style={{ marginBottom: 10 }}>◷ Parcours de conversion</div>
          <div className="grid gap-2 sm:grid-cols-3">
            {["Voir le cockpit", "Ouvrir le vendor 360", "Exporter la preuve"].map((item) => (
              <div
                key={item}
                className="fx-mono"
                style={{ fontSize: 11, padding: "8px 10px", background: "var(--panel)", border: "1px solid var(--border)", color: "var(--fg-2)" }}
              >
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {detectorPages.map((p) => (
            <Link key={p} href={p} className="fx-btn-ghost sm">
              Explorer {p} →
            </Link>
          ))}
          <Link href="/dashboard" className="fx-btn sm">
            Cockpit ↗
          </Link>
          {scenario.target_vendor ? (
            <Link
              href={`/vendors/${encodeURIComponent(scenario.target_vendor)}`}
              className="fx-btn-ghost sm"
            >
              Fiche fournisseur 360
            </Link>
          ) : null}
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

function ScenarioSkeleton() {
  return (
    <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="fx-skel" style={{ height: 90 }} />
        ))}
      </div>
      <div className="fx-skel" style={{ height: 320 }} />
    </div>
  );
}

function ScenarioError() {
  return (
    <div className="fx-notice">
      <span className="glyph">⚠</span>
      <div>
        <div className="nt">Scénarios indisponibles</div>
        <p className="nb">
          L&apos;API ne répond pas encore. Vérifiez le backend FastAPI puis rechargez la page.
        </p>
        <div className="mt-4">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="fx-btn sm"
          >
            ↻ Réessayer
          </button>
        </div>
      </div>
    </div>
  );
}
