/**
 * Client fetch typé pour FastAPI /api/v1/*.
 *
 * Phase 1 : types réels via `@p2pfd/shared-types` (générés depuis OpenAPI).
 * Regénérer après changement backend : `pnpm sdk:gen-types`.
 */

import type {
  AuditEntryOut,
  AuditPage,
  AuditVerifyResult,
  BulkResult,
  CockpitKPIs,
  DailyPoint,
  FindingOut,
  P2PDemoDataset as BackendP2PDemoDataset,
  TimelineEvent,
  TopVendor,
  VendorSummary,
  Schemas,
} from "@p2pfd/shared-types";
import type { P2PMetrics } from "@/types/p2p";

type FetchOpts = Omit<RequestInit, "body"> & { body?: unknown };

export function resolveApiUrl(
  path: string,
  options: { apiBase?: string; isBrowser?: boolean } = {},
): string {
  if (path.startsWith("http")) return path;

  const isBrowser = options.isBrowser ?? typeof window !== "undefined";
  const apiBase =
    options.apiBase ?? (isBrowser ? "" : process.env.NEXT_PUBLIC_API_URL ?? "");

  if (!isBrowser && apiBase) return `${apiBase}${path}`;
  return path;
}

async function _fetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const isBrowser = typeof window !== "undefined";
  const url = resolveApiUrl(path, { isBrowser });
  const headers = new Headers(opts.headers);
  const serverSecret = isBrowser ? "" : process.env.FRAUD_API_SECRET ?? "";
  if (serverSecret) headers.set("Authorization", `Bearer ${serverSecret}`);
  if (opts.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const init: RequestInit = {
    ...opts,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  };
  const resp = await fetch(url, init);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API ${resp.status} ${resp.statusText}: ${text}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  get: <T>(path: string) => _fetch<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    _fetch<T>(path, { method: "POST", body }),
};

// Re-export types pour les pages
export type {
  AuditEntryOut,
  AuditPage,
  AuditVerifyResult,
  BulkResult,
  CockpitKPIs,
  DailyPoint,
  FindingOut,
  BackendP2PDemoDataset,
  TimelineEvent,
  TopVendor,
  VendorSummary,
};

export type CaseOutV1 = Schemas["CaseOutV1"];
export type CaseBootstrapBody = Schemas["CaseBootstrapBody"];

export interface DemoSignalBreakdown {
  signal: string;
  label: string;
  count: number;
  share: number;
}

export interface DemoGraphMetrics {
  generatedAt: string;
  metrics: P2PMetrics;
  signalBreakdown: DemoSignalBreakdown[];
}

export type BackendP2PGraphDataset = BackendP2PDemoDataset;

// ─── Endpoints typés ────────────────────────────────────────────────────────

export const getCockpitKpis = () =>
  api.get<CockpitKPIs>("/api/v1/cockpit/kpis");

export const getTopVendors = (limit = 10) =>
  api.get<TopVendor[]>(`/api/v1/cockpit/top-vendors?limit=${limit}`);

