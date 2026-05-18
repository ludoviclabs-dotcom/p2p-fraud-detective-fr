export type Severity = "low" | "medium" | "high" | "critical";

export type GraphNodeKind = "vendor" | "iban" | "finding";

export interface GraphNode {
  id: string;
  kind: GraphNodeKind;
  label: string;
  severity: Severity;
  riskScore: number;
  exposureEur: number;
  maskedValue: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  kind: "uses_iban" | "has_finding" | "evidences" | string;
  weight: number;
  findingIds: string[];
}

export interface FindingSummary {
  id: string;
  invoiceId: string;
  vendorName: string;
  vendorId: string;
  ruleId: string;
  severity: Severity;
  signal: string;
  exposureEur: number;
  riskScore: number;
  evidence: Record<string, unknown>;
}

export interface VendorSummary {
  id: string;
  vendorId: string;
  name: string;
  siren: string | null;
  apeCode: string | null;
  severity: Severity;
  riskScore: number;
  exposureEur: number;
  findingIds: string[];
}

export interface P2PMetrics {
  invoiceCount: number;
  findingCount: number;
  vendorCount: number;
  ibanNodeCount: number;
  edgeCount: number;
  sharedIbanRings: number;
  vendorClusters: number;
  largestClusterSize: number;
  criticalFindings: number;
  highFindings: number;
  mediumFindings: number;
  signalCounts: Record<string, number>;
  exposureEur: number;
}

export interface P2PDemoDataset {
  generatedAt: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  findings: FindingSummary[];
  vendors: VendorSummary[];
  metrics: P2PMetrics;
}
