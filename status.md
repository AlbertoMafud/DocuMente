# Status — DocuMente

> Estado vivo del proyecto. Se lee al iniciar sesión y se actualiza al cerrar si hubo cambios significativos.

**Última actualización:** 2026-05-20 (sesión 17 — paralelización LLM + streaming SSE: latencia ~10 min → ~1-2 min y barra de progreso en vivo en lugar de pantalla en blanco. **5 commits S17 sobre S16.** Tests: 439 unit + 7 E2E.)

---

## Estado actual

**MVP + Prophet Fase 0 + Fase A + B + C + D.2 (S13) + Remediación UX completa + Rewrite arquitectónico a 3 servicios (S14) + Cierre técnico opción A (S15) + Feedback post-demo (S16)** todo en el branch `claude/affectionate-noether-8e038f`. Solo A.1.c (Cognito multi-tenant real) queda bloqueado pendiente reunión Vidal. D.1 (Prophet correctivos + demo MA) pendiente reunión MA — agenda preparada en `docs/PROPHET_AGENDA_MA.md`.

**Arquitectura nueva (S14):** la app ahora tiene 3 servicios coexistentes:

| Servicio | Puerto | Stack | Estado |
|---|---|---|---|
| **Frontend Next.js premium** | 3000 (dev: 3002) | Next.js 14 + Tailwind + shadcn/ui + TanStack Query | NUEVO — paridad funcional con Streamlit |
| **API REST FastAPI** | 8001 | FastAPI + Pydantic + uvicorn | NUEVO — 46 endpoints, OpenAPI 3.1, Swagger en /docs |
| Streamlit (legacy) | 8052 | Streamlit + theme SMNYL | Preservado por compatibilidad — same DB |

Ambos frontends consumen los mismos use cases en `src/core/usecases/`. El dominio Python no cambió.

**Repo GitHub `AlbertoMafud/DocuMente`:**
- `main` congelada en `51d845e` (MVP estable — el plan dice que main queda intacta hasta que Vidal valide deploy).
- **`claude/affectionate-noether-8e038f`** con todo S13+S14+S15 (26 commits sobre main). **PUSHEADO** a `origin/claude/affectionate-noether-8e038f` al cierre de S15 (último tip: `eedf693`).
- **PR a main** abierto pendiente — link: `https://github.com/AlbertoMafud/DocuMente/compare/main...claude/affectionate-noether-8e038f` (cuando Alberto haga click en "Create pull request").
- `feat/remediacion-s13-s16` aún existe en GitHub con el snapshot S13 puro (obsoleto, sin S14/S15).

**Tests: 528 Python + 7 E2E Playwright** (429 unit + 99 integration + 7 E2E). Ruff check + format clean. ESLint frontend clean. TypeScript `--noEmit` clean. 0 regresiones.

**Próximo inmediato (sesión 16) — orden ejecutable:**

### Operacional (path inmediato)

1. **Probar entrevista LLM** localmente: `cp /c/Users/alber/Claude_AI/proyectos/DocuMente/.env .env` y verificar que la entrevista funciona end-to-end en Next.js (puerto 3000) + API (puerto 8001).
2. **Compartir con Vidal**: el PR + los 4 docs (`HANDOFF_VIDAL.md`, `ARQUITECTURA.md`, `MIGRATION_TO_EC2.md`, `ARCHIVOS_AUDITORIA.md`). El PR ahora trae 3 commits adicionales de S15 (CORS env var listo, fix Unicode export, Playwright como base de testing).
3. **Agendar reunión Vidal (30 min)** para resolver §8 HANDOFF: Cognito (A.1.c), dominio interno, sunset Streamlit, Bedrock.

### Estratégico (post-aprobación Vidal)

4. **Merge PR a main**.
5. **Depuración** según `docs/ARCHIVOS_AUDITORIA.md`.
6. **D.1.a Template Prophet DOCX** + D.1.c self-service + D.1.d demo MA — destrabe negocio Prophet Fase 1.

### Mejoras posibles si hay tiempo

7. **Más tests E2E** — escalar Playwright a 5-8 tests pre-deploy: importar, editar sección persistente, omitir, transición estado MRM, audit trail, descargar versión, apéndice, fallo entrevista 503.
8. **Limpiar carpeta huérfana** `.claude/worktrees/optimistic-zhukovsky-b7e828/` (cosmético — `git worktree prune` + `rm -rf`).

---

## Avance acumulado

- Fase 0 ✅ — Setup, archivos de contexto, theme SMNYL, app branded.
- Fase 1 ✅ — Modelos Pydantic, Storage interface, DocxReader, GapAnalyzer, Repository SQLite, use case ImportarDocumento, UI dashboard.
- Fase 2 ✅ — LLMClient + AnthropicClient, prompts (tono/entrevista/drafting/contexto fijo cacheado ~12K tokens), InterviewEngine, Drafter, EstadoEntrevista persistido, pantalla de entrevista split chat↔preview.
- Fase 2.5 ✅ — Refinamiento post-prueba (memoria del modelo, apéndices Excel/CSV, drafter institucional, reporte de costo, vista previa HTML, tiered Anthropic).
- Fase 4 ✅ — Estados + audit trail (sesión 6).
- Fase 3 ✅ — DocxWriter con plantilla maestra (sesión 7). Render funcional end-to-end.
- Fase 6 ✅ — Documentos de migración (sesión 7): técnico para arquitecto + ejecutivo en español aterrizado para Alberto.
- Feature **"Omitir sección"** ✅ (sesión 7).
- Feature **"Editor de metadata"** ✅ (sesión 7) — botón en dashboard para editar nombre del modelo y otros campos.
- Feature **"Subdoc + RichText"** ✅ (sesión 7) — `**negritas**` ahora son negritas reales en Word; subtítulos detectados; bullets con prefijo `•`.
- Feature **"Tablas nativas + font adaptable"** ✅ (sesión 7) — apéndices con tabla markdown se renderizan como tablas nativas de Word con bordes y font 7-10pt según densidad.
- Feature **"Traducción ES/EN"** ✅ (sesión 7) — toggle al exportar; inglés corporativo americano con prompt específico; traducción efímera (no se persiste).
- Feature **"Cleanup de markdown"** ✅ (sesión 7) — quita asteriscos, hashes, separadores `---` literales del DOCX.
- Feature **"Crear documento desde cero"** ✅ (sesión 9) — pantalla `crear_nuevo.py` con form de 2 campos (nombre + model_id), use case `CrearDocumentoEnBlanco`, función pública `construir_secciones_vacias()` promovida a `template_catalog`. Botón habilitado en home; routing conectado. Flujo paralelo al de importar — converge en onboarding → dashboard → entrevista → export.
- **Documentación de soporte para arquitecto y validación** ✅ (sesión 9) — 3 documentos extensos generados: `docs/technical_architecture_for_data_architect.md` (1,351 líneas, 15 secciones en inglés para Vidal), `docs/E2E_TEST_SCENARIO.md` (2,158 líneas, simulación MRM-grade del Pricing GMM Individual con 28 secciones), `docs/DOCUMENTE_GUIA_PERSONAL.md` (397 líneas, guía ejecutiva en español, gitignored).

---

## Progreso de la sesión 6 (2026-05-06)

### Bug fix — widget de costo invisible
- **Causa raíz:** Streamlit cacheó módulos viejos antes de Fase 2.5; las llamadas LLM no se registraron en `metricas_uso`. Confirmado: tras restart, las métricas SÍ se registran.
- **Mejora UX:** widget ahora se muestra **siempre** (con `$0.00 USD` y `—` cuando vacío), con caption explicativo. `src/ui/pages/dashboard.py:129-148`.

### Fase 4 — backend (Día 1, TDD puro)
- **`src/core/rules/state_machine.py`** — `DocumentStateMachine` con las 5 transiciones MRM (§10):
  - `draft → in_review` (requiere 100% completitud obligatorias)
  - `in_review → approved` (requiere `signoff_reviewer` en audit_trail)
  - `in_review → draft` (rechazo, siempre permitido)
  - `approved → published` (requiere `signoff_fae`)
  - `approved → in_review` (retracción, siempre permitida)
  - `published → retired` (terminal)
  - `retired → *` (bloqueado, inmutable)
  - Devuelve `ResultadoTransicion(permitida, razones)` con razones legibles para mostrar al usuario.
- **`src/core/usecases/cambiar_estado.py`** — `CambiarEstadoDocumento` (valida vía StateMachine + persiste + audit), `RegistrarSignoff` (Reviewer o FAE), `TransicionRechazada` exception.
- **`src/core/models/auditoria.py`** — agregados tipos `signoff_reviewer` y `signoff_fae` al `Literal TipoEvento` (extensión backward-compatible).
- **Tests:** 13 unit (`test_state_machine.py`) + 6 integration (`test_cambiar_estado.py`).

### Fase 4 — UI (Día 2)
- **`src/ui/components/timeline.py`** — componente timeline vertical con marca SMNYL: marcadores coloreados por tipo de evento, sección como badge, timestamps locales, fondo `bg_soft`. Cero look "Streamlit default".
- **`src/ui/pages/auditoria.py`** — pantalla dedicada con 4 métricas estadísticas (eventos totales, secciones tocadas, cambios de estado, sign-offs) + filtro por tipo + timeline completo. Botón "Volver al dashboard".
- **`src/ui/pages/dashboard.py`** — nueva card **Gobernanza**:
  - Badge prominente del estado actual (paleta diferenciada por estado).
  - Botones de transiciones disponibles desde el estado actual; **deshabilitados con tooltip explicativo** cuando la state machine bloquea.
  - Expander de sign-off Reviewer (visible en `in_review`) con checkbox de afirmación de independencia.
  - Expander de sign-off FAE (visible en `approved`) con checkbox de aceptación de riesgo.
  - Botón "Ver auditoría completa" → navega a `auditoria.py`.
- **`app.py`** — router actualizado con la nueva página `auditoria`.

### Tests / lint
- **94/94 tests pasan** en ~7s (de 75 → 94, +19 nuevos de Fase 4).
- `ruff check` limpio. `ruff format` aplicado.

---

## Decisiones técnicas clave de Fase 4

- **State machine como lógica pura del dominio**: `src/core/rules/state_machine.py` no depende de UI, BD ni LLM. Se puede llamar desde tests sin fixtures pesados.
- **Razones de bloqueo legibles, no booleanas**: el `ResultadoTransicion.razones` lleva strings que se muestran tal cual al usuario en el tooltip. No requiere traducción adicional.
- **Sign-off como audit event, no como flag**: registrar `signoff_reviewer` o `signoff_fae` como evento inmutable en el audit_trail es más auditeable que un campo booleano. La state machine lo busca con `_tiene_evento`.
- **Sign-off MVP single-user = checkbox de afirmación**: el usuario afirma su rol independiente vía checkbox + click. Cuando llegue multi-user real, esto será flujo de aprobación con notificación. Está documentado en memoria como simplificación temporal.
- **Schema-aditivo, no destructivo**: agregar tipos al Literal `TipoEvento` es backward-compatible (docs viejos cargan sin error).
- **UX defensiva**: botones de transición visibles pero deshabilitados cuando bloqueados, con tooltip que explica exactamente qué falta. No esconde la acción — informa.

---

## Progreso de sesión 7 (2026-05-06)

### Bug fix — timeline renderizado como código en pantalla de auditoría
- **Causa:** `_render_item` producía HTML con indentación (4+ espacios), que markdown interpretaba como code block antes de procesarlo como HTML.
- **Fix:** producir HTML en una sola línea concatenada con `f"..."` strings, sin newlines internos. `src/ui/components/timeline.py`.

### Feature — Omitir sección con motivo (TDD, 11 tests)
- **Modelo (aditivo):** `Completitud` Literal extendido con `"omitida"`; `Seccion.motivo_omision: str | None`; `Documento.porcentaje_resuelto` property nueva (cuenta completas + omitidas).
- **Audit:** nuevo tipo de evento `seccion_omitida` con motivo en metadata.
- **Use case `OmitirSeccion`** con 4 motivos predefinidos ("No aplica al modelo", "Información no disponible", "Pendiente para versión futura", "Otro (especificar)").
- **State machine actualizada:** `draft → in_review` ahora valida `porcentaje_resuelto == 100%`. Mensaje: "X sección(es) sin resolver. Cada una debe completarse u omitirse explícitamente con motivo."
- **UI:** botón "Omitir" junto a "Entrevistar" en cada sección; modal con dropdown de motivo + textarea opcional + descripción de la sección. Card "Resolución" en dashboard incluye conteo "X completa(s)". Card "Omitidas" agregada al grid de resumen. Filtro "Omisiones" en pantalla de auditoría. Botón "Reactivar" para volver una omitida a vacía.

