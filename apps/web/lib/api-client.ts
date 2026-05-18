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
  TimelineEvent,
  TopVendor,
  VendorSummary,
  Schemas,
} from "@p2pfd/shared-types";
import type { P2PMetrics } from "@/types/p2p";

const _BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const _SECRET = process.env.FRAUD_API_SECRET ?? "";

type FetchOpts = Omit<RequestInit, "body"> & { body?: unknown };

async function _fetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const url = path.startsWith("http") ? path : `${_BASE}${path}`;
  const headers = new Headers(opts.headers);
  if (_SECRET) headers.set("Authorization", `Bearer ${_SECRET}`);
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

export const createCaseFromWorkflow = (body: CaseBootstrapBody) =>
  api.post<CaseOutV1>("/api/v1/cases/bootstrap", body);