export async function getDemoGraphMetrics(): Promise<DemoGraphMetrics> {
  const resp = await fetch("/api/graph/metrics");
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Demo graph metrics ${resp.status} ${resp.statusText}: ${text}`);
  }
  return (await resp.json()) as DemoGraphMetrics;
}

export const getBackendP2PGraph = (params: {
  cluster_min_size?: number;
  max_findings?: number;
} = {}) => {
  const qs = new URLSearchParams();
  if (params.cluster_min_size) qs.set("cluster_min_size", String(params.cluster_min_size));
  if (params.max_findings) qs.set("max_findings", String(params.max_findings));
  const q = qs.toString();
  return api.get<BackendP2PGraphDataset>(`/api/v1/graph${q ? `?${q}` : ""}`);
};

export const listCases = (params: {
  case_id?: string;
  invoice_id?: string;
  vendor_id?: string;
  status?: string;
  severity?: string;
  assignee?: string;
  limit?: number;
} = {}) => {
  const qs = new URLSearchParams();
  if (params.case_id) qs.set("case_id", params.case_id);
  if (params.invoice_id) qs.set("invoice_id", params.invoice_id);
  if (params.vendor_id) qs.set("vendor_id", params.vendor_id);
  if (params.status) qs.set("status", params.status);
  if (params.severity) qs.set("severity", params.severity);
  if (params.assignee) qs.set("assignee", params.assignee);
  if (params.limit) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return api.get<CaseOutV1[]>(`/api/v1/cases${q ? `?${q}` : ""}`);
};

export const getVendorSummary = (vendorId: string) =>
  api.get<VendorSummary>(`/api/v1/vendors/${encodeURIComponent(vendorId)}`);

export const getVendorTimeline = (vendorId: string, days = 30) =>
  api.get<TimelineEvent[]>(
    `/api/v1/vendors/${encodeURIComponent(vendorId)}/timeline?days=${days}`,
  );

export const listFindings = (params: {
  rule_id?: string;
  severity?: string;
  limit?: number;
} = {}) => {
  const qs = new URLSearchParams();
  if (params.rule_id) qs.set("rule_id", params.rule_id);
  if (params.severity) qs.set("severity", params.severity);
  if (params.limit) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return api.get<FindingOut[]>(`/api/v1/findings${q ? `?${q}` : ""}`);
};

export const listAudit = (cursor = 0, limit = 100) =>
  api.get<AuditPage>(`/api/v1/audit?cursor=${cursor}&limit=${limit}`);

export const verifyAudit = () =>
  api.get<AuditVerifyResult>("/api/v1/audit/verify");

// Sortie IA structurée de l'Audit Log Explainer (ADR-0007).
// Schéma source : src/p2p_fraud/llm/schemas.py — régénérer via `pnpm sdk:gen-types`
// quand le type OpenAPI sera publié.
export interface GroundedClaim {
  text: string;
  source_ids: string[];
}

export interface AuditExplanation {
  headline: string;
  explanation: GroundedClaim[];
  audit_implications: GroundedClaim[];
  missing_evidence: string[];
  human_review_required: boolean;
  recommended_next_actions: string[];
}

export interface AuditExplainResult {
  chain_status: "intact" | "broken" | "empty";
  n_total: number;
  n_signed: number;
  invalid_seqs: number[];
  signatures_checked: boolean;
  explanation: AuditExplanation;
  model: string;
  prompt_version: string;
}

export const explainAudit = () =>
  api.post<AuditExplainResult>("/api/v1/audit/explain");

// Dossier d'enquête FraudCase360 (Phase 3, ADR-0007).
// Schéma source : src/p2p_fraud/llm/schemas.py.
export interface RiskSignal extends GroundedClaim {
  rule_id: string;
  severity: "low" | "medium" | "high" | "critical";
}

export interface FraudCase360 {
  executive_summary: string;
  severity_assessment: "low" | "medium" | "high" | "critical";
  verified_facts: GroundedClaim[];
  risk_signals: RiskSignal[];
  contradictions: string[];
  missing_evidence: string[];
  open_questions: string[];
  human_review_required: boolean;
  recommended_next_actions: string[];
}

export interface Case360Result {
  case_id: string;
  dossier: FraudCase360;
  model: string;
  prompt_version: string;
}

export const generateCase360 = (caseId: string) =>
  api.post<Case360Result>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/case360`,
  );

// Copilote analyste (Phase 5, ADR-0007) — questions prédéfinies sur un cas.
export interface CopilotQuestion {
  question_id: string;
  label_fr: string;
}

export interface CopilotAnswer {
  answer_short: string;
  evidence: GroundedClaim[];
  uncertainties: string[];
  recommended_next_action: string;
  human_review_required: boolean;
}

export interface CopilotResult {
  case_id: string;
  question_id: string;
  answer: CopilotAnswer;
  model: string;
  prompt_version: string;
}

export const listCopilotQuestions = () =>
  api.get<CopilotQuestion[]>("/api/v1/copilot/questions");

export const askCopilot = (body: {
  question_id: string;
  case_id: string;
  actor?: string;
}) => api.post<CopilotResult>("/api/v1/copilot/ask", body);

// Risk Replay (Phase 6, ADR-0007) — séquence narrative d'un cas.
export interface ReplayStep {
  title: string;
  business_explanation: string;
  evidence: GroundedClaim[];
  risk_level: "info" | "low" | "medium" | "high" | "critical";
  reviewer_question: string;
}

export interface RiskReplay {
  case_summary: string;
  steps: ReplayStep[];
  human_review_required: boolean;
}

export interface ReplayResult {
  case_id: string;
  replay: RiskReplay;
  model: string;
  prompt_version: string;
}

