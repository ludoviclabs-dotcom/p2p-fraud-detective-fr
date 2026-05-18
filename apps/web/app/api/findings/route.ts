import { NextResponse } from "next/server";

import { getP2PDataset } from "@/data/get-dataset";

export function GET() {
  return NextResponse.json(getP2PDataset().findings);
}
