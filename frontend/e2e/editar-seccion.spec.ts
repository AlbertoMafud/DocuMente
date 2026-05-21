/**
 * E2E — editar contenido de una sección y verificar persistencia.
 *
 * Es el flujo más fundamental del producto: si esto se rompe, DocuMente
 * deja de servir. Cubre:
 *   - Abrir editor de sección
 *   - Escribir contenido markdown
 *   - Click "Guardar cambios"
 *   - Redirect al dashboard
 *   - Re-abrir el editor: el contenido sigue ahí
 *   - El badge de completitud cambió de "Vacía" a "Parcial"/"Completa"
 */
import { test, expect } from "@playwright/test";
import { crearDocumentoMRM, logHttpErrors } from "./helpers";

test.describe("editar sección con persistencia", () => {
  test("escribe contenido, guarda, recarga y el contenido sigue ahí", async ({ page }) => {
    logHttpErrors(page);

    const { id } = await crearDocumentoMRM(page, "E2E Editar");

    // Buscar el link "Editar" (sin "metadata") de la primera sección. El
    // accordion del capítulo 1 suele iniciar abierto si tiene pendientes.
    const editarLink = page.getByRole("link", { name: "Editar", exact: true }).first();
    if (!(await editarLink.isVisible().catch(() => false))) {
      await page.getByRole("button", { name: /Capítulo 1.*Problem Statement/ }).click();
    }

    // 1. Abrir editor de la primera sección disponible
    await page
      .getByRole("link", { name: "Editar", exact: true })
      .first()
      .click();
    await page.waitForURL(/\/documentos\/.+\/secciones\/.+$/, { timeout: 15_000 });

    // El textarea no tiene htmlFor en el Label de shadcn; lo encontramos por
    // placeholder (más estable que getByLabel).
    const textarea = page.getByPlaceholder(/Escribe el contenido en markdown/);
    await expect(textarea).toBeVisible();

    // 2. Escribir contenido suficiente para que sea "completa" (>200 chars)
    const contenido =
      "Este es el contenido de prueba E2E para la sección. " +
      "Tiene suficiente longitud para que el sistema lo clasifique como " +
      "**completa** y no como parcial. El propósito es validar que la " +
      "persistencia funciona correctamente en SQLite (local) o PostgreSQL (EC2).";

    await textarea.fill(contenido);
    await expect(page.getByText("Estado: completa")).toBeVisible();

    // 3. Guardar — redirect al dashboard
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await page.waitForURL(new RegExp(`/documentos/${id}$`), { timeout: 15_000 });

    // 4. Verificar que la sección ahora aparece como "Completa" en el dashboard
    await expect(page.getByText("Completa").first()).toBeVisible({ timeout: 10_000 });

    // 5. Re-abrir el mismo editor — contenido persistido
    const editarLink2 = page.getByRole("link", { name: "Editar", exact: true }).first();
    if (!(await editarLink2.isVisible().catch(() => false))) {
      await page.getByRole("button", { name: /Capítulo 1.*Problem Statement/ }).click();
    }
    await page
      .getByRole("link", { name: "Editar", exact: true })
      .first()
      .click();
    await page.waitForURL(/\/documentos\/.+\/secciones\/.+$/, { timeout: 15_000 });

    // Textarea trae el mismo contenido (no se perdió)
    const textarea2 = page.getByPlaceholder(/Escribe el contenido en markdown/);
    await expect(textarea2).toHaveValue(contenido);
  });
});
