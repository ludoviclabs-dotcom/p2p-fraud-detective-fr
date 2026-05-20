import { NextResponse } from "next/server";

import { assignDemoCases } from "@/lib/demo-investigation";

export async function POST(request: Request) {
  const body = (await request.json()) as {
    case_ids?: string[];
    assignee?: string;
    actor?: string;
  };

  return NextResponse.json(
    assignDemoCases(body.case_ids ?? [], body.assignee ?? "", body.actor ?? "web.demo"),
  );
}
