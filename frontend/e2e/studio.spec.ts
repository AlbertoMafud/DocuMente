/**
 * E2E — Template Studio: wizard completo de 5 pasos.
 *
 * Corre SIN modelo de lenguaje (el backend del E2E arranca con
 * ANTHROPIC_API_KEY vacía), así que la propuesta de la IA viene vacía y el
 * catálogo se construye a mano. Eso es deliberado: prueba el camino que
 * debe funcionar incluso cuando la IA no está disponible.
 *
 * Verifica:
 *   - La extracción del .docx detecta los encabezados reales
 *   - El wizard avanza por los 5 pasos
 *   - La validación de calidad BLOQUEA la publicación con errores
 *   - Corregidos los errores, se publica
 *   - El tipo publicado queda disponible para crear documentos
 */
import path from "path";

import { test, expect } from "@playwright/test";

import { logHttpErrors } from "./helpers";

const FIXTURE = path.join(__dirname, "fixtures", "plantilla-ejemplo.docx");

test.describe("Template Studio — wizard", () => {
  test("convierte un .docx en un tipo de documento publicado y usable", async ({ page }) => {
    logHttpErrors(page);

    const nombreTipo = `Procedimiento E2E ${Date.now()}`;

    // ---- Paso 1: subir la plantilla ----
    await page.goto("/studio");
    await expect(page.getByRole("heading", { name: "Template Studio" })).toBeVisible();

    await page.getByLabel("Nombre del tipo de documento").fill(nombreTipo);
    await page.getByLabel("Descripción (una línea)").fill("Plantilla de prueba E2E");

    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByText("Arrastra la plantilla aquí").click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(FIXTURE);

    await page.getByRole("button", { name: "Analizar plantilla" }).click();

    // ---- Paso 2: estructura detectada ----
    await expect(page.getByRole("heading", { name: "Esto es lo que encontré" })).toBeVisible({
      timeout: 20_000,
    });
    // Los 4 encabezados del fixture deben aparecer
    await expect(page.getByText("Objetivo", { exact: true })).toBeVisible();
    await expect(page.getByText("Controles clave", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Ver la propuesta" }).click();

    // ---- Paso 3: propuesta (vacía sin LLM, con aviso claro) ----
    await expect(page.getByRole("heading", { name: "Propuesta de la IA" })).toBeVisible();
    await page.getByRole("button", { name: "Revisar sección por sección" }).click();

    // ---- Paso 4: curación — construimos una sección a mano ----
    await expect(
      page.getByText("El catálogo está vacío. Agrega la primera sección para empezar."),
    ).toBeVisible();
    // Hay dos controles con ese nombre: el icono del panel lateral y este CTA
    // del estado vacío. Usamos el del estado vacío (el que ve el usuario aquí).
    await page.getByRole("button", { name: "Agregar sección", exact: true }).last().click();

    await page.getByLabel("Nombre de la sección").fill("Objetivo");
    // Intención vacía a propósito: debe bloquear la publicación.
    await page.getByRole("button", { name: "Validar calidad" }).click();

    // ---- Paso 5: la validación bloquea ----
    await expect(page.getByRole("heading", { name: "Validación de calidad" })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText(/Problemas que impiden publicar/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Publicar plantilla" })).toBeDisabled();

    // ---- Corregir y republicar ----
    await page.getByRole("button", { name: "Volver a corregir" }).click();
    await page
      .getByLabel("Qué conocimiento captura")
      .fill("Propósito del procedimiento y la necesidad de negocio que atiende.");
    await page
      .getByLabel("Preguntas guía (una por línea)")
      .fill("¿Qué problema resuelve este procedimiento?");
    await page.getByLabel("Nombres alternativos (uno por línea)").fill("objetivo");

    await page.getByRole("button", { name: "Validar calidad" }).click();
    await expect(page.getByRole("heading", { name: "Validación de calidad" })).toBeVisible({
      timeout: 15_000,
    });

    // Queda la advertencia L8 (100% obligatorias) — exige aceptación explícita
    const publicar = page.getByRole("button", { name: "Publicar plantilla" });
    if (await page.getByText(/Entiendo las advertencias/).isVisible()) {
      await page.getByText(/Entiendo las advertencias/).click();
    }
    await expect(publicar).toBeEnabled();
    await publicar.click();

    // ---- Publicado ----
    await expect(page.getByRole("heading", { name: "Plantilla publicada" })).toBeVisible({
      timeout: 15_000,
    });

    // ---- El tipo nuevo está disponible al crear un documento ----
    await page.goto("/documentos/crear");
    await expect(page.getByText(nombreTipo)).toBeVisible({ timeout: 15_000 });
  });
});
