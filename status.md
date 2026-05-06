# Status — DocuMente

> Estado vivo del proyecto. Se lee al iniciar sesión y se actualiza al cerrar si hubo cambios significativos.

**Última actualización:** 2026-05-05 (sesión 5 — Fase 2.5 completa, lista para 2da prueba)

---

## Estado actual

**Fase:** 2.5 — Refinamiento post-prueba ✅ **COMPLETA**

**Próximo:** Segunda prueba de Alberto retomando su documento de prueba. Si pasa la validación → Fase 3 (DocxWriter con plantilla maestra).

---

## Avance acumulado

- Fase 0 ✅ — Setup, archivos de contexto, theme SMNYL, app branded.
- Fase 1 ✅ — Modelos Pydantic, Storage interface, DocxReader, GapAnalyzer, Repository SQLite, use case ImportarDocumento, UI dashboard.
- Fase 2 ✅ — LLMClient + AnthropicClient, prompts (tono/entrevista/drafting/contexto fijo cacheado ~12K tokens), InterviewEngine, Drafter, EstadoEntrevista persistido, pantalla de entrevista split chat↔preview.
- **Fase 2.5 ✅ — Refinamiento post-prueba** (esta sesión).

---

## Progreso de Fase 2.5 — Refinamiento post-prueba ✅

### Restricción cumplida: el documento de prueba de Alberto NO se perdió
- Backup automático en `data/backups/documente_<timestamp>_pre_fase_2_5.db` antes de tocar nada.
- Pydantic con todos los campos nuevos opcionales (`MemoriaModelo`, `Apendice`, `MetricasUso`) con `Field(default_factory=...)`.
- Verificación final: el doc de prueba con sus 9 secciones completas, 1 parcial, 15 eventos audit y 20 brechas se carga intacto.

### 2.5.1 — Estrategia tiered de modelos Anthropic
- `LLMClient.chat()` ahora recibe parámetro `tarea: Literal["chat", "drafting", "extraction"]`.
- `AnthropicClient` mapea automáticamente:
  - `chat` → `claude-sonnet-4-6` (entrevista, ~3× más barato que Opus, mejor latencia)
  - `drafting` → `claude-opus-4-7` (calidad institucional)
  - `extraction` → `claude-haiku-4-5` (extracción JSON estructurada)
- `LLMResponse` ahora reporta el `modelo_usado` para cálculo correcto de costo.

### 2.5.2 — Memoria del modelo (resuelve repetición de conceptos básicos)
- `MemoriaModelo` (`src/core/models/memoria.py`): captura plataforma, lenguaje, frecuencia, ESG, rutas, owners, dependencias upstream/downstream + hechos libres. Auto-merge sin sobrescribir.
- **Pantalla de onboarding** (`src/ui/pages/onboarding.py`) — formulario de ~2 min con 6-8 campos. Banner en dashboard sugiere completarla cuando `MemoriaModelo` está vacía.
- **`KnowledgeExtractor`** (`src/core/usecases/knowledge_extractor.py`): después de cada cierre de sección, llama a Haiku con prompt JSON específico, extrae hechos transversales nuevos y los mergea sin sobrescribir.
- **Inyección en prompts de entrevista**: `InterviewEngine` agrega bloque "HECHOS YA CONOCIDOS DEL MODELO (no preguntes por estos)" al system prompt. La memoria visible para Claude crece sin invalidar el cache (vive en bloque NO cacheado).

### 2.5.3 — Apartado de tablas con upload Excel/CSV
- **`Apendice`** (`src/core/models/apendice.py`): tabla/diagrama/otro vinculado a una sección de origen.
- **`tabla_reader`** (`src/docs/tabla_reader.py`): lee `.xlsx`/`.xls`/`.csv` con pandas+openpyxl, devuelve `TablaLeida` con headers, primeras 5 filas markdown (para prompt), tabla completa markdown (para apéndice DOCX) y resumen estadístico.
- **Use case `AdjuntarTablaApendice`**: orquesta storage + reader + creación del apéndice + inyección de `system_note` en la entrevista activa para que Claude la referencie sin replicarla en la sección principal.
- **Drop zone en pantalla de entrevista** (sección data-heavy: 4.4, 5.1, 5.2, 5.3.x): expander con título + uploader + botón "Procesar y crear apéndice".

### 2.5.4 — Drafter con prosa institucional endurecida
- `DRAFTING_SYSTEM_INSTRUCTION` reescrito con reglas no-negociables:
  - Tercera persona impersonal estricta. Cero coloquialismos. Cero hedging vacío.
  - Vocabulario técnico-actuarial preciso (BEL, MP, ESG, calibración, IFRS 17, SAP, etc.).
  - Párrafos compactos, un solo eje, máximo 4-5 líneas.
  - Captura del "por qué" obligatoria en decisiones metodológicas.
  - Frases prohibidas explícitas ("Como se mencionó", "Es importante notar", "En conclusión", etc.).
  - Marcador `[Pendiente: ...]` cuando falta info esencial.

