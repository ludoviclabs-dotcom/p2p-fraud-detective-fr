import { NextResponse } from "next/server";

import { buildDemoAuditPage, getDemoInvestigationState } from "@/lib/demo-investigation";

export function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const cursor = Number(searchParams.get("cursor") ?? 0);
  const limit = Number(searchParams.get("limit") ?? 100);
  const state = getDemoInvestigationState();

  return NextResponse.json(
    buildDemoAuditPage(
      state.auditEntries,
      Number.isFinite(cursor) ? cursor : 0,
      Number.isFinite(limit) ? limit : 100,
    ),
  );
}
