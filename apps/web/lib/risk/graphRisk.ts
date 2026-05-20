import type { DetectorScore, P2PTransaction, ReasonCode } from "@/types/risk";
import { detectorResult, reason } from "@/lib/risk/risk-utils";

export function graphRisk(transaction: P2PTransaction): DetectorScore {
  const reasons: ReasonCode[] = [];
  const graph = transaction.graph;
  if (!graph) {
    return detectorResult({
      detector: "graphRisk",
      label: "Mule Account / Fraud Graph",
      status: "demo",
      maxScore: 24,
      dataUsed: ["graph signals unavailable"],
      reasonCodes: reasons,
      explanationWhenEmpty: "Aucun signal graphe fourni pour ce scénario.",
    });
  }

  if ((graph.clusterRiskScore ?? 0) >= 70) {
    reasons.push(
      reason(
        "graphRisk",
        "GRAPH_HIGH_RISK_CLUSTER",
        "Cluster graphe à risque",
        "Le bénéficiaire appartient à un cluster synthétique à risque élevé.",
        16,
        { clusterId: graph.clusterId ?? null, clusterRiskScore: graph.clusterRiskScore ?? 0 },
      ),
    );
  }

  if ((graph.linkedPayersCount ?? 0) >= 3) {
    reasons.push(
      reason(
        "graphRisk",
        "GRAPH_MULE_LINKED_PAYERS",
        "Multiples payeurs reliés",
        "Le compte bénéficiaire est relié à plusieurs payeurs, signal possible de mule account.",
        14,
        { linkedPayersCount: graph.linkedPayersCount ?? 0 },
      ),
    );
  }

  if ((graph.sharedDeviceCount ?? 0) >= 2) {
    reasons.push(
      reason(
        "graphRisk",
        "GRAPH_SHARED_DEVICE",
        "Appareil partagé",
        "Un même appareil est relié à plusieurs identités ou transactions synthétiques.",
        10,
        { sharedDeviceCount: graph.sharedDeviceCount ?? 0 },
      ),
    );
  }

  if ((graph.sharedIbanCount ?? 0) >= 2) {
    reasons.push(
      reason(
        "graphRisk",
        "GRAPH_SHARED_IBAN",
        "IBAN partagé dans le graphe",
        "L'IBAN relie plusieurs contreparties dans le graphe d'investigation.",
        12,
        { sharedIbanCount: graph.sharedIbanCount ?? 0 },
      ),
    );
  }

  if (graph.suspiciousPath?.length && graph.suspiciousPath.length >= 4) {
    reasons.push(
      reason(
        "graphRisk",
        "GRAPH_SUSPICIOUS_PATH",
        "Chemin suspect expliqué",
        "Un chemin graphe relie payeur, bénéficiaire, IBAN, appareil ou case existant.",
        8,
        { pathLength: graph.suspiciousPath.length },
      ),
    );
  }

  return detectorResult({
    detector: "graphRisk",
    label: "Mule Account / Fraud Graph",
    status: "demo",
    maxScore: 26,
    dataUsed: ["clusterRiskScore", "linkedPayersCount", "sharedDeviceCount", "suspiciousPath"],
    reasonCodes: reasons,
    explanationWhenEmpty: "Aucun motif graphe significatif dans le réseau synthétique.",
  });
}
