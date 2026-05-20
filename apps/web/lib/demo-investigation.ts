import { createHash } from "node:crypto";

import type {
  AuditEntryOut,
  AuditPage,
  AuditVerifyResult,
  BulkResult,
  Schemas,
} from "@p2pfd/shared-types";

import { getP2PDataset } from "@/data/get-dataset";
import { getSignalLabel, SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";
import type { FindingSummary, P2PDemoDataset } from "@/types/p2p";

type CaseOutV1 = Schemas["CaseOutV1"];

export interface DemoUploadFinding {
  invoice_id: string;
  rule_id: string;
  severity: string;
  signal: string;
  detector?: string;
  evidence?: Record<string, unknown>;
}

export interface DemoUploadResponse {
  n_invoices: number;
  detectors_run: string[];
  findings: DemoUploadFinding[];
}

interface DemoCaseBlueprint {
  status: string;
  decision: string;
  assignee: string | null;
  titlePrefix: string;
  createdOffsetDays: number;
  closedOffsetDays?: number;
  closureReason?: string | null;
}

interface DemoInvestigationState {
  cases: CaseOutV1[];
  auditEntries: AuditEntryOut[];
}

const DEMO_PUBLIC_KEY_B64 = "ZGVtby1wdWJsaWMta2V5LWVkMjU1MTktcDJw";
const DEMO_CASE_BLUEPRINTS: DemoCaseBlueprint[] = [
  {
    status: "new",
    decision: "pending",
    assignee: null,
    titlePrefix: "Revue initiale",
    createdOffsetDays: 1,
  },
  {
    status: "triaged",
    decision: "request_documents",
    assignee: "alice.controleur",
    titlePrefix: "Pieces a demander",
    createdOffsetDays: 2,
  },
  {
    status: "in_progress",
    decision: "monitor",
    assignee: "bob.audit",
    titlePrefix: "Investigation en cours",
    createdOffsetDays: 3,
  },
  {
    status: "escalated",
    decision: "block_payment",
    assignee: "claire.compliance",
    titlePrefix: "Escalade compliance",
    createdOffsetDays: 4,
  },
  {
    status: "closed_false_positive",
    decision: "close_false_positive",
    assignee: "alice.controleur",
    titlePrefix: "Faux positif clos",
    createdOffsetDays: 6,
    closedOffsetDays: 2,
    closureReason:
      "Verification documentaire OK : fournisseurs distincts, pieces conformes.",
  },
  {
    status: "closed_confirmed",
    decision: "block_payment",
    assignee: "claire.compliance",
    titlePrefix: "Blocage confirme",
    createdOffsetDays: 8,
    closedOffsetDays: 1,
    closureReason: "Paiement bloque et fournisseur place en revue renforcee.",
  },
];

function isoAt(baseIso: string, deltaDays: number, deltaHours = 0): string {
  const date = new Date(baseIso);
  date.setUTCDate(date.getUTCDate() - deltaDays);
  date.setUTCHours(9 + deltaHours, 15, 0, 0);
  return date.toISOString();
}

function sortFindings(left: FindingSummary, right: FindingSummary): number {
  return (
    SEVERITY_ORDER[right.severity] - SEVERITY_ORDER[left.severity] ||
    right.riskScore - left.riskScore ||
    right.exposureEur - left.exposureEur ||
    left.invoiceId.localeCompare(right.invoiceId)
  );
}

function buildCaseId(index: number): string {
  return `CASE-2026-${String(index + 1).padStart(4, "0")}`;
}

function buildHash(seq: number, prevHash: string, payload: Record<string, unknown>): string {
  return createHash("sha256")
    .update(JSON.stringify({ seq, prevHash, payload }))
    .digest("hex");
}

function buildAuditEntry(
  seq: number,
  actor: string,
  kind: string,
  at: string,
  payload: Record<string, unknown>,
  prevHash: string,
): AuditEntryOut {
  const hash = buildHash(seq, prevHash, payload);
  return {
    seq,
    at,
    actor,
    kind,
    payload,
    prev_hash: prevHash,
    hash,
    signature: `demo-ed25519-${seq.toString(16)}`,
  };
}

function mapDetector(signal: string): string {
  switch (signal) {
    case "shared_iban_ring":
    case "vendor_cluster":
      return "graph_analytics";
    case "duplicate_exact":
    case "duplicate_fuzzy":
      return "duplicates";
    case "amount_just_under_threshold":
      return "thresholds";
    default:
      return "rules_engine";
  }
}

export function buildDemoCases(dataset: P2PDemoDataset = getP2PDataset()): CaseOutV1[] {
  return [...dataset.findings]
    .sort(sortFindings)
    .slice(0, DEMO_CASE_BLUEPRINTS.length)
    .map((finding, index) => {
      const blueprint = DEMO_CASE_BLUEPRINTS[index]!;
      const createdAt = isoAt(dataset.generatedAt, blueprint.createdOffsetDays, index);
      const closedAt =
        blueprint.closedOffsetDays !== undefined
          ? isoAt(dataset.generatedAt, blueprint.closedOffsetDays, index + 1)
          : null;

      return {
        case_id: buildCaseId(index),
        title: `${blueprint.titlePrefix} - ${finding.vendorName}`,
        severity: finding.severity,
        status: blueprint.status,
        vendor_id: finding.vendorId,
        invoice_id: finding.invoiceId,
        exposure_eur: finding.exposureEur,
        decision: blueprint.decision,
        assignee: blueprint.assignee,
        created_at: createdAt,
        closed_at: closedAt,
        closure_reason: blueprint.closureReason ?? null,
      };
    });
}

export function buildDemoAuditEntries(cases: CaseOutV1[]): AuditEntryOut[] {
  const entries: AuditEntryOut[] = [];
  let prevHash = "root";

  const push = (
    actor: string,
    kind: string,
    at: string,
    payload: Record<string, unknown>,
  ) => {
    const entry = buildAuditEntry(entries.length + 1, actor, kind, at, payload, prevHash);
    entries.push(entry);
    prevHash = entry.hash;
  };

  for (const [index, item] of cases.entries()) {
    const basePayload = {
      case_id: item.case_id,
      severity: item.severity,
      vendor_id: item.vendor_id,
      invoice_id: item.invoice_id,
      decision: item.decision,
      status: item.status,
    };
    push("auditeur.demo", "case_created", item.created_at, basePayload);

    if (item.assignee) {
      push(
        "auditeur.demo",
        "case_assigned",
        isoAt(item.created_at, 0, index + 1),
        { ...basePayload, assignee: item.assignee },
      );
    }

    if (item.status === "triaged" || item.status === "in_progress" || item.status === "escalated") {
      push(
        item.assignee ?? "auditeur.demo",
        "case_status_changed",
        isoAt(item.created_at, 0, index + 2),
        { ...basePayload, status: item.status },
      );
    }

    if (item.decision && item.decision !== "pending") {
      push(
        item.assignee ?? "auditeur.demo",
        "case_decision_recorded",
        isoAt(item.created_at, 0, index + 3),
        { ...basePayload, decision: item.decision },
      );
    }

    if (item.closed_at) {
      push(
        item.assignee ?? "auditeur.demo",
        "case_closed",
        item.closed_at,
        {
          ...basePayload,
          status: item.status,
          reason: item.closure_reason,
        },
      );
    }
  }

  return entries;
}

export function filterDemoCases(
  cases: CaseOutV1[],
  filters: {
    case_id?: string;
    invoice_id?: string;
    vendor_id?: string;
    status?: string;
    severity?: string;
    assignee?: string;
    limit?: number;
  } = {},
): CaseOutV1[] {
  const matches = cases.filter((item) => {
    if (filters.case_id && item.case_id !== filters.case_id) return false;
    if (filters.invoice_id && item.invoice_id !== filters.invoice_id) return false;
    if (filters.vendor_id && item.vendor_id !== filters.vendor_id) return false;
    if (filters.status && item.status !== filters.status) return false;
    if (filters.severity && item.severity !== filters.severity) return false;
    if (filters.assignee && item.assignee !== filters.assignee) return false;
    return true;
  });

  return matches.slice(0, Math.max(filters.limit ?? matches.length, 0));
}

export function buildDemoAuditPage(
  entries: AuditEntryOut[],
  cursor = 0,
  limit = 50,
): AuditPage {
  const ordered = [...entries].sort((left, right) => right.seq - left.seq);
  const safeCursor = Math.max(cursor, 0);
  const safeLimit = Math.max(limit, 1);
  const pageEntries = ordered.slice(safeCursor, safeCursor + safeLimit);
  const nextCursor =
    safeCursor + safeLimit < ordered.length ? safeCursor + safeLimit : null;

  return {
    entries: pageEntries,
    total: ordered.length,
    cursor_next: nextCursor,
  };
}

export function buildDemoAuditVerify(entries: AuditEntryOut[]): AuditVerifyResult {
  return {
    valid: true,
    invalid_seqs: [],
    n_total: entries.length,
    n_signed: entries.filter((entry) => Boolean(entry.signature)).length,
    public_key_b64: DEMO_PUBLIC_KEY_B64,
  };
}

export function buildDemoUploadResponse(
  dataset: P2PDemoDataset = getP2PDataset(),
): DemoUploadResponse {
  const findings = [...dataset.findings]
    .sort(sortFindings)
    .slice(0, 12)
    .map((finding) => ({
      invoice_id: finding.invoiceId,
      rule_id: finding.ruleId,
      severity: finding.severity,
      signal: getSignalLabel(finding.signal),
      detector: mapDetector(finding.signal),
      evidence: finding.evidence,
    }));

  return {
    n_invoices: dataset.metrics.invoiceCount,
    detectors_run: Array.from(
      new Set(findings.map((finding) => finding.detector ?? "rules_engine")),
    ),
    findings,
  };
}

function cloneCases(cases: CaseOutV1[]): CaseOutV1[] {
  return cases.map((item) => ({ ...item }));
}

function cloneAudit(entries: AuditEntryOut[]): AuditEntryOut[] {
  return entries.map((entry) => ({ ...entry, payload: { ...entry.payload } }));
}

function createDemoInvestigationState(): DemoInvestigationState {
  const cases = buildDemoCases();
  const auditEntries = buildDemoAuditEntries(cases);
  return {
    cases: cloneCases(cases),
    auditEntries: cloneAudit(auditEntries),
  };
}

declare global {
  var __p2pDemoInvestigationState: DemoInvestigationState | undefined;
}

export function getDemoInvestigationState(): DemoInvestigationState {
  if (!globalThis.__p2pDemoInvestigationState) {
    globalThis.__p2pDemoInvestigationState = createDemoInvestigationState();
  }
  return globalThis.__p2pDemoInvestigationState;
}

export function assignDemoCases(caseIds: string[], assignee: string, actor: string): BulkResult {
  const state = getDemoInvestigationState();
  const error_case_ids: string[] = [];
  let n_ok = 0;

  for (const caseId of caseIds) {
    const target = state.cases.find((item) => item.case_id === caseId);
    if (!target) {
      error_case_ids.push(caseId);
      continue;
    }

    target.assignee = assignee;
    if (target.status === "new") {
      target.status = "triaged";
    }
    appendAuditEntry(state, actor, "case_assigned", {
      case_id: target.case_id,
      severity: target.severity,
      assignee,
      status: target.status,
      invoice_id: target.invoice_id,
      vendor_id: target.vendor_id,
    });
    n_ok += 1;
  }

  return {
    n_ok,
    n_errors: error_case_ids.length,
    error_case_ids,
  };
}

export function closeDemoCases(
  caseIds: string[],
  nextStatus: "confirmed" | "rejected" | "false_positive",
  reason: string,
  actor: string,
): BulkResult {
  const state = getDemoInvestigationState();
  const error_case_ids: string[] = [];
  let n_ok = 0;

  const mappedStatus =
    nextStatus === "confirmed"
      ? "closed_confirmed"
      : nextStatus === "rejected"
        ? "closed_rejected"
        : "closed_false_positive";

  for (const caseId of caseIds) {
    const target = state.cases.find((item) => item.case_id === caseId);
    if (!target) {
      error_case_ids.push(caseId);
      continue;
    }

    target.status = mappedStatus;
    target.closed_at = new Date().toISOString();
    target.closure_reason = reason;
    if (mappedStatus === "closed_false_positive") {
      target.decision = "close_false_positive";
    }
    appendAuditEntry(state, actor, "case_closed", {
      case_id: target.case_id,
      severity: target.severity,
      status: target.status,
      decision: target.decision,
      invoice_id: target.invoice_id,
      vendor_id: target.vendor_id,
      reason,
    });
    n_ok += 1;
  }

  return {
    n_ok,
    n_errors: error_case_ids.length,
    error_case_ids,
  };
}

function appendAuditEntry(
  state: DemoInvestigationState,
  actor: string,
  kind: string,
  payload: Record<string, unknown>,
) {
  const previous = state.auditEntries[state.auditEntries.length - 1];
  state.auditEntries.push(
    buildAuditEntry(
      state.auditEntries.length + 1,
      actor,
      kind,
      new Date().toISOString(),
      payload,
      previous?.hash ?? "root",
    ),
  );
}