### Fase 3 — DocxWriter (TDD, 18 tests nuevos)
- **Plantilla maestra editada por Alberto** en `src/docs/templates/model_development_smnyl.docx`. Cubre 45 placeholders simples + 5 loops de tabla (version_history, raw_data_sources, upstream_models, input_changes, process_changes).
- **Bug fix de plantilla:** detectados 10 loops mal escritos como `{%- tr ... %}` (Jinja whitespace control que docxtpl no soporta). Fix automático sobre el XML del .docx con backup.
- **`TableExtractor`** (`src/core/usecases/table_extractor.py`): use case que toma texto narrativo + schema → list[dict] vía Haiku. Tolerante a JSON malformado (devuelve []), maneja fences de código (```json), normaliza campos faltantes a string vacío. 7 tests.
- **`DocxWriter`** (`src/core/usecases/docx_writer.py`): renderiza la plantilla con docxtpl. Maneja secciones omitidas con marcador "Sección omitida — {motivo}". Construye `version_history` desde audit_trail (transiciones de estado). Si recibe `TableExtractor`, llena las 4 tablas tabulares; sin él, salen vacías. 8 tests.
- **`ExportarDocumento`** (`src/core/usecases/exportar_documento.py`): use case orquestador. Carga doc, renderiza, registra audit event `exportado`, devuelve `ResultadoExportacion(contenido, nombre_archivo)`. 3 tests integration.
- **UI dashboard:** card de Gobernanza ahora tiene 3 acciones — "Exportar DOCX" (con spinner + download_button), "Ver auditoría completa", y los botones de transición de estado existentes. El export auto-detecta si hay `ANTHROPIC_API_KEY` y usa Haiku para llenar tablas tabulares.

### Tests / lint
- **123/123 tests pasan** (105 → 123, +18 nuevos de Fase 3 + 11 de feature Omitir + bug fix).
- `ruff check` limpio. `ruff format` aplicado.

---

## Decisiones técnicas clave de Fase 3

- **Estrategia "plantilla manual + extracción tabular con Haiku":** la plantilla NYL editada por Alberto define la calidad estética. El writer NO genera estilos en código. Para las 4 secciones tabulares (5.1, 5.2, 5.5, 6.5) que requieren estructura, Haiku convierte texto narrativo a JSON cuando se exporta — costo aproximado $0.001 por export.
- **Manejo de placeholders fragmentados:** algunos placeholders con underscore (ej. `implementation_platform`) pueden fragmentarse en runs de Word y no reemplazarse. No es bug del writer; es la realidad de Word + docxtpl. Se diagnostica con script utilitario y se corrige editando la plantilla.
- **Pulido formal de plantilla diferido:** la plantilla actual es funcional pero no perfecta — falta `{{ nombre_modelo }}` en la celda Model Name de la tabla 1.1, `implementation_platform` no aparece, etc. Estos son issues de plantilla manual, no de código. Se corrigen en sesión de pulido formal antes de demo externa.
- **Sign-off como audit event inmutable**, no flag — más auditeable. Documentado en sesión 6.

---

## Cierre sesión 7 (tarde/noche del 2026-05-06)

### Refinamientos estéticos y bugs de DOCX
- **Bug fix (cost widget cache de Streamlit):** módulos cacheados pre-2.5 no registraban métricas; restart de Streamlit lo arregló y se hizo el widget siempre visible.
- **Bug fix (KeyError 'omitida' en interview):** dict de marcadores en `interview.py` y `entrevista.py` no tenía la key `"omitida"` después de extender el Literal `Completitud`.
- **Bug fix (timeline renderizado como código):** HTML con indentación >4 espacios → markdown lo trataba como code block. Fix: producir HTML en una sola línea.
- **Bug fix (apéndice no aparece en DOCX):** `DocxWriter` no leía ni rendereaba apéndices vinculados; ahora se inyectan al final del Subdoc de la sección de origen.
- **Subdoc + RichText:** reemplacé el cleanup que borraba asteriscos por parser markdown → Subdoc con runs `bold=True` reales. Líneas solas con `**xxx**` se detectan como subtítulos (alineación izquierda, evita justify-spread).
- **Tablas nativas:** `markdown_blocks.separar_bloques` divide el contenido en BloqueProsa / BloqueTabla. Las tablas se incrustan vía `subdoc.add_table()` con estilo `Table Grid` y font adaptable `font_size_para_tabla(n_filas, n_columnas)` con valores 10/9/8/7pt según densidad.
- **Editor de metadata:** dialog con form para 8 campos clave del modelo (nombre, ID, FAE, owner, versión, plataforma, tier, model_class). Cambios registrados como evento `metadata_actualizada` con delta exacto.

### Feature: Traducción al inglés corporativo americano
- `src/core/usecases/traductor.py` con `TraductorDocumento`. Prompt específico: U.S. corporate English, preserva markdown formatting + vocabulario actuarial (BEL, MP, ESG, IFRS) + identifiers verbatim.
- Usa Sonnet (no Opus) — costo ~$0.01-0.05 USD por export.
- **Traducción efímera:** muta el doc cargado de BD en memoria, pero NO persiste. El doc original en español queda intacto.
- Toggle UI: `_dialog_exportar_docx` con radio Español / English. El `ExportarDocumento` recibe `idioma_objetivo` y orquesta traducción + render.
- Audit event `exportado` registra el idioma en metadata.

### Fase 6 — Documentos de migración
- **`docs/MIGRATION_TO_EC2.md`** — técnico para el arquitecto. Incluye §8 nuevo: runbook paso a paso con archivos que se copian/no se copian, variables de entorno, comandos de instalación, servicio systemd, nginx HTTPS, plan de rollback, checklist post-deploy.
- **`docs/MIGRATION_GUIA_EJECUTIVA.md`** (nuevo) — ejecutivo en español aterrizado para Alberto. Sin jerga. Incluye: qué construimos, por qué migrar (y por qué no ahora), lista exacta para reunión con arquitecto, decisiones de Alberto vs TI, costo estimado mensual ($125-300 USD), riesgos y mitigaciones, glosario rápido, plan en 3 fases (~3 semanas), guion para la reunión, lo que NO debes prometer.

### Tests / lint
- **174/174 tests pasan** (de 105 al inicio de sesión, +69 nuevos en la sesión).
- Nuevos módulos: `markdown_cleanup`, `richtext_render`, `markdown_blocks`, `traductor`. Cada uno con tests TDD.
- `ruff check` limpio. `ruff format` aplicado.

---

## Lo que sigue — sesión 8 (mañana)

### 1. Validación end-to-end del DOCX con todas las mejoras de hoy
Restart Streamlit → reabrir doc real → exportar DOCX y auditar:
- **Negritas reales** (no asteriscos) en el texto.
- **Subtítulos** como "Algoritmo central" sin justify-spread raro (deben estar alineados a la izquierda, en bold).
- **Bullets** con prefijo `•`.
- **Apéndices con tabla nativa** (con bordes), no listas "Registro 1: -Producto:1.0". Font reducido si la tabla es grande.
- **Editar metadata** del modelo desde el botón nuevo en el dashboard. Reexportar y verificar que el nombre nuevo aparece en portada y archivo.
- **Excel upload** (residual Fase 2.5) en sección 4.4/5.1/5.2 → ver tabla nativa.

### 2. Validación de la traducción al inglés
- Click "Exportar DOCX" → modal con radio Español / English (US corporate).
- Elegir English → spinner "Traduciendo y generando…" (~$0.05 USD).
- Abrir el DOCX y validar: ¿inglés corporativo formal? ¿términos técnicos preservados (BEL, MP, ESG, IFRS)? ¿identifiers (model_id, file paths) verbatim? ¿formato intacto (negritas, tablas)?
- Verificar que el doc original en español NO se modificó (validar en español también).

### 3. Pulido de plantilla — placeholders rotos (residual)
Si en la validación se detectan celdas vacías o placeholders fragmentados (típicamente palabras con underscore largo), abrir plantilla en Word, borrar el placeholder roto y reescribirlo **de un tiro sin pausar** entre caracteres (Word fragmenta runs cuando pausas la escritura).

### 4. NUEVO — Redactar correo formal a Vidal (arquitecto) con mini business case
Solicitado por Alberto al cierre de sesión 7. Características esperadas:
- **Súper conciso**: 200-300 palabras máximo.
- **Solicitud formal** de provisión de instancia EC2 + RDS PostgreSQL + S3 + Cognito.
- **Mini business case**: qué resuelve, por qué AWS, costo estimado mensual, beneficios para SMNYL, riesgo de no migrar.
- Tono ejecutivo, sin jerga técnica innecesaria — el arquitecto lo entiende, pero la justificación debe ser legible para forwardear a stakeholders si requiere.
- Referencia a los dos documentos existentes (`MIGRATION_TO_EC2.md` técnico + `MIGRATION_GUIA_EJECUTIVA.md`).
- Propone reunión de 30 min para alcance.
- **Output:** archivo `docs/CORREO_VIDAL.md` listo para que Alberto copie/ajuste.

### 5. Fase 5 (post-validación)
- Microinteracciones, animaciones lottie, capturas de las 7 pantallas, demo grabada de 3 min.

---

## Bloqueos / decisiones pendientes

- **Sesión de pulido de plantilla `.docx`** en Word: diferida hasta antes de cualquier demo externa (Isabel/CFO/comité MRM).
- **Fuentes Alda Pro / Effra Pro**: opcionales — Georgia/Tahoma autorizadas oficialmente.

Plan completo aprobado: `C:\Users\alber\.claude\plans\lee-el-archivo-claude-md-http-claude-md-dapper-giraffe.md`.

---

## Progreso de sesión 8 (2026-05-07)

### Validación del MVP (estética y traducción)
- Alberto validó visualmente el DOCX exportado: negritas reales, subtítulos, bullets, tablas nativas con bordes y font adaptable. ✅
- Alberto validó la traducción ES → EN: inglés corporativo formal, términos técnicos preservados, formato intacto, doc original en español sin alterar. ✅
- **Veredicto:** MVP cerrado para piloto interno. Pulido formal de plantilla diferido hasta antes de demo externa.

### Commit y push a GitHub
- Repo `AlbertoMafud/DocuMente` (privado).
- Commit `48cb3c5` — *fases 3, 4 y 6 + features sesiones 6 y 7*. 42 archivos cambiados, +4533 / -128 líneas.
- Excluidos del repo (gitignored): `docs/CORREO_VIDAL*.md`, `docs/MIGRATION_GUIA_EJECUTIVA.md`, `docs/REUNION_*.md`. Son drafts personales que viven solo en la laptop.
- 174/174 tests pasan; ruff clean previo al commit.

### Reunión con Vidal — preparación
Vidal solicitó agenda con 4 puntos: demo + stack, volumen concurrente, clasificación de datos, integraciones requeridas.
- **`docs/CORREO_VIDAL_RESPUESTA.md`** (gitignored): respuesta formal lista para enviar, ~280 palabras, anticipa cada uno de los 4 puntos con resumen ejecutivo + propone pre-lectura de `MIGRATION_TO_EC2.md` + agenda de 30 min.
- **`docs/REUNION_VIDAL_PREP.md`** (gitignored): guía interna detallada para Alberto. Incluye:
  - Script de demo de 10 min con timing por minuto.
  - Stack técnico articulado por **decisiones**, no por listas.
  - Cifras de volumen justificadas (5-10 piloto → 30-40 pico MRM).
  - Clasificación de datos: Confidencial / Uso Interno; argumentos para Bedrock vs Anthropic directo.
  - Integraciones MVP vs eventual v2 (clara separación de alcance).
  - 10 preguntas probables de Vidal con respuestas listas.
  - Lo que NO debes prometer.
  - Cómo cerrar la reunión con próximos pasos concretos.

### Lo que sigue inmediato

1. **Enviar correo a Vidal** con la respuesta de `CORREO_VIDAL_RESPUESTA.md` y agendar.
2. **Reunión con Vidal:** llevar la app cargada con doc real, `MIGRATION_TO_EC2.md` impreso/digital, y la guía `REUNION_VIDAL_PREP.md` solo para uso interno de Alberto.
3. **Post-reunión:** arrancar Fase A (M1 — containerización con Dockerfile + docker-compose.yml). Esfuerzo: 1-2 días.
4. **Fase 5 (UX final):** post-piloto inicial. Capturas de las 7 pantallas + demo grabada de 3 min para defender el proyecto a stakeholders (Isabel, comité MRM).

---

## Cierre sesión 8

- MVP en estado de "listo para piloto interno". No hay deuda técnica bloqueante.
- Repo en GitHub privado actualizado y limpio.
- Materiales para reunión con TI/arquitecto preparados y separados (público técnico vs privado personal).
- Bloqueos: ninguno técnico. Bloqueo organizacional: depende de agenda de Vidal y decisión de Compliance sobre Bedrock vs Anthropic directo.

---

## Progreso de sesión 9 (2026-05-12)

### Feature — Flujo "Crear documento desde cero"

Se completó el segundo punto de entrada al flujo de DocuMente. Antes solo se podía mejorar un `.docx` existente; ahora también se puede arrancar con las 28 secciones vacías del template oficial NYL. Ambos flujos convergen en `onboarding → dashboard → entrevista → export`.

**Implementación (5 commits, +328 / -22 líneas de código):**

| Commit | Cambio |
|---|---|
| `2fe8612` | refactor: promover `construir_secciones_vacias()` de `src/docs/reader.py` (privada) a `src/core/template_catalog.py` (pública) |
| `f1e7879` | feat: nuevo use case `CrearDocumentoEnBlanco` en `src/core/usecases/crear_documento.py` (57 líneas, 10 tests TDD) |
| `02fb76c` | feat: pantalla `src/ui/pages/crear_nuevo.py` (81 líneas) con form de 2 campos (nombre + model_id) |
| `781c952` | feat: botón "Crear nuevo documento" en home enabled + routing + import en `app.py` |
| `7fbe3c8` | fix: conteo de secciones del template (32 → 28) en 4 lugares (docstrings + body copy + help text) |

**Calidad:**
- 182 tests pasando (172 baseline + 5 del builder público + 5 nuevos del use case). Las 7 fallas de `tests/integration/test_import_end_to_end.py` son **pre-existentes** (fixtures faltantes en worktrees), no regresiones.
- `ruff check` + `ruff format` clean.
- `mypy --strict` clean en archivos nuevos (los 11 errores pre-existentes en otros archivos no se tocaron).
- Cada commit pasó por revisión de spec compliance + revisión de code quality vía subagent-driven development.

### Documentos generados — 3 deliverables grandes

| Archivo | Líneas | Propósito | Estado |
|---|---|---|---|
| `docs/E2E_TEST_SCENARIO.md` | 2,158 | Simulación end-to-end MRM-grade del **Modelo de Pricing GMM Individual — Nuevos Negocios** (ficticio, Tier High). Cubre las 28 secciones del template (22 mandatorias completas + 3 opcionales completas + 3 omitidas), transcripts de interview, drafts MRM-grade, apéndice Excel en 4.4, tablas extraídas por Haiku en 5.1/5.2/5.5/6.5, state transitions, sign-offs Reviewer + FAE, export ES + EN, audit trail completo (~113 eventos), métricas de uso ($16 USD/documento estimado), checklist de validación (8 categorías). | En main |
| `docs/technical_architecture_for_data_architect.md` | 1,351 | Documento técnico en **inglés** para Vidal (arquitecto de datos) con las 15 secciones de arquitectura del proyecto: executive summary, layers (UI/Application/Domain/Infrastructure), data architecture (8 entidades core), tech stack, data flow, modules, storage & persistence, scalability roadmap (MVP → AWS), 8 architectural decisions, NFRs, security & access control, performance & monitoring, DR & backup, AWS infrastructure (con diagrama ASCII), API contracts. | En main |
| `docs/DOCUMENTE_GUIA_PERSONAL.md` | 397 | Guía nivel ejecutivo en **español** para Alberto: qué es DocuMente, problema que resuelve, arquitectura por capas con analogías de restaurante, stack tecnológico con "por qué" de cada elección, 8 decisiones arquitectónicas con trade-offs, **10 preguntas probables del arquitecto con respuestas listas**, estado actual y roadmap, glosario. | **Gitignored** (local-only) |

### Limpieza de repo

- Worktree `cool-wing-eca24c` desregistrado de git.
- Branch `claude/cool-wing-eca24c` borrado (mergeado a main).
- **Carpeta huérfana `.claude/worktrees/cool-wing-eca24c` quedó residual en disco** — no se pudo borrar por handle del shell del sandbox. Borrar manualmente desde Windows Explorer cuando convenga (no afecta git).
- `main` empujado a `origin/main` en GitHub privado `AlbertoMafud/DocuMente`. Commit final: `45748b4` (merge --no-ff).

### Lo que sigue inmediato (sesión 10)

1. **Alberto valida `docs/E2E_TEST_SCENARIO.md`** aplicando el checklist §7 (~60-90 min). Decisiones derivadas:
   - Si calidad simulada se siente fuerte → arrancar validación real con stakeholders directamente.
   - Si hay gaps → iterar prompts en `src/llm/prompts/` antes de mostrar a nadie (la tabla en §6 del E2E indica exactamente qué archivo tocar según el gap).
2. **Decidir si el simulado se convierte en test automatizado permanente** (opción C en §8 del E2E): 1-2 días de trabajo para mockear LLM y validar export.
3. **Reunión con Vidal** sigue siendo el path principal hacia AWS. Los dos documentos para él ya están listos en main:
   - `docs/MIGRATION_TO_EC2.md` (runbook técnico con §8 paso a paso)
   - `docs/technical_architecture_for_data_architect.md` (arquitectura completa nuevo)
4. **Post-reunión Vidal:** arrancar M1 (containerización Docker + docker-compose). 1-2 días.
5. **Fase 5** (collateral UX): capturas de pantallas, demo grabada 3 min, microinteracciones — para defender ante Isabel/Comité MRM cuando llegue ese momento.

### Bloqueos conocidos

- **Carpeta huérfana del worktree** en `.claude/worktrees/cool-wing-eca24c` (cosmético, borrar manualmente).
- **Pulido formal de plantilla `.docx`** sigue diferido hasta antes de demo externa.
- **Bedrock vs Anthropic API directa**: pendiente decisión de Compliance.
- **`ANTHROPIC_API_KEY`** en `.env` — sigue siendo precondición para usar entrevista/drafting/export EN.

---

## Cierre sesión 9

- Feature "crear desde cero" en producción local. Dos puertas de entrada al flujo (importar + crear) cubren los dos casos de uso reales: documentar modelo existente sin documentación previa, vs documentar modelo nuevo desde su concepción.
- Repo GitHub sincronizado en `45748b4`. Working tree limpio.
- 3 documentos de soporte generados que cubren las tres audiencias clave: tú (guía personal en español), Vidal (arquitectura técnica en inglés), validación interna (simulación E2E MRM-grade con checklist).
- Bloqueos: ninguno técnico. Ahora todo está en manos de la validación y de las decisiones organizacionales (Compliance, Vidal).

**Handoff a sesión 10:** Alberto tiene comentarios acumulados que va a traer a la próxima sesión. Leer este `status.md` + el `MEMORY.md` + el `next_session_handoff.md` antes de arrancar trabajo.

---

## Progreso de sesión 10 (2026-05-12)

### Contexto
Alberto trajo 6 comentarios resultado de pláticas preliminares con potenciales usuarios. Los puntos 1-5 son mejoras concretas al motor actual; el punto 6 es una solicitud distinta — un módulo especializado para Modelos Actuariales (Prophet) que requiere arquitectura propia. Alcance acordado: implementación completa de los 5 puntos + delineamiento básico de Prophet para sesión dedicada.

Plan aprobado: `C:\Users\alber\.claude\plans\dime-en-qu-nos-rustling-stardust.md`.

### Implementación de los 5 puntos

**Punto 2 — Traducción EN sin fugas en español ✅**
- Nuevo módulo `src/core/usecases/strings_localizados.py` con diccionario `STRINGS_UI` (ES/EN) + función `t(key, idioma)` para todas las cadenas hardcodeadas del writer y los 4 motivos predefinidos de omisión.
- `docx_writer.py` ahora recibe `idioma` como parámetro y resuelve marcadores ("Sección omitida — ", "[Pendiente — sin contenido capturado]", "[Sección no presente en el catálogo]") vía `t()`.
- `traductor.py` ya no salta secciones omitidas: traduce `motivo_omision` con swap directo (sin LLM) si es predefinido, o vía LLM si es texto libre. También maneja la forma híbrida `"<predefinido> — <comentario>"`.
- `exportar_documento.py` propaga `idioma_objetivo` al writer.
- **Tests:** +10 (test_strings_localizados.py) + 4 nuevos en test_traductor.py + 2 nuevos en test_docx_writer.py.

**Punto 3 — Botón "Volver" desde Importar + auditoría de navegación ✅**
- Componente reusable `src/ui/components/back_button.py` con factory de `key` automática.
- Agregado a `importar.py` (que no tenía) y `onboarding.py` (que tampoco). Las demás pantallas ya tenían su patrón propio funcional.
- **Tests:** +5 (test_back_button.py con mocks de `st.button` y `st.session_state`).

**Punto 4 — Apéndices reorganizados + cross-refs + traducción ✅**
- Reescritura del flujo en `docx_writer.py`: los apéndices YA NO se inyectan dentro del Subdoc de cada sección. Se acumulan y al final se agrega una sección dedicada **"Apéndices"** (o "Appendix" en EN) con headings nivel 1+2 y numeración `A.1`, `A.2`, ….
- Implementación: después del `tpl.render()` de docxtpl, se reabre el .docx con `python-docx` y se agrega la sección con `_agregar_seccion_apendices`. Las tablas markdown se renderean como tablas nativas con bordes y font adaptable (reusando `_agregar_tabla_documento` análogo al de Subdoc).
- Pre-procesamiento del body: regex `\(ver Apéndice|see Appendix:\s*<titulo>\)` → `(ver Apéndice A.N)` / `(see Appendix A.N)`, matching por título de apéndice. Fallback case-insensitive. Si no hay match, deja la referencia literal.
- **Tests:** +5 nuevos en test_docx_writer.py (sección dedicada, cross-refs, EN, sin apéndices, referencia inexistente, tabla en apéndice).

**Punto 1 — Multi-archivo (PDF, XLSX, TXT, DOCX como contexto) ✅**
- Nuevo modelo `FuenteContexto` (`src/core/models/fuente_contexto.py`) — backward-compatible (`fuentes_contexto: list[FuenteContexto] = []` en `Documento`).
- Paquete nuevo `src/docs/readers/` con:
  - `pdf_reader.py` (usa `pypdf 6.10.2`, agregado a `pyproject.toml`).
  - `xlsx_reader.py` (usa `openpyxl`, ahora en deps explícitas; truncado a 200 filas × 20 cols por hoja).
  - `txt_reader.py` (stdlib, fallback UTF-8 → UTF-8-sig → latin-1).
  - `docx_reader_simple.py` (DOCX como texto plano, NO compite con `DocxReader` ancla).
  - Factory `extraer_texto(archivo, nombre) -> (tipo, str)` con detección por extensión.
- Use case nuevo `SugerenciasMultiFuente` en `src/core/usecases/sugerencias_multifuente.py` — solo opera sobre secciones con `completitud=="vacia"`, llama a Sonnet con `SUGERENCIAS_MULTIFUENTE_SYSTEM` (prohíbe inventar, exige citar fuente al final), marca el contenido con `[Borrador automático — revisar]` y `completitud="parcial"`. Tolerante a errores LLM.
- `ImportarDocumento` y `CrearDocumentoEnBlanco` aceptan `fuentes_adicionales` opcional. Si hay LLM configurado + fuentes, disparan `SugerenciasMultiFuente`.
- UI: `importar.py` ahora muestra **dos secciones** (ancla + fuentes), `crear_nuevo.py` agrega uploader de fuentes opcional debajo del form. Ambos validan tipos por extensión y muestran lista de archivos antes de procesar. Spinner adaptable según cantidad de fuentes.
- **Tests:** +15 (test_readers_multifuente.py para 4 readers + factory) + +7 (test_sugerencias_multifuente.py).

**Punto 5 — Brief inicial opcional (10 preguntas de alto valor) ✅**
- Use case `AplicarBrief` en `src/core/usecases/aplicar_brief.py` con `PREGUNTAS_BRIEF` (10 preguntas open-ended con `seccion_id` destino verificado contra el catálogo).
  - Mapeo Q→sección: 1→1.3, 2→2.1, 3→2.2, 4→2.3, 5→4.2, 6→4.3, 7→4.4, 8→5.1, 9→7.4, 10→9.
- Prompt en `src/llm/prompts/brief_a_seccion.py` — "no inventar", proporcional al input, sin headings, sin meta-comentarios.
- Pantalla `src/ui/pages/brief_inicial.py` con 10 textareas + tip prominente + 2 botones ("Generar y continuar" / "Saltar").
- Routing en `app.py` actualizado: nueva ruta `brief_inicial`. En `onboarding.py`, si el doc es nuevo (todas secciones vacías), redirige a `brief_inicial`; si viene de importar (ya tiene contenido), va directo a `dashboard`.
- Backward-compat: el brief NO sobrescribe contenido existente (validado por test).
- **Tests:** +7 en test_aplicar_brief.py (10 preguntas presentes, mapeo válido, no pisa contenido, idioma EN usa `[Draft — review]`, etc.).

### Resumen de cambios

**Nuevos archivos (13):**
- `src/core/models/fuente_contexto.py`
- `src/core/usecases/strings_localizados.py`
- `src/core/usecases/sugerencias_multifuente.py`
- `src/core/usecases/aplicar_brief.py`
- `src/docs/readers/{__init__.py, pdf_reader.py, xlsx_reader.py, txt_reader.py, docx_reader_simple.py}`
- `src/llm/prompts/{sugerencias_multifuente.py, brief_a_seccion.py}`
- `src/ui/components/back_button.py`
- `src/ui/pages/brief_inicial.py`

**Archivos modificados (12):**
- `src/core/models/{__init__.py, documento.py}` — agregar `FuenteContexto` y campo `fuentes_contexto` opcional.
- `src/core/usecases/{docx_writer.py, traductor.py, exportar_documento.py, importar_documento.py, crear_documento.py}` — flujo apéndices reescrito, idioma propagado, multi-archivo orquestado.
- `src/ui/pages/{importar.py, crear_nuevo.py, onboarding.py}` — multi-archivo en UI, routing a brief_inicial, back_button.
- `src/ui/components/__init__.py` — export del back_button.
- `app.py` — nueva ruta brief_inicial.
- `pyproject.toml` — agregar `pypdf>=4.3.0`, `openpyxl>=3.1.0` a deps explícitas.

**Nuevos tests (5 archivos, +54 tests):**
- `test_strings_localizados.py` (10), `test_back_button.py` (5), `test_readers_multifuente.py` (8), `test_sugerencias_multifuente.py` (7), `test_aplicar_brief.py` (7).
- Más extensiones a `test_traductor.py` (+4) y `test_docx_writer.py` (+13).

### Calidad de código
- **pytest:** 236/236 pasan (~25s).
- **ruff check:** clean en src/ y tests/.
- **ruff format:** aplicado (6 archivos reformateados durante el ciclo).
- **mypy:** sin errores nuevos en archivos modificados. Los 5 errores reportados son pre-existentes (`storage/db.py`, `cambiar_estado.py`, `llm/client.py`, `interview_engine.py`, `drafter.py`).

### Decisiones de diseño tomadas (todas registradas en el plan aprobado)
1. Multi-archivo: docx ancla + N fuentes como contexto; no compiten por el rol estructural.
2. Multi-archivo también en flujo "Crear desde cero" (simetría).
3. Sección "Apéndices" se construye solo en render, NO se agrega al `template_catalog` (TEMPLATE_MODEL_DEVELOPMENT sigue siendo tupla congelada de 28).
4. Numeración A.1, A.2 por orden de creación del apéndice (no por orden de mención en body).
5. Brief inicial es OPCIONAL, preset fijo de 10 preguntas (no varía por tier).
6. "Apéndice" → "Appendix" se resuelve dentro del punto 4 (cohesión con el rework del writer), no del punto 2.

### Módulo Prophet — delineamiento básico para sesión propia

**Approach decidido: C híbrido por fases.**

**Fase Prophet-0 (1 semana, sesión dedicada próxima):**
- Importar el Excel `Registro Modelos_envioAlberto.xlsx` directamente (usando openpyxl + Haiku con schema).
- Generar borrador de ficha técnica con tablas pobladas (sin entrevista).
- Segundo template `prophet_model_doc_smnyl.docx` con placeholders + 4 table loops (runs, variables, inputs, skills_matrix).
- Selector de template en `crear_nuevo.py`: "MRM (Model Development)" vs "Ficha Prophet (Modelos Actuariales)".
- Demo con Carmona, Cynthia, Magallanes — feedback de 1 hora.

**Fase Prophet-1 (3-4 semanas, condicional a feedback positivo):**
- Módulo registry-based completo con entidades Pydantic relacionales (`ModeloProphet`, `Run`, `Variable`, `Input`, `Dependencia`, `SkillAssessment`).
- Schema SQLite con relaciones.
- UI con formularios + autocompletado de cross-refs.
- Vista de grafo navegable (opcional).
- Audit trail por entidad.

**4 preguntas abiertas para resolver al inicio de la sesión Prophet:**
1. ¿Unidad de documentación = un modelo Prophet por archivo, o UN registro integral para toda Rentabilidad?
2. ¿Dueños (Carmona/Cynthia/Magallanes) usan la app directamente, o alguien intermedio captura por ellos?
3. ¿Qué prioridad organizacional tiene vs reunión Vidal + piloto MRM? ¿Hay deadline impuesto por MA?
4. ¿Matriz de habilidades es parte del mismo entregable de documentación o es side-project de talento?

### Lo que sigue inmediato (sesión 11)

1. **Validación visual de Alberto** de las 5 mejoras en la app local (~30 min):
   - Subir docx + 2-3 fuentes adicionales → ver borradores automáticos en secciones vacías + card "Fuentes de contexto" en dashboard.
   - Exportar a EN → verificar que ya no aparece "Sección omitida", "Pendiente", "Apéndice" en español.
   - Click "Volver" desde Importar y Onboarding → verificar que regresa a home.
   - Doc con apéndices → exportar y verificar sección "Apéndices" al final con A.1, A.2 + cross-refs reemplazados.
   - Crear documento nuevo → llegar a brief_inicial → llenar 5-6 preguntas → ver borradores en dashboard.
2. **Si todo OK:** commit + push a `origin/main` (siete features atómicos sugeridos en el orden del plan).
3. **Reunión con Vidal** sigue siendo el path hacia AWS — materiales de S8/S9 listos.
4. **Sesión propia de Prophet (Fase 0).**

### Bloqueos conocidos

- **`ANTHROPIC_API_KEY`** sigue siendo precondición para usar sugerencias multi-fuente, brief inicial, traducción EN, drafter y extracción tabular. Sin key, esos flujos degradan elegantemente: el doc se crea/importa pero sin sugerencias automáticas.
- **Carpeta huérfana del worktree** en `.claude/worktrees/cool-wing-eca24c` sigue cosmética (no afecta git).
- **Pulido formal de plantilla `.docx`** sigue diferido para antes de demo externa.
- **Bedrock vs Anthropic API directa** sigue pendiente de Compliance.

---

## Cierre sesión 10

- **5/5 mejoras de feedback implementadas** sin regresiones — 236 tests pasando, lint clean.
- **Multi-archivo** convierte DocuMente de "1 docx → mejora" a "1 docx ancla + N fuentes → sugerencias automáticas en secciones vacías", lo cual es exactamente lo que pidieron los usuarios potenciales.
- **Traducción EN** ya queda íntegra: no más fugas en español en exports.
- **Apéndices** quedan en sección dedicada al final con numeración A.N, cross-refs reemplazados, y traducción a "Appendix" en EN.
- **Brief inicial** de 10 preguntas reduce drásticamente la fricción del onboarding: el usuario llega al dashboard con hasta 6 secciones ya con borrador.
- **Navegación consistente** con back_button compartido.
- **Prophet** queda con plan básico listo + 4 preguntas abiertas para su sesión propia. Esa sesión es independiente de la reunión con Vidal y del piloto MRM en curso.

### Bloqueo al lanzar Streamlit detectado al cierre

Al intentar `streamlit run app.py` se reveló que la variable de entorno `ANTHROPIC_API_KEY` está exportada **vacía** en el OS env de Windows (presente, len=0). Pydantic-settings prefiere OS env sobre `.env`, así que la cadena vacía sobrescribe la key real (válida, 108 chars) del archivo `.env`. La pantalla de entrevista crasheó al construir `AnthropicClient`.

**Solución temporal usada:** lanzar con `unset ANTHROPIC_API_KEY` antes de `streamlit run` en bash. La app boota OK pero la app crasheó por un segundo motivo (exit code 4/107 sin trace claro — posible conflicto de puerto con instancia previa de Streamlit zombie en 8501).

**Fix permanente a aplicar en sesión 11 (1 min):** desde una PowerShell normal del usuario, ejecutar `[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $null, "User")` y reiniciar terminal. Eso elimina la variable vacía a nivel usuario. Después relanzar `streamlit run app.py` debería funcionar limpio.

**Validación visual de las 5 mejoras quedó pendiente.** El checklist está en `pending_validation_items.md`.

**Handoff a sesión 11:** dos opciones de scope (no excluyentes):
1. **Quick win:** resolver fix de env var → validación visual local de las 5 mejoras (~30 min) → commit + push.
2. **Foco Prophet:** sesión dedicada al módulo Prophet Fase 0. Contexto completo en `prophet_module_context.md` en el folder de memoria. Las 4 preguntas abiertas se resuelven al inicio.

Alberto puede hacer (1) primero en una sesión corta y (2) en una sesión dedicada de 2-3 horas. O combinarlas.

---

## Progreso de sesión 11 (2026-05-14)

### Módulo Prophet — Fase 0 implementada completa

Se ejecutó el plan `docs/superpowers/plans/2026-05-14-prophet-fase0.md` vía Subagent-Driven Development (13 tareas, ~2-3 horas de trabajo, Haiku/Sonnet para subagentes mecánicos, Sonnet para revisores).

**Alberto verificó la app corriendo en `localhost:8502` con los tres botones en home (Importar, Crear, Iniciar Ficha Prophet).** Confirmó que todo está OK visualmente. Decisión de push a GitHub diferida a próxima sesión.

#### Nuevos archivos (15)

| Archivo | Propósito |
|---|---|
| `src/core/template_catalog_prophet.py` | Catálogo de 12 secciones Prophet, independiente del MRM |
| `src/llm/prompts/extraer_seccion_prophet.py` | Prompt Haiku: no inventar datos, mapeo best-effort, JSON puro |
| `src/core/usecases/detectar_modelos_prophet.py` | Lee .xlsx crudo (openpyxl) + detecta hoja catálogo + lista modelos |
| `src/core/usecases/importar_registro_prophet.py` | Import completo: openpyxl + Haiku → `Documento(tipo="prophet")` persistido |
| `src/core/usecases/docx_writer_prophet.py` | Writer Prophet independiente del MRM; `render(doc) -> bytes` |
| `src/ui/pages/crear_prophet.py` | UI: upload xlsx → selectbox → importar → navega a dashboard |
| `src/ui/pages/editar_seccion_prophet.py` | Editor de sección Prophet: tabla (st.data_editor), texto, campos |
| `src/docs/templates/prophet_model_doc_smnyl.docx` | Template Word minimal con placeholders de texto (Fase 0) |
| `docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx` | Template Excel para MA con 4 hojas y ejemplo SMNYL |
| `docs/Modulo Prophet MA/Guia_Llenado_Registro.md` | Guía para usuarios MA: hojas, columnas, niveles de skill |
| `tests/unit/test_template_catalog_prophet.py` | 9 tests del catálogo |
| `tests/unit/test_detectar_modelos_prophet.py` | 5 tests de detección de modelos |
| `tests/unit/test_importar_registro_prophet.py` | 5 tests de import (fixtures con xlsx real, DB aislada) |
| `tests/unit/test_docx_writer_prophet.py` | 5 tests del writer Prophet |
| `tests/unit/test_editar_seccion_prophet.py` | 3 tests de persistencia de edición |

#### Archivos modificados (4)

| Archivo | Cambio |
|---|---|
| `src/core/models/documento.py` | `TipoDocumento` extendido: `Literal["model_development", "prophet"]` |
| `src/core/usecases/__init__.py` | Exports de los 3 nuevos use cases Prophet |
| `app.py` | Tercer botón "Iniciar Ficha Prophet" en home + 2 rutas nuevas |
| `src/ui/pages/dashboard.py` | Botón "Exportar Ficha Prophet" en card Gobernanza cuando `tipo=="prophet"` |

#### Decisiones de implementación clave

- **`EventoAuditoria.tipo`:** usar `"seccion_editada"` (no `"seccion_actualizada"` — ese valor no existe en el Literal).
- **`DATABASE_URL`** (no `DOCUMENTE_DB_PATH`): variable de entorno que controla la BD en `src/storage/db.py`.
- **`repo.obtener(UUID(doc_id))`** (no `.obtener_por_str()`): la firma correcta del repositorio.
- **Template Word minimal:** placeholder de texto puro (sin loops docxtpl) por ahora; el template SMNYL completo con loops va antes de la demo con MA.
- **Heurística + LLM fallback en detección:** `DetectarModelosProphet` usa heurística de columnas si Haiku no está disponible.
- **`EventoAuditoria.metadata` es `dict[str, str]`:** valores int se convierten explícitamente a str.

#### Calidad

- **263/263 tests pasan** (de 236 baseline, +27 nuevos).
- `ruff check` y `ruff format` clean.
- `mypy` sin errores nuevos en archivos modificados.
- App arranca correctamente: `python -m streamlit run app.py` en `localhost:8502`.

---

## Progreso de sesión 12 (2026-05-18)

### Push a GitHub ✅
- Se hizo commit + push de todo lo pendiente (S10 + S11 + limpieza).
- Repo en `8d64520`. Working tree limpio.
- `.gitignore` actualizado: agrega `.superpowers/` y `docs/Comentarios/`.
- Archivos basura `=3.1.0` y `=4.3.0` (pip artifacts) eliminados.

### Reunión con Vidal (arquitecto de datos) ✅
- Se explicó la estrategia de migración a Bedrock: swap de adaptador `BedrockClient`, IAM role en EC2, sin cambios a lógica de negocio. 1-2 días de trabajo.
- Se compartió el repo: invitar a Vidal como colaborador Read en `github.com/AlbertoMafud/DocuMente → Settings → Collaborators`.
- Vidal tiene acceso al runbook técnico en `docs/MIGRATION_TO_EC2.md` y arquitectura en `docs/technical_architecture_for_data_architect.md`.

### Fixes locales ✅
- **`ANTHROPIC_API_KEY` vacía en OS env:** eliminada permanentemente con `[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $null, "User")`. Fix aplicado y verificado.
- **Anthropic SDK desactualizado:** actualizado de `0.40.0` → `0.102.0`. El parámetro `thinking` requería >=0.50.0 aprox.
- App corriendo localmente sin errores después de ambos fixes.

### ⚠️ Pendiente técnico detectado
- La versión de `anthropic` en `pyproject.toml` no está fijada con lower bound adecuado. En EC2 podría instalarse una versión vieja y reproducir el error de `thinking`. **Fijar en próxima sesión.**

---

## Lo que sigue — sesión 13

### Prioridad 1: Fijar versión de anthropic en pyproject.toml
- Cambiar a `anthropic>=0.50.0` (o la versión mínima que soporta `thinking`).
- Commitear y pushear.
- **Crítico para EC2:** si Vidal instala con la versión del pyproject.toml actual, tendrá el mismo error.

### Prioridad 2: Template DOCX Prophet completo (antes de demo)
- Archivo actual `src/docs/templates/prophet_model_doc_smnyl.docx` es minimal — solo texto plano.
- Necesita: diseño SMNYL + 4 loops docxtpl (`runs`, `variables_criticas`, `inputs`, `skills_matrix`).
- Hacerlo en Word o programáticamente con python-docx.

### Prioridad 3: Demo con MA
- Carmona, Cynthia Flores, Juan Carlos Magallanes.
- Llevar: app local + `Registro Modelos_envioAlberto.xlsx` + guía de llenado.

### Prioridad 4: Validación visual S10
- Checklist en `pending_validation_items.md` (aún sin completar).

### Pendientes menores
- Borrar carpeta huérfana `.claude/worktrees/cool-wing-eca24c` (cosmético, no afecta git).

### Bloqueos conocidos

- **Template Prophet minimal** — funcional pero sin diseño SMNYL ni loops de tabla.
- **Prophet Fase 1** — NO arrancar sin feedback positivo de la demo con MA.
- **Pulido formal de plantilla MRM** — diferido hasta antes de demo externa.
- **EC2 con Vidal** — en progreso; Vidal tiene el repo y el runbook.

---

## Progreso de sesión 13 (2026-05-19)

### Contexto

Alberto trajo 12 comentarios acumulados de pláticas con usuarios reales (Inversiones, MA, Riesgos, testers en EC2). Durante la sesión sumó 2 ítems más:
- **#13:** archivado/historial de docs en home (con tiempo se llena).
- **#14:** changelog técnico para Vidal + estrategia de branching (`main` congelada hasta que Vidal valide).

Plan de remediación completo escrito y aprobado: `C:\Users\alber\.claude\plans\ya-tengo-varios-comentarios-hidden-grove.md` (14 ítems en 4 fases S13 → S16+).

### Decisiones clave del plan (confirmadas por Alberto)

| Decisión | Resolución |
|---|---|
| Estructura | Plan integral por fases S13→S16 |
| Frontend (#5) | Auditoría + plan dedicado para migración Next.js + shadcn/cult-ui (Streamlit no escala visualmente) |
| Cognito (#8) | Mecánica a confirmar con Vidal; plan describe 2 ramas (ALB-header vs JWT-middleware) + password-gate de emergencia |
| Prophet (#4) | Unidad = una ficha por modelo; usuarios capturan directo; matriz integrada en ficha |
| Branching | `main` congelada en `51d845e`; todo S13 vive en `feat/remediacion-s13-s16` |

### Fase A implementada (5 de 6 sub-tareas)

**A.1.b — Password-gate de emergencia ✅**
- Nuevo `src/ui/components/auth_gate.py`. Lee `DOCUMENTE_GATE_PASSWORD` del env; si está set, pide password antes del router. Si está unset/vacío → gate desactivado (modo dev).
- Banner pequeño en header indica modo activo. 11 tests.

**A.2 — Onboarding nunca silenciosamente se pierde ✅**
- Reemplazo de `contextlib.suppress(Exception)` por `try/except` con logging explícito en `SugerenciasMultiFuente`, `AplicarBrief`, `CrearDocumentoEnBlanco`, `ImportarDocumento`.
- Nuevos dataclasses `ResultadoSugerencias`, `ResultadoBrief`, `ResultadoCrearDocumento` con conteos + errores + advertencias.
- `crear_nuevo.py` e `importar.py` validan que `AnthropicClient()` se construyó OK y muestran warning prominente si no.
- `brief_inicial.py` ya NO redirige silencioso si LLM falla: muestra opciones "Reintentar" / "Continuar sin borradores", preserva respuestas en session_state.
- Nuevo componente `onboarding_banner.py` que se renderea en el dashboard tras navegar de onboarding/importar/brief; consume el resultado del session_state (solo se ve una vez). Conteo total = sugerencias multifuente + brief. Lista advertencias en expander.
- 14 tests nuevos (sugerencias error path, brief error path, banner render, crear sin LLM, etc.).

**A.3 — Idioma normaliza ES/EN + opción bilingüe ✅**
- `traductor.py` ahora soporta 5 modos: `es` y `en` (legacy preservados sin cambios) + `es_normalize`, `en_normalize`, `bilingue` (nuevos).
- Detector de idioma por sección con Haiku (tarea `extraction`, ~1 prompt por bloque) + fallback a "mixed" si crashea (fuerza traducción para no ocultar contenido).
- Nuevo `src/llm/prompts/traduccion.py` con prompts en EN y ES + prompt de detección.
- `exportar_documento.py` propaga los 5 modos al writer; nombre del archivo y metadata de audit reflejan `modo_idioma` + `idioma_escritura`.
- UI `_dialog_exportar_docx` ahora tiene radio con 3 opciones + caption explicando costo y comportamiento de cada una.
- 7 tests nuevos.

**A.4 — PDF como ancla en "Mejorar documento" ✅**
- Nuevo `src/docs/readers/anchor_reader.py` factory que despacha .docx → `DocxReader` legacy; .pdf → `PdfAnchorReader` nuevo.
- `PdfAnchorReader` extrae texto plano con pypdf, recorre línea por línea con heurística: numeración tipo "4.4 ", todo-mayúsculas, title-case (≤10 palabras). Usa la misma `_coincide_con_catalogo()` del DocxReader.
- Si no detecta ninguna sección del catálogo NYL → guarda todo el PDF como `FuenteContexto` para que `SugerenciasMultiFuente` lo procese.
- `importar.py` UI acepta `.docx` o `.pdf`; muestra `st.info` aclarando que la extracción PDF es menos precisa.
- 12 tests nuevos.

**A.5 — Archivado, papelera y job de purge ✅**
- Modelo `Documento` extendido con `archivado: bool`, `en_papelera: bool`, `archivado_en: datetime | None`. Propiedad derivada `visibilidad` (`activo` / `archivado` / `papelera`).
- `EventoAuditoria.tipo` extendido con 6 nuevos tipos (backward-compatible): `archivado`, `desarchivado`, `enviado_a_papelera`, `restaurado_de_papelera`, `eliminado_permanente`, `purgado_automatico`.
- `db.py`: columnas nuevas + función `_aplicar_migraciones_aditivas(engine)` que corre al boot y agrega columnas faltantes con `ALTER TABLE` idempotente (sin migration script externo). Idempotente porque chequea con `inspect(engine)` antes de aplicar.
- `repositories.py`: `listar_por_usuario` filtra activos por default; flags `incluir_archivados=True` y `solo_papelera=True`. Nuevos métodos `listar_papelera_global` (admin) y `listar_papelera_expirada` (job).
- Use case nuevo `src/core/usecases/archivar_documento.py` con `ArchivarDocumento` (5 acciones: archivar/desarchivar/enviar_a_papelera/restaurar_de_papelera/eliminar_permanente) + función `purgar_papelera_expirada()`. `eliminar_permanente` requiere flag `es_admin=True` o levanta `PermissionError`.
- `app.py`: job de purga corre una vez por sesión de Streamlit al boot. Home reorganizada en 3 tabs (Activos / Archivados / Papelera) con acciones contextuales por tab.
- 11 tests nuevos (use case + job de purga + repositorio con BD efímera en tmp_path).

**Gotcha técnico SQLAlchemy + Python 3.14:** `Mapped[datetime | None]` y `Mapped[Optional[datetime]]` ambos fallan en ORM scan (`TypeError: descriptor '__getitem__' requires 'typing.Union' but received 'tuple'`). Workaround: usar la forma `Column` clásica sin `Mapped[...]` para columnas nullable. Documentado en `db.py`.

### A.1.c — bloqueado pendiente Vidal

- A.1.a (reunión 30 min con Vidal) sigue pendiente. Necesita confirmar:
  - ¿ALB hace OIDC con Cognito y forwardea `X-Amzn-Oidc-Identity` / `X-Amzn-Oidc-Data`?
  - ¿O Cognito-Hosted-UI redirige y la app debe leer JWT/cookie?
  - ¿Qué grupos Cognito habrá para definir roles `user` vs `admin`?
- Mientras tanto, la mitigación A.1.b (password-gate) protege el deploy en EC2.
- A.1.d (roles admin) queda como follow-up post A.1.c.

### Changelog técnico para Vidal

- Nuevo `docs/Migracion EC2/CHANGELOG_TECNICO_VIDAL.md` (carpeta dedicada). Cubre las 11 secciones del plan: resumen ejecutivo, decisiones que afectan deploy, nuevas dependencias, env vars nuevas, cómo se llama al LLM (sección clave para decisión Bedrock vs Anthropic), schema/migraciones aditivas, estructura nueva, archivos sensibles, checklist deploy, riesgos, Q&A esperado.
- Anexo S13 al final con resumen de los 5 sub-tareas implementadas, tabla de comportamiento que cambió, y "siguientes pasos para Vidal".

### Commit + push

- Commit `c15dba7` (37 archivos cambiados, +2902/-286). Mensaje detalla las 5 sub-tareas + lo bloqueado + tests.
- Push: rama local `claude/sweet-galileo-e2550b` (del worktree) → rama remota `feat/remediacion-s13-s16` en GitHub.
- **PR NO abierta todavía**. Se abre cuando Vidal confirme A.1.c.

### Calidad

- **pytest: 307/307 passing** (de 263 baseline → +44 nuevos). Los 7 fallos en `tests/integration/test_import_end_to_end.py` siguen siendo pre-existentes (fixtures SMNYL no copiadas al worktree).
- `ruff check` clean en `src/`, `tests/`, `app.py`.
- `ruff format` aplicado.

### Validación visual quedó pendiente

Alberto validó la app corriendo en `localhost:8502` durante la sesión. Los flujos no se ejercieron de extremo a extremo todavía:
- Subir docx + fuentes en "Crear nuevo" → ver banner de prellenado.
- Subir PDF en "Mejorar documento" → validar detección de headings.
- Archivar y restaurar docs desde home.
- Exportar DOCX con cada uno de los 3 modos de idioma.
- Activar `DOCUMENTE_GATE_PASSWORD` y validar password-gate.

---

## Lo que sigue — sesión 14

### Path crítico inmediato

1. **Compartir con Vidal el changelog** (`docs/Migracion EC2/CHANGELOG_TECNICO_VIDAL.md`) y agendar 30 min para A.1.a.
2. **Cerrar A.1.c** con la decisión de Vidal:
   - Si ALB-header: implementar `obtener_user_id_actual()` que lee `st.context.headers`, propagar `user_id` a use cases, defensa en profundidad en el repo.
   - Si JWT/middleware: agregar `python-jose` (o equivalente), middleware que valida y extrae sub claim, mismo wiring.
3. **A.1.d roles admin**: implementar lectura del grupo Cognito (header `X-Amzn-Oidc-Groups` o claim del JWT) + flag `es_admin` propagado a `eliminar_permanente`.

### Fase B (Sprint S14): Contenido inteligente

Arranca cuando A.1 esté cerrada. 4 sub-tareas:

- **B.1 — Análisis profundo del ancla con reestructuración (#2).** Nuevo `StructureRealigner` que detecta cuando un ancla no sigue el template NYL (cobertura < 50%) y dispara Sonnet para mapear fragmentos del ancla a las 28 secciones, marcando cada uno como `[Re-estructurado desde ancla — revisar]`. Resuelve "el output es casi idéntico al ancla".
- **B.2 — DocumentPolisher (revisión de coherencia narrativa) (#7).** Toggle opt-in en el modal de exportar ("Revisar coherencia con IA antes de exportar ~$0.02 USD"). Pasa el documento completo (con prompt caching) a Claude para detectar contradicciones cross-seccionales, referencias rotas y redacción dissonante. Devuelve sugerencias para aceptar/rechazar individualmente.
- **B.3 — Apéndices en todas las secciones + Excel multi-hoja + guía formato (#3).** Quitar el whitelist hardcoded en `entrevista.py:205`. `tabla_reader.py` itera `wb.sheetnames` y crea un apéndice por hoja con título `"{archivo} — {hoja}"`. Documentar 3 reglas básicas de formato Excel en una guía pública.
- **B.4 — Editor inline desde vista previa (#12).** Crear `src/ui/pages/editar_seccion_mrm.py` espejo del Prophet existente, con tipos de editor según `tipo_contenido` del catálogo (texto/lista/campos). Botón "✏️ Editar inline" en cada sección de `vista_previa.py`.

### Fase C (Sprint S15): Apéndices avanzados + Versionado

- **C.1 — Apéndices PDF + fórmulas matemáticas (#9).** PDF como apéndice se renderea a imagen embebida (cada página = PNG vía `pdf2image` o `PyMuPDF`). Fórmulas LaTeX → OMML con `pylatexenc` + XSLT (fallback a PNG con matplotlib si falla). Nuevo campo `formulas_inline` en `Seccion`.
- **C.2 — Versionado de documentos (#10).** Tabla nueva `versiones` con snapshot JSON + hash. Cada export crea v+1 opcionalmente. DocxWriter incrusta metadata identificadora en `core_properties` del docx. Al re-importar, app reconoce versión previa y ofrece "crear v{N+1}" o "documento nuevo". Vista de diff sección-por-sección.

### Fase D (Sprint S16+): Prophet + Frontend

- **D.1 — Prophet correctivos (#4).** Plantilla SMNYL completa con 4 loops docxtpl + botón "Exportar Ficha Prophet" en dashboard (lógica ya existe en `docx_writer_prophet.py`). UX self-service para MA. Demo controlada con Carmona/Cynthia/Magallanes con feedback estructurado. **NO arrancar Prophet Fase 1 sin demo positiva.**
- **D.2 — Frontend audit + plan migración Next.js (#5).** Capturas de las 11 pantallas. Ejecutar skill `design:design-critique` por pantalla. `design:accessibility-review` WCAG 2.1 AA. `design:design-system` para tokens portables. **Plan dedicado** de migración a FastAPI backend + Next.js + shadcn/cult-ui frontend (~5 semanas de ejecución). Decisión de migrar real se toma con datos en mano.

### Pendientes menores

- Borrar carpeta huérfana `.claude/worktrees/cool-wing-eca24c` (cosmético).
- Fijar `anthropic>=0.50.0` en `pyproject.toml` (heredado de S12, sigue pendiente).
- Template DOCX Prophet completo (sigue pendiente de S11).
- Validación visual S10 (checklist en `pending_validation_items.md`).
- Validación visual S13 (5 flujos descritos arriba).

### Reglas de oro vigentes

- `main` queda en `51d845e` — no merge hasta que Vidal valide deploy.
- Todo S13/S14/S15/S16 vive en `feat/remediacion-s13-s16` con sub-ramas por fase.
- Changelog técnico se actualiza al cerrar cada fase — sin update, no merge.
- TDD obligatorio; baseline post-S13 es 386+ tests passing.
- Schema migrations SOLO aditivas, idempotentes al boot.

---

## Progreso de sesión 13 (continuación maratón — 2026-05-19)

**Tras commit `c15dba7` (Fase A), arrancamos Fase B, C, D.2 y fix de breadcrumb en una sola sesión continua. Toda la lógica con TDD, ruff clean, 0 regresiones.**

### Fase B — Contenido inteligente ✅ (4 sub-tareas)

**B.1 — StructureRealigner del ancla (#2)**
- Nuevo `src/core/usecases/structure_realigner.py` + prompt en `src/llm/prompts/structure_realign.py`.
- Cuando la `cobertura_catalogo` < 50% tras leer el ancla, Sonnet remapea fragmentos verbatim del docx/pdf bruto a las 28 secciones NYL.
- Prompt obliga "NO inventar" — solo mover fragmentos del ancla.
- Marca cada sección remapeada con `[Re-estructurado desde ancla — revisar]` (nuevo string en `strings_localizados.py`, ES/EN).
- Documento extendido con propiedad `cobertura_catalogo`.
- Wire en `importar_documento.py` (Paso 4 del flujo) con extracción de texto crudo desde ancla.
- 16 tests nuevos.

**B.3 — Apéndices en todas las secciones + Excel multi-hoja (#3)**
- `tabla_reader.py`: `leer_excel_todas_hojas(ruta)` y `leer_tabla_todas(ruta)` que iteran `wb.sheetnames`. Hojas vacías se omiten. Para int de hoja, recupera el nombre real ("Mortalidad" en lugar de "Hoja1").
- `adjuntar_tabla.py`: nuevo método `ejecutar_multihoja()` — Excel con N hojas → N apéndices con título `"{base} — {hoja}"`. Para CSV / mono-hoja, no agrega sufijo.
- `entrevista.py:205`: **quitado el whitelist** `if es_seccion_data_heavy()`. El expander de apéndices ahora aparece en TODAS las secciones (con caption "típicamente data-heavy" si aplica).
- 9 tests nuevos.

**B.2 — DocumentPolisher (coherencia narrativa) (#7)**
- Nuevo `src/core/usecases/document_polisher.py` + prompt en `src/llm/prompts/document_polish.py`.
- Toma documento completo, devuelve `list[SugerenciaPolish]` con tipos: `inconsistencia`, `contradiccion`, `redaccion`, `referencia_rota`.
- Prompt obliga "no inventar" — cada hallazgo debe ser quotable del documento.
- Toggle opt-in en modal de export: "Revisar coherencia narrativa con IA antes de exportar (~$0.02 USD)".
- Resultado se muestra en card expandible del dashboard con sugerencias coloreadas por severidad.
- 15 tests nuevos.

**B.4 — Editor inline desde vista previa (#12)**
- Nuevo `src/ui/pages/editar_seccion_mrm.py`: textarea markdown + preview live lado a lado.
- Botón "✏️ Editar" en cada sección de `vista_previa.py` (junto al título).
- Persiste con `seccion.completitud` re-evaluada por longitud (>200 chars = completa, 0 = vacía, resto = parcial).
- Audit event `seccion_editada` con descripción "editada inline desde vista previa".
- 4 tests nuevos.

### Fase C — Apéndices avanzados + Versionado ✅ (2 sub-tareas)

**C.1 — Apéndices PDF + fórmulas matemáticas (#9)**
- **PyMuPDF** (>=1.23, sin deps SO) para renderizar páginas PDF a PNG embebido. `pdf_apendice_reader.py` con `renderizar_pdf_a_paginas_png(archivo, dpi=200, max_paginas=30)`.
- **matplotlib MathText** (>=3.7) para renderizar LaTeX → PNG. Nuevo `src/docs/formulas/latex_to_image.py`. NO requiere instalación de LaTeX en SO.
- Modelo `Apendice` extendido: `TipoApendice = Literal["tabla", "diagrama", "pdf", "formula", "otro"]` + nuevo campo `latex_source: str`.
- `DocxWriter._agregar_apendice_pdf()` y `._agregar_apendice_formula()` — para PDF carga desde Storage y embebe cada página como imagen; para fórmula renderea on-demand.
- Nuevos use cases `AdjuntarPdfApendice` y `AdjuntarFormulaApendice` (en `src/core/usecases/adjuntar_tabla.py`).
- UI: en entrevista, el file_uploader acepta ahora `.pdf` también; sección separada de fórmula LaTeX con preview KaTeX vivo (`st.latex()`).
- 20 tests nuevos (6 PDF reader + 7 LaTeX render + 7 integration).

**C.2 — Versionado de documentos (#10)**
- Nuevo modelo `Version` (`src/core/models/version.py`) con snapshot_json + hash_contenido SHA-256 + número monotónico.
- Nueva tabla `versiones` (SQLAlchemy `VersionRow` en `db.py`). `Base.metadata.create_all` la crea idempotente al boot.
- `VersionRepository` con `crear`, `obtener`, `listar_por_documento`, `proximo_numero`, `ultima_version`.
- Use case `CrearVersion` (`src/core/usecases/crear_version.py`): hash excluye `audit_trail`, `actualizado_en`, `metricas_uso` (campos volátiles). **Idempotente** — si hash igual al previo, NO duplica.
- `ExportarDocumento` con parámetros nuevos `crear_version: bool` y `comentario_version: str`.
- `_incrustar_metadata_version()`: el .docx exportado lleva `core_properties.category="DocuMente"` + `core_properties.comments="documento_id=X;version=N;hash=12hex"`. Sobrevive transit por email/OneDrive.
- `ImportarDocumento` lee `core_properties` antes de procesar. Si detecta `documento_id` previo, agrega advertencia en `ResultadoImportacion.documento_id_previo` para que UI pregunte "crear v{N+1} vs nuevo".
- UI dashboard: checkbox "Crear nueva versión al exportar" + input comentario + card "🔖 Historial de versiones (N)" expandible.
- Auditoría `TipoEvento` extendido con `version_creada`, `version_restaurada`.
- 8 tests nuevos.

**Gotcha técnico SQLAlchemy + Python 3.14:** `Mapped[datetime | None]` y `Mapped[Optional[datetime]]` fallan en ORM scan. Workaround: usar `Column` clásico (sin `Mapped[...]`) para columnas nullable. Documentado en `db.py:archivado_en`.

### Fix de UX — Breadcrumb clickeable

- Feedback Alberto: el breadcrumb del header **no era clickeable**, además aparecía visualmente desbalanceado.
- Componente `src/ui/components/header.py` reescrito:
  - Acepta `destinos: list[str | None]` opcional o auto-infiere (`Inicio→home`, `{nombre_doc}→dashboard` si hay 3+ items, último=current).
  - Cada nivel intermedio renderea con `st.button(type="tertiary")` con CSS de link (sin border, sin background, color `text_muted`, hover azul + underline).
  - **Fix visual final**: ratios de columnas estrechos (length × 0.08), `gap="small"`, `vertical_alignment="center"`, padding final grande (8.0) para empujar items a la izquierda, CSS `width: auto !important` + `min-width: 0` en botones tertiary para que NO ocupen toda la columna.
  - 7 tests unit (cobertura del auto-inferencia).

### D.2 — Auditoría frontend completa + plan dedicado de migración Next.js ✅

**4 documentos entregados** en `docs/superpowers/`:

1. **`specs/2026-05-19-design-system-audit.md`** — Score 62/100. Identifica:
   - 9 tokens definidos (3 colores + 2 fuentes + 6 spacings + 3 radii + 3 shadows = 23 tokens).
   - 5 colores hex hardcoded fuera de theme.py (en `gap_badge`, `chat_bubble`, `vista_previa`).
   - 102 ocurrencias de tipografía literal (`0.875rem`, `0.75rem`, etc.) en 20 archivos.
   - Faltan soft variants (`success_soft`, `warning_soft`, etc.) y escala tipográfica completa.
   - 3 patterns de "color por estado" duplicados (seccion_card, gap_badge, timeline) — refactor a `state_to_color()`.
   - **Propone `design_tokens.json` portable** que sirva a Streamlit hoy y Next.js mañana.

2. **`specs/2026-05-19-design-critique-por-pantalla.md`** — 50+ findings de UX/UI en las 12 pantallas, priorizados P0/P1/P2:
   - Home: 3 CTAs equivalentes (paradox of choice), tabs sin badges de cantidad.
   - Importar: 2 secciones numeradas planas, st.info default rompe marca.
   - Dashboard: 28 cards en grid 4×7 sin agrupar por capítulo NYL.
   - Brief inicial: 10 textareas amontonadas, scroll infinito.
   - Entrevista: split 1.4:1 sub-óptimo, expander apéndice con 3 sub-secciones.
   - Por cada pantalla, máximo 5 hallazgos con recomendación concreta.
   - 12 quick wins en Streamlit + 8 issues que solo se arreglan con migración.

3. **`specs/2026-05-19-accessibility-audit.md`** — WCAG 2.1 AA con **cálculos de contrast ratio reales**:
   - **5 críticos**: `success` #4b8b7f (3.96:1), `warning` #ce7046 (3.48:1), `info` #2e86af (4.08:1) FALLAN AA normal text. Gap badges "media" y "baja" también fallan.
   - **7 majors**: touch targets < 44px en breadcrumb buttons y icon-only ✏️, labels collapsed pierden contexto SR, status dots sin aria-label.
   - **4 minors**: landmarks semánticos, logo sin alt, focus indicators SMNYL.
   - Fix: agregar tokens `success_dark` (#264640 Dark Pine), `warning_dark` (#544235), `info_dark` (#0a385e) y usarlos como **texto**, dejando los originales solo para fondos/iconos/borders.

4. **`plans/2026-05-19-migracion-frontend-nextjs.md`** — **Plan dedicado** 5 sprints (~5 semanas full-time o 8-10 semanas part-time):
   - **W1**: FastAPI wrapping de use cases + OpenAPI → cliente TS auto-generado. design_tokens.json.
   - **W2**: Next.js 15 + Tailwind v4 + shadcn/ui + cult-ui scaffolding. Cognito real con @aws-amplify/auth (resuelve A.1.c). Home renderea.
   - **W3**: Páginas core (importar, crear, dashboard) con bento grid + accordion por capítulo NYL.
   - **W4**: Entrevista (resize draggable) + vista previa (hover-only edit) + editor MRM con toolbar.
   - **W5**: Polish a11y + microinteracciones + Playwright E2E + deploy EC2.
   - 21 tasks granulares. Mapeo componente-a-componente Streamlit → shadcn/cult-ui.
   - Riesgos identificados + mitigaciones.

### UX Pro Max audit (complemento) ✅

**Doc**: `docs/superpowers/specs/2026-05-19-uiux-pro-max-audit.md`

Auditoría adicional aplicando **UX laws + 99 reglas del skill ui-ux-pro-max**:

- **4 pecados de UX** identificados: Miller violado (home + dashboard), Doherty violado (LLM ops sin feedback), patrones web 2025 ausentes, onboarding sin gamificación.
- **10 UX laws aplicadas al journey real**: Hick, Miller, Fitts, Jakob, Doherty, Aesthetic-Usability, Goal-Gradient, Peak-End, Tesler, Zeigarnik. Por cada ley: violación específica + fix concreto.
- **Friction map** estima ~40-55% abandono acumulado en primer doc. Top 2 fixes (brief wizard + onboarding agrupado) lo bajan a ~25%.
- **12 patrones modernos faltantes**: skeleton screens, optimistic UI, undo toasts, command palette (cmd+K), recent-edits surfacing, streaming LLM text, empty states con CTA, progressive onboarding, autosave indicator, drag-and-drop, inline conflict resolution.
- **Estilo recomendado**: **Refined Minimalism + Bento Grid** del set de 50+.
- **Paleta refinada**: SMNYL base + variants intermedias (`primary-50`, `primary-100`, `primary-200`) + warm neutrals (`surface-warm: #fafaf9`) + dark variants para texto (resuelve los 5 a11y críticos).
- **Typography pair**: Georgia (display) + **Inter** (body UI denso, fallback Tahoma) + JetBrains Mono (model_ids).
- **TOP 10 quick wins** antes de Next.js (~25h total): stepper visual, hero "Continúa...", emojis → Lucide icons, empty states con CTA, tokens `_dark`, toast con Deshacer, confetti en peak-end export, "Guardado hace Xs" indicator, dashboard agrupado por capítulo NYL, microinteracciones globales.
- **Mockup ASCII del dashboard rediseñado** con bento grid (hero card completitud + sticky sidebar gobernanza + brechas críticas destacadas + capítulos en accordion).

### Tests + calidad

- Suite final: **386 tests pasando** (de 307 al cierre de S13 Fase A → +79 nuevos en B + C + D.2 fix breadcrumb).
- `ruff check` clean. `ruff format` aplicado.
- 0 regresiones.
- Los 7 fallos pre-existentes de fixtures siguen igual (fixtures `SMNYL/Ejemplos actuales/*.docx` no copiados al worktree).

### Estado al cierre absoluto de S13

| Sub-tarea | Estado |
|---|---|
| A.1.b password gate | ✅ committed `c15dba7` |
| A.2 onboarding nunca silencioso | ✅ committed |
| A.3 idioma normaliza | ✅ committed |
| A.4 PDF como ancla | ✅ committed |
| A.5 archivado/papelera | ✅ committed |
| **A.1.c Cognito real** | ⏸️ bloqueado pendiente Vidal |
| B.1 StructureRealigner | ✅ código completo, pendiente commit |
| B.2 DocumentPolisher | ✅ código completo, pendiente commit |
| B.3 Apéndices universales + multi-hoja | ✅ código completo, pendiente commit |
| B.4 Editor inline MRM | ✅ código completo, pendiente commit |
| C.1 Apéndices PDF + LaTeX | ✅ código completo, pendiente commit |
| C.2 Versionado | ✅ código completo, pendiente commit |
| Breadcrumb clickeable + visual fix | ✅ código completo, pendiente commit |
| **D.2 Auditoría frontend completa** | ✅ 4 audits + plan dedicado escritos, pendientes commit |
| **D.1 Prophet correctivos + demo MA** | ⏸️ siguiente prioridad |

---

## Progreso de sesión 14 (2026-05-20)

Sesión maratónica. Ejecuté todo el plan de remediación UX (S13→S16) + rewrite arquitectónico completo a Next.js + FastAPI. **18 commits sobre main**, 457 tests verdes, paridad funcional total entre Streamlit (legacy) y Next.js (nuevo).

### Bloque 1 — Remediación UX (commits c2a3b1a → c6c1b9b)

**a11y WCAG 2.1 AA** (commit `c2a3b1a`):
- 5 fixes críticos: tokens `success_dark`, `warning_dark`, `info_dark` agregados a `theme.py`
- Refactor de `seccion_card`, `gap_badge`, `timeline`, `vista_previa` para usar `*_dark` como texto
- Helper `_contrast_ratio()` sRGB con verificación AA ≥4.5:1 en tests automatizados

**Top 10 Quick Wins UX** (commits `0163675`, `c924117`, `9c226c2`, `0dc68cc`, `8b8c85a`, `e25a535`, `aebfee4`, `1bee041`, `d3ea1bf`, `de14aec`):
- QW#1 Stepper visual reusable + integración en onboarding/brief
- QW#2 Hero "Continúa donde te quedaste" con tiempo relativo
- QW#3 Empty states con CTA en tabs vacíos + celebración cero brechas
- QW#4 Dashboard agrupado por capítulo NYL en accordion (9 capítulos)
- QW#5 Tokens `*_soft` globales + eliminación de hex hardcoded
- QW#6 Banner "Deshacer" post archivar/papelera (pattern Gmail)
- QW#7 `st.balloons()` + toast 🎉 al primer export DOCX
- QW#8 Indicador "Guardado hace X" en editores MRM y Prophet
- QW#9 Emojis funcionales → Material Symbols (`:material/archive:`, etc.)
- QW#10 Microinteracciones `transition: all 200ms ease-out` global

**Premium polish T1** (commit `c6c1b9b`):
- Brechas críticas en accordion por severidad (Críticas/Atención/Sugerencias)
- Hero compacto del dashboard (nombre + pill + meta en 1 fila)
- 5 cards de métricas refactorizadas con border-left + mini progress bar
- Density global: H1 2.25→1.875rem, max-width 1200→1320px, shadows con 2 capas

### Bloque 2 — Rewrite arquitectónico (commits 6854547 → 1cac71a)

**F1 — API REST FastAPI** (commit `6854547`):
- 11 routers, 46 endpoints, OpenAPI 3.1 auto-generado en `/docs`
- DTOs Pydantic en `src/api/schemas/` separados del dominio
- Auth bearer token reutilizando `DOCUMENTE_GATE_PASSWORD`
- CORS abierto en dev (`*`) — restringir en prod
- 28 smoke tests con httpx.TestClient
- Cero cambios al dominio o repos — los use cases existentes siguen intactos
- Coexiste con Streamlit en la misma BD

**F2 — Next.js 14 skeleton** (commit `0b4700f`):
- Next.js 14 App Router + TypeScript estricto + Tailwind + shadcn/ui
- Sidebar fijo 240px + topbar sticky + main shell
- Tokens SMNYL portados de `theme.py` a `tailwind.config.ts`
- TanStack Query + sonner para toasts
- Home con ContinueHero/WelcomeHero + DocumentList con tabs (Activos/Archivados/Papelera)
- 380 packages npm; build OK

**F3 — 5 páginas core** (commit `041e154`):
- `/documentos/[id]` dashboard premium (hero + métricas + brechas accordion + secciones por capítulo)
- `/documentos/crear` form con tipo MRM/Prophet
- `/importar` drop zone .docx/.pdf + fuentes adicionales
- `/documentos/[id]/secciones/[sid]` editor inline split (textarea + preview)
- `/prophet` flujo 2 pasos (detectar Excel → crear ficha)
- Fix retroactivo: `.gitignore` raíz tenía `lib/` (regla Python) que ignoraba silenciosamente `frontend/src/lib/` — agregada excepción

**F4 — 8 páginas restantes + governance** (commit `1cac71a`):
- `/documentos/[id]/metadata` form con 17 campos MRM
- `/documentos/[id]/auditoria` timeline vertical con 17 tipos de evento
- `/documentos/[id]/vista-previa` render tipo paper + Exportar
- `/documentos/[id]/entrevista/[sid]` chat LLM con bubbles + auto-scroll + indicador escribiendo
- `/documentos/[id]/versiones` snapshots inmutables + crear con comentario
- `/documentos/[id]/apendices` tabs (tabla/PDF/LaTeX) + upload + lista
- `/documentos/[id]/onboarding` 6 campos con Stepper visual
- `/documentos/[id]/brief` textarea ejecutiva
- **GovernanceCard** en dashboard con state machine + signoffs Reviewer/FAE
- **QuickLinks chips** bajo el hero para navegación rápida

### Docs generados al cierre

| Doc | Propósito |
|---|---|
| `docs/HANDOFF_VIDAL.md` | Snapshot main → branch para Vidal: arquitectura, env vars, deps, checklist deploy |
| `docs/ARQUITECTURA.md` | Doc técnico atemporal — la arquitectura actual en 3 servicios |
| `docs/GUIA_DOCUMENTE.md` | Guía conceptual + walkthrough técnico simplificado, en español sencillo |
| `docs/MIGRATION_TO_EC2.md` | Actualizado con servicios nuevos (FastAPI, Next.js) |
| `docs/ARCHIVOS_AUDITORIA.md` | Inventario: vivos / candidatos a borrar / personales — base para depuración post-merge |

### Tests + calidad

- **Backend**: 457 tests pasando (429 unit + 28 integration de la API).
- **Frontend**: TypeScript `--noEmit` clean, ESLint sin warnings, todas las rutas responden 200 OK.
- `ruff check` clean. `ruff format` aplicado.
- 0 regresiones — todo el código Python preexistente sigue funcionando.

### Bloque 3 — Cierre técnico + post-PR (commits `ae54df9` → `7c323a0`)

Después de cerrar F4 y los docs, hicimos pulido + push + extensión del HANDOFF:

- **Logo `BrandLogo`** SVG inline cerebro+libro (commit `ae54df9`). Reemplaza el cuadrito "D" placeholder del sidebar. Link a home con hover scale-105.
- **Push de los 14 commits faltantes** a GitHub (`origin/claude/affectionate-noether-8e038f` actualizado). Link de PR generado: `https://github.com/AlbertoMafud/DocuMente/compare/main...claude/affectionate-noether-8e038f?expand=1`
- **Fix 404s sidebar** (commit `f7f7967`): quitamos "Documentos" (redundante con Inicio) y "Auditoría" (es contextual al doc, vive en `/documentos/[id]/auditoria`). Nuevas páginas `/configuracion` (estado app/health/env/auth) y `/ayuda` (FAQ + links a docs).
- **Favicon SMNYL** (mismo commit): borrado `favicon.ico` default, creado `app/icon.svg` con cerebro+libro. Next.js 14 lo sirve automáticamente.
- **Fonts Geist eliminadas** (mismo commit): borrados `app/fonts/GeistVF.woff` y `GeistMonoVF.woff`. Usamos Georgia/Tahoma per BRAND_GUIDELINES.
- **openapi-typescript autogen** (mismo commit): instalado v7.13.0, script `npm run gen:api-types`, `openapi.gen.ts` generado (3198 líneas) como fuente de verdad. `types.ts` ahora documenta el workflow de sync.
- **HANDOFF §14 paths exactos para Vidal** (mismo commit): Cognito (solo `src/api/auth.py`), PostgreSQL (solo URI en `.env`), Bedrock (`BedrockClient` en `src/llm/client.py`). Costo total 5-6 días.
- **HANDOFF §5 CORS VPN clarificado** (commit `7c323a0`): 3 opciones explícitas para Vidal (dejar `*` durante piloto / cerrar al IP 172.x.x.x / hostname interno `documente.smnyl.local`). Documenta intención; el cambio en código se hace en S15.

### Estado al cierre absoluto de S14

| Tarea | Estado |
|---|---|
| 5 fixes a11y WCAG AA | ✅ committed `c2a3b1a` |
| Top 10 Quick Wins UX | ✅ 10/10 committed |
| Premium polish T1 (densidad, brechas accordion) | ✅ committed `c6c1b9b` |
| F1 API REST FastAPI | ✅ committed `6854547` — 46 endpoints |
| F2 Next.js skeleton + home | ✅ committed `0b4700f` |
| F3 5 páginas core | ✅ committed `041e154` |
| F4 8 páginas + governance + quick links | ✅ committed `1cac71a` |
| Docs handoff/arquitectura/guía/auditoría | ✅ committed `5e37964` |
| Logo cerebro+libro | ✅ committed `ae54df9` |
| **Push a GitHub** | ✅ todos los 23 commits en `origin/claude/affectionate-noether-8e038f` |
| Fix 404s sidebar + favicon + openapi-typescript + HANDOFF §14 | ✅ committed `f7f7967` |
| HANDOFF §5 CORS para deploy VPN interno | ✅ committed `7c323a0` |
| **Abrir PR a main** | ⏸️ Alberto hace click en el link compare |
| **Implementar CORS env var** en `src/api/main.py` | ✅ committed `b2203c8` (S15) |
| **`npm run build` validación** | ✅ S15 — 10 rutas, bundle prod limpio |
| **Playwright opción B** (instalar + 1 test happy-path) | ✅ committed `eedf693` (S15) — pasa en 4s |
| **Fix Unicode em-dash en export DOCX** (bug latente descubierto por E2E) | ✅ committed `8f4835a` (S15) |
| **A.1.c Cognito real** | ⏸️ pendiente reunión Vidal |
| **D.1 Prophet correctivos + demo MA** | ⏸️ siguiente prioridad de negocio |

---

## Progreso de sesión 15 (2026-05-20, tarde — opción A aprobada)

Sesión corta y enfocada: ejecutar los 3 entregables de "opción A" aprobados al cierre de S14 (CORS env var, npm build, Playwright + 1 test E2E). Resultado: completado + un bug latente de Unicode descubierto y arreglado por el propio test E2E.

### Commits (3 atómicos, fast-forward sobre `0ab8498`)

| Commit | Tipo | Descripción |
|---|---|---|
| `b2203c8` | feat(api) | CORS configurable via `CORS_ORIGINS` env var (default `*` dev; tightened `allow_methods`/`allow_headers` a explícitos) |
| `8f4835a` | fix(api) | Export DOCX falla con Unicode en nombre del modelo — helper `_content_disposition()` con RFC 6266 + 5987 |
| `eedf693` | test(frontend) | Playwright setup + happy-path E2E (crear → dashboard → exportar DOCX descarga real) |

### Cambios concretos

1. **CORS env var** — `src/api/main.py:14-19, 55-69` + `.env.example`. Lee `CORS_ORIGINS` con default `*`. Vidal solo edita `.env`, no código. Snippet ya documentado en `docs/HANDOFF_VIDAL.md §5`; ahora también está implementado en código.

2. **Unicode encoding fix en export DOCX** — `src/api/routers/exportar.py:44-54`. **Bug latente real**: cualquier modelo con nombre tipo "VNB — GMM v2" (em-dash, acentos, ñ, etc.) crasheaba el export con HTTP 400 (`UnicodeEncodeError` en latin-1). Descubierto cuando el E2E corrió con nombre "E2E Test — N". Fix aplicado a `/exportar` (MRM) y `/exportar/prophet`.

3. **Playwright E2E starter** — `frontend/e2e/crear-y-exportar.spec.ts` + `frontend/playwright.config.ts`. Stack:
   - Dual webServer en `playwright.config.ts`: uvicorn `:8100` + Next.js `:3100` (puertos aislados para no chocar con dev local del usuario, que típicamente tiene servers en 3000-3002 y 8001).
   - `NEXT_PUBLIC_API_URL` override en `env` del webServer frontend → apunta al backend del E2E, no al dev local.
   - Scripts npm: `test:e2e` y `test:e2e:ui`.
   - Test cubre: navegar /documentos/crear → POST /documentos (form submission con TanStack Query) → redirect a /documentos/{uuid} → GET doc + brechas → POST /exportar → descarga DOCX validada.
   - Listener `page.on("response")` para capturar 4xx/5xx — útil para diagnóstico en CI.
   - Pasa en ~4s end-to-end.

### Validaciones al cierre

| Check | Resultado |
|---|---|
| pytest full suite | 499 pass / 7 fail (fixtures `SMNYL/Ejemplos actuales/*.docx` no copiados al worktree — esperado, no regresión) |
| pytest API smoke | 28/28 ✅ |
| Ruff lint + format (mi código) | clean ✅ |
| TypeScript `tsc --noEmit` | clean ✅ |
| ESLint frontend | clean ✅ |
| `npm run build` | 10 rutas (5 estáticas + 5 dinámicas), bundle prod limpio ✅ |
| Playwright E2E | 1/1 pasa, 4.0s ✅ |

### Estado git al cierre

- Branch `claude/affectionate-noether-8e038f` ahora en `eedf693` (de `0ab8498`, +3 commits S15).
- **Pusheado** a `origin/claude/affectionate-noether-8e038f`. PR link sigue siendo el mismo: https://github.com/AlbertoMafud/DocuMente/compare/main...claude/affectionate-noether-8e038f
- Branch huérfano `claude/optimistic-zhukovsky-b7e828` (creado automáticamente por el harness al iniciar el worktree S15) **borrado local**. No existe en GitHub.
- Worktree `optimistic-zhukovsky-b7e828` removido de git pero la **carpeta física huérfana** sigue en disco (Windows file lock por el shell del harness en sesión activa). Se borra al cerrar la sesión con `git worktree prune` + `rm -rf .claude/worktrees/optimistic-zhukovsky-b7e828`.

### Decisiones tomadas en S15

1. **Worktrees + branches del harness** — al iniciar un worktree, el harness crea automáticamente un branch nuevo para aislar. Para evitar acumular branches huérfanos al cierre, hacer **fast-forward al branch padre** (origen del worktree) en lugar de mergear/PR. Aplica para futuras sesiones que usen worktree.
2. **Puertos aislados para E2E** — Playwright usa `:8100/:3100` en vez de `:8001/:3000` para no colisionar con servers dev locales del usuario. Forzado con `next dev -p 3100` (sin esto, Next cae a 3001/3002 silenciosamente y Playwright queda esperando un puerto que nunca se levanta).
3. **`python -m uvicorn`** en lugar de `uvicorn` directo en `playwright.config.ts.webServer` — no asume uvicorn en PATH del shell de Playwright.

### Gotchas técnicos

- **Backend stale en background**: si arrancas uvicorn manualmente para debug (curl) y se queda corriendo, Playwright lo reusa por `reuseExistingServer: true` y enmascara fixes recientes. Matarlo antes de re-correr el test.
- **`git worktree remove` en Windows** falla con "Permission denied" si el shell está parado dentro del worktree. Necesitas cerrar la sesión o cambiar de cwd primero.
- **Em-dash en nombres de modelo**: AHORA SÍ funciona en export. Antes era un bug latente que nadie había notado porque los tests usaban ASCII.

### Sesión 17 (2026-05-20) — paralelización LLM + streaming SSE

Después del fix del toast realista (~10 min) Alberto pidió implementar
las 2 mejoras técnicas que mencioné: paralelización + streaming en UI.
Decisión cerrada: A+B juntas, NO cambiar tier Opus→Sonnet (sin eval).

**5 commits S17 (en orden, sobre `54ae8d6`):**

| Commit | Fase | Qué hizo |
|---|---|---|
| `7f44070` | A1+A2+A3 | AsyncAnthropic + chat_async + SugerenciasMultiFuente paralelo + 3 tests (paralelismo medido) |
| `5beb7cb` | B1 | Endpoint POST /documentos/crear-con-fuentes/stream con SSE (created/progress/done/error) |
| `60b24b3` | B2 | Frontend: streamSse helper + ProgressPanel con barra + lista en vivo + ETA |

**Diseño clave:**
- `AnthropicClient` ahora ofrece `chat()` (sync, legacy) y `chat_async()`
  (new). Use cases viejos sin cambios.
- `SugerenciasMultiFuente.ejecutar_async()` con `asyncio.gather` +
  `Semaphore(5)` por default. `ejecutar()` sync wrapper compatible.
- Endpoint SSE usa `StreamingResponse` nativo de FastAPI (sin deps
  nuevas como sse-starlette).
- Frontend: `EventSource` nativo no sirve para POST multipart; helper
  `streamSse` parsea SSE sobre `fetch` + `ReadableStream`.
- UI: barra de progreso shadcn + lista de secciones con badge de estado
  (poblada / sin_info / error) + ETA calculado del ritmo real.

**Resultado UX:**
- Antes: pantalla en blanco ~10 min con toast "típicamente ~10 min".
- Después: progreso en vivo con secciones rellenándose una a una; latencia
  total real ~1-2 min con paralelización (~6-10× speedup), y el usuario
  ve actividad desde el segundo 1.

**Lo que NO se hizo (deliberadamente):**
- Cambiar tier Opus→Sonnet (sin eval framework — documentado en
  `docs/MODEL_TIERING.md`).
- Convertir `crear_con_fuentes` (sync) en async — coexiste con el stream,
  no se necesita.
- Test E2E del flujo streaming — no trivial con SSE en Playwright; se
  validó vía unit tests del use case + smoke manual del endpoint.

### Sesión 16 (2026-05-20) — feedback post-demo S15 atendido

Tras el demo S15 Alberto identificó 6 puntos del producto (A1-A6) y 8
sobre Prophet (B1-B2.8). Se ejecutaron 5 fases en un branch dedicado
`claude/s16-feedback-pasada-1` (fast-forward a affectionate-noether al cierre).

**10 commits S16 (en orden, sobre `274aceb`):**

| Commit | Fase | Qué hizo |
|---|---|---|
| `b60a858` | F1.A3 | Preview con react-markdown + remark-gfm (negritas, tablas) |
| `79769aa` | F1.A5 | Selector de idioma en exportar DOCX (5 opciones, dropdown) |
| `ba8f296` | F1.A2 | Crear desde cero acepta fuentes opcionales (PDFs, Excel, etc.) |
| `f73f3c5` | F2.A1 | Visión Claude Haiku 4.5 multimodal + cache sha256 + 7 tests |
| `d31942a` | F2.A1 | Checkbox de visión en UI /crear y /importar |
| `0ad567c` | F3.A6 | Use case RestaurarVersion + 3 endpoints (ver/exportar/restaurar) |
| `cecef18` | F3.A6 | UI versiones con 3 botones por card + vista-previa de vN |
| `a37a113` | F4.A4 | docs/MODEL_TIERING.md con costos y justificación + bug DATABASE_URL anotado |
| `895343d` | F5.B | docs/PROPHET_FASE0_AUDIT.md + docs/PROPHET_AGENDA_MA.md |
| `4d5d2c6` | cierre | Fix tests E2E para el dropdown nuevo de idiomas |

**Decisiones cerradas con Alberto antes de ejecutar:**
1. Branch nuevo desde affectionate-noether, fast-forward al cierre.
2. A1 imágenes: visión multimodal Claude (NO OCR) — costo marginal por
   imagen + cache por hash, sin deps de sistema.
3. A6 versionado: alcance "ver + descargar + restaurar" — NO branches
   Git-like (ROI dudoso, no encaja con mental model).

**Lo que NO se hizo en S16 (deliberadamente):**
- Cambiar tiering de modelos LLM (riesgo sin eval framework — documentado).
- Módulo Prophet profundo (bloqueado por reunión MA pendiente).
- Subir a EC2 (Vidal).
- Cognito real (A.1.c — Vidal).
- Pulido formal template MRM `.docx` (diferido hasta demo externa).

### Extensión de S15 — Playwright escalado a 7 tests (commit `da0fb8b`)

Alberto pidió escalar la suite. Se hicieron 6 tests E2E nuevos + README:

| Test | Archivo | Cobertura |
|---|---|---|
| Importar (ciclo crear→exportar→importar) | `importar.spec.ts` | DOCX writer + reader simétricos |
| Editar + persistir sección | `editar-seccion.spec.ts` | El flujo más fundamental; persistencia BD |
| Guarda MRM (draft→in_review rechazado) | `gobernanza.spec.ts` | State machine bloquea con razón útil |
| Subir CSV como apéndice | `apendices.spec.ts` | Upload multipart en /apendices |
| Entrevista sin API key → 503 amigable | `llm-fallback.spec.ts` | Degradación elegante sin LLM |
| Crear versión + verificar lista | `versiones.spec.ts` | Snapshots inmutables |

Plus `helpers.ts` con `crearDocumentoMRM()` y `logHttpErrors()` compartidos, y `e2e/README.md` con doc completa en español.

**Suite 7/7 en ~40s.** TypeScript clean, ESLint clean.

**Bugs latentes descubiertos por la suite:**
- Em-dash en nombres de modelo (arreglado en `8f4835a`).
- Guarda MRM correcta: la transición draft→in_review SE rechaza con 409 cuando hay secciones obligatorias vacías. El test ahora documenta esta regla y verifica que el toast muestra la razón.

---

## Lo que sigue — sesión 16

### Operacional (path inmediato post-S15)

1. **Probar entrevista LLM** localmente end-to-end en Next.js: `cp /c/Users/alber/Claude_AI/proyectos/DocuMente/.env .env` (el worktree no hereda el `.env` gitignored). Verificar que la entrevista funciona en :3000 contra API :8001.
2. **Compartir con Vidal**: el PR + los 4 docs (`HANDOFF_VIDAL.md`, `ARQUITECTURA.md`, `MIGRATION_TO_EC2.md`, `ARCHIVOS_AUDITORIA.md`). El PR ahora trae 3 commits adicionales de S15 — recordar mencionar a Vidal que el CORS env var ya está implementado (no solo documentado) y que el flujo crear→export tiene cobertura E2E.
3. **Agendar reunión Vidal (30 min)** para resolver §8 HANDOFF: Cognito (A.1.c), dominio interno, sunset Streamlit, Bedrock.

### Estratégico (post-aprobación Vidal)

4. **Merge PR a main** una vez Vidal apruebe el deploy.
5. **Depuración post-merge** según `docs/ARCHIVOS_AUDITORIA.md`.
6. **D.1.a Template Prophet DOCX** + D.1.c self-service + D.1.d demo MA — destrabe negocio Prophet Fase 1.

### Mejoras técnicas posibles si hay tiempo

7. **Escalar suite Playwright a 5-8 tests pre-deploy**: importar documento, editar sección con persistencia, omitir sección con motivo, transición de estado MRM, audit trail validation, descargar versión, apéndice con archivo adjunto, fallo en entrevista LLM 503.
8. **Limpiar carpeta huérfana** `.claude/worktrees/optimistic-zhukovsky-b7e828/` (cosmético; cuando el shell ya no esté parado ahí).
9. Validación visual S10 quedó pendiente desde S11 — checklist en `pending_validation_items.md`. Probablemente obsoleta a estas alturas (post-rewrite).

### Bloqueos vigentes

- **A.1.c Cognito real** — pendiente reunión Vidal (no urgente porque password-gate A.1.b ya mitiga).
- **Prophet Fase 1** — NO arrancar sin feedback positivo de la demo con MA.
- **Pulido formal de plantilla MRM `.docx`** — diferido hasta antes de demo externa.
- **Bedrock vs Anthropic** — Vidal aceptó hacerlo con Bedrock directo. Cuando llegue el momento de deploy, swap del adaptador en `src/llm/`.

### Decisiones de fondo todavía vigentes (S13/S14)

- **Fase D order invertido**: D.2 (frontend audit) ANTES de D.1 (Prophet). La auditoría aplica a TODO incluyendo Prophet.
- **Refined Minimalism + Bento Grid** como estilo objetivo post-migración (Next.js premium ya lo refleja).
- **Stack frontend**: Next.js 14 App Router + Tailwind + shadcn/ui + TanStack Query + Sonner + Framer Motion + Lucide. SVG inline para logo.

### Reglas de oro vigentes

1. `main` queda en `51d845e` — no merge hasta que Vidal valide deploy.
2. Todo el trabajo vive en `claude/affectionate-noether-8e038f` (S13+S14+S15 acumulado).
3. TDD obligatorio. **Baseline al cierre de S15 = 528 tests passing** (incluye 1 E2E Playwright).
4. Schema migrations SOLO aditivas, idempotentes al boot.
5. NUNCA borrar el avance del usuario. Backup antes de cambios arriesgados a BD.
6. **Cualquier worktree nuevo se hace fast-forward al branch padre al cierre** (S15 aprendido — evita acumular branches huérfanos).
