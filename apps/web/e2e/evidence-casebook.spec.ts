import { expect, test } from "@playwright/test";

const caseId = "CASE-APP-BANK-001";
const rawIban = "FR7612345987650123456789014";

test.use({ acceptDownloads: true });

test.describe("Evidence Casebook", () => {
  test("opens Fraud Case 360 from the score explorer", async ({ page }) => {
    await page.goto("/score");

    await expect(page.locator("[data-testid='score-index-table']")).toBeVisible();
    const caseLink = page.getByTestId("score-case-360-link").first();
    await expect(caseLink).toHaveAttribute("href", /\/fraud-case-360\/CASE-/);

    await caseLink.click();

    await expect(page).toHaveURL(/\/fraud-case-360\/CASE-/);
    await expect(
      page.locator(".fx-eyebrow").filter({ hasText: "Fraud Case 360" }),
    ).toBeVisible();
    await expect(page.getByTestId("case-360-audit-chain")).toBeVisible();
  });

  test("exports an evidence pack with integrity metadata and redacted transaction data", async ({
    page,
    request,
  }) => {
    await page.goto(`/fraud-case-360/${caseId}`);

    await page.locator("#case-360-analyst-notes").fill("E2E evidence export check.");
    const downloadPromise = page.waitForEvent("download");
    await page.getByTestId("case-360-export-evidence").click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toBe(`${caseId}-evidence-pack.json`);
    await expect(page.getByRole("status")).toContainText("Evidence pack JSON");
    await expect(page.getByTestId("case-360-root-hash")).toContainText(
      /[a-f0-9]{64}/,
    );
    await expect(page.getByTestId("case-360-source-ref")).toHaveCount(3);

    const response = await request.post("/api/evidence/export", {
      data: { caseId },
    });
    expect(response.ok()).toBeTruthy();

    const payload = await response.json();
    const evidencePack = payload.evidencePack;
    const exportedJson = JSON.stringify(evidencePack);
    const maskedIban = evidencePack.transaction.beneficiary.iban;

    expect(evidencePack.integrity.rootHash).toMatch(/^[a-f0-9]{64}$/);
    expect(evidencePack.sourceRefs).toHaveLength(3);
    expect(exportedJson).not.toContain(rawIban);
    expect(maskedIban).toMatch(/^FR76.+9014$/);
  });

  test("verifies the audit chain from the audit page and API", async ({ page, request }) => {
    await page.goto("/audit");

    await expect(page.getByTestId("audit-table")).toBeVisible();
    await page.getByTestId("audit-verify-button").click();
    await expect(page.getByTestId("audit-verify-panel")).toContainText(/valide/i);

    const response = await request.get("/api/v1/audit/verify");
    expect(response.ok()).toBeTruthy();

    const verification = await response.json();
    expect(verification.valid).toBe(true);
    expect(verification.n_total).toBeGreaterThan(0);
    expect(verification.n_signed).toBe(verification.n_total);
  });
});
