# Status — DocuMente

> Estado vivo del proyecto. Se lee al iniciar sesión y se actualiza al cerrar si hubo cambios significativos.

**Última actualización:** 2026-05-18 (sesión 12 — push a GitHub, reunión Vidal, fixes locales)

---

## Estado actual

**Fases 0-4 + Fase 3 + Fase 6 ✅ completas + features "crear desde cero" (S9) + v2.10 mejoras (S10) + Prophet Fase 0 (S11) ✅.** Solo falta Fase 5 (pulido UX final).

**MVP cerrado + módulo Prophet Fase 0 implementado.** Repo GitHub `AlbertoMafud/DocuMente` en `8d64520` (todo pusheado incluyendo S10 + S11 + limpieza de S12). **263 tests pasando**, ruff/format clean.

**Próximo:** Template DOCX Prophet completo (diseño SMNYL + loops) → demo con Carmona/Cynthia/Magallanes → seguimiento con Vidal para EC2 → Fase Prophet-1 solo si demo es positiva.

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
