"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  DatabaseZap,
  FileText,
  FlaskConical,
  Loader2,
  Play,
  ShieldCheck,
  TerminalSquare,
  TriangleAlert,
} from "lucide-react";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { scoreTransaction } from "@/lib/risk/scoreEngine";
import type { RiskScenario, RiskScoreResult } from "@/types/risk";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";

type ScenarioFeed = {
  source: "huggingface" | "local";
  scenarios: RiskScenario[];
  message: string;
};

export default function P2PScenariosPage() {
  const [feed, setFeed] = useState<ScenarioFeed>({
    source: "local",
    scenarios: RISK_SCENARIOS,
    message: "Scénarios locaux chargés.",
  });
  const [selectedId, setSelectedId] = useState(RISK_SCENARIOS[0]?.id ?? "");
  const [results, setResults] = useState<Record<string, RiskScoreResult>>({});
  const [pendingId, setPendingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/risk/scenarios")
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((payload: ScenarioFeed) => {
        if (!cancelled && Array.isArray(payload.scenarios) && payload.scenarios.length) {
          setFeed(payload);
          setSelectedId(payload.scenarios[0].id);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFeed({
            source: "local",
            scenarios: RISK_SCENARIOS,
            message: "Source locale de démo utilisée: API scénarios indisponible.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () => feed.scenarios.find((item) => item.id === selectedId) ?? feed.scenarios[0],
    [feed.scenarios, selectedId],
  );
  const selectedResult = selected ? results[selected.id] : undefined;

  async function analyze(scenario: RiskScenario) {
    setPendingId(scenario.id);
    try {
      const response = await fetch("/api/risk/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction: scenario.transaction }),
      });
      if (!response.ok) throw new Error(await response.text());
      const result = (await response.json()) as RiskScoreResult;
      setResults((previous) => ({ ...previous, [scenario.id]: result }));
      setSelectedId(scenario.id);
    } catch {
      setResults((previous) => ({
        ...previous,
        [scenario.id]: scoreTransaction(scenario.transaction),
      }));
      setSelectedId(scenario.id);
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#667085]">
            Paiements P2P · SEPA · Procure-to-Pay
          </p>
          <h1 className="mt-2 text-3xl font-bold text-[#08111f] dark:text-white">
            Scénarios P2P explicables
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#667085]">
            Six parcours synthétiques pour démontrer le cycle détecter, scorer,
            expliquer, investiguer, documenter et exporter.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge severity={feed.source === "huggingface" ? "low" : "neutral"}>
            {feed.source === "huggingface" ? "Hugging Face" : "Source locale"}
          </Badge>
          <Link
            href="/risk-test-lab"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-[#2f6bff] px-4 text-sm font-semibold text-white"
          >
            Test Lab
            <ArrowRight size={15} />
          </Link>
          <Link
            href="/risk-docs"
            className="inline-flex h-10 items-center gap-2 rounded-md border border-[#e6ebf2] bg-white px-4 text-sm font-semibold text-[#667085] hover:border-[#2f6bff] hover:text-[#2f6bff]"
          >
            Docs & glossaire
            <ArrowRight size={15} />
          </Link>
          <Link
            href="/detection-studio"
            className="inline-flex h-10 items-center gap-2 rounded-md border border-[#2f6bff] bg-white px-4 text-sm font-semibold text-[#2f6bff]"
          >
            Detection Studio
            <ArrowRight size={15} />
          </Link>
        </div>
      </div>

      <Card className="mt-6 border-l-4 border-l-[#2f6bff]">
        <CardContent className="flex flex-col gap-3 text-sm text-[#667085] md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2">
            <DatabaseZap size={16} className="text-[#2f6bff]" />
            {feed.message}
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-[#12a876]" />
            Données synthétiques, décision finale humaine.
          </div>
        </CardContent>
      </Card>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <PathCard
          title="1. Scénarios guidés"
          body="Sélectionner une fraude synthétique, lancer l'analyse et voir score, reason codes et action recommandée."
          icon={FlaskConical}
          href="/p2p-scenarios"
        />
        <PathCard
          title="2. Test Lab API"
          body="Modifier le JSON, appeler /api/risk/score, créer un case et générer un evidence pack."
          icon={TerminalSquare}
          href="/risk-test-lab"
        />
        <PathCard
          title="3. Documentation"
          body="Lire le glossaire, les endpoints, les typologies, les limites et le fonctionnement du moteur."
          icon={BookOpen}
          href="/risk-docs"
        />
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="grid gap-3">
          {feed.scenarios.map((scenario) => {
            const result = results[scenario.id];
            const active = selected?.id === scenario.id;
            return (
              <button
                key={scenario.id}
                type="button"
                onClick={() => setSelectedId(scenario.id)}
                className={`rounded-md border bg-white p-4 text-left shadow-sm transition-colors dark:bg-white/[0.04] ${
                  active
                    ? "border-[#2f6bff]"
                    : "border-[#e6ebf2] hover:border-[#2f6bff] dark:border-white/10"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-[#111827] dark:text-white">
                      {scenario.title}
                    </h2>
                    <p className="mt-1 text-sm leading-6 text-[#667085]">
                      {scenario.description}
                    </p>
                  </div>
                  {result ? <SeverityBadge value={result.level} /> : <Badge>Demo</Badge>}
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-[#667085]">
                  <span className="font-mono">{scenario.caseId}</span>
                  <span>{formatEur(scenario.transaction.amount)}</span>
                  <span>{scenario.transaction.rail}</span>
                </div>
              </button>
            );
          })}
        </div>

        {selected ? (
          <Card className="overflow-hidden">
            <CardHeader className="bg-[#08111f] text-white">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-white/50">
                    Analyse scénario
                  </div>
                  <CardTitle className="mt-2 text-white">{selected.title}</CardTitle>
                </div>
                {selectedResult ? <SeverityBadge value={selectedResult.level} /> : null}
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <p className="text-sm leading-7 text-[#667085]">{selected.businessContext}</p>

              <div className="grid gap-3 sm:grid-cols-3">
                <Fact label="Montant" value={formatEur(selected.transaction.amount)} />
                <Fact label="Rail" value={selected.transaction.rail} />
                <Fact label="Case" value={selected.caseId} />
              </div>

              <details className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-4 dark:border-white/10 dark:bg-white/[0.03]">
                <summary className="flex cursor-pointer items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#667085]">
                  <FileText size={14} />
                  Voir les données synthétiques JSON
                </summary>
                <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap text-xs leading-6 text-[#111827] dark:text-white/80">
                  {JSON.stringify(selected.transaction, null, 2)}
                </pre>
              </details>

              <Button
                type="button"
                onClick={() => analyze(selected)}
                disabled={pendingId === selected.id}
              >
                {pendingId === selected.id ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                Lancer l'analyse
              </Button>

              {selectedResult ? (
                <div className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-4">
                    <Fact label="Score" value={`${selectedResult.score}/100`} />
                    <Fact label="Niveau" value={selectedResult.level} />
                    <Fact label="Décision" value={selectedResult.decision} />
                    <Fact label="Typologie" value={selectedResult.typology} />
                  </div>

                  <div>
                    <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#667085]">
                      <TriangleAlert size={14} />
                      Reason codes
                    </div>
                    <div className="grid gap-2">
                      {selectedResult.reasonCodes.slice(0, 8).map((reasonCode) => (
                        <div
                          key={`${reasonCode.detector}-${reasonCode.code}`}
                          className="rounded-md border border-[#e6ebf2] bg-white p-3 dark:border-white/10 dark:bg-white/[0.04]"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <code className="text-xs font-semibold text-[#2f6bff]">
                              {reasonCode.code}
                            </code>
                            <span className="text-xs font-semibold text-[#667085]">
                              +{reasonCode.weight}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-[#111827] dark:text-white">
                            {reasonCode.label}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-md bg-[#eaf1ff] p-4 text-sm text-[#111827]">
                    <div className="font-semibold">Action recommandée</div>
                    <p className="mt-1 leading-6">{selectedResult.recommendedActions[0]}</p>
                  </div>

                  <Link
                    href={`/fraud-case-360/${encodeURIComponent(selected.caseId)}`}
                    className="inline-flex h-10 items-center gap-2 rounded-md bg-[#08111f] px-4 text-sm font-semibold text-white"
                  >
                    Ouvrir Fraud Case 360
                    <ArrowRight size={15} />
                  </Link>
                  <Link
                    href="/risk-test-lab"
                    className="inline-flex h-10 items-center gap-2 rounded-md border border-[#2f6bff] bg-white px-4 text-sm font-semibold text-[#2f6bff]"
                  >
                    Modifier le JSON dans le Test Lab
                    <ArrowRight size={15} />
                  </Link>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </section>
    </div>
  );
}

function PathCard({
  title,
  body,
  href,
  icon: Icon,
}: {
  title: string;
  body: string;
  href: string;
  icon: typeof BookOpen;
}) {
  return (
    <Link
      href={href}
      className="rounded-md border border-[#e6ebf2] bg-white p-5 shadow-sm transition-colors hover:border-[#2f6bff] dark:border-white/10 dark:bg-white/[0.04]"
    >
      <Icon size={20} className="text-[#2f6bff]" />
      <div className="mt-3 font-semibold text-[#111827] dark:text-white">{title}</div>
      <p className="mt-2 text-sm leading-6 text-[#667085]">{body}</p>
    </Link>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#e6ebf2] bg-white p-3 dark:border-white/10 dark:bg-white/[0.04]">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-[#667085]">
        {label}
      </div>
      <div className="mt-1 truncate font-mono text-sm font-semibold text-[#111827] dark:text-white">
        {value}
      </div>
    </div>
  );
}
