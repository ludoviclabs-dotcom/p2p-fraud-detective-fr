export type PaymentRail = "SEPA" | "SEPA_INSTANT" | "P2P" | "WIRE" | "CARD";

export type RiskDecision =
  | "ALLOW"
  | "MONITOR"
  | "MANUAL_REVIEW"
  | "BLOCK_RECOMMENDED";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type FraudTypology =
  | "NORMAL_PAYMENT"
  | "APP_FRAUD_BANK_IMPERSONATION"
  | "APP_FRAUD_SOCIAL_ENGINEERING"
  | "SUPPLIER_RIB_FRAUD"
  | "QR_CODE_FRAUD"
  | "MULE_ACCOUNT_NETWORK"
  | "ROMANCE_INVESTMENT_SCAM"
  | "SANCTIONS_OR_PEP"
  | "DOCUMENT_INVOICE_FRAUD";

export type DetectorId =
  | "beneficiaryTrust"
  | "scamNarrative"
  | "velocity"
  | "deviceSession"
  | "qrRisk"
  | "graphRisk"
  | "documentRibRisk"
  | "sanctionsRisk";

export type DetectorStatus = "active" | "demo" | "mock";

export type IbanNameMatch = "match" | "close_match" | "no_match" | "unavailable";

export interface ReasonCode {
  code: string;
  label: string;
  description: string;
  detector: DetectorId;
  weight: number;
  severity: RiskLevel;
  evidence?: Record<string, string | number | boolean | null>;
}

export interface DetectorScore {
  detector: DetectorId;
  label: string;
  status: DetectorStatus;
  score: number;
  maxScore: number;
  signals: string[];
  dataUsed: string[];
  reasonCodes: ReasonCode[];
  explanation: string;
}

export interface P2PTransaction {
  transactionId: string;
  caseId?: string;
  createdAt: string;
  amount: number;
  currency: "EUR" | string;
  rail: PaymentRail;
  isInstant?: boolean;
  channel?: "web" | "mobile" | "branch" | "api" | "invoice_portal";
  payer: {
    id: string;
    displayName: string;
    usualCountry?: string;
    historicalAverageAmount?: number;
    recentPaymentCount24h?: number;
    recentNewBeneficiaries24h?: number;
    splitPaymentsCount24h?: number;
    approvalThresholdEur?: number;
  };
  beneficiary: {
    id: string;
    name: string;
    expectedName?: string;
    iban: string;
    expectedIban?: string;
    ibanCountry?: string;
    accountAgeDays?: number;
    addedHoursAgo?: number;
    firstPayment?: boolean;
    sharedIbanCount?: number;
    linkedPayersCount?: number;
    supplierRibChangedDaysAgo?: number;
    vendorCreatedDaysAgo?: number;
  };
  narrative?: {
    text: string;
  };
  device?: {
    id: string;
    seenBefore?: boolean;
    ipCountry?: string;
    usualCountry?: string;
    remoteAccessDetected?: boolean;
    impossibleTravel?: boolean;
    vpnOrProxy?: boolean;
    phoneChangedHoursAgo?: number;
    emailChangedHoursAgo?: number;
  };
  qr?: {
    payload: string;
    expectedIban?: string;
    expectedDomain?: string;
  };
  document?: {
    type?: "RIB" | "invoice" | "payment_request";
    ibanOnDocument?: string;
    expectedIban?: string;
    beneficiaryNameOnDocument?: string;
    expectedBeneficiaryName?: string;
    ribChangeRequested?: boolean;
    invoiceNumber?: string;
    suspiciousFormatting?: boolean;
  };
  graph?: {
    clusterId?: string;
    clusterRiskScore?: number;
    sharedDeviceCount?: number;
    sharedIbanCount?: number;
    linkedPayersCount?: number;
    suspiciousPath?: string[];
  };
  sanctions?: {
    sanctionsHit?: boolean;
    pepHit?: boolean;
    highRiskCountry?: boolean;
    listName?: string;
    matchName?: string;
  };
  analystContext?: {
    notes?: string;
    expectedCounterparty?: string;
  };
}

export interface RiskScoreResult {
  score: number;
  level: RiskLevel;
  decision: RiskDecision;
  typology: FraudTypology;
  reasonCodes: ReasonCode[];
  detectorScores: DetectorScore[];
  recommendedActions: string[];
  modelVersion: "risk-engine-demo-v1";
  generatedAt: string;
}

export interface RiskGraphSummary {
  nodes: { id: string; label: string; kind: string; risk?: RiskLevel }[];
  links: { source: string; target: string; label: string }[];
  clusters: string[];
  graphScore: number;
  suspiciousPath: string;
}

export interface RiskScenario {
  id: string;
  caseId: string;
  title: string;
  shortTitle: string;
  description: string;
  businessContext: string;
  transaction: P2PTransaction;
  expectedTypology: FraudTypology;
  graphSummary: RiskGraphSummary;
}

export interface EvidenceSourceRef {
  id: string;
  label: string;
  kind: "transaction" | "detector" | "graph" | "audit" | "analyst_note";
  claim: string;
  confidence: "synthetic" | "demo" | "derived";
  method?: string;
}

export interface EvidenceTimelineEvent {
  at: string;
  actor: string;
  event: string;
  detail: string;
}

export interface EvidenceAuditEntry {
  at: string;
  actor: string;
  action: string;
  detail: string;
  prevHash?: string;
  hash?: string;
  signature?: string;
  integrityStatus?: "verified" | "unsigned";
}

export interface EvidenceIntegrity {
  algorithm: "sha256-demo-chain";
  rootHash: string;
  chainValid: boolean;
  signedEntries: number;
  verificationRoute: "/audit";
  generatedBy: "risk-engine-demo-v1";
}

export interface EvidencePack {
  caseId: string;
  generatedAt: string;
  transaction: P2PTransaction;
  score: RiskScoreResult;
  typology: FraudTypology;
  decision: RiskDecision;
  reasonCodes: ReasonCode[];
  detectorScores: DetectorScore[];
  timeline: EvidenceTimelineEvent[];
  graphSummary: RiskGraphSummary;
  sourceRefs: EvidenceSourceRef[];
  recommendedActions: string[];
  analystNotes: string;
  auditTrail: EvidenceAuditEntry[];
  integrity: EvidenceIntegrity;
  disclaimer: string;
}
