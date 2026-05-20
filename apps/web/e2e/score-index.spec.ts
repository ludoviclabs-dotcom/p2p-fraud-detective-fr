import { expect, test } from "@playwright/test";

test("score index drills into evidence then vendor detail", async ({ page }) => {
  await page.goto("/score");

  await expect(
    page.getByRole("heading", { level: 1, name: "Explorateur de score" }),
  ).toBeVisible();

  const invoiceLinks = page.locator("[data-testid='score-index-table'] tbody a[href^='/score/']");
  await expect.poll(async () => invoiceLinks.count()).toBeGreaterThan(0);

  await invoiceLinks.first().click();
  await expect(page).toHaveURL(/\/score\//);
  await expect(page.getByText("Preuve exploitable")).toBeVisible();
  await expect(page.getByRole("link", { name: "Preparer l'export" })).toBeVisible();

  await page.getByRole("link", { name: "Ouvrir la fiche" }).click();
  await expect(page).toHaveURL(/\/vendors\//);
  await expect(page.locator("[data-testid='vendor-signal-breakdown']")).toBeVisible();
  await expect(page.locator("[data-testid='vendor-iban-connections']")).toBeVisible();
});
