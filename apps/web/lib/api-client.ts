/**
 * Client fetch typé pour FastAPI /api/v1/*.
 *
 * En production : pointe vers le backend FastAPI hébergé sur Hugging Face
 * Spaces (variable d'env `NEXT_PUBLIC_API_URL`), avec un proxy Next.js
 * `rewrites()` configuré dans `next.config.ts` pour éviter les soucis CORS.
 *
 * Phase 0 : types `any` pour le payload. Phase 1 : remplacer par les types
 * générés depuis `packages/shared-types/src/api.ts` (cmd `pnpm sdk:gen-types`).
 */

const _BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const _SECRET = process.env.FRAUD_API_SECRET ?? "";

type FetchOpts = Omit<RequestInit, "body"> & { body?: unknown };

async function _fetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const url = path.startsWith("http") ? path : `${_BASE}${path}`;
  const headers = new Headers(opts.headers);
  if (_SECRET) {
    headers.set("Authorization", `Bearer ${_SECRET}`);
  }
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

// ─── Endpoints typés Phase 0 (Cockpit + Vendor) ─────────────────────────────

export type DailyPoint = { date: string; value: number };

export type CockpitKPIs = {
  exposure_total_eur: number;
  exposure_critical_eur: number;
  n_cases_open: number;
  n_cases_overdue: number;
  n_cases_unassigned_critical: number;
  trend_cases_created: DailyPoint[];
  trend_cases_closed: DailyPoint[];
  trend_critical_alerts: DailyPoint[];
  trend_audit_activity: DailyPoint[];
};

export type TopVendor = {
  vendor_id: string;
  vendor_name: string | null;
  exposure_eur: number;
  n_findings: number;
  max_severity: string;
};

export const getCockpitKpis = () =>
  api.get<CockpitKPIs>("/api/v1/cockpit/kpis");

export const getTopVendors = (limit = 10) =>
  api.get<TopVendor[]>(`/api/v1/cockpit/top-vendors?limit=${limit}`);
