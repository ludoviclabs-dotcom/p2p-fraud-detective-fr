import { NextResponse } from "next/server";

import { getP2PDataset } from "@/data/get-dataset";

export function GET() {
  const dataset = getP2PDataset();
  return NextResponse.json({
    generatedAt: dataset.generatedAt,
    nodes: dataset.nodes,
    edges: dataset.edges,
    metrics: dataset.metrics,
  });
}
