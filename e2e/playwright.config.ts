import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  retries: 0,
  workers: 1,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    channel: process.env.PW_CHANNEL || (process.platform === "darwin" ? "chrome" : undefined),
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    headless: true,
  },
});
