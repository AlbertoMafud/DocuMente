# Status — DocuMente

> Estado vivo del proyecto. Se lee al iniciar sesión y se actualiza al cerrar si hubo cambios significativos.

**Última actualización:** 2026-05-06 (sesión 7 — refinamiento DOCX + traducción ES/EN + docs migración Fase 6)

---

## Estado actual

**Fases 0-4 + Fase 3 + Fase 6 ✅ completas.** Solo falta Fase 5 (pulido UX).

**Próximo (mañana):** validación visual end-to-end del .docx con tablas nativas + traducción inglés + redactar correo formal a Vidal (arquitecto) con mini business case para solicitar EC2.

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
