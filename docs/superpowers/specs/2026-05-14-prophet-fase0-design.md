# Diseño — Módulo Prophet Fase 0

**Fecha:** 2026-05-14  
**Proyecto:** DocuMente — SMNYL  
**Alcance:** Fase 0 del módulo Prophet para Modelos Actuariales (MA)  
**Estado:** Aprobado por Alberto Solano

---

## Contexto y motivación

El área de Modelos Actuariales (MA) necesita documentar sus modelos Prophet con un esquema estandarizado: propósito, dueños, corridas, variables críticas, inputs, supuestos y matriz de conocimiento técnico. El Excel existente (`Registro Modelos_envioAlberto.xlsx`) ya contiene esta información pero en formato no estructurado ni auditeable.

**Objetivo de Fase 0:** poner algo funcionando en manos de MA en ~1 semana. Importar el Excel existente → generar fichas Prophet individuales pre-pobladas → permitir edición y exportación a DOCX con marca SMNYL. Demo con Carmona, Cynthia Flores y Juan Carlos Magallanes.

**Fase 1 (condicional a feedback positivo):** registro maestro relacional, índice del área, multi-owner concurrente, grafo de dependencias — fuera de scope de Fase 0.

---

## Decisiones de diseño

| Pregunta | Decisión | Razón |
|---|---|---|
| Unidad de documentación | Ficha por modelo individual | Índice del área → Fase 1 |
| Usuarios de la app | Los 3 dueños directamente (Carmona, Cynthia, Magallanes) | Requiere UX pulida, sin jerga técnica |
| Matriz de conocimiento | Incluida en la ficha como sección 12 | Parte del entregable de documentación |
| Prioridad | Alta, sin deadline duro | Va en paralelo con Vidal/AWS |
| Import del Excel | Selección individual de modelo (no batch) | Un modelo por sesión de importación |
| Punto de entrada en Home | Tercer botón "Iniciar Ficha Prophet" | Sin selector de template; directo al flujo Prophet |
| Experiencia de edición | Página completa por sección (no modal) | Tablas de 30+ runs necesitan espacio |
| LLM en import | No — openpyxl directo | Excel bien estructurado; sin costo ni latencia LLM |
| Modelo de datos | Reusar `Documento` con `tipo="prophet"` | Sin cambio de schema SQLite; reusa todo el stack |
| Multi-user | `user_id="default"` igual que MVP | Limitación documentada; Fase 1 agrega auth si necesario |

---

## Arquitectura

Prophet Fase 0 se integra en las capas existentes de DocuMente sin modificar nada del flujo MRM:

```
UI Layer
  src/ui/pages/crear_prophet.py        ← entry + Excel upload + selector modelo
  src/ui/pages/editar_seccion_prophet.py ← editor pantalla completa (tabla o textarea)
  src/ui/pages/home.py                 ← +1 botón "Iniciar Ficha Prophet"
  app.py                               ← +2 rutas nuevas

Application Layer
  src/core/usecases/detectar_modelos_prophet.py
  src/core/usecases/importar_registro_prophet.py
  src/core/usecases/docx_writer_prophet.py

Domain Layer
  src/core/template_catalog_prophet.py ← 12 secciones (catálogo independiente)
  src/core/models/documento.py         ← SIN cambios (tipo="prophet" ya soportado)

Infrastructure
  src/docs/templates/prophet_model_doc_smnyl.docx ← template Word nuevo
  src/core/usecases/__init__.py        ← exports nuevos
```

**Regla de capas:** idéntica al resto del proyecto. Dominio no importa de UI ni Infra.

**Datos estructurados:** las tablas de Runs, Variables, Inputs y Skills se almacenan como JSON en `Seccion.contenido` (string). El writer Prophet deserializa y renderiza. Sin cambio de schema SQLite.

---

## Catálogo de secciones Prophet (12 secciones)

| # | `section_id` | Nombre visible | Tipo | Obligatoria |
|---|---|---|---|---|
| 1 | `identificacion` | Identificación del modelo | campos simples | Sí |
| 2 | `objetivo_alcance` | Objetivo y alcance | texto | Sí |
| 3 | `responsables_roles` | Responsables y roles | tabla | Sí |
| 4 | `corridas_runs` | Corridas (Runs) | tabla | Sí |
| 5 | `variables_criticas` | Variables críticas | tabla | Sí |
| 6 | `inputs_dependencias` | Inputs y dependencias | tabla | Sí |
| 7 | `supuestos` | Supuestos relevantes | texto | Sí |
| 8 | `outputs_reportes` | Outputs y reportes | tabla | Sí |
| 9 | `componentes_librerias` | Componentes y librerías Prophet | texto | No |
| 10 | `historial_cambios` | Historial de cambios | tabla | Sí |
| 11 | `limitaciones_riesgos` | Limitaciones y riesgos | texto | No |
| 12 | `matriz_conocimiento` | Matriz de conocimiento técnico | tabla | Sí |

