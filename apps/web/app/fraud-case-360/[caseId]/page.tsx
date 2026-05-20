import { notFound } from "next/navigation";
import { getRiskScenarioByCaseId } from "@/data/risk-scenarios";
import { scoreTransaction } from "@/lib/risk/scoreEngine";
import { FraudCase360Client } from "@/app/fraud-case-360/[caseId]/fraud-case-360-client";

type Params = Promise<{ caseId: string }>;

export default async function FraudCase360Page({ params }: { params: Params }) {
  const { caseId } = await params;
  const scenario = getRiskScenarioByCaseId(decodeURIComponent(caseId));
  if (!scenario) notFound();

  return (
    <FraudCase360Client
      scenario={scenario}
      score={scoreTransaction(scenario.transaction)}
    />
  );
}
