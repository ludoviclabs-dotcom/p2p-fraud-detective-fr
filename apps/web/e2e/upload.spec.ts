import { Buffer } from "node:buffer";

import { expect, test } from "@playwright/test";

test("upload page returns a demo detection result", async ({ page }) => {
  await page.goto("/upload");

  await expect(
    page.getByRole("heading", { level: 1, name: /Import des/i }),
  ).toBeVisible();

  await page.locator("[data-testid='upload-input']").setInputFiles({
    name: "demo-invoices.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("invoice_id,amount\nINV-001,1200\n", "utf8"),
  });

  await page.getByTestId("upload-detect-button").click();
  await expect(page.locator("[data-testid='upload-result']")).toBeVisible();
  await expect
    .poll(
      async () => page.locator("[data-testid='upload-findings-table'] tbody tr").count(),
    )
    .toBeGreaterThan(0);
});
