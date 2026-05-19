import {
  bulkAssignCases,
  bulkCloseCases,
  commentCase,
  createCaseFromWorkflow,
  listCases,
  setCaseDecision,
  setCaseStatus,
  type CaseOutV1,
} from "@/lib/api-client";
import {
  CASE_WORKFLOW_ACTOR,
  createDefaultCaseWorkflowRecord,
  readStoredCaseWorkflowRecords,
  writeStoredCaseWorkflowRecords,
  type CaseDecision,
  type CaseStatus,
  type CaseWorkflowContext,
  type CaseWorkflowRecord,
} from "@/lib/case-workflow";

const API_ENABLED = Boolean(process.env.NEXT_PUBLIC_API_URL);

export interface CaseWorkflowBridgeLoadResult {
  mode: "local" | "fastapi" | "hybrid";
  record: CaseWorkflowRecord;
}

export interface CaseWorkflowBridgeSaveResult {
  mode: "local" | "fastapi" | "hybrid";
  record: CaseWorkflowRecord;
  warning?: string | null;
}

export function isCaseWorkflowApiEnabled(): boolean {
  return API_ENABLED;
}

export async function loadCaseWorkflowRecord(
  context: CaseWorkflowContext,
): Promise<CaseWorkflowBridgeLoadResult> {
  const local = findStoredRecord(context);

  if (!API_ENABLED) {
    return {
      mode: "local",
      record: local ?? createDefaultCaseWorkflowRecord(context),
    };
  }

  const remoteCase = await findRemoteCase(context);
  if (!remoteCase) {
    return {
      mode: local ? "hybrid" : "local",
      record: local ?? createDefaultCaseWorkflowRecord(context),
    };
  }

  const remoteRecord = mapApiCaseToWorkflowRecord(context, remoteCase);
  if (!local) {
    persistRecord(remoteRecord);
    return { mode: "fastapi", record: remoteRecord };
  }

  const merged: CaseWorkflowRecord = {
    ...remoteRecord,
    decision: remoteRecord.decision !== "pending" ? remoteRecord.decision : local.decision,
    note: local.note,
    updatedAt: local.updatedAt,
    source: "hybrid",
  };
  persistRecord(merged);
  return { mode: "hybrid", record: merged };
}

export async function saveCaseWorkflowRecord(
  context: CaseWorkflowContext,
  nextRecord: CaseWorkflowRecord,
): Promise<CaseWorkflowBridgeSaveResult> {
  const previous = findStoredRecord(context);
  const localSaved: CaseWorkflowRecord = {
    ...nextRecord,
    updatedAt: new Date().toISOString(),
    source: nextRecord.source ?? "local",
  };
  persistRecord(localSaved);

  if (!API_ENABLED) {
    return { mode: "local", record: localSaved };
  }

  const remoteCase =
    (localSaved.backendCaseId
      ? await findRemoteCase(context, localSaved.backendCaseId)
      : await findRemoteCase(context)) ?? null;

  const ensuredRemoteCase = remoteCase ?? (await createRemoteCase(context));

  if (!ensuredRemoteCase) {
    return {
      mode: "local",
      record: localSaved,
      warning: "Aucun case FastAPI correspondant n'a ete trouve.",
    };
  }

  if (localSaved.assignee && localSaved.assignee !== (ensuredRemoteCase.assignee ?? "")) {
    await bulkAssignCases({
      case_ids: [ensuredRemoteCase.case_id],
      assignee: localSaved.assignee,
      actor: CASE_WORKFLOW_ACTOR,
    });
  }

  if (
    localSaved.decision !== mapApiDecision(ensuredRemoteCase) &&
    !ensuredRemoteCase.closed_at
  ) {
    await setCaseDecision(ensuredRemoteCase.case_id, {
      decision: localSaved.decision,
      actor: CASE_WORKFLOW_ACTOR,
    });
  }

  const syncStatus = mapWorkflowStatusToApi(localSaved.status);
  if (syncStatus) {
    await setCaseStatus(ensuredRemoteCase.case_id, {
      status: syncStatus,
      actor: CASE_WORKFLOW_ACTOR,
      reason:
        localSaved.status === "escalated"
          ? localSaved.note || "Escalade depuis le workflow web."
          : undefined,
      channel: localSaved.status === "escalated" ? "web-workflow" : undefined,
    });
  } else if (
    localSaved.status === "cleared" &&
    localSaved.decision === "close_false_positive" &&
    !ensuredRemoteCase.closed_at
  ) {
    await bulkCloseCases({
      case_ids: [ensuredRemoteCase.case_id],
      status: "false_positive",
      reason: localSaved.note || "Cloture depuis le workflow web.",
      actor: CASE_WORKFLOW_ACTOR,
    });
  }

  const normalizedNote = localSaved.note.trim();
  const previousNote = previous?.note.trim() ?? "";
  if (normalizedNote && normalizedNote !== previousNote) {
    const prefix = getDecisionCommentPrefix(localSaved.decision);
    await commentCase(ensuredRemoteCase.case_id, {
      actor: CASE_WORKFLOW_ACTOR,
      text: `${prefix}: ${normalizedNote}`,
    });
  }

  const refreshed = await findRemoteCase(context, ensuredRemoteCase.case_id);
  const merged = refreshed
    ? {
        ...mapApiCaseToWorkflowRecord(context, refreshed),
        decision: localSaved.decision,
        note: localSaved.note,
        source: "hybrid" as const,
      }
    : {
        ...localSaved,
        backendCaseId: ensuredRemoteCase.case_id,
        source: "hybrid" as const,
      };

  persistRecord(merged);
  return { mode: "hybrid", record: merged };
}