### 2.5.5 — Reporte de costo
- **`MetricasUso`** (`src/core/models/metricas.py`) acumula `LlamadaLLM` con tokens y costo por llamada.
- **`pricing.py`** (`src/llm/pricing.py`): tarifas oficiales 2026 de Anthropic por modelo, función `costo_usd()` que calcula USD a partir de tokens y modelo.
- **Auto-registro**: `InterviewEngine`, `Drafter` y `KnowledgeExtractor` registran cada llamada en `documento.metricas_uso` automáticamente.
- **Widget en dashboard**: card con "Costo de generación: $X.XX USD · Cache hit rate: Y%" y warning si cache < 50% (silent invalidator).

### 2.5.6 — Vista previa HTML del documento completo
- **Pantalla `vista_previa.py`**: renderiza todas las secciones concatenadas con marca SMNYL (paleta + tipografías Georgia/Tahoma). Secciones vacías como placeholders amarillos. Apéndices al final. Panel lateral con metadata + costo + estado.
- Botón "Vista previa" en el dashboard.

### Tests añadidos
- `test_memoria.py` — 5 tests de `MemoriaModelo` (vacía, render, merge, no-duplicación, dict-vacío).
- `test_pricing.py` — 6 tests de cálculo de costo (Opus, Sonnet, Haiku, modelo desconocido, construcción).
- `test_knowledge_extractor.py` — 7 tests del extractor (parse JSON con/sin fences, merge, no-cambios, tarea correcta).
- `test_tabla_reader.py` — 6 tests de lectura CSV/Excel.
- `test_adjuntar_tabla.py` (integration) — 4 tests del flujo completo de adjuntar tabla.

**Total: 75/75 tests pasan en ~7s. `ruff check` limpio. `ruff format` aplicado.**

---

## Decisiones técnicas clave de Fase 2.5

- **Tiered Anthropic puro** (no mezclar OpenAI): MRM/Compliance prefiere un solo proveedor; ahorro estimado 50-65% del costo total vs todo-Opus.
- **Memoria del modelo en bloque NO cacheado**: la memoria crece dinámicamente; ponerla en un bloque cacheado invalidaría la cache cada vez. El bloque cacheado (~12K tokens) sigue intacto entre llamadas.
- **`KnowledgeExtractor` corre con Haiku** (no Opus): tarea de extracción JSON estructurada, ~50× más barata. Best-effort: si falla, no rompe la entrevista.
- **Apéndices auto-creados como referencia**: la sección principal solo lleva narrativa + referencia (`(ver Apéndice: Tabla X)`); la tabla completa vive en el apéndice. Esta es la práctica MRM estándar.
- **Drop zone solo en secciones data-heavy** (`SECCIONES_DATA_HEAVY` = 4.4, 5.1, 5.2, 5.3.x): el resto de las secciones no muestran la opción para no agregar ruido.
- **Schema-aditivo, no destructivo**: agregar columnas con defaults; nunca renombrar/borrar.

---

## Lo que sigue — segunda prueba con Alberto

Al retomar el documento existente:
1. **Verificar persistencia**: tu documento sigue cargando con sus 9 secciones completas.
2. **Onboarding**: el banner de onboarding aparece en el dashboard. Llenarlo con los hechos del modelo VNB que ya capturaste mentalmente.
3. **Continuar la sección parcial** que dejaste a la mitad. Validar que Claude:
   - **No vuelve a preguntar** plataforma, frecuencia, rutas (ya están en memoria).
   - Mantiene el tono más institucional en el borrador final (Drafter endurecido).
4. **Probar adjuntar tabla**: en la sección 4.4 Assumptions o 5.1 Raw Data, subir un Excel/CSV con tabla de mortalidad o lapses. Validar que se crea apéndice y la sección principal lo referencia.
5. **Vista previa HTML**: ver el doc completo concatenado con marca SMNYL y placeholders donde falta.
6. **Reporte de costo**: validar que el dashboard muestra costo en USD y cache hit rate >= 50%.

Si la prueba sale bien → luz verde para Fase 3 (DocxWriter con plantilla maestra Word).

---

## Bloqueos / decisiones pendientes

- **Sesión de diseño de plantilla `.docx` en Word**: pendiente. Bloquea Fase 3.
- **Fuentes Alda Pro / Effra Pro**: opcionales — Georgia/Tahoma están aplicados (autorizadas oficialmente por manual SMNYL p. 75).

Plan completo aprobado: `C:\Users\alber\.claude\plans\lee-el-archivo-claude-md-http-claude-md-dapper-giraffe.md`.
