/**
 * Helpers compartidos entre tests E2E.
 *
 * Cada test es independiente (crea su propio documento). Estos helpers
 * encapsulan la precondición más común: tener un documento recién creado
 * para operar sobre él.
 */
import { Page, expect } from "@playwright/test";

/**
 * Crea un documento Model Development vía la UI y devuelve su ID + nombre.
 *
 * Deja al usuario parado en el dashboard `/documentos/{id}`.
 */
export async function crearDocumentoMRM(
  page: Page,
  prefijoNombre = "E2E",
): Promise<{ id: string; nombre: string }> {
  const nombre = `${prefijoNombre} — ${Date.now()}`;

  await page.goto("/documentos/crear");
  await expect(page.getByRole("heading", { name: "Crear documento nuevo" })).toBeVisible();
  await page.getByLabel("Nombre del modelo").fill(nombre);
  await page.getByRole("button", { name: "Crear documento" }).click();

  await page.waitForURL(/\/documentos\/[0-9a-f-]{36}$/, { timeout: 15_000 });
  const url = page.url();
  const id = url.match(/documentos\/([0-9a-f-]{36})/)![1];

  await expect(page.getByRole("heading", { name: nombre })).toBeVisible();
  return { id, nombre };
}

/**
 * Registra un listener de responses HTTP 4xx/5xx para diagnóstico en CI.
 * Llamar al inicio de cada test que pueda fallar por red.
 */
export function logHttpErrors(page: Page): void {
  page.on("response", async (res) => {
    if (res.status() >= 400) {
      let body = "";
      try {
        body = await res.text();
      } catch {
        body = "<no body>";
      }
      // eslint-disable-next-line no-console
      console.log(
        `[E2E] ${res.status()} ${res.request().method()} ${res.url()}\n  body: ${body.slice(0, 500)}`,
      );
    }
  });
}
