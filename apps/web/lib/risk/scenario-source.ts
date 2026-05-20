import { RISK_SCENARIOS } from "@/data/risk-scenarios";
import { isP2PTransaction } from "@/lib/risk/scoreEngine";
import type { RiskScenario } from "@/types/risk";

export type ScenarioFeed = {
  source: "huggingface" | "local";
  scenarios: RiskScenario[];
  message: string;
};

export async function getRiskScenarioFeed(): Promise<ScenarioFeed> {
  const url = process.env.HF_SYNTHETIC_SCENARIOS_URL;
  if (!url) {
    return {
      source: "local",
      scenarios: RISK_SCENARIOS,
      message:
        "Source locale de démo utilisée. Connectez HF_SYNTHETIC_SCENARIOS_URL pour charger des scénarios Hugging Face.",
    };
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2500);
    const headers = new Headers({ Accept: "application/json" });
    if (process.env.HF_TOKEN) {
      headers.set("Authorization", `Bearer ${process.env.HF_TOKEN}`);
    }
    const response = await fetch(url, {
      headers,
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Hugging Face returned ${response.status}`);
    }

    const payload = (await response.json()) as unknown;
    const scenarios = parseScenarioPayload(payload);
    if (!scenarios.length) {
      throw new Error("Hugging Face payload does not contain valid scenarios");
    }

    return {
      source: "huggingface",
      scenarios,
      message: "Scénarios synthétiques chargés depuis Hugging Face.",
    };
  } catch (error) {
    return {
      source: "local",
      scenarios: RISK_SCENARIOS,
      message: `Source locale de démo utilisée après échec Hugging Face: ${
        error instanceof Error ? error.message : "erreur inconnue"
      }.`,
    };
  }
}

function parseScenarioPayload(payload: unknown): RiskScenario[] {
  const value = payload as { scenarios?: unknown };
  const list = Array.isArray(payload)
    ? payload
    : Array.isArray(value.scenarios)
      ? value.scenarios
      : [];

  return list.filter(isRiskScenario);
}

function isRiskScenario(value: unknown): value is RiskScenario {
  if (!value || typeof value !== "object") return false;
  const scenario = value as Partial<RiskScenario>;
  return (
    typeof scenario.id === "string" &&
    typeof scenario.caseId === "string" &&
    typeof scenario.title === "string" &&
    typeof scenario.description === "string" &&
    isP2PTransaction(scenario.transaction) &&
    Boolean(scenario.graphSummary)
  );
}
