"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  Code2,
  Download,
  FileJson,
  Loader2,
  Play,
  RotateCcw,
  ShieldAlert,
  TerminalSquare,
} from "lucide-react";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { scoreTransaction } from "@/lib/risk/scoreEngine";
import type { EvidencePack, P2PTransaction, RiskScenario, RiskScoreResult } from "@/types/risk";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";

const FIRST_SCENARIO = RISK_SCENARIOS[0];

export default function RiskTestLabPage() {
  const [scenarioId, setScenarioId] = useState(FIRST_SCENARIO.id);
  const [jsonInput, setJsonInput] = useState(
    JSON.stringify(FIRST_SCENARIO.transaction, null, 2),
  );
  const [result, setResult] = useState<RiskScoreResult | null>(
    scoreTransaction(FIRST_SCENARIO.transaction),
  );
  const [evidencePack, setEvidencePack] = useState<EvidencePack | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<"score" | "case" | "evidence" | null>(null);

  const scenario = useMemo(
    () => RISK_SCENARIOS.find((item) => item.id === scenarioId) ?? FIRST_SCENARIO,
    [scenarioId],
  );

  function loadScenario(next: RiskScenario) {
    setScenarioId(next.id);
    setJsonInput(JSON.stringify(next.transaction, null, 2));
    setResult(scoreTransaction(next.transaction));
    setEvidencePack(null);
    setError(null);
  }

  function parseTransaction(): P2PTransaction | null {
    try {
      const value = JSON.parse(jsonInput) as P2PTransaction;
      setError(null);
      return value;
    } catch (parseError) {
      setError(parseError instanceof Error ? parseError.message : "JSON invalide");
      return null;
    }
  }

  async function runScore() {
    const transaction = parseTransaction();
    if (!transaction) return;
    setPending("score");
    try {
      const response = await fetch("/api/risk/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction }),
      });
      if (!response.ok) throw new Error(await response.text());
      setResult((await response.json()) as RiskScoreResult);
      setEvidencePack(null);
      setError(null);
    } catch (apiError) {
      setResult(scoreTransaction(transaction));
      setError(
        `Mode local utilisé: ${
          apiError instanceof Error ? apiError.message : "API indisponible"
        }`,
      );
    } finally {
      setPending(null);
    }
  }

  async function createCase() {
    const transaction = parseTransaction();
    if (!transaction) return;
    setPending("case");
    try {
      const response = await fetch("/api/risk/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ caseId: transaction.caseId ?? scenario.caseId, transaction }),
      });
      if (!response.ok) throw new Error(await response.text());
      const payload = (await response.json()) as { href: string };
      window.location.href = payload.href;
    } catch (caseError) {
      setError(caseError instanceof Error ? caseError.message : "Création case impossible");
    } finally {
      setPending(null);
    }
  }

  async function exportEvidence() {
    const transaction = parseTransaction();
    if (!transaction) return;
    setPending("evidence");
    try {
      const response = await fetch("/api/evidence/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          caseId: transaction.caseId ?? scenario.caseId,
          transaction,
          analystNotes: "Export généré depuis le Risk Test Lab.",
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      const payload = (await response.json()) as { evidencePack: EvidencePack };
      setEvidencePack(payload.evidencePack);
      setError(null);
    } catch (evidenceError) {
      setError(evidenceError instanceof Error ? evidenceError.message : "Export impossible");
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#667085]">
            Console de test
          </p>
          <h1 className="mt-2 text-3xl font-bold text-[#08111f] dark:text-white">
            Risk Test Lab
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#667085]">
            Testez le moteur avec un scénario, modifiez le JSON, appelez l'API,
            créez un case et générez un evidence pack. Tout reste synthétique.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/risk-docs"
            className="inline-flex h-10 items-center gap-2 rounded-md border border-[#2f6bff] bg-white px-4 text-sm font-semibold text-[#2f6bff]"
          >
            Documentation & glossaire
            <ArrowRight size={15} />
          </Link>
          <Link
            href="/p2p-scenarios"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-[#2f6bff] px-4 text-sm font-semibold text-white"
          >
            Scénarios guidés
            <ArrowRight size={15} />
          </Link>
        </div>
      </div>

      <section className="mt-6 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardCheck size={18} className="text-[#2f6bff]" />
                Choisir un scénario de départ
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              {RISK_SCENARIOS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => loadScenario(item)}
                  className={`rounded-md border p-3 text-left transition-colors ${
                    scenario.id === item.id
                      ? "border-[#2f6bff] bg-[#eaf1ff]"
                      : "border-[#e6ebf2] bg-white hover:border-[#2f6bff] dark:border-white/10 dark:bg-white/[0.04]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-semibold text-[#111827] dark:text-white">
                        {item.title}
                      </div>
                      <div className="mt-1 text-xs text-[#667085]">
                        {item.caseId} · {formatEur(item.transaction.amount)} ·{" "}
                        {item.transaction.rail}
                      </div>
                    </div>
                    <Badge>Demo</Badge>
                  </div>
                </button>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TerminalSquare size={18} className="text-[#2f6bff]" />
                Actions de test
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <Button type="button" onClick={runScore} disabled={pending !== null}>
                {pending === "score" ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
                Scorer via API
              </Button>
              <Button type="button" variant="secondary" onClick={createCase} disabled={pending !== null}>
                <ShieldAlert size={15} />
                Créer Fraud Case 360
              </Button>
              <Button type="button" variant="outline" onClick={exportEvidence} disabled={pending !== null}>
                {pending === "evidence" ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />}
                Générer evidence pack
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => loadScenario(scenario)}
                disabled={pending !== null}
              >
                <RotateCcw size={15} />
                Réinitialiser JSON
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Code2 size={18} className="text-[#2f6bff]" />
                <label htmlFor="risk-lab-transaction-json">
                  Transaction JSON éditable
                </label>
              </CardTitle>
              <Badge severity="neutral">POST /api/risk/score</Badge>
            </CardHeader>
            <CardContent>
              <textarea
                id="risk-lab-transaction-json"
                value={jsonInput}
                onChange={(event) => setJsonInput(event.target.value)}
                rows={18}
                spellCheck={false}
                aria-describedby={error ? "risk-lab-json-error" : "risk-lab-json-help"}
                className="w-full rounded-md border border-[#e6ebf2] bg-[#08111f] p-4 font-mono text-xs leading-6 text-white outline-none focus:border-[#2f6bff] dark:border-white/10"
              />
              <p id="risk-lab-json-help" className="mt-2 text-xs leading-5 text-[#667085]">
                Utilisez uniquement des données synthétiques. Le JSON est envoyé à /api/risk/score.
              </p>
              {error ? (
                <div id="risk-lab-json-error" role="alert" className="mt-3 rounded-md border border-[#fff0f1] bg-[#fff0f1] p-3 text-sm text-[#b42318]">
                  {error}
                </div>
              ) : null}
            </CardContent>
          </Card>

          {result ? <ScoreResultPanel result={result} /> : null}
          {evidencePack ? <EvidenceResultPanel evidencePack={evidencePack} /> : null}
        </div>
      </section>
    </div>
  );
}

function ScoreResultPanel({ result }: { result: RiskScoreResult }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <CheckCircle2 size={18} className="text-[#027a48]" />
          Résultat moteur
        </CardTitle>
        <SeverityBadge value={result.level} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-4">
          <Fact label="Score" value={`${result.score}/100`} />
          <Fact label="Décision" value={result.decision} />
          <Fact label="Typologie" value={result.typology} />
          <Fact label="Version" value={result.modelVersion} />
        </div>
        <div className="grid gap-2">
          {result.reasonCodes.slice(0, 10).map((reasonCode) => (
            <div
              key={`${reasonCode.detector}-${reasonCode.code}`}
              className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-3 dark:border-white/10 dark:bg-white/[0.03]"
            >
              <div className="flex items-center justify-between gap-3">
                <code className="text-xs font-semibold text-[#2f6bff]">
                  {reasonCode.code}
                </code>
                <span className="font-mono text-xs text-[#667085]">
                  +{reasonCode.weight}
                </span>
              </div>
              <p className="mt-1 text-sm text-[#111827] dark:text-white">
                {reasonCode.label}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function EvidenceResultPanel({ evidencePack }: { evidencePack: EvidencePack }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileJson size={18} className="text-[#2f6bff]" />
          Evidence pack généré
        </CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="max-h-80 overflow-auto rounded-md bg-[#08111f] p-4 text-xs leading-6 text-white">
          {JSON.stringify(evidencePack, null, 2)}
        </pre>
      </CardContent>
    </Card>
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
