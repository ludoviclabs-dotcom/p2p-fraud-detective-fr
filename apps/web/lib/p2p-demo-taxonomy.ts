import type { Severity } from "@/types/p2p";

export const SEVERITY_ORDER: Record<Severity, number> = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
};

export const SEVERITY_LABELS: Record<Severity, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

export const SEVERITY_COLORS: Record<Severity, string> = {
  low: "#3E7C5A",
  medium: "#C97B1F",
  high: "#D35F2A",
  critical: "#A23E48",
};

export const SIGNAL_LABELS: Record<string, string> = {
  amount_just_under_threshold: "Sous seuils",
  duplicate_exact: "Doublons exacts",
  duplicate_fuzzy: "Doublons proches",
  shared_iban_ring: "Anneaux IBAN partages",
  vendor_cluster: "Clusters fournisseurs",
};

export const SIGNAL_ORDER = [
  "shared_iban_ring",
  "vendor_cluster",
  "duplicate_exact",
  "duplicate_fuzzy",
  "amount_just_under_threshold",
];

export function getSignalLabel(signal: string): string {
  return SIGNAL_LABELS[signal] ?? signal.replaceAll("_", " ");
}
