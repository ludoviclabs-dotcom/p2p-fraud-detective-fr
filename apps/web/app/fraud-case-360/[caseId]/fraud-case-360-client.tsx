"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  FileClock,
  FileJson,
  Landmark,
  MessageSquareWarning,
  Network,
  QrCode,
  Smartphone,
} from "lucide-react";
import type { EvidencePack, RiskScenario, RiskScoreResult } from "@/types/risk";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { formatEur } from "@/lib/utils";

type AnalystAction =
  | "assign"
  | "review"
  | "escalate"
  | "false_positive"
  | "block_recommended"
  | "export_evidence";

const ACTION_LABELS: Record<AnalystAction, string> = {
  assign: "Assigner",
  review: "Mettre en revue",
  escalate: "Escalader",
  false_positive: "Marquer faux positif",
  block_recommended: "Recommander blocage",
  export_evidence: "Exporter evidence pack",
};

export function FraudCase360Client({
  scenario,
  score,
}: {
  scenario: RiskScenario;
  score: RiskScoreResult;
}) {
  const storageKey = `p2pfd.case360.${scenario.caseId}`;
  const [assignee, setAssignee] = useState("analyst-demo@p2pfd.local");
  const [notes, setNotes] = useState("");
  const [auditTrail, setAuditTrail] = useState<
    { at: string; actor: string; action: string; detail: string }[]
  >([]);
  const [evidence, setEvidence] = useState<EvidencePack | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);

  useEffect(() => {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as {
        assignee?: string;
        notes?: string;
        auditTrail?: { at: string; actor: string; action: string; detail: string }[];
      };
      if (parsed.assignee) setAssignee(parsed.assignee);
      if (parsed.notes) setNotes(parsed.notes);
      if (Array.isArray(parsed.auditTrail)) setAuditTrail(parsed.auditTrail);
    } catch {
      window.localStorage.removeItem(storageKey);
    }
  }, [storageKey]);

  useEffect(() => {
    window.localStorage.setItem(
      storageKey,
      JSON.stringify({ assignee, notes, auditTrail }),
    );
  }, [assignee, auditTrail, notes, storageKey]);

  const timeline = useMemo(
    () => [
      {
        at: scenario.transaction.createdAt,
        actor: "payment-workbench",
        event: "Transaction chargée",
        detail: scenario.description,
      },
      {
        at: score.generatedAt,
        actor: score.modelVersion,
        event: "Score calculé",
        detail: `${score.score}/100 · ${score.level} · ${score.decision}`,
      },
      ...auditTrail.map((item) => ({
        at: item.at,
        actor: item.actor,
        event: item.action,
        detail: item.detail,
      })),
    ],
    [auditTrail, scenario.description, scenario.transaction.createdAt, score],
  );

  function record(action: AnalystAction) {
    const entry = {
      at: new Date().toISOString(),
      actor: assignee || "demo-analyst",
      action,
      detail: ACTION_LABELS[action],
    };
    setAuditTrail((previous) => [entry, ...previous]);
    return entry;
  }

  async function exportEvidence() {
    const exportEntry = record("export_evidence");
    setExportStatus("Génération de l'evidence pack en cours...");
    const response = await fetch("/api/evidence/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId: scenario.caseId,
        transaction: scenario.transaction,
        analystNotes: notes,
        auditTrail: [exportEntry, ...auditTrail],
      }),
    });
    if (!response.ok) {
      setExportStatus("Export impossible pour le moment.");
      return;
    }
    const payload = (await response.json()) as {
      evidencePack: EvidencePack;
      printableHtml: string;
    };
    setEvidence(payload.evidencePack);

    const blob = new Blob([JSON.stringify(payload.evidencePack, null, 2)], {
      type: "application/json",
    });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${scenario.caseId}-evidence-pack.json`;
    anchor.click();
    window.URL.revokeObjectURL(url);
    setExportStatus(`Evidence pack JSON généré pour ${scenario.caseId}.`);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Link
        href="/p2p-scenarios"
        className="inline-flex items-center gap-2 text-sm font-semibold text-[#2f6bff]"
      >
        <ArrowLeft size={16} />
        Retour aux scénarios
      </Link>

      <section className="mt-6 grid gap-5 lg:grid-cols-[1fr_360px]">
        <Card className="overflow-hidden">
          <CardHeader className="bg-[#08111f] text-white">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-white/45">
                  Fraud Case 360
                </div>
                <h1 className="mt-2 text-3xl font-bold">{scenario.title}</h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-white/65">
                  {scenario.businessContext}
                </p>
              </div>
              <SeverityBadge value={score.level} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-4">
              <Kpi label="Score" value={`${score.score}/100`} />
              <Kpi label="Décision" value={score.decision} />
              <Kpi label="Typologie" value={score.typology} />
              <Kpi label="Montant" value={formatEur(scenario.transaction.amount)} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Analyst Action Bar</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <label htmlFor="case-360-assignee" className="block text-xs font-semibold uppercase tracking-wider text-[#667085]">
              Assigné à
            </label>
            <input
              id="case-360-assignee"
              value={assignee}
              onChange={(event) => setAssignee(event.target.value)}
              className="h-10 w-full rounded-md border border-[#e6ebf2] bg-white px-3 text-sm dark:border-white/10 dark:bg-white/[0.04]"
            />
            <div className="grid grid-cols-2 gap-2">
              <Button type="button" size="sm" variant="outline" onClick={() => record("assign")}>
                Assigner
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => record("review")}>
                Revue
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => record("escalate")}>
                Escalader
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => record("false_positive")}
              >
                Faux positif
              </Button>
            </div>
            <Button type="button" className="w-full" onClick={() => record("block_recommended")}>
              Recommander blocage
            </Button>
            <Button type="button" variant="secondary" className="w-full" onClick={exportEvidence}>
              <Download size={15} />
              Exporter evidence pack
            </Button>
            {exportStatus ? (
              <div role="status" className="rounded-md bg-[#eaf1ff] p-3 text-sm font-medium text-[#111827]">
                {exportStatus}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Transaction details</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-3 sm:grid-cols-2">
              <Detail label="Transaction" value={scenario.transaction.transactionId} />
              <Detail label="Rail" value={scenario.transaction.rail} />
              <Detail label="Payeur" value={scenario.transaction.payer.displayName} />
              <Detail label="Bénéficiaire" value={scenario.transaction.beneficiary.name} />
              <Detail label="IBAN" value={scenario.transaction.beneficiary.iban} />
              <Detail label="Canal" value={scenario.transaction.channel ?? "n/a"} />
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Timeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {timeline.map((item) => (
              <div
                key={`${item.at}-${item.event}-${item.detail}`}
                className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-3 dark:border-white/10 dark:bg-white/[0.03]"
              >
                <div className="flex items-center gap-2 text-xs font-semibold text-[#667085]">
                  <FileClock size={14} />
                  {new Date(item.at).toLocaleString("fr-FR")} · {item.actor}
                </div>
                <div className="mt-1 text-sm font-semibold text-[#111827] dark:text-white">
                  {item.event}
                </div>
                <p className="mt-1 text-sm leading-6 text-[#667085]">{item.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-2">
        <ReasonCodesPanel score={score} />
        <BeneficiaryTrustPanel score={score} />
        <DetectorPanel
          icon={MessageSquareWarning}
          title="Scam Narrative Panel"
          detector="scamNarrative"
          score={score}
        />
        <DetectorPanel icon={CheckCircle2} title="Velocity Signals Panel" detector="velocity" score={score} />
        <DetectorPanel icon={Smartphone} title="Device Risk Panel" detector="deviceSession" score={score} />
        {scenario.transaction.qr ? (
          <DetectorPanel icon={QrCode} title="QR Analyzer Panel" detector="qrRisk" score={score} />
        ) : null}
        <FraudGraphPanel scenario={scenario} />
        <EvidencePanel evidence={evidence} notes={notes} setNotes={setNotes} />
      </section>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-3 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-[#667085]">
        {label}
      </div>
      <div className="mt-1 truncate font-mono text-sm font-semibold text-[#111827] dark:text-white">
        {value}
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] font-semibold uppercase tracking-wider text-[#667085]">
        {label}
      </dt>
      <dd className="mt-1 break-words font-mono text-sm text-[#111827] dark:text-white">
        {value}
      </dd>
    </div>
  );
}

function ReasonCodesPanel({ score }: { score: RiskScoreResult }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Reason codes cliquables</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {score.reasonCodes.map((reasonCode) => (
          <details
            key={`${reasonCode.detector}-${reasonCode.code}`}
            className="rounded-md border border-[#e6ebf2] bg-white p-3 dark:border-white/10 dark:bg-white/[0.04]"
          >
            <summary className="cursor-pointer list-none">
              <span className="font-mono text-xs font-semibold text-[#2f6bff]">
                {reasonCode.code}
              </span>
              <span className="ml-2 text-sm font-semibold text-[#111827] dark:text-white">
                {reasonCode.label}
              </span>
            </summary>
            <p className="mt-2 text-sm leading-6 text-[#667085]">
              {reasonCode.description}
            </p>
          </details>
        ))}
      </CardContent>
    </Card>
  );
}

function BeneficiaryTrustPanel({ score }: { score: RiskScoreResult }) {
  return (
    <DetectorPanel
      icon={Landmark}
      title="Beneficiary Trust Card"
      detector="beneficiaryTrust"
      score={score}
    />
  );
}

function DetectorPanel({
  icon: Icon,
  title,
  detector,
  score,
}: {
  icon: typeof Landmark;
  title: string;
  detector: RiskScoreResult["detectorScores"][number]["detector"];
  score: RiskScoreResult;
}) {
  const detectorScore = score.detectorScores.find((item) => item.detector === detector);
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Icon size={18} className="text-[#2f6bff]" />
          {title}
        </CardTitle>
        {detectorScore ? <Badge>{detectorScore.status}</Badge> : null}
      </CardHeader>
      <CardContent>
        {detectorScore ? (
          <>
            <div className="font-mono text-2xl font-bold text-[#08111f] dark:text-white">
              {detectorScore.score}/{detectorScore.maxScore}
            </div>
            <p className="mt-2 text-sm leading-6 text-[#667085]">
              {detectorScore.explanation}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {detectorScore.reasonCodes.map((item) => (
                <Badge key={item.code} severity={item.severity.toLowerCase() as "critical" | "high" | "medium" | "low"}>
                  {item.code}
                </Badge>
              ))}
              {!detectorScore.reasonCodes.length ? <Badge severity="low">Aucun signal</Badge> : null}
            </div>
          </>
        ) : (
          <div className="text-sm text-[#667085]">Module non exécuté.</div>
        )}
      </CardContent>
    </Card>
  );
}

function FraudGraphPanel({ scenario }: { scenario: RiskScenario }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network size={18} className="text-[#2f6bff]" />
          Fraud Graph Panel
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-3 text-sm text-[#667085]">
          {scenario.graphSummary.suspiciousPath}
        </div>
        <div className="grid gap-2">
          {scenario.graphSummary.nodes.map((node) => (
            <div
              key={node.id}
              className="flex items-center justify-between rounded-md border border-[#e6ebf2] bg-[#f7f9fc] p-3 dark:border-white/10 dark:bg-white/[0.03]"
            >
              <div>
                <div className="text-sm font-semibold text-[#111827] dark:text-white">
                  {node.label}
                </div>
                <div className="text-xs text-[#667085]">{node.kind}</div>
              </div>
              {node.risk ? <SeverityBadge value={node.risk} /> : null}
            </div>
          ))}
        </div>
        <div className="mt-3 rounded-md bg-[#08111f] p-3 text-sm text-white">
          Score graphe: {scenario.graphSummary.graphScore}/100 · Clusters:{" "}
          {scenario.graphSummary.clusters.join(", ")}
        </div>
      </CardContent>
    </Card>
  );
}

function EvidencePanel({
  evidence,
  notes,
  setNotes,
}: {
  evidence: EvidencePack | null;
  notes: string;
  setNotes: (value: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileJson size={18} className="text-[#2f6bff]" />
          Evidence Pack Panel
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <label htmlFor="case-360-analyst-notes" className="block text-xs font-semibold uppercase tracking-wider text-[#667085]">
          Notes analyste
        </label>
        <textarea
          id="case-360-analyst-notes"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={5}
          placeholder="Notes analyste synthétiques..."
          className="w-full rounded-md border border-[#e6ebf2] bg-white p-3 text-sm dark:border-white/10 dark:bg-white/[0.04]"
        />
        {evidence ? (
          <pre className="max-h-72 overflow-auto rounded-md bg-[#08111f] p-4 text-xs leading-6 text-white">
            {JSON.stringify(evidence, null, 2)}
          </pre>
        ) : (
          <p className="text-sm leading-6 text-[#667085]">
            Exportez le dossier pour générer un JSON incluant transaction, score,
            reason codes, graphe, timeline, notes et audit trail.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