export const generateReplay = (caseId: string) =>
  api.post<ReplayResult>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/replay`,
  );

// Narratif de scénario synthétique (Phase 6, ADR-0007).
export interface ScenarioNarrative {
  pitch: string;
  fraud_story: GroundedClaim[];
  expected_detectors: string[];
  false_positive_traps: string[];
  human_review_required: boolean;
}

export interface ScenarioNarrativeResult {
  scenario_id: string;
  narrative: ScenarioNarrative;
  model: string;
  prompt_version: string;
}

export const generateScenarioNarrative = (scenarioId: string) =>
  api.post<ScenarioNarrativeResult>(
    `/api/v1/scenarios/${encodeURIComponent(scenarioId)}/narrative`,
  );

// Detection Studio — règles versionnées (Phase 4, ADR-0007).
// Schémas source : src/p2p_fraud/rules/ + src/p2p_fraud/api/v1.py.
export interface RuleTestResult {
  name: string;
  expected: boolean;
  actual: boolean;
  passed: boolean;
}

export interface RuleTestReport {
  all_passed: boolean;
  n_total: number;
  n_passed: number;
  results: RuleTestResult[];
}

export interface RuleBacktestSummary {
  n_records: number;
  n_flagged: number;
  alert_rate: number;
  n_labeled: number;
  n_true_positive: number;
  n_false_positive: number;
  precision: number | null;
  sample_flagged_ids: string[];
}

export interface RuleVersionOut {
  rule_id: string;
  version: number;
  status: "draft" | "tested" | "active" | "superseded" | "rejected";
  yaml: string;
  author: string;
  created_at: string;
  name: string;
  severity: string;
  reason_code: string;
  tests: { name: string; record: Record<string, unknown>; expect_match: boolean }[];
  test_report: RuleTestReport | null;
  backtest: RuleBacktestSummary | null;
  approved_by: string | null;
  activated_at: string | null;
}

export const draftRule = (body: { description_fr: string; author: string }) =>
  api.post<RuleVersionOut>("/api/v1/rules/draft", body);

export const listRules = (ruleId?: string) =>
  api.get<RuleVersionOut[]>(
    `/api/v1/rules${ruleId ? `?rule_id=${encodeURIComponent(ruleId)}` : ""}`,
  );

export const runRuleTests = (ruleId: string, version: number) =>
  api.post<RuleVersionOut>(
    `/api/v1/rules/${encodeURIComponent(ruleId)}/versions/${version}/test`,
  );

export const backtestRule = (
  ruleId: string,
  version: number,
  body: { n_invoices?: number; seed?: number; actor?: string } = {},
) =>
  api.post<RuleVersionOut>(
    `/api/v1/rules/${encodeURIComponent(ruleId)}/versions/${version}/backtest`,
    body,
  );

export const activateRule = (
  ruleId: string,
  version: number,
  body: { approver: string },
) =>
  api.post<RuleVersionOut>(
    `/api/v1/rules/${encodeURIComponent(ruleId)}/versions/${version}/activate`,
    body,
  );

export const bulkAssignCases = (body: {
  case_ids: string[];
  assignee: string;
  actor: string;
}) => api.post<BulkResult>("/api/v1/cases/bulk/assign", body);

export const bulkCloseCases = (body: {
  case_ids: string[];
  status: "confirmed" | "rejected" | "false_positive";
  reason: string;
  actor: string;
}) => api.post<BulkResult>("/api/v1/cases/bulk/close", body);

export const commentCase = (
  caseId: string,
  body: { text: string; actor: string },
) =>
  api.post<{ ok: boolean; case_id: string }>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/comment`,
    body,
  );

export const setCaseStatus = (
  caseId: string,
  body: {
    status: "new" | "triaged" | "in_progress" | "escalated";
    actor: string;
    reason?: string;
    channel?: string;
  },
) =>
  api.post<CaseOutV1>(`/api/v1/cases/${encodeURIComponent(caseId)}/status`, body);

export const setCaseDecision = (
  caseId: string,
  body: {
    decision: string;
    actor: string;
  },
) =>
  api.post<CaseOutV1>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/decision`,
    body,
  );

export const createCaseFromWorkflow = (body: CaseBootstrapBody) =>
  api.post<CaseOutV1>("/api/v1/cases/bootstrap", body);
