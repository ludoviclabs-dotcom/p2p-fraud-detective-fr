import { getRiskScenarioByCaseId, RISK_SCENARIOS } from "@/data/risk-scenarios";
import { isP2PTransaction, scoreTransaction } from "@/lib/risk/scoreEngine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const body = payload as {
    scenarioId?: string;
    caseId?: string;
    transaction?: unknown;
  };
  const scenario =
    (body.caseId ? getRiskScenarioByCaseId(body.caseId) : undefined) ??
    RISK_SCENARIOS.find((item) => item.id === body.scenarioId);

  const transaction = scenario?.transaction ?? body.transaction;
  if (!isP2PTransaction(transaction)) {
    return Response.json(
      { error: "Unable to create demo case: invalid transaction or scenarioId" },
      { status: 400 },
    );
  }

  const caseId = body.caseId ?? scenario?.caseId ?? transaction.caseId ?? `CASE-${transaction.transactionId}`;
  const score = scoreTransaction(transaction);
  return Response.json({
    caseId,
    status: "created",
    score,
    href: `/fraud-case-360/${encodeURIComponent(caseId)}`,
    generatedAt: new Date().toISOString(),
    disclaimer: "Case simulé en mémoire pour données synthétiques.",
  });
}
