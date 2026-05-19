import { expect, test } from "@playwright/test";

test("dashboard renders demo cockpit fallback data", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(
    page.getByRole("heading", { level: 1, name: "Cockpit risque P2P" }),
  ).toBeVisible();
  await expect(page.locator("[data-testid='dashboard-signal-breakdown']")).toBeVisible();

  await expect
    .poll(async () => page.locator("[data-testid='dashboard-top-vendors'] tbody tr").count())
    .toBeGreaterThan(0);

  await page.getByRole("link", { name: "Explorer le graphe" }).click();
  await expect(page).toHaveURL(/\/rings$/);
});
