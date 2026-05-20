import { NextResponse } from "next/server";

import { assignDemoCases } from "@/lib/demo-investigation";
import { proxyApiV1Request } from "@/lib/api-v1-proxy";

export async function POST(request: Request) {
  const upstream = await proxyApiV1Request(request, "/api/v1/cases/bulk/assign");
  if (upstream) return upstream;

  const body = (await request.json()) as {
    case_ids?: string[];
    assignee?: string;
    actor?: string;
  };

  return NextResponse.json(
    assignDemoCases(body.case_ids ?? [], body.assignee ?? "", body.actor ?? "web.demo"),
  );
}
