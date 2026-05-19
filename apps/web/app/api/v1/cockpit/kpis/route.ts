import { NextResponse } from "next/server";

import { buildDemoCockpitKpis } from "@/lib/demo-cockpit";

export function GET() {
  return NextResponse.json(buildDemoCockpitKpis());
}
