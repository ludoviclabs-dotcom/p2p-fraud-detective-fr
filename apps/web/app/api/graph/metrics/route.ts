import { NextResponse } from "next/server";

import { getP2PDataset } from "@/data/get-dataset";
import { getSignalLabel, SIGNAL_ORDER } from "@/lib/p2p-demo-taxonomy";

export function GET() {
  const dataset = getP2PDataset();
  const totalFindings = dataset.metrics.findingCount || 1;
  const remainingSignals = new Set(Object.keys(dataset.metrics.signalCounts));
  const orderedSignals = SIGNAL_ORDER.filter((signal) => remainingSignals.delete(signal));

  return NextResponse.json({
    generatedAt: dataset.generatedAt,
    metrics: dataset.metrics,
    signalBreakdown: [...orderedSignals, ...Array.from(remainingSignals).sort()].map((signal) => {
      const count = dataset.metrics.signalCounts[signal] ?? 0;
      return {
        signal,
        label: getSignalLabel(signal),
        count,
        share: count / totalFindings,
      };
    }),
  });
}
