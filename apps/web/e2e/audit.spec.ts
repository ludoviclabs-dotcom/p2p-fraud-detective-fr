import { expect, test } from "@playwright/test";

test("audit page verifies the demo chain and lists entries", async ({ page }) => {
  await page.goto("/audit");

  await expect(
    page.getByRole("heading", { level: 1, name: "Piste d'audit" }),
  ).toBeVisible();
  await expect(page.locator("[data-testid='audit-table']")).toBeVisible();

  const rows = page.locator("[data-testid='audit-table'] tbody tr");
  await expect.poll(async () => rows.count()).toBeGreaterThan(0);

  await page.getByRole("button", { name: "Recalculer la chaîne" }).click();
  await expect(page.locator("[data-testid='audit-verify-panel']")).toContainText(
    "Chaîne valide",
  );
});
