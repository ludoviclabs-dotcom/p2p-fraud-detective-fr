// Donnees structurelles locale-independantes de la demo guidee P2P.
// Toutes les valeurs sont fictives et de demonstration.

export type P2PSeverity = "critical" | "high" | "medium" | "low";

export type P2PCockpitMode = "cockpit" | "search" | "loading" | "results";

export type P2PDemoScene =
  | "cold-open"
  | "command-launch"
  | "cockpit-wide"
  | "search-zoom"
  | "data-cascade"
  | "supplier-row"
  | "case-file-open"
  | "score-breakdown"
  | "evidence-build"
  | "alert-sequence"
  | "review-path"
  | "final-summary";

export const FINAL_DEMO_SCENE: P2PDemoScene = "final-summary";

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
  points: number;
  evidenceId: string;
}

export const DEMO_REASON_CODES: DemoReasonCode[] = [
  { code: "IBAN_RING", severity: "critical", points: 30, evidenceId: "ev-iban" },
  { code: "THRESHOLD_SPLIT", severity: "high", points: 24, evidenceId: "ev-invoice" },
  { code: "FOUR_EYES_BREAK", severity: "high", points: 21, evidenceId: "ev-four-eyes" },
  { code: "RBE_MISMATCH", severity: "medium", points: 12, evidenceId: "ev-rbe" },
  { code: "SLA_UNASSIGNED", severity: "medium", points: 5, evidenceId: "ev-sla" },
];

export interface DemoEvidenceRef {
  id: string;
  hash: string;
  severity: P2PSeverity;
}

export const DEMO_EVIDENCE: DemoEvidenceRef[] = [
  { id: "ev-iban", hash: "ed25519:7f3a...91c2", severity: "critical" },
  { id: "ev-invoice", hash: "ed25519:93ab...4d20", severity: "high" },
  { id: "ev-four-eyes", hash: "ed25519:11dc...8fa1", severity: "high" },
  { id: "ev-rbe", hash: "ed25519:b9aa...31e7", severity: "medium" },
  { id: "ev-sla", hash: "ed25519:41f0...72ad", severity: "medium" },
];

export interface DemoAlertRef {
  id: string;
  severity: P2PSeverity;
  evidenceId: string;
}

export const DEMO_ALERTS: DemoAlertRef[] = [
  { id: "iban-ring", severity: "critical", evidenceId: "ev-iban" },
  { id: "threshold", severity: "high", evidenceId: "ev-invoice" },
  { id: "rbe", severity: "medium", evidenceId: "ev-rbe" },
  { id: "concentration", severity: "high", evidenceId: "ev-sla" },
];

export const DEMO_RAIL_STEPS = [
  "brief",
  "search",
  "cascade",
  "case360",
  "evidence",
  "recommendations",
] as const;

export type DemoRailStep = (typeof DEMO_RAIL_STEPS)[number];

export type DemoCameraPreset =
  | "cockpitWide"
  | "commandFocus"
  | "searchFocus"
  | "kpiFocus"
  | "supplierRowFocus"
  | "case360Focus"
  | "scoreFocus"
  | "evidenceFocus"
  | "reviewFocus"
  | "finalWide";

export interface CameraPreset {
  scale: number;
  x: number;
  y: number;
}

export const CAMERA_PRESETS: Record<DemoCameraPreset, CameraPreset> = {
  cockpitWide: { scale: 1, x: 0, y: 0 },
  commandFocus: { scale: 1.06, x: 0, y: 28 },
  searchFocus: { scale: 1.14, x: 0, y: 78 },
  kpiFocus: { scale: 1.18, x: -78, y: 36 },
  supplierRowFocus: { scale: 1.2, x: -42, y: -112 },
  case360Focus: { scale: 1.08, x: 0, y: 0 },
  scoreFocus: { scale: 1.14, x: 70, y: 10 },
  evidenceFocus: { scale: 1.12, x: -150, y: 0 },
  reviewFocus: { scale: 1.06, x: 0, y: 0 },
  finalWide: { scale: 1, x: 0, y: 0 },
};

export type P2PCalloutId =
  | "priority-score"
  | "global-search"
  | "critical-kpi"
  | "supplier-row"
  | "data-lineage"
  | "case-score"
  | "iban-ring"
  | "threshold-strip"
  | "rbe-mismatch"
  | "four-eyes"
  | "evidence-seal"
  | "review-human";

export type P2PConsoleEventId =
  | "init"
  | "load-case"
  | "query-supplier"
  | "fetch-ledger"
  | "scan-iban"
  | "detect-threshold"
  | "compare-rbe"
  | "compute-score"
  | "open-case"
  | "seal-evidence"
  | "prepare-review"
  | "packet-ready";

/**
 * Ancres DOM ciblees par le reticule d'analyse (focus). Chaque scene pointe
 * vers un element reel rendu *dans* le cadre camera ; le reticule mesure sa
 * position ecran (getBoundingClientRect relatif au stage) et se cale dessus.
 * Cela supprime tout decalage lie au pan/zoom de la camera ou au reflow
 * responsive — l'ancien systeme de pourcentages statiques etait, lui, calcule
 * dans le repere du stage et non du contenu transforme, d'ou les carres mal
 * places.
 */
