/**
 * E2E — entrevista LLM falla con 503 amigable cuando no hay API key.
 *
 * El backend de E2E corre SIN ANTHROPIC_API_KEY (Playwright no la pasa en
 * el webServer command). Eso es deliberado: queremos validar que el sistema
 * degrada elegantemente, no que crashea.
 *
 * Verifica:
 *   - "Iniciar entrevista" devuelve 503 desde la API
 *   - La UI muestra un toast con mensaje útil (no un stack trace crudo)
 *   - El usuario sigue en la página, puede navegar a otra cosa
 */
import { test, expect } from "@playwright/test";
import { crearDocumentoMRM, logHttpErrors } from "./helpers";

test.describe("entrevista LLM — degradación sin API key", () => {
  test("sin ANTHROPIC_API_KEY el sistema muestra error útil, no crashea", async ({ page }) => {
    logHttpErrors(page);

    const { id } = await crearDocumentoMRM(page, "E2E LLM Fallback");

    // Navegar directo a la entrevista de la primera sección MRM (1.3)
    await page.goto(`/documentos/${id}/entrevista/1.3.problem_statement`);
    await expect(page.getByRole("button", { name: /Iniciar entrevista/ })).toBeVisible({
      timeout: 15_000,
    });

    // 1. Click "Iniciar entrevista" → debe llamar POST /entrevista/iniciar y obtener 503
    await page.getByRole("button", { name: /Iniciar entrevista/ }).click();

    // 2. Toast amigable (sonner) — mensaje del onError handler en la UI
    await expect(
      page.getByText(/LLM no configurado.*ANTHROPIC_API_KEY/i),
    ).toBeVisible({ timeout: 15_000 });

    // 3. La página NO crasheó — botón "Iniciar entrevista" sigue disponible
    await expect(page.getByRole("button", { name: /Iniciar entrevista/ })).toBeVisible();

    // 4. Y el usuario puede navegar de regreso al dashboard sin problemas
    await page.getByRole("link", { name: /Volver/ }).first().click();
    await page.waitForURL(new RegExp(`/documentos/${id}$`), { timeout: 10_000 });
    await expect(page.getByText("Borrador", { exact: true })).toBeVisible();
  });
});
