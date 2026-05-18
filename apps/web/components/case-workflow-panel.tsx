"use client";

import { Download, Save, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  CASE_DECISION_OPTIONS,
  CASE_STATUS_OPTIONS,
  createDefaultCaseWorkflowRecord,
  exportCaseWorkflowCsv,
  getCaseDecisionLabel,
  getCaseStatusLabel,
  type CaseDecision,
  type CaseStatus,
  type CaseWorkflowContext,
  type CaseWorkflowRecord,
} from "@/lib/case-workflow";
import {
  isCaseWorkflowApiEnabled,
  loadCaseWorkflowRecord,
  saveCaseWorkflowRecord,
} from "@/lib/case-workflow-bridge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatEuro } from "@/lib/p2p-demo-format";

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function CaseWorkflowPanel({
  context,
  compact = false,
}: {
  context: CaseWorkflowContext;
  compact?: boolean;
}) {
  const [record, setRecord] = useState<CaseWorkflowRecord>(() =>
    createDefaultCaseWorkflowRecord(context),
  );
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [bridgeMode, setBridgeMode] = useState<"local" | "fastapi" | "hybrid">("local");
  const [bridgeMessage, setBridgeMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        const loaded = await loadCaseWorkflowRecord(context);
        if (cancelled) return;
        setRecord(loaded.record);
        setSavedAt(loaded.record.updatedAt ?? null);
        setBridgeMode(loaded.mode);
        setBridgeMessage(
          loaded.mode === "fastapi"
            ? "Case lie au backend FastAPI."
            : loaded.mode === "hybrid"
              ? "Mode hybride : sauvegarde locale + synchronisation FastAPI."
              : isCaseWorkflowApiEnabled()
                ? "Bridge FastAPI indisponible pour ce case."
                : "Mode demo local.",
        );
      } catch {
        if (cancelled) return;
        setRecord(createDefaultCaseWorkflowRecord(context));
        setSavedAt(null);
        setBridgeMode("local");
        setBridgeMessage("Mode demo local.");
      }
    };

    run();
    return () => {
      cancelled = true;
    };
  }, [context]);

  const statusTone = useMemo(
    () =>
      CASE_STATUS_OPTIONS.find((option) => option.value === record.status)?.tone ??
      "bg-[#eef3fb] text-[#1f3a6e]",
    [record.status],
  );

  const updateRecord = (
    patch: Partial<
      Pick<CaseWorkflowRecord, "status" | "decision" | "assignee" | "note">
    >,
  ) => {
    setRecord((current) => ({ ...current, ...patch }));
  };

  const saveRecord = async () => {
    setIsSaving(true);
    setBridgeMessage(null);
    try {
      const saved = await saveCaseWorkflowRecord(context, record);
      setRecord(saved.record);
      setSavedAt(saved.record.updatedAt);
      setBridgeMode(saved.mode);
      setBridgeMessage(
        saved.warning ??
          (saved.mode === "hybrid"
            ? "Sauvegarde locale et synchronisation FastAPI effectuees."
            : "Sauvegarde locale effectuee."),
      );
      window.dispatchEvent(new Event("p2p-case-workflow-updated"));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erreur de sauvegarde.";
      setBridgeMessage(message);
    } finally {
      setIsSaving(false);
    }
  };

  const exportOne = () => {
    downloadText(
      `${record.id}_workflow.csv`,
      exportCaseWorkflowCsv([record]),
      "text/csv;charset=utf-8",
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle>Qualification audit</CardTitle>
          <span className={`rounded px-2 py-1 text-xs font-semibold ${statusTone}`}>
            {getCaseStatusLabel(record.status)}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border border-[#e6ebf2] bg-[#f6f7fb] p-3 text-sm">
          <div className="flex items-start gap-2">
            <ShieldCheck aria-hidden className="mt-0.5 h-4 w-4 text-[#1f3a6e]" />
            <div>
              <div className="font-semibold text-[#141927]">{record.invoiceId}</div>
              <div className="mt-1 text-xs leading-5 text-[#5a6478]">
                {record.vendorName} - {record.riskScore}/100 -{" "}
                {formatEuro(record.exposureEur)}
              </div>
            </div>
          </div>
        </div>

        <div className={compact ? "grid gap-3" : "grid gap-3 md:grid-cols-2"}>
          <label className="grid gap-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#5a6478]">
            Statut
            <select
              value={record.status}
              onChange={(event) =>
                updateRecord({ status: event.target.value as CaseStatus })
              }
              className="h-10 rounded-md border border-[#e1e5ee] bg-white px-3 text-sm font-normal normal-case tracking-normal text-[#141927]"
            >
              {CASE_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#5a6478]">
            Decision
            <select
              value={record.decision}
              onChange={(event) =>
                updateRecord({ decision: event.target.value as CaseDecision })
              }
              className="h-10 rounded-md border border-[#e1e5ee] bg-white px-3 text-sm font-normal normal-case tracking-normal text-[#141927]"
            >
              {CASE_DECISION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="grid gap-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#5a6478]">
          Responsable
          <input
            value={record.assignee}
            onChange={(event) => updateRecord({ assignee: event.target.value })}
            placeholder="Equipe audit, acheteur, controle interne..."
            className="h-10 rounded-md border border-[#e1e5ee] bg-white px-3 text-sm font-normal normal-case tracking-normal text-[#141927]"
          />
        </label>

        <label className="grid gap-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#5a6478]">
          Note d'investigation
          <textarea
            value={record.note}
            onChange={(event) => updateRecord({ note: event.target.value })}
            placeholder="Decision, pieces verifiees, actions attendues..."
            className="min-h-28 rounded-md border border-[#e1e5ee] bg-white px-3 py-2 text-sm font-normal normal-case leading-6 tracking-normal text-[#141927]"
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="button" onClick={saveRecord} disabled={isSaving}>
            <Save aria-hidden className="h-4 w-4" />
            {isSaving ? "Sauvegarde..." : "Enregistrer"}
          </Button>
          <Button type="button" variant="outline" onClick={exportOne}>
            <Download aria-hidden className="h-4 w-4" />
            CSV
          </Button>
          <span className="text-xs text-[#5a6478]">
            {savedAt
              ? `Sauve le ${new Intl.DateTimeFormat("fr-FR", {
                  dateStyle: "short",
                  timeStyle: "short",
                }).format(new Date(savedAt))}`
              : "Workflow exportable depuis le navigateur."}
          </span>
        </div>

        {bridgeMessage ? (
          <p className="text-xs leading-5 text-[#5a6478]">{bridgeMessage}</p>
        ) : null}

        <p className="text-xs leading-5 text-[#5a6478]">
          Statut actuel: {getCaseStatusLabel(record.status)} - Decision:{" "}
          {getCaseDecisionLabel(record.decision)} - Mode: {bridgeMode}
        </p>
      </CardContent>
    </Card>
  );
}