function findStoredRecord(context: CaseWorkflowContext): CaseWorkflowRecord | undefined {
  return readStoredCaseWorkflowRecords().find(
    (record) =>
      record.id === context.id ||
      record.findingId === context.findingId ||
      record.invoiceId === context.invoiceId,
  );
}

function persistRecord(record: CaseWorkflowRecord) {
  const next = [
    record,
    ...readStoredCaseWorkflowRecords().filter((item) => item.id !== record.id),
  ];
  writeStoredCaseWorkflowRecords(next);
}

async function findRemoteCase(
  context: CaseWorkflowContext,
  caseId?: string,
): Promise<CaseOutV1 | undefined> {
  const rows = await listCases({
    case_id: caseId,
    invoice_id: context.invoiceId,
    vendor_id: context.vendorId,
    limit: 50,
  });

  return (
    rows.find((row) => caseId && row.case_id === caseId) ??
    rows.find((row) => row.invoice_id === context.invoiceId) ??
    rows.find((row) => row.vendor_id === context.vendorId)
  );
}

async function createRemoteCase(
  context: CaseWorkflowContext,
): Promise<CaseOutV1 | undefined> {
  return createCaseFromWorkflow({
    finding_id: context.findingId,
    invoice_id: context.invoiceId,
    vendor_id: context.vendorId,
    vendor_name: context.vendorName,
    rule_id: context.ruleId,
    signal: context.signal,
    severity: context.severity,
    exposure_eur: context.exposureEur,
    risk_score: context.riskScore,
    actor: CASE_WORKFLOW_ACTOR,
    title: `${context.ruleId} - ${context.invoiceId}`,
  });
}

function mapApiCaseToWorkflowRecord(
  context: CaseWorkflowContext,
  apiCase: CaseOutV1,
): CaseWorkflowRecord {
  return {
    ...createDefaultCaseWorkflowRecord(context),
    assignee: apiCase.assignee ?? "",
    backendCaseId: apiCase.case_id,
    createdAt: apiCase.created_at || new Date().toISOString(),
    decision: mapApiDecision(apiCase),
    note: apiCase.closure_reason ?? "",
    source: "fastapi",
    status: mapApiStatus(apiCase),
    updatedAt: apiCase.closed_at ?? apiCase.created_at ?? new Date().toISOString(),
  };
}

function mapApiStatus(apiCase: CaseOutV1): CaseStatus {
  switch (apiCase.status) {
    case "new":
      return "new";
    case "triaged":
    case "in_progress":
      return "reviewing";
    case "escalated":
      return "escalated";
    case "closed_confirmed":
    case "closed_rejected":
    case "closed_false_positive":
      return "cleared";
    default:
      return "new";
  }
}

function mapApiDecision(apiCase: CaseOutV1): CaseDecision {
  if (isCaseDecision(apiCase.decision)) return apiCase.decision;

  switch (apiCase.status) {
    case "closed_false_positive":
      return "close_false_positive";
    case "escalated":
      return "block_payment";
    default:
      return "pending";
  }
}

function isCaseDecision(value: unknown): value is CaseDecision {
  return (
    value === "pending" ||
    value === "monitor" ||
    value === "request_documents" ||
    value === "block_payment" ||
    value === "close_false_positive"
  );
}

function mapWorkflowStatusToApi(
  status: CaseStatus,
): "new" | "triaged" | "in_progress" | "escalated" | null {
  switch (status) {
    case "new":
      return "new";
    case "reviewing":
      return "in_progress";
    case "needs_evidence":
      return "triaged";
    case "escalated":
      return "escalated";
    case "cleared":
      return null;
    default:
      return null;
  }
}

function getDecisionCommentPrefix(decision: CaseDecision): string {
  switch (decision) {
    case "monitor":
      return "Decision workflow - surveiller";
    case "request_documents":
      return "Decision workflow - demander des pieces";
    case "block_payment":
      return "Decision workflow - bloquer paiement";
    case "close_false_positive":
      return "Decision workflow - faux positif";
    case "pending":
    default:
      return "Decision workflow - en attente";
  }
}
