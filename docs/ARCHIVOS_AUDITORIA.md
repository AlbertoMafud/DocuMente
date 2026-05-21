# Auditoría de archivos — qué se queda, qué se borra

> **Propósito:** después del merge a `main`, depurar el repo. Este doc es la guía para esa depuración.
>
> **Convención de columnas:**
>
> - **VIVO** — el código lo usa o el equipo lo necesita. Se queda.
> - **CANDIDATO** — probablemente sobra. Revisar antes de borrar, pero con bajo riesgo.
> - **PERSONAL** — gitignored, vive solo en la máquina de Alberto. No entra al repo.
> - **ARCHIVE** — útil como historia pero no operativo. Considerar mover a `docs/archive/` o `docs/legacy/`.

---

## 1. Root del repo

| Archivo | Estado | Razón |
|---|---|---|
| `app.py` | **VIVO** | Entry point de Streamlit. Hasta sunset del legacy, indispensable |
| `pyproject.toml` | **VIVO** | Deps + ruff + mypy + pytest config |
| `README.md` | **VIVO** | Bienvenida al repo. Considerar actualizar con instrucciones para los 3 servicios |
| `status.md` | **VIVO** | Estado vivo, se lee al iniciar cada sesión |
| `CLAUDE.md` | **VIVO** | Instrucciones de Claude por proyecto |
| `.gitignore` | **VIVO** | Crítico — incluye fix S14 para `frontend/src/lib/` |
| `.env` | **PERSONAL** | Gitignored. Tiene `ANTHROPIC_API_KEY` |
| `.env.example` | **VIVO** | Plantilla para nuevos devs |

---

## 2. Carpeta `src/` — código de producción

### `src/core/` (DOMINIO)

| Subcarpeta / archivo | Estado | Razón |
|---|---|---|
| `models/` (todos los `.py`) | **VIVO** | Entidades Pydantic, fundación del sistema |
| `usecases/` (todos los `.py`) | **VIVO** | 28+ use cases consumidos por Streamlit y FastAPI |
| `rules/state_machine.py` | **VIVO** | Validación de transiciones MRM |
| `template_catalog.py` | **VIVO** | Catálogo NYL Model Development (28 secciones, 9 capítulos) |
| `template_catalog_prophet.py` | **VIVO** | Catálogo Ficha Prophet (12 secciones) |

### `src/api/` (S14 — REST API)

| Archivo | Estado | Razón |
|---|---|---|
| `main.py`, `deps.py`, `auth.py`, `errors.py` | **VIVO** | Core de FastAPI |
| `routers/*.py` (11 archivos) | **VIVO** | Cada router expone un dominio |
| `schemas/*.py` (10 archivos) | **VIVO** | DTOs Pydantic para JSON |

### `src/ui/` (Streamlit legacy)

| Subcarpeta | Estado | Razón |
|---|---|---|
| `pages/` (13 archivos) | **VIVO mientras Streamlit coexiste** — al sunset, **TODA esta carpeta es candidata a borrar** |
| `components/` (13 archivos) | **VIVO** mientras Streamlit coexiste. Algunos componentes (chat_bubble, continue_hero, gap_badge) ya tienen equivalente en Next.js |
| `theme.py` | **VIVO mientras Streamlit coexiste** |

**Plan de sunset Streamlit:** definir fecha (sugerencia: 2-3 semanas post-go-live de Next.js en prod). Cuando se apague:
- Borrar `src/ui/` completo
- Borrar `app.py`
- Quitar `streamlit*` de `pyproject.toml`
- Quitar tests asociados a `src/ui/` en `tests/unit/`

### `src/llm/`, `src/docs/`, `src/storage/`

