# Suite E2E — Playwright

Pruebas end-to-end de DocuMente con [Playwright](https://playwright.dev/).
Cada test abre un navegador (Chromium headless), recorre la app como lo
haría un usuario real, y valida que el flujo termine como debe.

---

## Qué cubre la suite (7 tests)

| Archivo | Qué simula | Por qué importa |
|---|---|---|
| `crear-y-exportar.spec.ts` | Usuario crea un documento desde cero y descarga el DOCX | Camino feliz mínimo — si esto falla, todo lo demás falla |
| `importar.spec.ts` | Crear → exportar → importar el mismo archivo de regreso | Valida el ciclo completo. Cero fixtures binarios commiteados |
| `editar-seccion.spec.ts` | Abrir sección, escribir, guardar, recargar, contenido sigue ahí | La persistencia en SQLite/Postgres funciona. Si esto se rompe, el producto se rompe |
| `gobernanza.spec.ts` | Transición MRM Borrador → En Revisión + sign-off Reviewer | Gobernanza del marco MRM funcional |
| `apendices.spec.ts` | Subir un CSV como apéndice a una sección | El upload multipart de archivos funciona |
| `llm-fallback.spec.ts` | Sin `ANTHROPIC_API_KEY`, la entrevista da 503 amigable | El sistema degrada elegantemente cuando falta config, no crashea |
| `versiones.spec.ts` | Crear un snapshot inmutable con comentario y verificarlo en la lista | Versionado para auditoría MRM funcional |

---

## Cómo correr

```bash
# Desde frontend/, instalación una sola vez:
npm install
npx playwright install chromium

# Correr la suite completa (headless, ~30-60s):
npm run test:e2e

# Modo interactivo con UI de Playwright (debugging visual):
npm run test:e2e:ui

# Solo un archivo:
npx playwright test e2e/editar-seccion.spec.ts

# Solo un test por nombre:
npx playwright test --grep "transición"

# Con navegador visible (no headless) para ver qué hace:
npx playwright test --headed
```

---

## Cómo funciona la infraestructura

`playwright.config.ts` define **dual webServer**: Playwright arranca
automáticamente el backend FastAPI y el frontend Next.js antes de los tests,
y los apaga al terminar.

```
Backend:  python -m uvicorn src.api.main:app --port 8100   (cwd: raíz del repo)
Frontend: npm run dev -- -p 3100                            (cwd: frontend/)
```

**Puertos aislados** (8100/3100) para no chocar con servers dev locales
que típicamente corren en 8001/3000.

El frontend recibe `NEXT_PUBLIC_API_URL=http://localhost:8100` via env para
apuntar al backend del E2E (no al dev local).

---

## Gotchas conocidos

### Backend stale en background

Si arrancaste `uvicorn` manualmente para debug (curl) y se quedó corriendo
en el puerto 8100, Playwright lo reusa por `reuseExistingServer: true`. Eso
puede ocultar fixes recientes — el backend reusado tiene código viejo.

**Síntoma:** un test que debería pasar falla con un error que ya arreglaste.

**Fix:** matar el uvicorn manual antes de correr Playwright:
```bash
# Encontrar el PID en 8100:
netstat -ano | findstr ":8100"
# Matar (PowerShell):
Stop-Process -Id <PID> -Force
```

### `next dev` cae a otro puerto silenciosamente

Si el 3100 está ocupado, Next.js por default cae a 3101, 3102, etc., **sin
avisar**. Playwright queda esperando un puerto que nunca se levanta. Por eso
el config usa `npm run dev -- -p 3100` (con flag explícito), que fuerza el
puerto y falla rápido si está ocupado.

### Worktree no hereda `.env`

Los tests corren con el backend **sin `ANTHROPIC_API_KEY`** — es deliberado
(eso hace que `llm-fallback.spec.ts` valide el 503). Los otros tests no
necesitan la key porque crear/editar/exportar/importar no llaman al LLM.

Si quieres ejecutar la suite con LLM disponible (por ejemplo para validar
flujos de entrevista en otra rama), copia tu `.env` con la key al raíz del
worktree y modifica `playwright.config.ts` para pasarla en el webServer
command del backend.

### Unicode en nombres de archivo (resuelto en S15)

Antes de `8f4835a`, exportar un .docx con caracteres no-ASCII en el nombre
(em-dash, acentos) devolvía HTTP 400. Si reaparece, revisar
`src/api/routers/exportar.py:_content_disposition()` que aplica encoding
RFC 6266 + 5987.

---

## Cómo escribir un test nuevo

1. **Toma `crear-y-exportar.spec.ts` como template.** Es el más simple y
   muestra el patrón básico.
2. **Reusa el helper `crearDocumentoMRM(page, prefijo)`** de `helpers.ts`
   para tener un documento como precondición. Devuelve `{ id, nombre }`.
3. **Activa `logHttpErrors(page)`** al inicio si vas a depurar fallos —
   imprime el body de cada respuesta 4xx/5xx en el output del test.
4. **Cada test es independiente.** Crea su propio documento; no asumas
   estado compartido con otros tests.
5. **Selectores preferidos**, en orden:
   - `page.getByRole("button", { name: "..." })` — más estable
   - `page.getByLabel("...")` — para inputs con label
   - `page.getByText("...")` — para validar contenido visible
   - Locators con `data-testid` — solo si no hay otra opción
6. **Timeouts**: el default es 30s globalmente, 10s para acciones, 15s
   para navegaciones. Ajusta solo si tienes una razón concreta.

---

## Resultados y artefactos

- `test-results/` — screenshots, traces, error-context en fallos. **Ignored
  por git** (`frontend/.gitignore`).
- `playwright-report/` — reporte HTML interactivo. Abre con
  `npx playwright show-report`.

---

## Próximos pasos (sesión 16+)

- Más cobertura: editar metadata, omitir sección (cuando exista UI en
  Next.js — actualmente solo en Streamlit legacy), apéndice tipo fórmula
  LaTeX, transiciones MRM avanzadas (in_review → approved → published).
- **Smoke en CI**: integrar `npm run test:e2e` en GitHub Actions cuando
  Vidal apruebe el deploy. Cuidado con secrets: la API key NO debe vivir
  en CI; el LLM se mockea o se skip-ea ese test específico.
