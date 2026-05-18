import type { Severity } from "@/types/p2p";

export const CASE_WORKFLOW_STORAGE_KEY = "p2p.caseWorkflow.v1";
export const CASE_WORKFLOW_ACTOR = "web.audit";

export type CaseStatus =
  | "new"
  | "reviewing"
  | "needs_evidence"
  | "escalated"
  | "cleared";

export type CaseDecision =
  | "pending"
  | "monitor"
  | "request_documents"
  | "block_payment"
  | "close_false_positive";

export type CaseWorkflowSource = "local" | "fastapi" | "hybrid";

export interface CaseWorkflowContext {
  id: string;
  findingId: string;
  invoiceId: string;
  vendorId: string;
  vendorName: string;
  ruleId: string;
  signal: string;
  severity: Severity;
  exposureEur: number;
  riskScore: number;
}

export interface CaseWorkflowRecord extends CaseWorkflowContext {
  status: CaseStatus;
  decision: CaseDecision;
  assignee: string;
  note: string;
  createdAt: string;
  updatedAt: string;
  backendCaseId?: string | null;
  source?: CaseWorkflowSource;
}

export const CASE_STATUS_OPTIONS: Array<{
  value: CaseStatus;
  label: string;
  tone: string;
}> = [
  { value: "new", label: "Nouveau", tone: "bg-[#eef3fb] text-[#1f3a6e]" },
  { value: "reviewing", label: "En revue", tone: "bg-[#fff7e8] text-[#9a5b00]" },
  {
    value: "needs_evidence",
    label: "Piece requise",
    tone: "bg-[#fff7e8] text-[#9a5b00]",
  },
  { value: "escalated", label: "Escalade", tone: "bg-[#fff0f1] text-[#a23e48]" },
  { value: "cleared", label: "Cloture", tone: "bg-[#e8f8f1] text-[#22754c]" },
];

export const CASE_DECISION_OPTIONS: Array<{
  value: CaseDecision;
  label: string;
}> = [
  { value: "pending", label: "Decision en attente" },
  { value: "monitor", label: "Surveiller" },
  { value: "request_documents", label: "Demander des pieces" },
  { value: "block_payment", label: "Bloquer paiement" },
  { value: "close_false_positive", label: "Clore faux positif" },
];

export function createDefaultCaseWorkflowRecord(
  context: CaseWorkflowContext,
): CaseWorkflowRecord {
  const now = new Date().toISOString();

  return {
    ...context,
    status: "new",
    decision: "pending",
    assignee: "",
    note: "",
    createdAt: now,
    updatedAt: now,
    backendCaseId: null,
    source: "local",
  };
}

export function getCaseStatusLabel(status: CaseStatus): string {
  return CASE_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
}

export function getCaseDecisionLabel(decision: CaseDecision): string {
  return (
    CASE_DECISION_OPTIONS.find((option) => option.value === decision)?.label ?? decision
  );
}

export function exportCaseWorkflowCsv(records: CaseWorkflowRecord[]): string {
  const headers = [
    "case_id",
    "backend_case_id",
    "invoice_id",
    "finding_id",
    "vendor_id",
    "vendor_name",
    "rule_id",
    "signal",
    "severity",
    "risk_score",
    "exposure_eur",
    "status",
    "decision",
    "assignee",
    "note",
    "created_at",
    "updated_at",
  ];

  const rows = records.map((record) =>
    [
      record.id,
      record.backendCaseId ?? "",
      record.invoiceId,
      record.findingId,
      record.vendorId,
      record.vendorName,
      record.ruleId,
      record.signal,
      record.severity,
      String(record.riskScore),
      String(record.exposureEur),
      getCaseStatusLabel(record.status),
      getCaseDecisionLabel(record.decision),
      record.assignee,
      record.note,
      record.createdAt,
      record.updatedAt,
    ].map(toCsvCell),
  );

  return [headers, ...rows].map((row) => row.join(",")).join("\n");
}

function toCsvCell(value: string): string {
  const escaped = value.replaceAll('"', '""');
  return /[",\n\r]/.test(escaped) ? `"${escaped}"` : escaped;
}

export function readStoredCaseWorkflowRecords(): CaseWorkflowRecord[] {
  if (typeof window === "undefined") return [];

  try {
    const raw = window.localStorage.getItem(CASE_WORKFLOW_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function writeStoredCaseWorkflowRecords(records: CaseWorkflowRecord[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(CASE_WORKFLOW_STORAGE_KEY, JSON.stringify(records));
}
