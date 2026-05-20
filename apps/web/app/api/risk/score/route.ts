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

  const transaction =
    payload && typeof payload === "object" && "transaction" in payload
      ? (payload as { transaction: unknown }).transaction
      : payload;

  if (!isP2PTransaction(transaction)) {
    return Response.json(
      {
        error: "Invalid P2PTransaction",
        hint: "Envoyer une transaction synthétique avec transactionId, amount, currency, rail, payer et beneficiary.",
      },
      { status: 400 },
    );
  }

  return Response.json(scoreTransaction(transaction));
}
