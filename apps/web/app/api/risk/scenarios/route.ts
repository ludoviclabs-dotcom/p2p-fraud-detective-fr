import { getRiskScenarioFeed } from "@/lib/risk/scenario-source";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const feed = await getRiskScenarioFeed();
  return Response.json({
    ...feed,
    disclaimer:
      "Scénarios synthétiques pour démonstrateur professionnel. Aucune donnée personnelle réelle.",
  });
}
