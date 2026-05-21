/**
 * Playwright config para DocuMente — E2E con dual webServer.
 *
 * Levanta backend FastAPI (uvicorn) y frontend Next.js antes de los
 * tests. Backend no requiere ANTHROPIC_API_KEY para los flujos que NO
 * tocan entrevista LLM (crear/editar/exportar funcionan sin él).
 *
 * Comandos:
 *   npm run test:e2e            # headless
 *   npm run test:e2e -- --ui    # modo interactivo
 */
import { defineConfig, devices } from "@playwright/test";
import path from "path";

const PROJECT_ROOT = path.resolve(__dirname, "..");
// Puertos aislados para E2E para no colisionar con dev local del usuario
// (que típicamente usa 8001 + 3000-3002). Si están ocupados, Playwright
// fallará explícitamente en lugar de saltar a otro puerto silenciosamente.
const API_PORT = 8100;
const WEB_PORT = 3100;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",
  timeout: 60_000,

  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "on-first-retry",
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: [
    {
      // python -m uvicorn (no asume uvicorn en PATH; usa el del venv activo)
      command: `python -m uvicorn src.api.main:app --port ${API_PORT}`,
      cwd: PROJECT_ROOT,
      url: `http://localhost:${API_PORT}/healthz`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      // -p fuerza el puerto. Sin esto Next.js cae a 3001/3002/...
      // silenciosamente si 3100 está ocupado y Playwright nunca lo detecta.
      command: `npm run dev -- -p ${WEB_PORT}`,
      cwd: __dirname,
      url: `http://localhost:${WEB_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        // Apunta al backend del E2E (puerto aislado), no al 8001 del dev local
        NEXT_PUBLIC_API_URL: `http://localhost:${API_PORT}`,
      },
    },
  ],
});