| Carpeta | Estado | Razón |
|---|---|---|
| `src/llm/` | **VIVO** | AnthropicClient + prompts + pricing. Centro neurálgico LLM |
| `src/docs/readers/`, `src/docs/formulas/` | **VIVO** | Lectores DocxReader, AnchorReader, PdfReader; render LaTeX |
| `src/docs/templates/model_development_smnyl_final.docx` | **VIVO** | Plantilla maestra MRM con marca SMNYL (el `_final` indica versión definitiva) |
| `src/docs/templates/model_development_smnyl.docx` | **CANDIDATO** | Versión vieja sin el sufijo `_final`. Verificar que el código apunte al `_final`; si sí, borrar este |
| `src/docs/templates/prophet_model_doc_smnyl.docx` | **VIVO** | Plantilla Prophet — aún necesita pulido (D.1.a). NO BORRAR |
| `src/storage/` | **VIVO** | Repos + Storage abstraction |
| `src/config.py` | **VIVO** | Settings tipados |

---

## 3. Carpeta `frontend/` (Next.js — S14)

| Subcarpeta / archivo | Estado | Razón |
|---|---|---|
| `package.json`, `package-lock.json` | **VIVO** | Manifests de deps Node |
| `tsconfig.json`, `next.config.mjs`, `postcss.config.mjs` | **VIVO** | Config Next.js |
| `tailwind.config.ts` | **VIVO** | Tokens SMNYL + shadcn HSL |
| `components.json` | **VIVO** | Config shadcn/ui |
| `.eslintrc.json` | **VIVO** | ESLint config |
| `.gitignore` | **VIVO** | Específico de Next.js (node_modules, .next, etc.) |
| `.env.local.example` | **VIVO** | Plantilla env vars frontend |
| `README.md` | **VIVO** | Instrucciones específicas del frontend |
| `src/app/` (todas las rutas) | **VIVO** | 17 páginas funcionales |
| `src/components/ui/` (10 primitives) | **VIVO** | Button, Card, Badge, etc. |
| `src/components/layout/` | **VIVO** | Sidebar + Topbar |
| `src/components/home/` | **VIVO** | ContinueHero, WelcomeHero, DocumentCard, DocumentList |
| `src/components/dashboard/` | **VIVO** | DashboardHero, MetricsRow, GovernanceCard, BrechasAccordion, SeccionesAccordion, QuickLinks |
| `src/components/auditoria/timeline.tsx` | **VIVO** | Timeline vertical de eventos |
| `src/components/entrevista/chat-bubble.tsx` | **VIVO** | Bubble de chat LLM |
| `src/components/providers.tsx` | **VIVO** | QueryClient + Toaster |
| `src/lib/utils.ts` | **VIVO** | `cn()` + `tiempoRelativo()` |
| `src/lib/api/types.ts`, `client.ts`, `hooks.ts` | **VIVO** | Cliente API + types + hooks |
| `src/app/fonts/GeistVF.woff`, `GeistMonoVF.woff` | **CANDIDATO** | Fuentes Geist instaladas por `create-next-app` pero **no las usamos** (usamos Georgia/Tahoma). Borrar para reducir el bundle |
| `src/app/favicon.ico` | **CANDIDATO** | Favicon default de Next.js — reemplazar por uno con marca SMNYL antes de prod |
| `node_modules/` | **GITIGNORED** | Se regenera con `npm install` |
| `.next/` | **GITIGNORED** | Build cache |

---

## 4. Carpeta `tests/`

| Subcarpeta | Estado | Razón |
|---|---|---|
| `tests/unit/` (~50+ archivos) | **VIVO mientras Streamlit coexiste**. Cuando se haga sunset del legacy, los tests de UI Streamlit (`test_continue_hero`, `test_stepper`, `test_seccion_card`, etc.) se eliminan junto con `src/ui/` |
| `tests/integration/` | **VIVO** | Smoke tests del API + integración con docs reales |
| `tests/integration/test_api_smoke.py` | **VIVO** | 28 tests críticos del contrato REST — **NO BORRAR** |
| `tests/integration/test_import_end_to_end.py` | **VIVO** pero fixtures `SMNYL/Ejemplos actuales/*.docx` no se copian al worktree. En main + EC2 sí están |

