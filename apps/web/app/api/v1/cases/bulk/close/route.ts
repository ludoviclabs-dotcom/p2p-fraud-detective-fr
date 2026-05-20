import { NextResponse } from "next/server";

import { closeDemoCases } from "@/lib/demo-investigation";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export async function POST(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cases/bulk/close");
  if (upstream) return upstream;

  const body = (await request.json()) as {
    case_ids?: string[];
    status?: "confirmed" | "rejected" | "false_positive";
    reason?: string;
    actor?: string;
  };

  return NextResponse.json(
    closeDemoCases(
      body.case_ids ?? [],
      body.status ?? "false_positive",
      body.reason ?? "Cloture demo.",
      body.actor ?? "web.demo",
    ),
  );
}
