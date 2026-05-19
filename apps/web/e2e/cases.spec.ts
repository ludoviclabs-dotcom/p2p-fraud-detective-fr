import { expect, test } from "@playwright/test";

test("cases page supports demo triage actions", async ({ page }) => {
  await page.goto("/cases");

  await expect(
    page.getByRole("heading", { level: 1, name: "File d'investigation" }),
  ).toBeVisible();

  const rows = page.locator("[data-testid='cases-table'] tbody tr");
  await expect.poll(async () => rows.count()).toBeGreaterThan(1);

  await page.locator("[data-testid='cases-status-filter']").selectOption("new");
  await expect.poll(async () => rows.count()).toBeGreaterThan(0);
  await page.locator("[data-testid='cases-status-filter']").selectOption("");
  await expect.poll(async () => rows.count()).toBeGreaterThan(1);

  const checkboxes = page.locator("[data-testid='cases-table'] tbody input[type='checkbox']");
  await checkboxes.nth(0).check();
  await checkboxes.nth(1).check();
  await expect(page.locator("[data-testid='cases-bulk-panel']")).toBeVisible();

  await page.getByPlaceholder("Assigner à (email)").fill("qa.audit@example.test");
  await page.getByRole("button", { name: "👥 Assigner" }).click();
  await expect(page.locator("[data-testid='cases-bulk-panel']")).toBeHidden();
  await expect
    .poll(async () => page.getByText("qa.audit@example.test").count())
    .toBeGreaterThan(0);
});
