import { NextResponse } from "next/server";

import { buildDemoAuditPage, getDemoInvestigationState } from "@/lib/demo-investigation";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/audit");
  const { searchParams } = new URL(request.url);
  const cursor = Number(searchParams.get("cursor") ?? 0);
  const limit = Number(searchParams.get("limit") ?? 100);
  const state = getDemoInvestigationState();
  const demoPage = buildDemoAuditPage(
    state.auditEntries,
    Number.isFinite(cursor) ? cursor : 0,
    Number.isFinite(limit) ? limit : 100,
  );

  if (upstream) {
    const payload = await readJson(upstream);
    if (upstream.ok && hasAuditEntries(payload)) {
      return NextResponse.json(payload);
    }
  }

  return NextResponse.json(demoPage);
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.clone().json();
  } catch {
    return null;
  }
}

function hasAuditEntries(payload: unknown): boolean {
  if (!payload || typeof payload !== "object") return false;
  const data = payload as { entries?: unknown };
  return Array.isArray(data.entries) && data.entries.length > 0;
}
