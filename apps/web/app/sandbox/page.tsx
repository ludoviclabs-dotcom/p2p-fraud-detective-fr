"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { Schemas } from "@p2pfd/shared-types";
import { Card, CardContent } from "@/components/ui/card";
import { SeverityBadge } from "@/components/ui/badge";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FileSearch,
  GitBranch,
  ShieldAlert,
  Sparkles,
  TimerReset,
  type LucideIcon,
} from "lucide-react";

type ScenarioMeta = Schemas["ScenarioMeta"];

const SEVERITY_TONE: Record<string, string> = {
  critical: "border-[#e5484d] bg-[#fff0f1]",
  high: "border-[#f5a524] bg-[#fff7e8]",
  medium: "border-[#f5a524] bg-[#fff7e8]",
  low: "border-[#12a876] bg-[#e8f8f1]",
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
    retry: false,
  });

  const scenarios = query.data ?? [];
  const current = scenarios.find((s) => s.name === selected) ?? scenarios[0];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <div>
          <h1 className="text-3xl font-bold text-[#08111f] dark:text-white">
            Démo interactive fraude en 60 secondes
          </h1>
          <p className="mt-3 text-sm leading-6 text-[#667085]">
            Choisissez une typologie synthétique et suivez le parcours jusqu'au
            cockpit, au fournisseur 360 et aux contrôles associés, sans uploader
            de fichier client.
          </p>

          <div className="mt-6 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {[
              ["01", "Scénario", "Sélectionnez un risque préchargé."],
              ["02", "Investigation", "Ouvrez les détecteurs déclenchés."],
              ["03", "Preuve", "Exportez une piste d'audit signée."],
            ].map(([step, title, body]) => (
              <div
                key={step}
                className="rounded-md border border-[#e6ebf2] bg-white p-4 shadow-sm dark:border-white/10 dark:bg-white/[0.04]"
              >
                <div className="flex items-center gap-3">
                  <span className="grid h-8 w-8 place-items-center rounded bg-[#eaf1ff] text-xs font-bold text-[#2f6bff]">
                    {step}
                  </span>
                  <div className="font-semibold text-[#111827] dark:text-white">
                    {title}
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-[#667085]">{body}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-[#e6ebf2] bg-white p-4 shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
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
                      className={`block w-full rounded-md border p-4 text-left transition-all ${
                        isActive
                          ? "border-[#2f6bff] bg-[#eaf1ff] shadow-sm"
                          : "border-[#e6ebf2] bg-white hover:border-[#2f6bff] dark:border-white/10 dark:bg-white/[0.03]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-[#111827] dark:text-white">
                            {s.title}
                          </div>
                          <div className="mt-1 text-xs leading-5 text-[#667085]">
                            {s.short}
                          </div>
                        </div>
                        <SeverityBadge value={s.severity} />
                      </div>
                      <div className="mt-3 text-[11px] font-semibold uppercase tracking-wider text-[#667085]">
                        {s.pillar}
                      </div>
                    </button>
                  );
                })}
              </div>

              {current ? (
                <ScenarioDetail scenario={current} />
              ) : (
                <Card>
                  <CardContent>Sélectionnez un scénario à gauche.</CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
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
  const tone = SEVERITY_TONE[scenario.severity] ?? "border-[#e6ebf2] bg-white";

  return (
    <Card className="overflow-hidden">
      <div className={`border-b ${tone} p-5 dark:border-white/10`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#667085]">
              <Sparkles size={14} />
              Scénario préchargé
            </div>
            <h2 className="mt-2 text-xl font-bold text-[#111827] dark:text-white">
              {scenario.title}
            </h2>
          </div>
          <SeverityBadge value={scenario.severity} />
        </div>
      </div>

      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-3">
          <Fact label="Pilier" value={scenario.pillar} Icon={ShieldAlert} />
          <Fact
            label="Cible"
            value={scenario.target_vendor ?? "Multi-vendor"}
            Icon={FileSearch}
          />
          <Fact
            label="Détecteurs"
            value={String(scenario.detectors.length)}
            Icon={GitBranch}
          />
        </div>

        <div className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-4 dark:border-white/10 dark:bg-white/[0.03]">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-[#667085]">
            Storyline audit
          </div>
          <p className="whitespace-pre-wrap text-sm leading-7 text-[#111827] dark:text-white/82">
            {scenario.storyline}
          </p>
        </div>

        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-[#667085]">
            Contrôles déclenchés
          </div>
          <div className="flex flex-wrap gap-2">
            {scenario.detectors.map((d) => (
              <code
                key={d}
                className="rounded bg-[#eef3fb] px-2 py-1 text-xs text-[#2f6bff] dark:bg-white/10"
              >
                {d}
              </code>
            ))}
          </div>
        </div>

        <div className="rounded-md bg-[#08111f] p-4 text-white">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <TimerReset size={16} className="text-[#f5a524]" />
            Parcours de conversion
          </div>
          <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
            <div className="rounded bg-white/[0.07] p-3">Voir le cockpit</div>
            <div className="rounded bg-white/[0.07] p-3">Ouvrir le vendor 360</div>
            <div className="rounded bg-white/[0.07] p-3">Exporter la preuve</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {detectorPages.map((p) => (
            <Link
              key={p}
              href={p}
              className="inline-flex h-9 items-center gap-2 rounded-md border border-[#2f6bff] bg-white px-3 text-sm font-semibold text-[#2f6bff] transition-colors hover:bg-[#eaf1ff] dark:bg-white/[0.04]"
            >
              Explorer {p}
              <ArrowRight size={14} />
            </Link>
          ))}
          <Link
            href="/dashboard"
            className="inline-flex h-9 items-center gap-2 rounded-md bg-[#2f6bff] px-3 text-sm font-semibold text-white transition-colors hover:bg-[#2457d6]"
          >
            Cockpit
            <ArrowRight size={14} />
          </Link>
          {scenario.target_vendor ? (
            <Link
              href={`/vendors/${encodeURIComponent(scenario.target_vendor)}`}
              className="inline-flex h-9 items-center gap-2 rounded-md border border-[#e6ebf2] bg-white px-3 text-sm font-semibold text-[#667085] transition-colors hover:border-[#2f6bff] hover:text-[#2f6bff] dark:border-white/10 dark:bg-white/[0.04]"
            >
              Fiche fournisseur 360
              <ArrowRight size={14} />
            </Link>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function Fact({
  label,
  value,
  Icon,
}: {
  label: string;
  value: string;
  Icon: LucideIcon;
}) {
  return (
    <div className="rounded-md border border-[#e6ebf2] bg-white p-3 dark:border-white/10 dark:bg-white/[0.03]">
      <Icon size={16} className="text-[#2f6bff]" />
      <div className="mt-2 text-[11px] font-semibold uppercase tracking-wider text-[#667085]">
        {label}
      </div>
      <div className="mt-1 truncate text-sm font-semibold text-[#111827] dark:text-white">
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
          <div key={i} className="h-28 animate-pulse rounded-md bg-[#eef3fb]" />
        ))}
      </div>
      <div className="h-96 animate-pulse rounded-md bg-[#eef3fb]" />
    </div>
  );
}

function ScenarioError() {
  return (
    <div className="rounded-md border border-[#fff7e8] bg-[#fffaf0] p-5">
      <div className="flex items-start gap-3">
        <AlertTriangle size={20} className="mt-0.5 text-[#b56b00]" />
        <div>
          <div className="font-semibold text-[#111827]">
            Scénarios indisponibles
          </div>
          <p className="mt-1 text-sm leading-6 text-[#667085]">
            L'API ne répond pas encore. Vérifiez le backend FastAPI puis
            rechargez la page.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 inline-flex h-9 items-center gap-2 rounded-md bg-[#2f6bff] px-3 text-sm font-semibold text-white"
          >
            <CheckCircle2 size={14} />
            Réessayer
          </button>
        </div>
      </div>
    </div>
  );
}