**Tipos de contenido:**
- `campos`: inputs individuales mapeados directamente desde el Excel (sección 1)
- `tabla`: JSON array of dicts — editable con add/remove filas
- `texto`: textarea libre

---

## Flujo de importación del Excel

```
crear_prophet.py
  1. Usuario sube Registro_Modelos_*.xlsx
  2. DetectarModelosProphet.ejecutar(xlsx_bytes)
       └─ Lee hoja Descripcion_General
       └─ Devuelve list[tuple[int, str, str]]  # (fila_idx, nombre_modelo, encargado)
  3. UI muestra selectbox con los modelos detectados
  4. Usuario selecciona modelo → click "Importar"
  5. ImportarRegistroProphet.ejecutar(xlsx_bytes, fila_idx)
       ├─ Hoja Descripcion_General[fila_idx] → secciones 1, 2, 6 (parcial)
       ├─ Hoja Detalle Runs (filtrado por corridas del modelo) → sección 4
       ├─ Hoja Variables criticas (filtrado por corridas del modelo) → sección 5
       └─ Hoja Conocimiento_Tecnico (completa) → sección 12
       └─ Crea Documento(tipo="prophet", user_id="default") + Secciones
       └─ Persiste en SQLite vía DocumentoRepository
  6. Navega a dashboard del documento creado
```

**Mapeo de hojas:**

| Hoja Excel | Columnas clave | → Secciones |
|---|---|---|
| `Descripcion_General` | Area, Proceso, Encargado, Corridas, Descripcion, Variables involucradas, Supuestos que se actualizan, Frecuencia, Insumo, Área encargada, Tiempo de ejecución, Qué problema ataca | 1, 2, 6 (parcial) |
| `Detalle Runs` | # corrida, Detalle, Corrida Precedente, Es ALM?, Tiempo de ejecución, Outputs Principales, Variables críticas, Responsable | 4 |
| `Variables criticas` | Corrida, Nombre, Descripción, Fórmula, Frecuencia de actualización, Responsable de la info, Variables dependientes | 5 |
| `Conocimiento_Tecnico` | Persona × 18 capacidades × nivel | 12 |

**Secciones vacías tras import** (el dueño las llena en app): `supuestos` (7), `outputs_reportes` (8), `componentes_librerias` (9), `historial_cambios` (10), `limitaciones_riesgos` (11).

**Tolerancia a errores:** columna o hoja faltante → sección queda `completitud="vacia"` con mensaje descriptivo. El import nunca lanza excepción al usuario — degrada graciosamente.

**Validación de headers:** `ImportarRegistroProphet` valida los nombres de columna esperados al abrir cada hoja. Si hay discrepancia, registra advertencia en el resultado (no excepción) y muestra al usuario: *"La columna 'Responsable' no encontrada en 'Detalle Runs' — esa sección quedará parcial."*

---

## Experiencia de edición (formularios)

Después del import el usuario llega al **dashboard existente** (misma pantalla que MRM). Cada sección Prophet tiene un botón "Editar" que navega a `editar_seccion_prophet.py`.

### Editor de tabla (`tipo_contenido == "tabla"`)
- Tabla completa en pantalla con todas las columnas de la sección
- Botón **"+ Agregar fila"** agrega fila vacía al final
- Cada fila tiene botones **✏️ Editar** (inline edit de celdas) y **🗑 Eliminar**
- Botón **"Guardar cambios"** serializa la tabla a JSON y actualiza `Seccion.contenido` + registra evento `seccion_actualizada` en audit trail
- Botón **"← Volver al dashboard"** descarta cambios no guardados (con confirmación)

### Editor de texto (`tipo_contenido == "texto"`)
- Textarea amplia (mismo patrón que secciones MRM)
- Sin LLM en Fase 0 — el dueño escribe directamente
- Guardar actualiza `Seccion.contenido` + audit trail

### Editor de campos (`tipo_contenido == "campos"`) — sección `identificacion`
- Formulario con inputs individuales: Nombre del modelo, Área, Proceso, Encargado principal, Frecuencia de uso, Ruta del modelo, Tiempo de ejecución
- Pre-llenado desde el Excel
- Guardar serializa a JSON estructurado

**Completitud Prophet:** una sección tabla/campos se considera `completa` cuando tiene al menos 1 fila/valor. Una sección texto se considera `completa` cuando tiene ≥ 50 caracteres. Las secciones `No obligatorias` pueden omitirse sin afectar el estado del documento.

---

## Template DOCX Prophet

Archivo: `src/docs/templates/prophet_model_doc_smnyl.docx`

Diseñado manualmente en Word con marca SMNYL (paleta NYL Blue / Steel / Iron, tipografías Georgia/Tahoma). `docxtpl` rellena placeholders — misma estrategia que la plantilla MRM.

