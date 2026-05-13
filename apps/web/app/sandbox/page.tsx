"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { Schemas } from "@p2pfd/shared-types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SeverityBadge } from "@/components/ui/badge";
import { Play, Sparkles } from "lucide-react";

type ScenarioMeta = Schemas["ScenarioMeta"];

const SEV_EMOJI: Record<string, string> = {
  critical: "🔴",
  high: "🟠",
  medium: "🟡",
  low: "🟢",
};

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
  });

  const scenarios = query.data ?? [];
  const current = scenarios.find((s) => s.name === selected) ?? scenarios[0];

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Pilotage
      </div>
      <h1 className="mb-1 flex items-center gap-2 text-3xl font-bold text-[#0f1b33] dark:text-white">
        <Play size={28} /> Sandbox commerciale
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        5 scénarios pré-chargés cliquables — démos institutionnelles en 60
        secondes sans uploader de fichier. Chaque scénario amplifie un pattern
        de fraude pour que le détecteur correspondant remonte clairement
        (typologies inspirées du rapport Tracfin Tome III 2024-2025).
      </p>

      {query.isLoading ? (
        <div className="text-sm text-[#5a6478]">Chargement des scénarios…</div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_2fr]">
          <div className="space-y-2">
            {scenarios.map((s) => {
              const isActive = current?.name === s.name;
              return (
                <button
                  key={s.name}
                  type="button"
                  onClick={() => setSelected(s.name)}
                  className={`block w-full rounded-md border bg-white p-3 text-left transition-colors ${
                    isActive
                      ? "border-[#1f3a6e] shadow-sm"
                      : "border-[#e1e5ee] hover:border-[#1f3a6e]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-semibold text-[#0f1b33]">
                      {SEV_EMOJI[s.severity] ?? ""} {s.title}
                    </span>
                    <SeverityBadge value={s.severity} />
                  </div>
                  <div className="mt-1 text-xs text-[#5a6478]">{s.short}</div>
                  <div className="mt-1 text-[10px] uppercase tracking-wider text-[#9aa3b2]">
                    {s.pillar}
                  </div>
                </button>
              );
            })}
          </div>

          <div>
            {current ? (
              <ScenarioDetail scenario={current} />
            ) : (
              <Card>
                <CardContent>Sélectionner un scénario à gauche.</CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
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
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles size={18} /> {scenario.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <SeverityBadge value={scenario.severity} />
          <span className="text-[#5a6478]">
            <strong className="text-[#0f1b33]">Pilier</strong> : {scenario.pillar}
          </span>
          {scenario.target_vendor ? (
            <span className="text-[#5a6478]">
              <strong className="text-[#0f1b33]">Vendor cible</strong> :{" "}
              <Link
                href={`/vendors/${encodeURIComponent(scenario.target_vendor)}`}
                className="font-mono text-[#1f3a6e] hover:underline"
              >
                {scenario.target_vendor}
              </Link>
            </span>
          ) : null}
        </div>

        <div className="rounded border border-[#e1e5ee] bg-[#f9fafc] p-4">
          <div className="mb-2 text-xs uppercase tracking-wider text-[#5a6478]">
            Storyline
          </div>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#1a1f2c]">
            {scenario.storyline}
          </p>
        </div>

        <div>
          <div className="mb-2 text-xs uppercase tracking-wider text-[#5a6478]">
            Détecteurs déclenchés
          </div>
          <div className="flex flex-wrap gap-2">
            {scenario.detectors.map((d) => (
              <code
                key={d}
                className="rounded bg-[#f4f6fa] px-2 py-1 text-xs text-[#1f3a6e]"
              >
                {d}
              </code>
            ))}
          </div>
        </div>

        {detectorPages.length > 0 ? (
          <div>
            <div className="mb-2 text-xs uppercase tracking-wider text-[#5a6478]">
              🚀 Explorer le scénario
            </div>
            <div className="flex flex-wrap gap-2">
              {detectorPages.map((p) => (
                <Link
                  key={p}
                  href={p}
                  className="inline-flex items-center gap-1 rounded border border-[#1f3a6e] bg-white px-3 py-1.5 text-xs font-medium text-[#1f3a6e] transition-colors hover:bg-[#f4f6fa]"
                >
                  ➡️ {p}
                </Link>
              ))}
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1 rounded border border-[#e1e5ee] bg-white px-3 py-1.5 text-xs font-medium text-[#5a6478] transition-colors hover:border-[#1f3a6e] hover:text-[#1f3a6e]"
              >
                🎯 Cockpit
              </Link>
            </div>
          </div>
        ) : null}

        <div className="rounded border-l-4 border-[#e5a93a] bg-[#fff8ec] p-3 text-xs text-[#5a6478]">
          💡 Côté Streamlit (legacy v0.5), ce scénario est chargeable en
          session via la page <strong>Sandbox commerciale</strong> qui appelle{" "}
          <code className="rounded bg-[#f4f6fa] px-1 py-0.5">
            load_scenario(&quot;{scenario.name}&quot;)
          </code>
          . En v2 Next.js, les pages détecteurs lisent directement les cases
          déjà créés depuis l&apos;API — pas de session client lourde.
        </div>

        <a
          href="https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/blob/main/src/p2p_fraud/synthetic/scenarios.py"
          target="_blank"
          rel="noreferrer"
          className="inline-flex h-10 items-center gap-1 rounded-md border border-[#e1e5ee] bg-white px-4 text-sm font-medium text-[#5a6478] transition-colors hover:border-[#1f3a6e] hover:text-[#1f3a6e]"
        >
          📚 Voir le code synthetic/scenarios.py
        </a>
      </CardContent>
    </Card>
  );
}