**Tests específicos a borrar cuando sunset Streamlit:**
`test_back_button`, `test_continue_hero`, `test_header_breadcrumbs`, `test_seccion_card`, `test_stepper`, `test_timeline`, `test_theme_a11y`, `test_theme_microinteractions`, `test_undo_banner`, `test_onboarding_banner`, `test_auth_gate`, `test_editar_seccion_mrm/prophet` (los de UI inline) — todos los que mockean `streamlit.markdown`.

---

## 5. Carpeta `docs/`

### Documentos VIVOS (referencia continua)

| Archivo | Estado | Razón |
|---|---|---|
| `BRAND_GUIDELINES.md` | **VIVO** | Fuente canónica de paleta SMNYL |
| `MRM_REQUIREMENTS.md` | **VIVO** | Marco regulatorio interno — referencia para feature decisions |
| `TEMPLATE_MODEL_DEV.md` | **VIVO** | Estructura del template oficial NYL |
| `UX_PRINCIPLES.md` | **VIVO** | Principios UI/UX del proyecto |
| `MIGRATION_TO_EC2.md` | **VIVO** | Plan de migración actualizado en S14 |
| **`ARQUITECTURA.md`** (NUEVO S14) | **VIVO** | Arquitectura técnica atemporal |
| **`GUIA_DOCUMENTE.md`** (NUEVO S14) | **VIVO** | Guía conceptual + técnica para Alberto |
| **`HANDOFF_VIDAL.md`** (NUEVO S14) | **VIVO** | Snapshot main → branch para Vidal |
| **`ARCHIVOS_AUDITORIA.md`** (este archivo) | **VIVO** | Esta auditoría |

### Documentos ARCHIVE — mover a `docs/archive/` post-merge

| Archivo | Estado | Razón |
|---|---|---|
| `technical_architecture_for_data_architect.md` | **ARCHIVE** | 1351 líneas en inglés, escrito antes del rewrite S14. **Reemplazado por `ARQUITECTURA.md` (atemporal) + `HANDOFF_VIDAL.md` (snapshot)**. Útil como historia. Considerar mover a `docs/archive/` |
| `E2E_TEST_SCENARIO.md` | **ARCHIVE** | 2158 líneas, escenario MRM-grade del Pricing GMM Individual. Útil para validación; no es referencia operativa. Mover a `docs/archive/` |
| `TEMPLATE_DESIGN_SESSION.md` | **ARCHIVE** | Notas de diseño del template hechas en una sesión. Snapshot histórico |
| `TEMPLATE_PLACEHOLDERS_GUIDE.md` | **ARCHIVE** | Guía de placeholders Jinja del .docx. Útil pero relevante solo cuando se rediseña el template |
| `Migracion EC2/CHANGELOG_TECNICO_VIDAL.md` | **ARCHIVE** | Reemplazado por `HANDOFF_VIDAL.md` (más actual y completo). El changelog histórico se preserva en git log |

### Documentos VIVOS de soporte específico

