import type { DetectorScore, P2PTransaction, ReasonCode } from "@/types/risk";
import { detectorResult, reason } from "@/lib/risk/risk-utils";

export function sanctionsRisk(transaction: P2PTransaction): DetectorScore {
  const reasons: ReasonCode[] = [];
  const sanctions = transaction.sanctions;
  if (!sanctions) {
    return detectorResult({
      detector: "sanctionsRisk",
      label: "Sanctions / PEP / AML Screening",
      status: "mock",
      maxScore: 30,
      dataUsed: ["sanctions mock unavailable"],
      reasonCodes: reasons,
      explanationWhenEmpty: "Aucun signal sanctions/PEP fourni pour ce scénario.",
    });
  }

  if (sanctions.sanctionsHit) {
    reasons.push(
      reason(
        "sanctionsRisk",
        "SANCTIONS_POSSIBLE_HIT",
        "Match sanctions simulé",
        "Le bénéficiaire présente un match sanctions synthétique à revue obligatoire.",
        28,
        { listName: sanctions.listName ?? null, matchName: sanctions.matchName ?? null },
      ),
    );
  }

  if (sanctions.pepHit) {
    reasons.push(
      reason(
        "sanctionsRisk",
        "PEP_POSSIBLE_HIT",
        "Match PEP simulé",
        "Le bénéficiaire présente un signal PEP synthétique à documenter.",
        18,
        { listName: sanctions.listName ?? null, matchName: sanctions.matchName ?? null },
      ),
    );
  }

  if (sanctions.highRiskCountry) {
    reasons.push(
      reason(
        "sanctionsRisk",
        "HIGH_RISK_COUNTRY",
        "Pays sensible",
        "Le pays de contrepartie est marqué sensible dans la donnée de démonstration.",
        12,
      ),
    );
  }

  return detectorResult({
    detector: "sanctionsRisk",
    label: "Sanctions / PEP / AML Screening",
    status: "mock",
    maxScore: 30,
    dataUsed: ["sanctionsHit", "pepHit", "highRiskCountry"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Aucun signal sanctions ou PEP dans le scénario synthétique.",
  });
}
