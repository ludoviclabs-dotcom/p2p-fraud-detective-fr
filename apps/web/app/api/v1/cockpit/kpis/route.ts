import { NextResponse } from "next/server";

import { buildDemoCockpitKpis } from "@/lib/demo-cockpit";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cockpit/kpis");
  if (upstream) return upstream;

  return NextResponse.json(buildDemoCockpitKpis());
}
