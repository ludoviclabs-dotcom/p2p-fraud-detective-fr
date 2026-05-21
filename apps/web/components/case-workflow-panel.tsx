"use client";

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

const selectStyle: React.CSSProperties = {
  height: 38,
  width: "100%",
  background: "var(--bg)",
  border: "1px solid var(--border)",
  padding: "0 12px",
  fontFamily: "var(--font-mono)",
  fontSize: 12,
  color: "var(--fg)",
  outline: "none",
};

const textareaStyle: React.CSSProperties = {
  width: "100%",
  minHeight: 112,
  background: "var(--bg)",
  border: "1px solid var(--border)",
  padding: "10px 12px",
  fontFamily: "var(--font-mono)",
  fontSize: 12,
  color: "var(--fg)",
  lineHeight: 1.6,
  outline: "none",
  resize: "vertical",
};

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
  void statusTone; // retained for logic parity

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
    <div className="fx-panel">
      <div className="fx-panel-head">
        <div>
          <h2>Qualification audit</h2>
        </div>
        <span
          className="fx-mono"
          style={{
            fontSize: 10,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--muted)",
            border: "1px solid var(--border-strong)",
            padding: "2px 8px",
          }}
        >
          {getCaseStatusLabel(record.status)}
        </span>
      </div>

      <div className="fx-panel-body space-y-4">
        {/* Case identity strip */}
        <div
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            padding: "12px 14px",
          }}
        >
          <div className="flex items-start gap-2">
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--risk)" }}>
              §
            </span>
            <div>
              <div
                className="fx-mono"
                style={{ fontSize: 13, color: "var(--fg)", fontWeight: 600 }}
              >
                {record.invoiceId}
              </div>
              <div
                className="fx-mono"
                style={{ marginTop: 4, fontSize: 11, color: "var(--muted)" }}
              >
                {record.vendorName} &mdash; {record.riskScore}/100 &mdash;{" "}
                {formatEuro(record.exposureEur)}
              </div>
            </div>
          </div>
        </div>

        {/* Status + Decision */}
        <div className={compact ? "grid gap-3" : "grid gap-3 md:grid-cols-2"}>
          <label className="grid gap-1">
            <span className="fx-eyebrow">Statut</span>
            <select
              value={record.status}
              onChange={(event) =>
                updateRecord({ status: event.target.value as CaseStatus })
              }
              style={selectStyle}
            >
              {CASE_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-1">
            <span className="fx-eyebrow">Decision</span>
            <select
              value={record.decision}
              onChange={(event) =>
                updateRecord({ decision: event.target.value as CaseDecision })
              }
              style={selectStyle}
            >
              {CASE_DECISION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {/* Assignee */}
        <label className="grid gap-1">
          <span className="fx-eyebrow">Responsable</span>
          <input
            value={record.assignee}
            onChange={(event) => updateRecord({ assignee: event.target.value })}
            placeholder="Equipe audit, acheteur, controle interne..."
            className="fx-input"
          />
        </label>

        {/* Note */}
        <label className="grid gap-1">
          <span className="fx-eyebrow">Note d&apos;investigation</span>
          <textarea
            value={record.note}
            onChange={(event) => updateRecord({ note: event.target.value })}
            placeholder="Decision, pieces verifiees, actions attendues..."
            style={textareaStyle}
          />
        </label>

        {/* Actions row */}
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={saveRecord} disabled={isSaving} className="fx-btn sm">
            ✓ {isSaving ? "Sauvegarde..." : "Enregistrer"}
          </button>
          <button type="button" onClick={exportOne} className="fx-btn-ghost sm">
            ↓ CSV
          </button>
          <span
            className="fx-mono"
            style={{ fontSize: 10, color: "var(--muted)", letterSpacing: "0.04em" }}
          >
            {savedAt
              ? `Sauve le ${new Intl.DateTimeFormat("fr-FR", {
                  dateStyle: "short",
                  timeStyle: "short",
                }).format(new Date(savedAt))}`
              : "Workflow exportable depuis le navigateur."}
          </span>
        </div>

        {/* Bridge message */}
        {bridgeMessage ? (
          <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.6 }}>
            {bridgeMessage}
          </p>
        ) : null}

        {/* Status summary */}
        <p className="fx-mono" style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.6 }}>
          Statut actuel: {getCaseStatusLabel(record.status)} &mdash; Decision:{" "}
          {getCaseDecisionLabel(record.decision)} &mdash; Mode: {bridgeMode}
        </p>
      </div>
    </div>
  );
}
