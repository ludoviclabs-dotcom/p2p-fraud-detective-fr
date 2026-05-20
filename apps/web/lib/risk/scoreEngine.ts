import type {
  DetectorScore,
  FraudTypology,
  P2PTransaction,
  ReasonCode,
  RiskDecision,
  RiskLevel,
  RiskScoreResult,
} from "@/types/risk";
import { beneficiaryTrust } from "@/lib/risk/beneficiaryTrust";
import { deviceSession } from "@/lib/risk/deviceSession";
import { documentRibRisk } from "@/lib/risk/documentRibRisk";
import { graphRisk } from "@/lib/risk/graphRisk";
import { qrRisk } from "@/lib/risk/qrRisk";
import { sanctionsRisk } from "@/lib/risk/sanctionsRisk";
import { scamNarrative } from "@/lib/risk/scamNarrative";
import { clampScore } from "@/lib/risk/risk-utils";
import { velocity } from "@/lib/risk/velocity";

export const RISK_ENGINE_MODEL_VERSION = "risk-engine-demo-v1" as const;

export function scoreTransaction(transaction: P2PTransaction): RiskScoreResult {
  const detectorScores = runDetectors(transaction);
  const reasonCodes = detectorScores.flatMap((detector) => detector.reasonCodes);
  const score = clampScore(
    detectorScores.reduce((total, detector) => total + detector.score, 0),
  );
  const level = riskLevel(score);
  const typology = inferTypology(reasonCodes);
  const decision = riskDecision(score, reasonCodes);

  return {
    score,
    level,
    decision,
    typology,
    reasonCodes,
    detectorScores,
    recommendedActions: recommendedActions(level, typology, reasonCodes),
    modelVersion: RISK_ENGINE_MODEL_VERSION,
    generatedAt: new Date().toISOString(),
  };
}

export function runDetectors(transaction: P2PTransaction): DetectorScore[] {
  return [
    beneficiaryTrust(transaction),
    scamNarrative(transaction),
    velocity(transaction),
    deviceSession(transaction),
    qrRisk(transaction),
    graphRisk(transaction),
    documentRibRisk(transaction),
    sanctionsRisk(transaction),
  ];
}

export function riskLevel(score: number): RiskLevel {
  if (score >= 75) return "CRITICAL";
  if (score >= 50) return "HIGH";
  if (score >= 25) return "MEDIUM";
  return "LOW";
}

export function riskDecision(score: number, reasonCodes: ReasonCode[]): RiskDecision {
  const codes = new Set(reasonCodes.map((item) => item.code));
  if (
    score >= 85 ||
    codes.has("SANCTIONS_POSSIBLE_HIT") ||
    codes.has("QR_IBAN_MISMATCH")
  ) {
    return "BLOCK_RECOMMENDED";
  }
  if (score >= 50) return "MANUAL_REVIEW";
  if (score >= 25) return "MONITOR";
  return "ALLOW";
}

export function inferTypology(reasonCodes: ReasonCode[]): FraudTypology {
  const codes = new Set(reasonCodes.map((item) => item.code));

  if (codes.has("SANCTIONS_POSSIBLE_HIT") || codes.has("PEP_POSSIBLE_HIT")) {
    return "SANCTIONS_OR_PEP";
  }
  if (codes.has("QR_IBAN_MISMATCH") || codes.has("QR_SUSPICIOUS_URL")) {
    return "QR_CODE_FRAUD";
  }
  if (
    codes.has("SUPPLIER_RIB_RECENT_CHANGE") ||
    codes.has("DOCUMENT_RIB_CHANGE_REQUEST") ||
    codes.has("DOCUMENT_IBAN_MISMATCH")
  ) {
    return "SUPPLIER_RIB_FRAUD";
  }
  if (codes.has("NARRATIVE_ROMANCE") || codes.has("NARRATIVE_INVESTMENT")) {
    return "ROMANCE_INVESTMENT_SCAM";
  }
  if (
    codes.has("NARRATIVE_AUTHORITY_IMPERSONATION") &&
    codes.has("NARRATIVE_SAFE_ACCOUNT")
  ) {
    return "APP_FRAUD_BANK_IMPERSONATION";
  }
  if (
    codes.has("GRAPH_HIGH_RISK_CLUSTER") ||
    codes.has("GRAPH_MULE_LINKED_PAYERS")
  ) {
    return "MULE_ACCOUNT_NETWORK";
  }
  if (
    codes.has("NARRATIVE_URGENCY") ||
    codes.has("NARRATIVE_SECRECY") ||
    codes.has("NARRATIVE_TECH_SUPPORT")
  ) {
    return "APP_FRAUD_SOCIAL_ENGINEERING";
  }
  if (codes.has("DOCUMENT_FORMATTING_ANOMALY") || codes.has("DOCUMENT_NAME_MISMATCH")) {
    return "DOCUMENT_INVOICE_FRAUD";
  }
  return "NORMAL_PAYMENT";
}

export function recommendedActions(
  level: RiskLevel,
  typology: FraudTypology,
  reasonCodes: ReasonCode[],
): string[] {
  const actions = new Set<string>();
  const codes = new Set(reasonCodes.map((item) => item.code));

  if (level === "CRITICAL") {
    actions.add("Suspendre le paiement dans le démonstrateur et ouvrir une revue humaine.");
  } else if (level === "HIGH") {
    actions.add("Mettre en revue manuelle avant exécution ou libération.");
  } else if (level === "MEDIUM") {
    actions.add("Surveiller et documenter les signaux avant validation.");
  } else {
    actions.add("Autoriser avec journalisation standard de démonstration.");
  }

  if (typology === "APP_FRAUD_BANK_IMPERSONATION") {
    actions.add("Réaliser un contre-appel via un canal connu, jamais via le contact fourni dans la demande.");
  }
  if (typology === "SUPPLIER_RIB_FRAUD") {
    actions.add("Vérifier le changement RIB avec le fournisseur via le processus 4-eyes.");
  }
  if (typology === "QR_CODE_FRAUD") {
    actions.add("Comparer le payload QR avec la facture et bloquer si IBAN ou domaine divergent.");
  }
  if (typology === "MULE_ACCOUNT_NETWORK") {
    actions.add("Explorer le graphe payeur-bénéficiaire-IBAN-device et rechercher des cases reliés.");
  }
  if (typology === "SANCTIONS_OR_PEP") {
    actions.add("Escalader conformité AML/LCB-FT et conserver la preuve de revue.");
  }
  if (codes.has("NARRATIVE_URGENCY")) {
    actions.add("Demander une confirmation hors canal initial et retirer la pression temporelle.");
  }
  if (codes.has("IBAN_NAME_MISMATCH")) {
    actions.add("Documenter le résultat de vérification nom/IBAN simulé avant toute décision.");
  }

  actions.add("Rappeler que la décision finale reste humaine et que les données sont synthétiques.");
  return Array.from(actions);
}

export function isP2PTransaction(value: unknown): value is P2PTransaction {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<P2PTransaction>;
  return (
    typeof candidate.transactionId === "string" &&
    typeof candidate.createdAt === "string" &&
    typeof candidate.amount === "number" &&
    typeof candidate.currency === "string" &&
    typeof candidate.rail === "string" &&
    Boolean(candidate.payer?.id) &&
    Boolean(candidate.beneficiary?.id) &&
    Boolean(candidate.beneficiary?.iban)
  );
}
