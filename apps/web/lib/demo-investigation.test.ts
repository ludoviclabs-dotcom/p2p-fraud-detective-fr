import { describe, expect, it } from "vitest";

import {
  buildDemoAuditEntries,
  buildDemoAuditPage,
  buildDemoAuditVerify,
  buildDemoCases,
  buildDemoUploadResponse,
  filterDemoCases,
} from "@/lib/demo-investigation";

describe("buildDemoCases", () => {
  it("creates a realistic mix of demo cases from the graph dataset", () => {
    const cases = buildDemoCases();
    const statuses = new Set(cases.map((item) => item.status));

    expect(cases.length).toBeGreaterThanOrEqual(6);
    expect(statuses.has("new")).toBe(true);
    expect(statuses.has("triaged")).toBe(true);
    expect(statuses.has("in_progress")).toBe(true);
    expect(statuses.has("escalated")).toBe(true);
    expect(statuses.has("closed_false_positive")).toBe(true);
    expect(statuses.has("closed_confirmed")).toBe(true);
  });
});

describe("filterDemoCases", () => {
  it("filters by severity and status without mutating the source list", () => {
    const cases = buildDemoCases();
    const filtered = filterDemoCases(cases, { severity: "critical", status: "new" });

    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered.every((item) => item.severity === "critical")).toBe(true);
    expect(filtered.every((item) => item.status === "new")).toBe(true);
    expect(cases.length).toBeGreaterThan(filtered.length);
  });
});

describe("audit helpers", () => {
  it("builds a paginated signed audit trail and a valid verify payload", () => {
    const entries = buildDemoAuditEntries(buildDemoCases());
    const page = buildDemoAuditPage(entries, 0, 5);
    const verify = buildDemoAuditVerify(entries);

    expect(page.entries).toHaveLength(5);
    expect(page.total).toBe(entries.length);
    expect(page.entries[0]!.seq).toBeGreaterThan(page.entries[4]!.seq);
    expect(verify.valid).toBe(true);
    expect(verify.n_total).toBe(entries.length);
    expect(verify.n_signed).toBe(entries.length);
  });
});

describe("buildDemoUploadResponse", () => {
  it("returns a demo detection payload with findings and detector families", () => {
    const result = buildDemoUploadResponse();

    expect(result.n_invoices).toBeGreaterThan(0);
    expect(result.detectors_run.length).toBeGreaterThan(0);
    expect(result.findings.length).toBeGreaterThan(0);
    expect(result.findings.every((finding) => finding.detector)).toBe(true);
  });
});
