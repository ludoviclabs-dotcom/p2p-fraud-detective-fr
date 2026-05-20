import { NextResponse } from "next/server";

import { buildDemoAuditVerify, getDemoInvestigationState } from "@/lib/demo-investigation";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/audit/verify");
  if (upstream) return upstream;

  const state = getDemoInvestigationState();
  return NextResponse.json(buildDemoAuditVerify(state.auditEntries));
}
