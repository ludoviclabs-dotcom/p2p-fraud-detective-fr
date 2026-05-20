import type { DetectorId, DetectorScore, DetectorStatus, ReasonCode, RiskLevel } from "@/types/risk";

export function clampScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

export function normalizeText(value: string | undefined): string {
  return (value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

export function includesAny(text: string | undefined, patterns: string[]): boolean {
  const normalized = normalizeText(text);
  return patterns.some((pattern) => normalized.includes(normalizeText(pattern)));
}

export function extractIban(value: string | undefined): string | null {
  const compact = (value ?? "").replace(/\s+/g, "").toUpperCase();
  const match = compact.match(/[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}/);
  return match?.[0] ?? null;
}

export function maskIban(iban: string | undefined): string {
  if (!iban) return "unavailable";
  const compact = iban.replace(/\s+/g, "").toUpperCase();
  if (compact.length <= 8) return compact;
  return `${compact.slice(0, 4)}••••••••${compact.slice(-4)}`;
}

export function ibanCountry(iban: string | undefined): string | undefined {
  const compact = iban?.replace(/\s+/g, "").toUpperCase();
  return compact?.slice(0, 2);
}

export function domainFromUrl(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return new URL(value).hostname.replace(/^www\./, "").toLowerCase();
  } catch {
    const match = value.match(/https?:\/\/([^/\s]+)/i);
    return match?.[1]?.replace(/^www\./, "").toLowerCase() ?? null;
  }
}

export function simpleSimilarity(a: string | undefined, b: string | undefined): number {
  const left = normalizeText(a).replace(/[^a-z0-9]/g, "");
  const right = normalizeText(b).replace(/[^a-z0-9]/g, "");
  if (!left || !right) return 0;
  if (left === right) return 1;
  const shorter = left.length < right.length ? left : right;
  const longer = left.length >= right.length ? left : right;
  let overlap = 0;
  for (let index = 0; index < shorter.length; index += 1) {
    if (longer.includes(shorter.slice(index, index + 2))) overlap += 1;
  }
  return Math.min(1, overlap / Math.max(shorter.length - 1, 1));
}

export function levelFromContribution(weight: number): RiskLevel {
  if (weight >= 22) return "CRITICAL";
  if (weight >= 14) return "HIGH";
  if (weight >= 8) return "MEDIUM";
  return "LOW";
}

export function reason(
  detector: DetectorId,
  code: string,
  label: string,
  description: string,
  weight: number,
  evidence?: ReasonCode["evidence"],
): ReasonCode {
  return {
    detector,
    code,
    label,
    description,
    weight,
    severity: levelFromContribution(weight),
    evidence,
  };
}

export function detectorResult(input: {
  detector: DetectorId;
  label: string;
  status?: DetectorStatus;
  maxScore: number;
  dataUsed: string[];
  reasonCodes: ReasonCode[];
  explanationWhenEmpty: string;
}): DetectorScore {
  const score = clampScore(
    Math.min(
      input.maxScore,
      input.reasonCodes.reduce((total, item) => total + item.weight, 0),
    ),
  );

  return {
    detector: input.detector,
    label: input.label,
    status: input.status ?? "active",
    maxScore: input.maxScore,
    score,
    signals: input.reasonCodes.map((item) => item.label),
    dataUsed: input.dataUsed,
    reasonCodes: input.reasonCodes,
    explanation: input.reasonCodes.length
      ? input.reasonCodes.map((item) => item.description).join(" ")
      : input.explanationWhenEmpty,
  };
}
