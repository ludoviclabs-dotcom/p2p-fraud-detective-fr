import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import type { RiskScenario } from "@/types/risk";

const SIGNAL_TO_SCENARIO_ID: Record<string, string> = {
  amount_just_under_threshold: "supplier-rib-change",
  duplicate_exact: "supplier-rib-change",
  duplicate_fuzzy: "supplier-rib-change",
  shared_iban_ring: "mule-account-network",
  vendor_cluster: "mule-account-network",
};

export function case360Href(caseId: string): string {
  return `/fraud-case-360/${encodeURIComponent(caseId)}`;
}

export function getScenarioForP2PFindingSignal(signal: string): RiskScenario {
  const scenarioId = SIGNAL_TO_SCENARIO_ID[signal] ?? "supplier-rib-change";
  return (
    RISK_SCENARIOS.find((scenario) => scenario.id === scenarioId) ??
    RISK_SCENARIOS[0]
  );
}

export function getPrimaryCase360Scenario(): RiskScenario {
  return RISK_SCENARIOS[0];
}
