/**
 * Browser E2E for the admin UI against the real backend: serve-api.mjs runs
 * qa-api + qa-worker on a fresh data dir, the Vite dev server serves WebUI and
 * proxies /v1 to it, and the browser drives the real pages.
 *
 * The ports differ from the dev defaults (8000/5173) so a running dev setup is
 * never reused or disturbed. The browser is the installed Microsoft Edge by
 * default (no browser download); set QA_E2E_BROWSER_CHANNEL="" to use
 * Playwright's own Chromium after `playwright install chromium`.
 */

import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

const repo = fileURLToPath(new URL("../../../", import.meta.url));
const apiPort = process.env.QA_E2E_API_PORT ?? "18765";
const webPort = process.env.QA_E2E_WEB_PORT ?? "14180";
const channel = process.env.QA_E2E_BROWSER_CHANNEL ?? "msedge";

export default defineConfig({
  testDir: ".",
  testMatch: "*.e2e.ts",
  outputDir: "./test-results",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180_000,
  expect: { timeout: 15_000 },
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${webPort}`,
    ...(channel ? { channel } : {}),
    headless: true,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "node tests/frontend/e2e/serve-api.mjs",
      cwd: repo,
      url: `http://127.0.0.1:${apiPort}/healthz`,
      env: { QA_E2E_API_PORT: apiPort },
      reuseExistingServer: false,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: `node scripts/run-bin.mjs vite vite --port ${webPort} --strictPort`,
      cwd: `${repo}WebUI`,
      url: `http://127.0.0.1:${webPort}/`,
      env: { QA_API_TARGET: `http://127.0.0.1:${apiPort}` },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
