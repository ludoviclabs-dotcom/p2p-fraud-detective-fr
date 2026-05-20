import { NextResponse } from "next/server";

import { filterDemoCases, getDemoInvestigationState } from "@/lib/demo-investigation";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cases");
  if (upstream) return upstream;

  const { searchParams } = new URL(request.url);
  const limitParam = searchParams.get("limit");
  const limit = limitParam ? Number(limitParam) : undefined;
  const state = getDemoInvestigationState();

  return NextResponse.json(
    filterDemoCases(state.cases, {
      case_id: searchParams.get("case_id") ?? undefined,
      invoice_id: searchParams.get("invoice_id") ?? undefined,
      vendor_id: searchParams.get("vendor_id") ?? undefined,
      status: searchParams.get("status") ?? undefined,
      severity: searchParams.get("severity") ?? undefined,
      assignee: searchParams.get("assignee") ?? undefined,
      limit: Number.isFinite(limit) ? limit : undefined,
    }),
  );
}
