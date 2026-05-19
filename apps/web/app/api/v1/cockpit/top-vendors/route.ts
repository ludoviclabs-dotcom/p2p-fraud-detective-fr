import { NextResponse } from "next/server";

import { buildDemoTopVendors } from "@/lib/demo-cockpit";

export function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const requested = Number(searchParams.get("limit") ?? "10");
  const limit = Number.isFinite(requested)
    ? Math.min(Math.max(Math.trunc(requested), 1), 50)
    : 10;

  return NextResponse.json(buildDemoTopVendors(undefined, limit));
}
