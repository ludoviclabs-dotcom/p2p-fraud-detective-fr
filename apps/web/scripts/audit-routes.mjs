// Route audit sweep — visits every route, captures console errors, page errors,
// failed network requests (>=400), and screenshots (desktop + mobile).
//
// Usage:
//   AUDIT_BASE_URL=https://p2p-fraud-detective-fr-web.vercel.app node apps/web/scripts/audit-routes.mjs
//   AUDIT_BASE_URL=http://127.0.0.1:3000 node apps/web/scripts/audit-routes.mjs
//
// Output: <AUDIT_OUT>/audit-results.json + audit-summary.md + per-route PNGs.

import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const BASE = (process.env.AUDIT_BASE_URL ?? "https://p2p-fraud-detective-fr-web.vercel.app").replace(/\/$/, "");
const OUT = process.env.AUDIT_OUT ?? "audit-artifacts";
const SETTLE_MS = Number(process.env.AUDIT_SETTLE_MS ?? 1800);

// Canonical route list (page routes — anchors of the home page are covered by "/").
const ROUTES = [
  "/",
  "/dashboard",
  "/sandbox",
  "/tour",
  "/p2p-scenarios",
  "/risk-test-lab",
  "/risk-lab-sepa",
  "/detection-studio",
  "/fraud-case-360/CASE-APP-BANK-001",
  "/risk-docs",
  "/cases",
  "/vendors",
  "/alerts",
  "/collab",
  "/anomalies",
  "/duplicates",
  "/structuring",
  "/sanctions",
  "/rings",
  "/score",
  "/findings",
  "/benford",
  "/upload",
  "/sirene",
  "/decp-rbe",
  "/master-history",
  "/methodology",
  "/audit",
  "/exports",
  "/governance",
];

const VIEWPORTS = {
  desktop: { width: 1440, height: 900 },
  mobile: { width: 390, height: 844 },
};

// Known-benign noise to flag separately rather than count as a defect.
const isFaviconNoise = (s) => /favicon\.ico/.test(s);

function slug(route) {
  if (route === "/") return "home";
  return route.replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "");
}

async function run() {
  await mkdir(OUT, { recursive: true });
  const results = [];
  const browser = await chromium.launch();

  for (const [vpName, viewport] of Object.entries(VIEWPORTS)) {
    const context = await browser.newContext({
      viewport,
      locale: "fr-FR",
      timezoneId: "Europe/Paris",
    });

    for (const route of ROUTES) {
      const page = await context.newPage();
      const consoleErrors = [];
      const pageErrors = [];
      const failedRequests = [];

      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });
      page.on("pageerror", (err) => pageErrors.push(String(err)));
      page.on("response", (res) => {
        const status = res.status();
        if (status >= 400) failedRequests.push(`${status} ${res.request().method()} ${res.url()}`);
      });

      let navStatus = null;
      let navError = null;
      try {
        const resp = await page.goto(`${BASE}${route}`, {
          waitUntil: "domcontentloaded",
          timeout: 30000,
        });
        navStatus = resp ? resp.status() : null;
        // Let hydration, client fetches, and intro animations settle.
        await page.waitForTimeout(SETTLE_MS);
      } catch (e) {
        navError = String(e);
      }

      if (vpName === "desktop") {
        await page
          .screenshot({ path: path.join(OUT, `${slug(route)}.png`), fullPage: true })
          .catch(() => {});
      }

      const realConsoleErrors = consoleErrors.filter((s) => !isFaviconNoise(s));
      const realFailed = failedRequests.filter((s) => !isFaviconNoise(s));
      const faviconNoise = consoleErrors.length - realConsoleErrors.length + (failedRequests.length - realFailed.length);

      results.push({
        viewport: vpName,
        route,
        navStatus,
        navError,
        consoleErrors: realConsoleErrors,
        pageErrors,
        failedRequests: realFailed,
        faviconNoise,
        clean: !navError && realConsoleErrors.length === 0 && pageErrors.length === 0 && realFailed.length === 0,
      });

      await page.close();
    }
    await context.close();
  }

  await browser.close();

  await writeFile(path.join(OUT, "audit-results.json"), JSON.stringify(results, null, 2), "utf8");

  // Markdown summary
  const lines = [];
  lines.push(`# Audit sweep — ${BASE}`);
  lines.push("");
  lines.push(`Routes: ${ROUTES.length} · Viewports: ${Object.keys(VIEWPORTS).join(", ")}`);
  lines.push("");
  lines.push("| Viewport | Route | Nav | Console err | Page err | Net 4xx/5xx | Clean |");
  lines.push("|---|---|---|---|---|---|---|");
  for (const r of results) {
    const status = r.navError ? "ERR" : r.navStatus ?? "?";
    lines.push(
      `| ${r.viewport} | ${r.route} | ${status} | ${r.consoleErrors.length} | ${r.pageErrors.length} | ${r.failedRequests.length} | ${r.clean ? "✓" : "✗"} |`,
    );
  }
  lines.push("");
  lines.push("## Détails des anomalies");
  lines.push("");
  for (const r of results.filter((x) => !x.clean)) {
    lines.push(`### [${r.viewport}] ${r.route}`);
    if (r.navError) lines.push(`- navError: ${r.navError}`);
    for (const e of r.consoleErrors) lines.push(`- console.error: ${e}`);
    for (const e of r.pageErrors) lines.push(`- pageerror: ${e}`);
    for (const f of r.failedRequests) lines.push(`- net: ${f}`);
    lines.push("");
  }
  const faviconTotal = results.reduce((a, r) => a + (r.faviconNoise || 0), 0);
  if (faviconTotal > 0) {
    lines.push(`> Note: ${faviconTotal} requêtes favicon.ico 404 filtrées (constat C4, cosmétique).`);
  }
  await writeFile(path.join(OUT, "audit-summary.md"), lines.join("\n"), "utf8");

  const dirty = results.filter((r) => !r.clean);
  console.log(`\nAudit done: ${results.length} page-loads, ${dirty.length} with anomalies.`);
  for (const r of dirty) {
    console.log(`  ✗ [${r.viewport}] ${r.route} — console:${r.consoleErrors.length} page:${r.pageErrors.length} net:${r.failedRequests.length}${r.navError ? " navError" : ""}`);
  }
  console.log(`\nArtifacts in ${OUT}/ (audit-results.json, audit-summary.md, *.png)`);
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