export type DemoAnchorId =
  | "priority-card"
  | "mission-brief"
  | "search-bar"
  | "kpi-critical"
  | "supplier-row"
  | "data-lineage"
  | "case-gauge"
  | "score-total"
  | "evidence-drawer"
  | "findings-list"
  | "review-panel"
  | "audit-seal";

export interface DemoSceneConfig {
  id: P2PDemoScene;
  durationMs: number;
  camera: DemoCameraPreset;
  railStep: DemoRailStep;
  consoleEvents: P2PConsoleEventId[];
  callouts: P2PCalloutId[];
  /** Element reel encadre par le reticule pour cette scene (ancre mesuree). */
  focus?: DemoAnchorId;
  cockpitMode?: P2PCockpitMode;
}

/** Severite portee par chaque notification du flux de signaux (toasts). */
export const CALLOUT_SEVERITY: Record<P2PCalloutId, P2PSeverity> = {
  "priority-score": "critical",
  "global-search": "low",
  "critical-kpi": "high",
  "supplier-row": "critical",
  "data-lineage": "medium",
  "case-score": "high",
  "iban-ring": "critical",
  "threshold-strip": "high",
  "rbe-mismatch": "medium",
  "four-eyes": "high",
  "evidence-seal": "low",
  "review-human": "medium",
};

export const DEMO_SCENES: DemoSceneConfig[] = [
  {
    id: "cold-open",
    durationMs: 3500,
    camera: "cockpitWide",
    railStep: "brief",
    consoleEvents: ["init", "load-case"],
    callouts: ["priority-score"],
    focus: "priority-card",
    cockpitMode: "cockpit",
  },
  {
    id: "command-launch",
    durationMs: 4500,
    camera: "commandFocus",
    railStep: "brief",
    consoleEvents: ["init", "load-case"],
    callouts: ["review-human"],
    focus: "mission-brief",
  },
  {
    id: "cockpit-wide",
    durationMs: 4500,
    camera: "cockpitWide",
    railStep: "search",
    consoleEvents: ["query-supplier"],
    callouts: ["global-search", "critical-kpi"],
    focus: "search-bar",
    cockpitMode: "cockpit",
  },
  {
    id: "search-zoom",
    durationMs: 5000,
    camera: "searchFocus",
    railStep: "search",
    consoleEvents: ["query-supplier"],
    callouts: ["global-search"],
    focus: "search-bar",
    cockpitMode: "search",
  },
  {
    id: "data-cascade",
    durationMs: 6500,
    camera: "kpiFocus",
    railStep: "cascade",
    consoleEvents: ["fetch-ledger", "scan-iban", "detect-threshold", "compare-rbe"],
    callouts: ["data-lineage", "critical-kpi"],
    focus: "data-lineage",
    cockpitMode: "loading",
  },
  {
    id: "supplier-row",
    durationMs: 4500,
    camera: "supplierRowFocus",
    railStep: "cascade",
    consoleEvents: ["compute-score"],
    callouts: ["supplier-row"],
    focus: "supplier-row",
    cockpitMode: "results",
  },
  {
    id: "case-file-open",
    durationMs: 5000,
    camera: "case360Focus",
    railStep: "case360",
    consoleEvents: ["open-case"],
    callouts: ["case-score"],
    focus: "case-gauge",
  },
  {
    id: "score-breakdown",
    durationMs: 6000,
    camera: "scoreFocus",
    railStep: "case360",
    consoleEvents: ["compute-score"],
    callouts: ["case-score", "iban-ring", "threshold-strip"],
    focus: "score-total",
  },
  {
    id: "evidence-build",
    durationMs: 6000,
    camera: "evidenceFocus",
    railStep: "evidence",
    consoleEvents: ["seal-evidence"],
    callouts: ["rbe-mismatch", "four-eyes", "evidence-seal"],
    focus: "evidence-drawer",
  },
  {
    id: "alert-sequence",
    durationMs: 5500,
    camera: "reviewFocus",
    railStep: "evidence",
    consoleEvents: ["seal-evidence"],
    callouts: ["iban-ring", "threshold-strip", "evidence-seal"],
    focus: "findings-list",
  },
  {
    id: "review-path",
    durationMs: 4000,
    camera: "reviewFocus",
    railStep: "recommendations",
    consoleEvents: ["prepare-review"],
    callouts: ["review-human"],
    focus: "review-panel",
  },
  {
    id: "final-summary",
    durationMs: 4000,
    camera: "finalWide",
    railStep: "recommendations",
    consoleEvents: ["packet-ready"],
    callouts: ["evidence-seal", "review-human"],
    focus: "audit-seal",
  },
];

export const DEMO_SCENE_IDS = DEMO_SCENES.map((scene) => scene.id);

export const DEMO_TOTAL_DURATION_MS = DEMO_SCENES.reduce(
  (total, scene) => total + scene.durationMs,
  0,
);

export const SCENE_TO_RAIL = DEMO_SCENES.reduce(
  (acc, scene) => {
    acc[scene.id] = scene.railStep;
    return acc;
  },
  {} as Record<P2PDemoScene, DemoRailStep>,
);

export const DEMO_FORBIDDEN_TERMS = [
  "fraude confirmée",
  "fraude confirmee",
  "coupable",
  "TRACFIN automatique",
  "notification automatique TRACFIN",
];
