import { expect, test } from "@playwright/test";

const ROUTES = [
  "/p2p-scenarios",
  "/risk-test-lab",
  "/detection-studio",
  "/fraud-case-360/CASE-APP-BANK-001",
  "/risk-docs",
  "/vendors/V00007",
];

test("workbench routes and legacy vendor deep link stay reachable", async ({ page }) => {
  for (const route of ROUTES) {
    const response = await page.goto(route);
    expect(response?.status(), route).toBe(200);
    await expect(page.locator("main")).toBeVisible();
  }
});

test("scenario analysis exposes score, reason codes and case navigation", async ({ page }) => {
  await page.goto("/p2p-scenarios");

  await page.getByRole("button", { name: "Faux conseiller bancaire" }).click();
  await page.getByRole("button", { name: "Lancer l'analyse" }).click();

  const resultPanel = page.locator("[data-testid='p2p-scenario-result']");
  await expect(resultPanel).toBeVisible();
  await expect(resultPanel.getByText("CRITICAL")).toBeVisible();
  await expect(resultPanel.getByText("NARRATIVE_URGENCY")).toBeVisible();

  await page.getByRole("link", { name: /Ouvrir Fraud Case 360/ }).click();
  await expect(page).toHaveURL(/\/fraud-case-360\/CASE-APP-BANK-001$/);
});

test("risk APIs expose scenarios, score and evidence pack with required fields", async ({ request }) => {
  const scenariosResponse = await request.get("/api/risk/scenarios");
  expect(scenariosResponse.ok()).toBe(true);
  const scenarios = await scenariosResponse.json();
  expect(scenarios.scenarios).toHaveLength(6);
  expect(scenarios.disclaimer).toContain("Scénarios synthétiques");

  const transaction = scenarios.scenarios[0].transaction;
  const scoreResponse = await request.post("/api/risk/score", {
    data: { transaction },
  });
  expect(scoreResponse.ok()).toBe(true);
  const score = await scoreResponse.json();
  expect(score.score).toBeGreaterThanOrEqual(0);
  expect(score.score).toBeLessThanOrEqual(100);
  expect(score.reasonCodes.length).toBeGreaterThan(0);
  expect(score.detectorScores.length).toBeGreaterThan(0);

  const evidenceResponse = await request.post("/api/evidence/export", {
    data: {
      caseId: scenarios.scenarios[0].caseId,
      transaction,
      analystNotes: "Synthetic QA note",
    },
  });
  expect(evidenceResponse.ok()).toBe(true);
  const evidence = await evidenceResponse.json();
  expect(evidence.evidencePack.caseId).toBe(scenarios.scenarios[0].caseId);
  expect(evidence.evidencePack.reasonCodes.length).toBeGreaterThan(0);
  expect(evidence.evidencePack.detectorScores.length).toBeGreaterThan(0);
  expect(evidence.evidencePack.disclaimer).toContain("Démonstrateur");
  expect(evidence.printableHtml).toContain("<!doctype html>");
});
