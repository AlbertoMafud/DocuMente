/**
 * E2E — adjuntar tabla CSV como apéndice.
 *
 * Cubre el path de upload de archivos. CSV en vez de PDF porque:
 *   - CSV es texto plano; podemos generar el contenido inline sin fixtures
 *   - El flujo es idéntico al de PDF en términos de UI; ejercita el mismo
 *     stack de upload multipart
 *
 * Verifica:
 *   - Tab "Tabla (Excel/CSV)" funciona
 *   - File picker acepta CSV
 *   - Submit crea el apéndice
 *   - El apéndice aparece en la lista con su título y origen
 */
import { test, expect } from "@playwright/test";
import { crearDocumentoMRM, logHttpErrors } from "./helpers";

test.describe("apéndices — adjuntar tabla CSV", () => {
  test("sube CSV inline y aparece en la lista de apéndices", async ({ page }) => {
    logHttpErrors(page);

    const { id } = await crearDocumentoMRM(page, "E2E Apendice");

    // Ir a /apendices
    await page.goto(`/documentos/${id}/apendices`);
    await expect(page.getByRole("heading", { name: "Apéndices", exact: true })).toBeVisible();
    await expect(page.getByText("Sin apéndices todavía. Sube uno arriba.")).toBeVisible();

    // 1. Tab "Tabla" ya está activa por default
    await expect(page.getByRole("tab", { name: /Tabla \(Excel\/CSV\)/ })).toHaveAttribute(
      "data-state",
      "active",
    );

    // 2. Llenar título — el Label de shadcn no asocia htmlFor, usamos placeholder
    const tituloApendice = `Tabla E2E ${Date.now()}`;
    await page.getByPlaceholder(/Tabla de mortalidad SOA/).fill(tituloApendice);

    // 3. Click "Seleccionar archivo" → file chooser → CSV inline (sin fixture binario)
    const csvContent = "col_a,col_b,col_c\n1,2,3\n4,5,6\n7,8,9";
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "Seleccionar archivo" }).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: "test-e2e.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(csvContent, "utf-8"),
    });

    // El archivo aparece en el preview
    await expect(page.getByText("test-e2e.csv")).toBeVisible();

    // 4. Submit
    await page.getByRole("button", { name: "Adjuntar", exact: true }).click();

    // 5. Toast de éxito
    await expect(page.getByText(/apéndice\(s\) creado\(s\)/)).toBeVisible({
      timeout: 15_000,
    });

    // 6. El apéndice aparece en la lista — el conteo cambió a 1 o más
    await expect(page.getByRole("heading", { name: /\d+ apéndice/ })).toBeVisible();
    await expect(page.getByText(tituloApendice).first()).toBeVisible();

    // 7. Badge "tabla" en el apéndice
    await expect(page.getByText("tabla", { exact: true }).first()).toBeVisible();
  });
});
