/**
 * E2E — guarda MRM: bloquea draft→in_review con razón útil.
 *
 * El state machine de MRM exige que TODAS las secciones obligatorias estén
 * resueltas (completa u omitida) antes de pasar a En Revisión. Un documento
 * recién creado tiene 22 secciones obligatorias vacías, así que la
 * transición DEBE rechazarse con 409 + mensaje accionable.
 *
 * Esto es valioso de testear:
 *   - El botón está visible en la UI (no escondido por la guarda)
 *   - El backend devuelve 409 con razones legibles
 *   - El frontend muestra un toast informativo (no un crash)
 *   - El estado del doc NO cambia (sigue en Borrador)
 *
 * Un test que valide la transición exitosa requeriría llenar 22 secciones
 * primero — demasiado lento para una suite básica. Se puede agregar como
 * test largo en otra spec si vale la pena.
 */
import { test, expect } from "@playwright/test";
import { crearDocumentoMRM, logHttpErrors } from "./helpers";

test.describe("gobernanza MRM — guarda del state machine", () => {
  test("draft → in_review se rechaza con razón útil cuando hay secciones obligatorias vacías", async ({
    page,
  }) => {
    logHttpErrors(page);

    await crearDocumentoMRM(page, "E2E Gobernanza");

    // Estado inicial: Borrador, sign-offs deshabilitados
    await expect(page.getByText("Borrador", { exact: true })).toBeVisible();
    await expect(
      page.getByText("Solo disponibles cuando el documento está En Revisión."),
    ).toBeVisible();

    // 1. El botón "Pasar a En Revisión" SÍ aparece (la UI lista la transición
    // como candidata; la guarda vive en el backend, no en la UI).
    const botonTransicion = page.getByRole("button", { name: "Pasar a En Revisión" });
    await expect(botonTransicion).toBeVisible();

    // 2. Click — el backend rechaza con 409 + razón "X sección(es) obligatoria(s)
    // sin resolver". El frontend muestra toast.error.
    await botonTransicion.click();

    // 3. Toast de error con la razón del state machine
    await expect(page.getByText(/Transición rechazada/)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/sección\(es\) obligatoria\(s\) sin resolver/)).toBeVisible();

    // 4. El estado del documento NO cambió — sigue Borrador y sign-offs
    // siguen deshabilitados.
    await expect(page.getByText("Borrador", { exact: true })).toBeVisible();
    await expect(
      page.getByText("Solo disponibles cuando el documento está En Revisión."),
    ).toBeVisible();
  });
});
