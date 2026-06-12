import { NextResponse } from "next/server";

import { buildDemoCockpitKpis } from "@/lib/demo-cockpit";
import { isEmptyCockpitKpisPayload } from "@/lib/cockpit-payload";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cockpit/kpis");
  if (upstream) {
    const payload = await readJson(upstream);
    if (upstream.ok && payload && !isEmptyCockpitKpisPayload(payload)) {
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
