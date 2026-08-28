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
import fs from "fs";
import path from "path";

import { defineConfig, devices } from "@playwright/test";

const PROJECT_ROOT = path.resolve(__dirname, "..");

// Base de datos nueva por corrida. Sin esto el estado se acumula entre
// corridas (cada pasada del Template Studio publica una plantilla más) y la
// suite se vuelve intermitente. Se genera aquí, al evaluar la config, porque
// Playwright arranca los servidores ANTES del globalSetup: borrar el archivo
// después sería quitárselo a un proceso que ya lo tiene abierto.
const DATA_DIR = path.join(PROJECT_ROOT, "data");
const RUN_DB = path.join(DATA_DIR, `e2e-${Date.now().toString(36)}.db`);

fs.mkdirSync(DATA_DIR, { recursive: true });
// Limpia las de corridas anteriores; a estas alturas ya nadie las tiene abierta.
for (const archivo of fs.readdirSync(DATA_DIR)) {
  if (/^e2e[-.].*\.db(-wal|-shm)?$/.test(archivo)) {
    try {
      fs.rmSync(path.join(DATA_DIR, archivo), { force: true });
    } catch {
      // Si alguna sigue bloqueada, no importa: esta corrida usa una nueva.
    }
  }
}
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

  // El frontend corre en modo desarrollo: Next.js compila cada ruta la
  // primera vez que se visita, y ese arranque en frío puede pasar de los 5s
  // por defecto. Subirlo evita fallas intermitentes que no son del producto.
  expect: { timeout: 15_000 },

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
      env: {
        // Hermético: string vacío hace que pydantic-settings ignore el
        // `.env` real de la máquina → get_llm_client devuelve None y los
        // specs de degradación (llm-fallback) son deterministas en
        // cualquier máquina. Mismo principio que la fixture sin_llm de
        // tests/integration/test_api_smoke.py.
        ANTHROPIC_API_KEY: "",
        // BD dedicada y nueva por corrida (ver arriba). Antes de S18 el E2E
        // escribía en data/documente.db, la base de desarrollo.
        DATABASE_URL: `sqlite:///${RUN_DB.replace(/\\/g, "/")}`,
      },
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
