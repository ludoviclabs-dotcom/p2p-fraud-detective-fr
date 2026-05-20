import { NextResponse } from "next/server";

import { filterDemoCases, getDemoInvestigationState } from "@/lib/demo-investigation";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cases");
  const { searchParams } = new URL(request.url);
  const limitParam = searchParams.get("limit");
  const limit = limitParam ? Number(limitParam) : undefined;
  const state = getDemoInvestigationState();
  const demoCases = filterDemoCases(state.cases, {
    case_id: searchParams.get("case_id") ?? undefined,
    invoice_id: searchParams.get("invoice_id") ?? undefined,
    vendor_id: searchParams.get("vendor_id") ?? undefined,
    status: searchParams.get("status") ?? undefined,
    severity: searchParams.get("severity") ?? undefined,
    assignee: searchParams.get("assignee") ?? undefined,
    limit: Number.isFinite(limit) ? limit : undefined,
  });

  if (upstream) {
    const payload = await readJson(upstream);
    if (upstream.ok && Array.isArray(payload) && payload.length > 0) {
      return NextResponse.json(payload);
    }
  }

  return NextResponse.json(demoCases);
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.clone().json();
  } catch {
    return null;
  }
}
