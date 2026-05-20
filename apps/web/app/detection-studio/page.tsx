"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  Binary,
  FileScan,
  Gauge,
  GitBranch,
  Landmark,
  MonitorSmartphone,
  QrCode,
  SearchCheck,
  ShieldAlert,
} from "lucide-react";
import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { scoreTransaction } from "@/lib/risk/scoreEngine";
import type { DetectorId, DetectorScore } from "@/types/risk";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, SeverityBadge } from "@/components/ui/badge";

const MODULES: {
  id: DetectorId;
  title: string;
  status: "active" | "demo" | "mock";
  dataUsed: string;
  icon: typeof Gauge;
}[] = [
  {
    id: "beneficiaryTrust",
    title: "Beneficiary / IBAN Trust Check",
    status: "active",
    dataUsed: "Nom bénéficiaire, IBAN, historique, pays, changement RIB.",
    icon: Landmark,
  },
  {
    id: "scamNarrative",
    title: "APP Fraud & Scam Narrative Detector",
    status: "active",
    dataUsed: "Texte narratif, urgence, autorité, secret, investissement.",
    icon: SearchCheck,
  },
  {
    id: "velocity",
    title: "Velocity Checks",
    status: "active",
    dataUsed: "Montant, 24h, seuil, instant payment, fractionnement.",
    icon: Activity,
  },
  {
    id: "qrRisk",
    title: "QR Code Fraud Analyzer",
    status: "demo",
    dataUsed: "Payload textuel, URL, IBAN extrait, domaine attendu.",
    icon: QrCode,
  },
  {
    id: "deviceSession",
    title: "Device & Session Risk Lite",
    status: "demo",
    dataUsed: "Nouvel appareil, pays IP, remote access, impossible travel.",
    icon: MonitorSmartphone,
  },
  {
    id: "graphRisk",
    title: "Mule Account / Fraud Graph",
    status: "demo",
    dataUsed: "Clusters, IBAN partagé, appareils, payeurs reliés.",
    icon: GitBranch,
  },
  {
    id: "documentRibRisk",
    title: "Document / RIB / Invoice Fraud Check",
    status: "demo",
    dataUsed: "Facture, RIB, IBAN attendu, nom fournisseur, format.",
    icon: FileScan,
  },
  {
    id: "sanctionsRisk",
    title: "Sanctions / PEP / AML Screening",
    status: "mock",
    dataUsed: "Match sanctions/PEP synthétique, pays sensible.",
    icon: ShieldAlert,
  },
];

