import { describe, expect, it } from "vitest";
import { NORMAL_SCENARIO, RISK_SCENARIOS } from "@/data/risk-scenarios";
import { buildEvidencePack } from "@/lib/risk/evidence-pack";
import { scoreTransaction } from "@/lib/risk/scoreEngine";

function scenario(id: string) {
  const found = RISK_SCENARIOS.find((item) => item.id === id);
  if (!found) throw new Error(`Missing scenario ${id}`);
  return found;
}

describe("risk-engine-demo-v1", () => {
  it("keeps every scenario score between 0 and 100", () => {
    for (const item of [...RISK_SCENARIOS, NORMAL_SCENARIO]) {
      const result = scoreTransaction(item.transaction);
      expect(result.score).toBeGreaterThanOrEqual(0);
      expect(result.score).toBeLessThanOrEqual(100);
    }
  });

  it("scores fake bank advisor as critical", () => {
    const result = scoreTransaction(scenario("fake-bank-advisor").transaction);
    expect(result.level).toBe("CRITICAL");
    expect(result.typology).toBe("APP_FRAUD_BANK_IMPERSONATION");
  });

  it("scores normal payment as low or medium", () => {
    const result = scoreTransaction(NORMAL_SCENARIO.transaction);
    expect(["LOW", "MEDIUM"]).toContain(result.level);
  });

  it("generates reason code for IBAN/name mismatch", () => {
    const result = scoreTransaction(scenario("supplier-rib-change").transaction);
    expect(result.reasonCodes.map((item) => item.code)).toContain("DOCUMENT_IBAN_MISMATCH");
  });

  it("generates reason code for urgency narrative", () => {
    const result = scoreTransaction(scenario("fake-bank-advisor").transaction);
    expect(result.reasonCodes.map((item) => item.code)).toContain("NARRATIVE_URGENCY");
  });

  it("generates reason code for QR IBAN mismatch", () => {
    const result = scoreTransaction(scenario("tampered-qr-code").transaction);
    expect(result.reasonCodes.map((item) => item.code)).toContain("QR_IBAN_MISMATCH");
  });

  it("builds an evidence pack with required fields", () => {
    const item = scenario("mule-account-network");
    const score = scoreTransaction(item.transaction);
    const pack = buildEvidencePack({
      caseId: item.caseId,
      transaction: item.transaction,
      score,
      graphSummary: item.graphSummary,
      analystNotes: "Synthetic analyst note",
    });

    expect(pack.caseId).toBe(item.caseId);
    expect(pack.generatedAt).toBeTruthy();
    expect(pack.transaction.transactionId).toBe(item.transaction.transactionId);
    expect(pack.score.score).toBe(score.score);
    expect(pack.typology).toBe(score.typology);
    expect(pack.decision).toBe(score.decision);
    expect(pack.reasonCodes.length).toBeGreaterThan(0);
    expect(pack.detectorScores.length).toBeGreaterThan(0);
    expect(pack.timeline.length).toBeGreaterThan(0);
    expect(pack.graphSummary.nodes.length).toBeGreaterThan(0);
    expect(pack.sourceRefs.length).toBeGreaterThan(0);
    expect(pack.recommendedActions.length).toBeGreaterThan(0);
    expect(pack.analystNotes).toContain("Synthetic");
    expect(pack.auditTrail.length).toBeGreaterThan(0);
    expect(pack.auditTrail[0]?.hash).toMatch(/^[a-f0-9]{64}$/);
    expect(pack.integrity.rootHash).toMatch(/^[a-f0-9]{64}$/);
    expect(pack.integrity.chainValid).toBe(true);
    expect(pack.transaction.beneficiary.iban).toContain("••••");
    expect(pack.transaction.beneficiary.iban).not.toBe(item.transaction.beneficiary.iban);
    expect(pack.disclaimer).toContain("Démonstrateur");
  });
});
