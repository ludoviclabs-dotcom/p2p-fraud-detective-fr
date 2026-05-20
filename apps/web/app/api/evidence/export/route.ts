import { getRiskScenarioByCaseId } from "@/data/risk-scenarios";
import { buildEvidencePack, evidencePackHtml } from "@/lib/risk/evidence-pack";
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
    caseId?: string;
    transaction?: unknown;
    analystNotes?: string;
    auditTrail?: unknown;
  };
  const scenario = body.caseId ? getRiskScenarioByCaseId(body.caseId) : undefined;
  const transaction = scenario?.transaction ?? body.transaction;

  if (!body.caseId || !isP2PTransaction(transaction)) {
    return Response.json(
      { error: "Evidence export requires caseId and a valid synthetic transaction" },
      { status: 400 },
    );
  }

  const score = scoreTransaction(transaction);
  const pack = buildEvidencePack({
    caseId: body.caseId,
    transaction,
    score,
    graphSummary: scenario?.graphSummary ?? {
      nodes: [],
      links: [],
      clusters: [],
      graphScore: 0,
      suspiciousPath: "non fourni",
    },
    analystNotes: body.analystNotes,
    auditTrail: Array.isArray(body.auditTrail)
      ? (body.auditTrail as ReturnType<typeof buildEvidencePack>["auditTrail"])
      : undefined,
  });

  return Response.json({
    evidencePack: pack,
    printableHtml: evidencePackHtml(pack),
  });
}