**Placeholders simples:** `{{ nombre_modelo }}`, `{{ area }}`, `{{ proceso }}`, `{{ encargado_principal }}`, `{{ frecuencia_uso }}`, `{{ objetivo }}`, `{{ supuestos }}`, `{{ componentes }}`, `{{ limitaciones }}`

**Table loops (4):**
```
{% for run in runs %}
{% for var in variables_criticas %}
{% for inp in inputs_dependencias %}
{% for skill in skills_matrix %}
```

**Pie de página:** "Borrador asistido — requiere revisión humana · DocuMente v{version} · {fecha}"

**Writer dedicado:** `docx_writer_prophet.py` con método `render(documento: Documento) -> bytes`. No modifica ni importa `docx_writer.py` (MRM).

---

## Entregables de soporte para MA

| Entregable | Archivo | Cuándo |
|---|---|---|
| Template Excel | `docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx` | Con Fase 0 |
| Guía de llenado | `docs/Modulo Prophet MA/Guia_Llenado_Registro.md` | Con Fase 0 |
| Video/tutorial | Por grabar | Post-demo con MA |

El template Excel incluye: nombres de hojas exactos, headers con formato visual, una fila de ejemplo por hoja, comentarios en celdas críticas ("no modificar este header").

---

## Tests

**Baseline:** 236/236 tests pasan. Meta al cierre de Fase 0: ~256 tests.

| Archivo de test | Casos clave |
|---|---|
| `test_template_catalog_prophet.py` | 12 secciones presentes; `section_id` únicos; `tipo_contenido` válido; obligatorias correctas |
| `test_importar_registro_prophet.py` | Excel fixture completo → secciones pobladas; columna faltante → sección vacía sin excepción; hoja faltante → degrada graciosamente; modelo inexistente → error descriptivo |
| `test_detectar_modelos_prophet.py` | Excel con 2 modelos → lista de 2 items; Excel sin hoja → error descriptivo |
| `test_docx_writer_prophet.py` | Documento con runs → DOCX contiene tabla de runs; sección vacía → marcador "[Pendiente]"; export retorna bytes |
| `test_editar_seccion_prophet.py` (UI) | Guardar tabla actualiza `Seccion.contenido`; audit trail registra evento; volver sin guardar no modifica |

---

## Archivos nuevos y modificados

### Nuevos (15 archivos)
- `src/core/template_catalog_prophet.py`
- `src/core/usecases/detectar_modelos_prophet.py`
- `src/core/usecases/importar_registro_prophet.py`
- `src/core/usecases/docx_writer_prophet.py`
- `src/ui/pages/crear_prophet.py`
- `src/ui/pages/editar_seccion_prophet.py`
- `src/docs/templates/prophet_model_doc_smnyl.docx`
- `src/llm/prompts/prophet_gaps.py` (stub vacío — Fase 1)
- `docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx`
- `docs/Modulo Prophet MA/Guia_Llenado_Registro.md`
- `tests/unit/test_template_catalog_prophet.py`
- `tests/unit/test_importar_registro_prophet.py`
- `tests/unit/test_detectar_modelos_prophet.py`
- `tests/unit/test_docx_writer_prophet.py`
- `tests/unit/test_editar_seccion_prophet.py`

### Modificados (3 archivos)
- `src/ui/pages/home.py` — tercer botón "Iniciar Ficha Prophet"
- `app.py` — rutas `crear_prophet` y `editar_seccion_prophet`
- `src/core/usecases/__init__.py` — exports nuevos

### NO se toca
- `src/core/template_catalog.py` (MRM, congelado)
- `src/core/models/documento.py` (schema sin cambios)
- `src/core/usecases/docx_writer.py` (writer MRM, intacto)
- Todos los use cases MRM existentes

---

## Limitaciones documentadas (Fase 0)

1. **Single-user:** `user_id="default"`. Los 3 dueños comparten la instancia local. Edición concurrente real → Fase 1 con auth.
2. **Sin LLM en edición:** las secciones narrativas (supuestos, limitaciones) se llenan manualmente. LLM assist → Fase 1 si el feedback lo justifica.
3. **Sin índice del área:** cada ficha vive independiente. Registro maestro relacional → Fase 1.
4. **Import desde Excel local:** no hay integración con SharePoint ni OneDrive. El dueño descarga el Excel y lo sube a la app.
5. **Sin versionado de ficha:** el historial de cambios es manual (el dueño lo llena). Versionado automático por periodo → Fase 1.

---

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Excel de MA no tiene los headers exactos esperados | Validación con mensajes descriptivos + template Excel de referencia |
| Skills Matrix (18 columnas) demasiado ancha para el DOCX | Font 7pt + columnas angostas, igual que tablas densas del writer MRM |
| Sobre-ingeniería de Fase 1 sin validar Fase 0 | No construir Fase 1 sin feedback positivo de la demo con MA |
| Información sensible (fórmulas de modelos productivos) commiteada al repo | Validar con MA qué puede ir a GitHub; datos reales en `.gitignore` si necesario |
