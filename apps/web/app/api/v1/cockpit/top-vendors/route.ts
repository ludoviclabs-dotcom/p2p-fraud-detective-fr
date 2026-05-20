import { NextResponse } from "next/server";

import { buildDemoTopVendors } from "@/lib/demo-cockpit";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export async function GET(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cockpit/top-vendors");
  if (upstream) return upstream;

  const { searchParams } = new URL(request.url);
  const requested = Number(searchParams.get("limit") ?? "10");
  const limit = Number.isFinite(requested)
    ? Math.min(Math.max(Math.trunc(requested), 1), 50)
    : 10;

  return NextResponse.json(buildDemoTopVendors(undefined, limit));
}
