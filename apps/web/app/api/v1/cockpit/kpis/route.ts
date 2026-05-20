import { NextResponse } from "next/server";

import { buildDemoCockpitKpis } from "@/lib/demo-cockpit";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cockpit/kpis");
  if (upstream) {
    const payload = await readJson(upstream);
    if (upstream.ok && payload && !isEmptyCockpitPayload(payload)) {
      return NextResponse.json(payload);
    }
  }

  return NextResponse.json(buildDemoCockpitKpis());
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.clone().json();
  } catch {
    return null;
  }
}

function isEmptyCockpitPayload(payload: unknown): boolean {
  if (!payload || typeof payload !== "object") return true;
  const data = payload as {
    exposure_total_eur?: unknown;
    exposure_critical_eur?: unknown;
    n_cases_open?: unknown;
    n_cases_overdue?: unknown;
    trend_cases_created?: unknown;
    trend_cases_closed?: unknown;
    trend_critical_alerts?: unknown;
    trend_audit_activity?: unknown;
  };
  const numericValues = [
    data.exposure_total_eur,
    data.exposure_critical_eur,
    data.n_cases_open,
    data.n_cases_overdue,
  ];
  const hasPositiveMetric = numericValues.some(
    (value) => typeof value === "number" && value > 0,
  );
  const hasTrend = [
    data.trend_cases_created,
    data.trend_cases_closed,
    data.trend_critical_alerts,
    data.trend_audit_activity,
  ].some((value) => Array.isArray(value) && value.length > 0);

  return !hasPositiveMetric && !hasTrend;
}
