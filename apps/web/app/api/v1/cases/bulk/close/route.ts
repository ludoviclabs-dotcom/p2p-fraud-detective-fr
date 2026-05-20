import { NextResponse } from "next/server";

import { closeDemoCases } from "@/lib/demo-investigation";

export async function POST(request: Request) {
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
