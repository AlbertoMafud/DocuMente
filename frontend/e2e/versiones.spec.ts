/**
 * E2E — crear una versión manual y verificar que aparece en la lista.
 *
 * Versiones son snapshots inmutables con hash de contenido. El idempotency
 * key es el hash: si nada cambió desde la última versión, no se crea una
 * duplicada (el sistema devuelve la existente).
 *
 * Aquí solo probamos el camino feliz: documento nuevo → crear versión →
 * aparece v1 con el comentario.
 */
import { test, expect } from "@playwright/test";
import { crearDocumentoMRM, logHttpErrors } from "./helpers";

test.describe("versiones — snapshot manual", () => {
  test("crear versión desde UI: aparece v1 con comentario en la lista", async ({ page }) => {
    logHttpErrors(page);

    const { id } = await crearDocumentoMRM(page, "E2E Versiones");

    // Ir a /versiones
    await page.goto(`/documentos/${id}/versiones`);
    await expect(page.getByRole("heading", { name: "Versiones", exact: true })).toBeVisible();
    await expect(page.getByText("Sin versiones todavía")).toBeVisible();

    // 1. Click "Crear versión ahora"
    await page.getByRole("button", { name: /Crear versión ahora/ }).click();

    // 2. Aparece el form con input de comentario
    await expect(page.getByLabel(/Comentario \(opcional\)/)).toBeVisible();

    const comentario = `E2E snapshot ${Date.now()}`;
    await page.getByLabel(/Comentario \(opcional\)/).fill(comentario);

    // 3. Click "Crear snapshot"
    await page.getByRole("button", { name: "Crear snapshot" }).click();

    // 4. Toast de éxito
    await expect(page.getByText(/Versión v1 creada/)).toBeVisible({ timeout: 15_000 });

    // 5. El empty state desaparece y aparece la card con v1 + comentario
    await expect(page.getByText("Sin versiones todavía")).not.toBeVisible();
    await expect(page.getByText("v1", { exact: true })).toBeVisible();
    await expect(page.getByText(comentario)).toBeVisible();
  });
});
