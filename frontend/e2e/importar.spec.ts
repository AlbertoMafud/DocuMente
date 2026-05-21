/**
 * E2E — ciclo completo: crear → exportar DOCX → importar el mismo archivo.
 *
 * Esto valida los 2 caminos principales del producto al mismo tiempo:
 *   - Crear/exportar funcionan (Test 1)
 *   - Importar reconstruye un documento desde un .docx generado por DocuMente
 *
 * Cero fixtures binarios — el propio sistema produce el archivo de prueba.
 */
import path from "path";
import { test, expect } from "@playwright/test";
import { crearDocumentoMRM, logHttpErrors } from "./helpers";

test.describe("importar documento .docx", () => {
  test("crea → exporta → importa el mismo archivo de regreso", async ({ page }, testInfo) => {
    logHttpErrors(page);

    // 1. Crear un doc nuevo y exportarlo
    await crearDocumentoMRM(page, "E2E Importar");

    await page.getByRole("button", { name: /Exportar DOCX/ }).click();
    const downloadPromise = page.waitForEvent("download", { timeout: 30_000 });
    await page.getByRole("menuitem", { name: /Bilingüe \(recomendado\)/ }).click();
    const download = await downloadPromise;

    // Guardar con extensión .docx para que el validador del frontend lo
    // acepte (el path temporal de Playwright no la conserva por default).
    const archivoExportado = path.join(testInfo.outputDir, "exportado.docx");
    await download.saveAs(archivoExportado);

    // 2. Ir a importar y subir el .docx descargado
    await page.goto("/importar");
    await expect(page.getByRole("heading", { name: "Importar documento existente" })).toBeVisible();

    // El input está oculto (hidden + display:none). Usamos el event filechooser
    // disparado al clickear la dropzone — más confiable que setInputFiles
    // contra un input no visible.
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: /Arrastra el \.docx o \.pdf aquí/ }).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(archivoExportado);

    // El botón "Importar documento" pasa de disabled a enabled cuando el ancla
    // se setea. Lo esperamos en vez de un texto del archivo (que puede aparecer
    // en truncado distinto según la longitud del nombre).
    const submitBtn = page.getByRole("button", { name: "Importar documento" });
    await expect(submitBtn).toBeEnabled({ timeout: 10_000 });

    // 3. Submit y esperar redirect al dashboard del nuevo doc
    await submitBtn.click();
    await page.waitForURL(/\/documentos\/[0-9a-f-]{36}$/, { timeout: 60_000 });

    // 4. El nuevo doc importado renderiza un dashboard válido (28 secciones
    //    MRM, badge Borrador). No exigimos que el nombre del modelo coincida
    //    palabra por palabra — el reader puede normalizar; lo importante es
    //    que parsea estructura sin crashear.
    await expect(page.getByText("Borrador", { exact: true })).toBeVisible();
    await expect(page.getByText(/secciones del template/)).toBeVisible();

    // 5. Audit trail tiene al menos 1 evento (el de importación) — usamos
    // first() porque hay 2 textos que mencionan "evento" en el dashboard.
    await expect(page.getByText(/\d+ evento.*audit/).first()).toBeVisible();
  });
});
