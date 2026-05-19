import type { CockpitKPIs, DailyPoint, TopVendor } from "@p2pfd/shared-types";

import { getP2PDataset } from "@/data/get-dataset";
import { SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";
import type { P2PDemoDataset, Severity, VendorSummary } from "@/types/p2p";

const TREND_WINDOW_DAYS = 30;

function severityAtLeast(value: Severity, minimum: Severity): boolean {
  return SEVERITY_ORDER[value] >= SEVERITY_ORDER[minimum];
}

function formatUtcDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function buildTrendSeries(endAt: string, total: number, seed: number): DailyPoint[] {
  const endDate = new Date(endAt);
  const baseline = Math.max(total / TREND_WINDOW_DAYS, 0.8);

  return Array.from({ length: TREND_WINDOW_DAYS }, (_, index) => {
    const pointDate = new Date(endDate);
    pointDate.setUTCDate(endDate.getUTCDate() - (TREND_WINDOW_DAYS - 1 - index));

    const wave =
      Math.sin((index + 1 + seed) * 0.52) * 0.34 +
      Math.cos((index + seed * 2) * 0.21) * 0.18;
    const impulse = (index + seed) % 8 === 0 ? 0.42 : 0;
    const value = Math.max(0, Math.round(baseline * (1.06 + wave + impulse)));

    return {
      date: formatUtcDate(pointDate),
      value,
    };
  });
}

function sortVendors(left: VendorSummary, right: VendorSummary): number {
  return (
    SEVERITY_ORDER[right.severity] - SEVERITY_ORDER[left.severity] ||
    right.exposureEur - left.exposureEur ||
    right.riskScore - left.riskScore ||
    left.name.localeCompare(right.name)
  );
}

export function buildDemoTopVendors(
  dataset: P2PDemoDataset = getP2PDataset(),
  limit = 10,
): TopVendor[] {
  return [...dataset.vendors]
    .sort(sortVendors)
    .slice(0, Math.max(limit, 1))
    .map((vendor) => ({
      vendor_id: vendor.vendorId,
      vendor_name: vendor.name,
      exposure_eur: vendor.exposureEur,
      n_findings: vendor.findingIds.length,
      max_severity: vendor.severity,
    }));
}

export function buildDemoCockpitKpis(
  dataset: P2PDemoDataset = getP2PDataset(),
): CockpitKPIs {
  const exposureCritical = dataset.findings
    .filter((finding) => finding.severity === "critical")
    .reduce((sum, finding) => sum + finding.exposureEur, 0);
  const overdueCount = dataset.findings.filter((finding) =>
    severityAtLeast(finding.severity, "high"),
  ).length;
  const unassignedCritical = dataset.metrics.criticalFindings
    ? Math.max(1, Math.ceil(dataset.metrics.criticalFindings / 3))
    : 0;

  return {
    exposure_total_eur: dataset.metrics.exposureEur,
    exposure_critical_eur: exposureCritical,
    n_cases_open: dataset.findings.length,
    n_cases_overdue: overdueCount,
    n_cases_unassigned_critical: unassignedCritical,
    trend_cases_created: buildTrendSeries(
      dataset.generatedAt,
      dataset.findings.length * 3,
      3,
    ),
    trend_cases_closed: buildTrendSeries(
      dataset.generatedAt,
      Math.max(dataset.findings.length * 2, 1),
      7,
    ),
    trend_critical_alerts: buildTrendSeries(
      dataset.generatedAt,
      Math.max(dataset.metrics.criticalFindings * 4, 1),
      11,
    ),
    trend_audit_activity: buildTrendSeries(
      dataset.generatedAt,
      Math.max(dataset.findings.length * 5, 1),
      17,
    ),
  };
}
