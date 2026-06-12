// Données structurelles (locale-indépendantes) de la démo guidée P2P.
//
// Toutes les valeurs sont FICTIVES et de DÉMONSTRATION. Les libellés et la
// narration vivent dans `p2p-demo-content.ts` (bilingue), fusionnés par `id`/`code`.
// Les KPI et la ligne V00474 sont alignés sur la démo du cockpit (`/dashboard`).

export type P2PSeverity = "critical" | "high" | "medium" | "low";

export type P2PDemoPhase =
  | "preflight"
  | "cockpit"
  | "search"
  | "loading"
  | "results"
  | "case360"
  | "evidence"
  | "alerts"
  | "recommendations"
  | "final";

export const DEMO_PHASES: P2PDemoPhase[] = [
  "preflight",
  "cockpit",
  "search",
  "loading",
  "results",
  "case360",
  "evidence",
  "alerts",
  "recommendations",
  "final",
];

export const DEMO_SUPPLIER = {
  id: "V00474",
  name: "ALPHACOM SERVICES",
  siren: "812 446 901",
  score: 92,
  exposure: 4_706_422,
  severity: "critical" as P2PSeverity,
};

export const DEMO_KPIS = {
  totalExposure: 6_579_354,
  criticalExposure: 1_671_619,
  openCases: 383,
  lateSla: 341,
};

export interface DemoVendorRow {
  id: string;
  exposure: number;
  findings: number;
  severity: P2PSeverity;
}

// Aligné sur la table « Top fournisseurs par exposition » du cockpit démo.
export const DEMO_VENDORS: DemoVendorRow[] = [
  { id: "V00474", exposure: 4_706_422, findings: 173, severity: "critical" },
  { id: "V00444", exposure: 105_441, findings: 4, severity: "critical" },
  { id: "V00343", exposure: 98_598, findings: 7, severity: "critical" },
  { id: "V00167", exposure: 83_732, findings: 4, severity: "critical" },
  { id: "V00132", exposure: 52_967, findings: 6, severity: "critical" },
  { id: "V00237", exposure: 51_951, findings: 6, severity: "critical" },
];

export interface DemoReasonCode {
  code: string;
  severity: P2PSeverity;
}

export const DEMO_REASON_CODES: DemoReasonCode[] = [
  { code: "IBAN_RING", severity: "critical" },
  { code: "THRESHOLD_SPLIT", severity: "high" },
  { code: "FOUR_EYES_BREAK", severity: "high" },
  { code: "RBE_MISMATCH", severity: "medium" },
];

export interface DemoEvidenceRef {
  id: string;
  hash: string;
  severity: P2PSeverity;
}

export const DEMO_EVIDENCE: DemoEvidenceRef[] = [
  { id: "ev-iban", hash: "ed25519:7f3a…91c2", severity: "critical" },
  { id: "ev-invoice", hash: "ed25519:93ab…4d20", severity: "high" },
  { id: "ev-four-eyes", hash: "ed25519:11dc…8fa1", severity: "high" },
  { id: "ev-rbe", hash: "ed25519:b9aa…31e7", severity: "medium" },
];

export interface DemoAlertRef {
  id: string;
  severity: P2PSeverity;
}

export const DEMO_ALERTS: DemoAlertRef[] = [
  { id: "iban-ring", severity: "critical" },
  { id: "threshold", severity: "high" },
  { id: "rbe", severity: "medium" },
  { id: "concentration", severity: "high" },
];

// Étapes du rail de progression (libellés fournis par le contenu bilingue).
export const DEMO_RAIL_STEPS = [
  "brief",
  "search",
  "cascade",
  "case360",
  "evidence",
  "recommendations",
] as const;

export type DemoRailStep = (typeof DEMO_RAIL_STEPS)[number];

// Quelle étape du rail est active pour une phase donnée.
export const PHASE_TO_RAIL: Record<P2PDemoPhase, DemoRailStep> = {
  preflight: "brief",
  cockpit: "search",
  search: "search",
  loading: "cascade",
  results: "cascade",
  case360: "case360",
  evidence: "evidence",
  alerts: "evidence",
  recommendations: "recommendations",
  final: "recommendations",
};
