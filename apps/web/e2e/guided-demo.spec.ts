import { expect, test } from "@playwright/test";

test("cinematic guided demo opens from the dashboard topbar and reaches the case packet", async ({
  page,
}) => {
  await page.goto("/dashboard");

  await page.getByTestId("demo-launch-topbar").click();
  const dialog = page.getByRole("dialog", { name: /Mission demo|Mission démo/i });

  await expect(dialog).toBeVisible();
  await expect(dialog.getByText(/Console d'analyse|Analysis console/i)).toBeVisible();
  await expect(dialog.getByText(/Scene 01|Sc[eè]ne 01/i)).toBeVisible();
  await expect(dialog.getByText("Alerte prioritaire", { exact: true })).toBeVisible();

  await dialog.getByRole("button", { name: /Passer|Skip/i }).click();
  await expect(dialog.getByRole("heading", { name: /Dossier ALPHACOM pr[eê]t pour revue/i })).toBeVisible();
  await expect(dialog.getByText("CASE-P2P-V00474", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Revue humaine requise", { exact: true })).toBeVisible();
  await expect(dialog.getByText(/Export d'analyse pr[eê]t/i).first()).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Exporter pour analyse" })).toBeVisible();

  await dialog.getByRole("button", { name: /Rejouer la d[eé]mo|Replay demo/i }).click();
  await expect(dialog.getByText("Alerte prioritaire", { exact: true })).toBeVisible();
});

test("cinematic guided demo respects English locale and reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/dashboard");

  await page.locator(".topbar-lang").getByRole("button", { name: "EN" }).click();
  await page.getByTestId("demo-launch-topbar").click();

  const dialog = page.getByRole("dialog", { name: /Demo mission/i });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("ALPHACOM case ready for review")).toBeVisible();
  await expect(dialog.getByText("Human review required")).toBeVisible();
  await expect(dialog.getByText("Analysis export ready").first()).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Export for analysis" })).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Explore cockpit" })).toBeVisible();
});
