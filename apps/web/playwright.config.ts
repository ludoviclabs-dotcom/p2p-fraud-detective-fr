import { defineConfig, devices } from "@playwright/test";

const useWebServer = process.env.PLAYWRIGHT_SKIP_WEBSERVER !== "1";
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3100";
const serverPort = Number(new URL(baseURL).port || "3100");
const nextStartCommand = `"${process.execPath}" ./node_modules/next/dist/bin/next start --port ${serverPort}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  webServer: useWebServer
    ? {
        command: nextStartCommand,
        cwd: ".",
        port: serverPort,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      }
    : undefined,
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
