import { NextResponse } from "next/server";

import { buildDemoAuditVerify, getDemoInvestigationState } from "@/lib/demo-investigation";

export function GET() {
  const state = getDemoInvestigationState();
  return NextResponse.json(buildDemoAuditVerify(state.auditEntries));
}