| Archivo | Estado | Razón |
|---|---|---|
| `Modulo Prophet MA/Guia_Llenado_Registro.md` | **VIVO** | Instrucciones para que MA llene el Excel de Prophet — útil para demo |
| `Modulo Prophet MA/Ficha_Tecnica_Modelo_Rentabilidad.docx` | **VIVO** | Ejemplo de ficha técnica para referencia visual |
| `Modulo Prophet MA/Registro Modelos_envioAlberto.xlsx` | **VIVO** | Registro Prophet real que MA mandó — input para tests |
| `Modulo Prophet MA/Registro_Modelos_Template.xlsx` | **VIVO** | Plantilla del registro para auto-llenado |
| `superpowers/plans/2026-05-07-crear-documento-desde-cero.md` | **ARCHIVE** | Plan ejecutado en sesión 9. Historia útil |
| `superpowers/plans/2026-05-14-prophet-fase0.md` | **ARCHIVE** | Plan ejecutado en sesiones 11-12. Historia útil |
| `superpowers/plans/2026-05-19-migracion-frontend-nextjs.md` | **VIVO** | El plan original de migración. Útil para comparar contra lo que terminamos haciendo en S14. Considerar marcarlo "ejecutado en S14" en el header |
| `superpowers/specs/2026-05-14-prophet-fase0-design.md` | **ARCHIVE** | Spec ejecutado. Historia |
| `superpowers/specs/2026-05-19-accessibility-audit.md` | **ARCHIVE** | Audit ejecutado en S14 (5 fixes a11y críticos commiteados). Historia |
| `superpowers/specs/2026-05-19-design-critique-por-pantalla.md` | **ARCHIVE** | Audit ejecutado en S14 (Premium T1). Historia |
| `superpowers/specs/2026-05-19-design-system-audit.md` | **ARCHIVE** | Audit ejecutado en S14 (tokens dark/soft + density). Historia |
| `superpowers/specs/2026-05-19-uiux-pro-max-audit.md` | **ARCHIVE** | Audit ejecutado en S14 (10/10 quick wins commiteados). Historia |

### Documentos PERSONALES (no entran al repo — gitignored)

> Estos no aparecen en este worktree porque están en main / sin commitear. Pero existen en `/c/Users/alber/Claude_AI/proyectos/DocuMente/docs/` localmente.

| Patrón | Estado | Razón |
|---|---|---|
| `docs/CORREO_VIDAL*.md` | **PERSONAL** | Drafts de correo — no se commitea |
| `docs/MIGRATION_GUIA_EJECUTIVA.md` | **PERSONAL** | Versión ejecutiva en español de Alberto |
| `docs/REUNION_*.md` | **PERSONAL** | Notas de reuniones |
| `docs/DOCUMENTE_GUIA_PERSONAL.md` | **PERSONAL** | Guía vieja en español. **Reemplazada por `GUIA_DOCUMENTE.md` (S14)** — considerar borrar la versión personal o renombrar la nueva |
| `docs/Comentarios/` | **PERSONAL** | Notas personales locales |

**Acción recomendada post-merge:** decidir si `DOCUMENTE_GUIA_PERSONAL.md` (personal) se reemplaza por `GUIA_DOCUMENTE.md` (commiteado). La nueva está más actualizada y cubre la arquitectura S14.

---

## 6. Carpetas top-level

| Carpeta | Estado | Razón |
|---|---|---|
| `assets/` | **VIVO** (carpeta), **GITIGNORED** el logo | El logo SMNYL no se commitea (marca registrada). La carpeta sí |
| `data/` | **GITIGNORED** | BD local + uploads + exports — solo en máquina local |
| `SMNYL/` | **GITIGNORED** | Material fuente — IP de la empresa, NO se commitea |
| `scripts/` | **VIVO** | `build_template.py` — script para construir plantilla DOCX. Útil para mantenimiento |
| `tests/` | **VIVO** | Ver §4 |
| `.claude/` | **GITIGNORED** | Worktrees y planes locales de Claude Code |
| `.superpowers/` | **GITIGNORED** | Internals de Claude |
| `.ruff_cache/`, `.mypy_cache/`, `__pycache__/` | **GITIGNORED** | Caches de tooling |
| `.venv/`, `venv/` | **GITIGNORED** | Virtualenv local |

---

## 7. Checklist de depuración post-merge

Cuando hagas merge a main y quieras depurar, ejecuta estas tareas en orden:

### Fase 1 — Limpieza inmediata (sin riesgo)

