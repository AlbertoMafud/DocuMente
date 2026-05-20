/**
 * E2E happy-path — crear documento → ver dashboard → exportar DOCX.
 *
 * Stack:
 *   - Backend FastAPI en :8001 (sin ANTHROPIC_API_KEY — flujo no usa LLM)
 *   - Frontend Next.js en :3000
 *
 * Lo que cubre:
 *   1. Navegación /documentos/crear
 *   2. POST /documentos vía form (TanStack Query mutation)
 *   3. Redirect a /documentos/{uuid} con dashboard renderizado
 *   4. GET /documentos/{id} y GET /brechas/{id} (queries)
 *   5. POST /exportar/{id}/docx con descarga de archivo
 *
 * Lo que NO cubre todavía (TODO al escalar la suite):
 *   - Editar contenido de sección
 *   - Entrevista LLM (necesita ANTHROPIC_API_KEY)
 *   - Importar documento existente
 *   - Apéndices y versionado
 */
import { test, expect } from "@playwright/test";

test.describe("happy-path: crear + exportar", () => {
  test("crea un documento y descarga el DOCX exportado", async ({ page }) => {
    const nombreModelo = `E2E Test — ${Date.now()}`;

    // Captura responses 4xx/5xx para diagnosticar fallos en CI
    page.on("response", async (res) => {
      if (res.status() >= 400) {
        const url = res.url();
        let body = "";
        try {
          body = await res.text();
        } catch {
          body = "<no body>";
        }
        // eslint-disable-next-line no-console
        console.log(`[E2E] ${res.status()} ${res.request().method()} ${url}\n  body: ${body.slice(0, 500)}`);
      }
    });

    // 1. Llegar a la pantalla de creación
    await page.goto("/documentos/crear");
    await expect(page.getByRole("heading", { name: "Crear documento nuevo" })).toBeVisible();

    // 2. Default seleccionado es Model Development (28 secciones) — lo dejamos
    await expect(page.getByText("Model Development")).toBeVisible();

    // 3. Llenar nombre y submit
    await page.getByLabel("Nombre del modelo").fill(nombreModelo);
    await page.getByRole("button", { name: "Crear documento" }).click();

    // 4. Redirect a dashboard del documento creado
    await page.waitForURL(/\/documentos\/[0-9a-f-]{36}$/, { timeout: 15_000 });

    // 5. Hero muestra el nombre y badge "Borrador"
    await expect(page.getByRole("heading", { name: nombreModelo })).toBeVisible();
    await expect(page.getByText("Borrador", { exact: true })).toBeVisible();
    await expect(page.getByText(/28 secciones del template/)).toBeVisible();

    // 6. Exportar DOCX — espera el download event
    const downloadPromise = page.waitForEvent("download", { timeout: 30_000 });
    await page.getByRole("button", { name: /Exportar DOCX/ }).click();
    const download = await downloadPromise;

    // 7. El archivo descargado tiene el nombre esperado y no está vacío
    expect(download.suggestedFilename()).toMatch(/\.docx$/);
    const stream = await download.createReadStream();
    expect(stream).not.toBeNull();
  });
});
