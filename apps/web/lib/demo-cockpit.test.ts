import { describe, expect, it } from "vitest";

import { getP2PDataset } from "@/data/get-dataset";
import { buildDemoCockpitKpis, buildDemoTopVendors } from "@/lib/demo-cockpit";
import { SEVERITY_ORDER } from "@/lib/p2p-demo-taxonomy";

describe("buildDemoTopVendors", () => {
  it("returns limited rows sorted by severity and exposure", () => {
    const rows = buildDemoTopVendors(getP2PDataset(), 5);

    expect(rows).toHaveLength(5);
    for (let index = 1; index < rows.length; index += 1) {
      const previous = rows[index - 1];
      const current = rows[index];
      expect(previous).toBeDefined();
      expect(current).toBeDefined();

      const severityGap =
        SEVERITY_ORDER[previous!.max_severity as keyof typeof SEVERITY_ORDER] -
        SEVERITY_ORDER[current!.max_severity as keyof typeof SEVERITY_ORDER];
      const exposureGap = previous!.exposure_eur - current!.exposure_eur;

      expect(severityGap > 0 || (severityGap === 0 && exposureGap >= 0)).toBe(true);
    }
  });
});

describe("buildDemoCockpitKpis", () => {
  it("derives non-empty KPI series from the static dataset", () => {
    const dataset = getP2PDataset();
    const kpis = buildDemoCockpitKpis(dataset);

    expect(kpis.exposure_total_eur).toBe(dataset.metrics.exposureEur);
    expect(kpis.n_cases_open).toBe(dataset.findings.length);
    expect(kpis.n_cases_overdue).toBeGreaterThan(0);
    expect(kpis.trend_cases_created).toHaveLength(30);
    expect(kpis.trend_cases_closed).toHaveLength(30);
    expect(kpis.trend_critical_alerts).toHaveLength(30);
    expect(kpis.trend_audit_activity).toHaveLength(30);
    expect(kpis.trend_cases_created?.every((point) => point.value >= 0)).toBe(true);
  });
});