- [ ] Crear `docs/archive/` y mover ahí:
    - [ ] `technical_architecture_for_data_architect.md`
    - [ ] `E2E_TEST_SCENARIO.md`
    - [ ] `TEMPLATE_DESIGN_SESSION.md`
    - [ ] `TEMPLATE_PLACEHOLDERS_GUIDE.md`
    - [ ] `Migracion EC2/CHANGELOG_TECNICO_VIDAL.md`
    - [ ] `superpowers/plans/2026-05-07-crear-documento-desde-cero.md`
    - [ ] `superpowers/plans/2026-05-14-prophet-fase0.md`
    - [ ] `superpowers/specs/2026-05-14-prophet-fase0-design.md`
    - [ ] `superpowers/specs/2026-05-19-*` (4 audits)
- [ ] Borrar `src/docs/templates/model_development_smnyl.docx` (versión vieja, sin `_final`) — verificar primero que `dashboard.py` y `exportar.py` usan `model_development_smnyl_final.docx`
- [ ] Borrar `frontend/src/app/fonts/GeistVF.woff` y `GeistMonoVF.woff` (no se usan)
- [ ] Reemplazar `frontend/src/app/favicon.ico` por uno con marca SMNYL

### Fase 2 — Reconciliación de docs personales (decisión)

- [ ] Decidir si `docs/DOCUMENTE_GUIA_PERSONAL.md` (personal, local) se borra al haber sido reemplazada por `docs/GUIA_DOCUMENTE.md` (versión nueva commiteada)
- [ ] Revisar `docs/Comentarios/` y archivar lo que ya no aplique

### Fase 3 — Sunset Streamlit (después de validar Next.js en producción 2-3 semanas)

- [ ] Borrar `app.py`
- [ ] Borrar `src/ui/` (completo)
- [ ] Borrar tests específicos de Streamlit en `tests/unit/`:
    - [ ] `test_back_button.py`
    - [ ] `test_continue_hero.py`
    - [ ] `test_header_breadcrumbs.py`
    - [ ] `test_seccion_card.py`
    - [ ] `test_stepper.py`
    - [ ] `test_timeline.py`
    - [ ] `test_theme_a11y.py`
    - [ ] `test_theme_microinteractions.py`
    - [ ] `test_undo_banner.py`
    - [ ] `test_onboarding_banner.py`
    - [ ] `test_editar_seccion_mrm.py` (tests del editor Streamlit; si hay equivalentes para el editor Next.js que aún no escribimos, esos no se borran)
    - [ ] `test_editar_seccion_prophet.py`
- [ ] Quitar de `pyproject.toml`:
    - [ ] `streamlit>=1.36.0`
    - [ ] `streamlit-extras>=0.4.7`
- [ ] Quitar systemd unit `documente-streamlit.service` en EC2
- [ ] Quitar location `/legacy/` del nginx config

### Fase 4 — Mejoras pendientes (no son depuración, son completitud)

- [ ] Validar `npm run build` en máquina limpia con Node 20+
- [ ] Reemplazar CORS `*` por `CORS_ORIGINS` env var
- [ ] Migrar tipos manuales a auto-generación con `openapi-typescript`
- [ ] Agregar tests E2E con Playwright (mínimo flujo happy path: crear → editar → exportar)
- [ ] Agregar al menos 5 unit tests de componentes React con Vitest

---

## 8. Resumen ejecutivo

**Lo que se queda obligatoriamente:** todo `src/core/`, todo `src/api/`, todo `frontend/src/` (excepto fonts Geist), todos los docs nuevos S14, `MIGRATION_TO_EC2.md`, `BRAND_GUIDELINES.md`, `MRM_REQUIREMENTS.md`, `TEMPLATE_MODEL_DEV.md`, `UX_PRINCIPLES.md`.

**Lo que se mueve a `docs/archive/`:** 10 documentos históricos (audits ejecutados, plans completados, technical_architecture_for_data_architect).

**Lo que se borra inmediato:** 1 .docx viejo, 2 .woff de fonts no usadas.

**Lo que se borra al sunset de Streamlit:** `app.py` + `src/ui/` + ~12 tests + 2 deps de pyproject.

**Volumen total de depuración esperado:** ~15-20 archivos relocalizados + ~15 archivos borrados. Repo más limpio sin perder historia.
