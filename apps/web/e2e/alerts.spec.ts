import { expect, test } from "@playwright/test";

test("alerts page stays usable in fallback mode without FastAPI", async ({ page }) => {
  await page.goto("/alerts");

  await expect(
    page.getByRole("heading", { level: 1, name: "Alertes & monitoring" }),
  ).toBeVisible();
  await expect(page.locator("[data-testid='alerts-channel-table']")).toBeVisible();
  await expect(page.locator("[data-testid='alerts-channel-table'] tbody tr")).toHaveCount(3);
  await expect(page.locator("[data-testid='alerts-stream-message']")).toContainText(
    "bascule en polling",
  );
});
