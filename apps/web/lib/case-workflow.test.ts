import { describe, expect, it } from "vitest";

import {
  createDefaultCaseWorkflowRecord,
  exportCaseWorkflowCsv,
  getCaseDecisionLabel,
  getCaseStatusLabel,
  readStoredCaseWorkflowRecords,
  type CaseWorkflowContext,
} from "@/lib/case-workflow";

const BASE_CONTEXT: CaseWorkflowContext = {
  id: "case:finding-001",
  findingId: "finding-001",
  invoiceId: "INV-2026-0001",
  vendorId: "vendor-001",
  vendorName: 'Vendor "Alpha", SAS',
  ruleId: "RING_SHARED_IBAN",
  signal: "shared_iban",
  severity: "high",
  exposureEur: 125000,
  riskScore: 82,
};

describe("createDefaultCaseWorkflowRecord", () => {
  it("creates a local pending workflow seeded from the case context", () => {
    const record = createDefaultCaseWorkflowRecord(BASE_CONTEXT);

    expect(record.id).toBe(BASE_CONTEXT.id);
    expect(record.status).toBe("new");
    expect(record.decision).toBe("pending");
    expect(record.source).toBe("local");
    expect(record.backendCaseId).toBeNull();
    expect(record.createdAt).toBe(record.updatedAt);
  });
});

describe("workflow label helpers", () => {
  it("returns French labels and falls back to the raw code when unknown", () => {
    expect(getCaseStatusLabel("needs_evidence")).toBe("Piece requise");
    expect(getCaseDecisionLabel("block_payment")).toBe("Bloquer paiement");
    expect(getCaseStatusLabel("custom_status" as never)).toBe("custom_status");
    expect(getCaseDecisionLabel("custom_decision" as never)).toBe("custom_decision");
  });
});

describe("exportCaseWorkflowCsv", () => {
  it("exports localized status labels and escapes commas, quotes and new lines", () => {
    const csv = exportCaseWorkflowCsv([
      {
        ...createDefaultCaseWorkflowRecord(BASE_CONTEXT),
        status: "reviewing",
        decision: "request_documents",
        assignee: "audit@example.test",
        note: 'Verifier "RIB", relancer,\npriorite haute',
      },
    ]);

    const lines = csv.split("\n");
    expect(lines[0]).toContain("case_id,backend_case_id,invoice_id");
    expect(lines[1]).toContain('"Vendor ""Alpha"", SAS"');
    expect(lines[1]).toContain("En revue");
    expect(lines[1]).toContain("Demander des pieces");
    expect(lines[1]).toContain('"Verifier ""RIB"", relancer,');
  });
});

describe("readStoredCaseWorkflowRecords", () => {
  it("returns an empty list during server-side execution", () => {
    expect(readStoredCaseWorkflowRecords()).toEqual([]);
  });
});