export default function DetectionStudioPage() {
  const [scenarioId, setScenarioId] = useState(RISK_SCENARIOS[0]?.id ?? "");
  const [tested, setTested] = useState<DetectorId>("beneficiaryTrust");
  const scenario = RISK_SCENARIOS.find((item) => item.id === scenarioId) ?? RISK_SCENARIOS[0];
  const result = useMemo(() => scoreTransaction(scenario.transaction), [scenario]);
  const selectedDetector = result.detectorScores.find((item) => item.detector === tested);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#667085]">
            P2P Fraud Detection Workbench
          </p>
          <h1 className="mt-2 text-3xl font-bold text-[#08111f] dark:text-white">
            Detection Studio
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#667085]">
            Modules de détection explicables pour paiements P2P, virements SEPA, QR code,
            fournisseurs et conformité. Données 100% synthétiques.
          </p>
        </div>
        <Link
          href="/p2p-scenarios"
          className="inline-flex h-10 items-center gap-2 rounded-md bg-[#2f6bff] px-4 text-sm font-semibold text-white"
        >
          Lancer les scénarios
          <ArrowRight size={15} />
        </Link>
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-[0.72fr_1.28fr]">
        <Card>
          <CardHeader>
            <CardTitle>Transaction de test</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#667085]">
              Scénario
            </label>
            <select
              value={scenarioId}
              onChange={(event) => setScenarioId(event.target.value)}
              className="h-10 w-full rounded-md border border-[#e6ebf2] bg-white px-3 text-sm dark:border-white/10 dark:bg-white/[0.04]"
            >
              {RISK_SCENARIOS.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title}
                </option>
              ))}
            </select>

            <div className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-4 dark:border-white/10 dark:bg-white/[0.03]">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-wider text-[#667085]">
                    Score global
                  </div>
                  <div className="mt-1 text-3xl font-bold text-[#08111f] dark:text-white">
                    {result.score}/100
                  </div>
                </div>
                <SeverityBadge value={result.level} />
              </div>
              <div className="mt-3 text-sm text-[#667085]">{result.typology}</div>
              <div className="mt-2 text-sm font-semibold text-[#111827] dark:text-white">
                {result.decision}
              </div>
            </div>

            <div className="rounded-md bg-[#08111f] p-4 text-white">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Binary size={16} className="text-[#f5a524]" />
                Décision humaine finale
              </div>
              <p className="mt-2 text-sm leading-6 text-white/65">
                Le moteur est un démonstrateur explicable. Il documente les signaux, mais
                ne prend aucune décision bancaire réelle.
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          {MODULES.map((module) => {
            const score = result.detectorScores.find((item) => item.detector === module.id);
            return (
              <ModuleCard
                key={module.id}
                module={module}
                score={score}
                active={tested === module.id}
                onTest={() => setTested(module.id)}
              />
            );
          })}
        </div>
      </section>

      {selectedDetector ? (
        <Card className="mt-6">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Résultat du test module</CardTitle>
            <Badge severity={selectedDetector.score > 0 ? "high" : "low"}>
              {selectedDetector.status}
            </Badge>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <div className="text-sm font-semibold text-[#111827] dark:text-white">
                {selectedDetector.label}
              </div>
              <div className="mt-2 text-4xl font-bold text-[#2f6bff]">
                {selectedDetector.score}/{selectedDetector.maxScore}
              </div>
              <p className="mt-3 text-sm leading-6 text-[#667085]">
                {selectedDetector.explanation}
              </p>
            </div>
            <div className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-4 dark:border-white/10 dark:bg-white/[0.03]">
              <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#667085]">
                Reason codes générés
              </div>
              {selectedDetector.reasonCodes.length ? (
                <div className="space-y-2">
                  {selectedDetector.reasonCodes.map((reasonCode) => (
                    <div
                      key={reasonCode.code}
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
              ) : (
                <div className="text-sm text-[#667085]">
                  Aucun reason code pour ce module sur ce scénario.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function ModuleCard({
  module,
  score,
  active,
  onTest,
}: {
  module: (typeof MODULES)[number];
  score?: DetectorScore;
  active: boolean;
  onTest: () => void;
}) {
  const Icon = module.icon;
  return (
    <Card className={active ? "border-[#2f6bff]" : undefined}>
      <CardContent className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-[#eaf1ff] text-[#2f6bff]">
            <Icon size={20} />
          </div>
          <Badge
            severity={
              module.status === "active"
                ? "low"
                : module.status === "demo"
                  ? "medium"
                  : "neutral"
            }
          >
            {module.status}
          </Badge>
        </div>
        <div>
          <h2 className="text-base font-semibold text-[#111827] dark:text-white">
            {module.title}
          </h2>
          <p className="mt-2 text-sm leading-6 text-[#667085]">{module.dataUsed}</p>
        </div>
        <div className="flex items-center justify-between gap-3 rounded-md bg-[#f7f9fc] p-3 dark:bg-white/[0.03]">
          <div>
            <div className="text-xs uppercase tracking-wider text-[#667085]">
              Score partiel
            </div>
            <div className="mt-1 font-mono text-lg font-semibold text-[#08111f] dark:text-white">
              {score ? `${score.score}/${score.maxScore}` : "n/a"}
            </div>
          </div>
          <BadgeCheck size={18} className="text-[#12a876]" />
        </div>
        <Button type="button" variant={active ? "primary" : "outline"} onClick={onTest}>
          Tester le module
        </Button>
      </CardContent>
    </Card>
  );
}
