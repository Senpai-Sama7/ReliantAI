import { defineConfig } from "@playwright/test";

const MOCK_API_PORT = 8765;

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  retries: 1,
  workers: 3,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    channel: "chrome",
  },
  webServer: [
    {
      command: "node tests/mocks/api-server.mjs",
      url: `http://127.0.0.1:${MOCK_API_PORT}/health`,
      reuseExistingServer: true,
      timeout: 15000,
      env: {
        MOCK_API_PORT: String(MOCK_API_PORT),
      },
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000",
      reuseExistingServer: true,
      timeout: 30000,
      env: {
        REVALIDATE_SECRET: "dev_revalidate_secret",
        API_BASE_URL: `http://127.0.0.1:${MOCK_API_PORT}`,
      },
    },
  ],
});
