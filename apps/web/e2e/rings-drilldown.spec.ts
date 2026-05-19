import { expect, test } from "@playwright/test";

test("rings drilldown reaches score and vendor detail pages", async ({ page }) => {
  await page.goto("/rings");

  await expect(page.locator("[data-testid='graph-frame']")).toBeVisible();
  await page.selectOption("#severity-filter", "critical");

  const findingButtons = page.locator(
    "[data-testid='priority-node'][data-node-kind='finding']",
  );
  await expect.poll(async () => findingButtons.count()).toBeGreaterThan(0);

  await findingButtons.nth(0).click();

  const selectionPanel = page.locator("[data-testid='graph-selection-panel']");
  const scoreLink = selectionPanel.getByRole("link", { name: "Ouvrir le score" });
  await expect(scoreLink).toBeVisible();

  await scoreLink.click();
  await expect(page).toHaveURL(/\/score\//);
  await expect(page.getByText("Preuve exploitable")).toBeVisible();

  await page.getByRole("link", { name: "Ouvrir la fiche" }).click();
  await expect(page).toHaveURL(/\/vendors\//);
  await expect(page.getByText("Fiche fournisseur 360")).toBeVisible();
});
