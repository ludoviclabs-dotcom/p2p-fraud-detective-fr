import { NextResponse } from "next/server";

import { buildDemoTopVendors } from "@/lib/demo-cockpit";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cockpit/top-vendors");
  const { searchParams } = new URL(request.url);
  const requested = Number(searchParams.get("limit") ?? "10");
  const limit = Number.isFinite(requested)
    ? Math.min(Math.max(Math.trunc(requested), 1), 50)
    : 10;

  if (upstream) {
    const payload = await readJson(upstream);
    if (upstream.ok && Array.isArray(payload) && payload.length > 0) {
      return NextResponse.json(payload.slice(0, limit));
    }
  }

  return NextResponse.json(buildDemoTopVendors(undefined, limit));
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.clone().json();
  } catch {
    return null;
  }
}
