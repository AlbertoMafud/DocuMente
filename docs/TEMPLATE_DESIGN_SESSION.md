# Sesión de diseño: plantilla maestra `model_development_smnyl.docx`

> Este archivo guía la sesión dedicada (Alberto + Claude) para diseñar manualmente en Word la plantilla maestra que `docxtpl` rellenará en runtime. Es el activo del que depende toda la calidad estética del DOCX exportado.

---

## Contexto que la sesión necesita cargar

1. Leer **`docs/BRAND_GUIDELINES.md`** completo — paleta exacta, tipografías (Georgia display / Tahoma body), reglas de logo, espaciado.
2. Leer **`docs/TEMPLATE_MODEL_DEV.md`** completo — las 32 secciones del template oficial NYL con sus IDs.
3. Abrir referencias visuales:
   - `SMNYL/Templates/NYL Model Development Template.docx` (estructura oficial NYL).
   - `SMNYL/Ejemplos actuales/M07.P07.S04.019.B Value of New Business.docx` (ejemplo real).
   - `SMNYL/Identidad de marca/SMNYL Guideline 2022 (1).pdf` (manual de marca).

---

## Output esperado

Un archivo `.docx` en `src/docs/templates/model_development_smnyl.docx` que:
- Tiene aplicada toda la marca SMNYL (logo, paleta, tipografías, espaciado).
- Contiene placeholders Jinja (sintaxis docxtpl: `{{variable}}`, `{%tr ... %}`, `{%for ... %}`) en cada lugar donde el contenido se va a inyectar dinámicamente.
- Conserva los estilos de párrafo, tablas con bordes correctos, header/footer, numeración de secciones.

---

## Procedimiento paso a paso (a ejecutar en la sesión dedicada)

### Paso 0 — Setup (5 min)
- Abrir Word.
- Cargar el `NYL Model Development Template.docx` original como base (Archivo → Abrir → Guardar Como → `src/docs/templates/model_development_smnyl.docx`).
- Activar la regla y guías de cuadrícula para alineación precisa.

### Paso 1 — Definir estilos de párrafo (15 min)
Crear/ajustar estilos de párrafo (Inicio → Estilos → Modificar):

| Estilo | Fuente | Tamaño | Color | Uso |
|---|---|---|---|---|
| `Title SMNYL` | Georgia | 32pt | Steel `#0a3c53` | Título de portada |
| `Subtitle SMNYL` | Tahoma | 14pt | Iron `#565656` | Subtítulos de portada |
| `Heading 1 SMNYL` | Georgia | 22pt | Steel `#0a3c53` | Secciones principales |
| `Heading 2 SMNYL` | Georgia | 16pt | Steel `#0a3c53` | Subsecciones |
| `Heading 3 SMNYL` | Tahoma | 13pt bold | Steel `#0a3c53` | Sub-subsecciones |
| `Body SMNYL` | Tahoma | 11pt | Steel `#0a3c53` | Cuerpo |
| `Caption SMNYL` | Tahoma | 9pt italic | Iron `#565656` | Pies de tabla/figura |
| `Table Header SMNYL` | Tahoma | 10pt bold | White sobre Blue `#0079c2` | Headers de tabla |
| `Table Cell SMNYL` | Tahoma | 10pt | Steel `#0a3c53` | Celdas de tabla |

### Paso 2 — Header y footer (10 min)
- **Header**: logo SMNYL (`assets/logo-smnyl.jpg`) en esquina superior izquierda, tamaño 2.5cm, fondo blanco. Línea horizontal Blue `#0079c2` 1pt debajo.
- **Footer**: nombre del modelo a la izquierda (placeholder `{{nombre_modelo}}`), número de página a la derecha (formato "Página X de Y").

### Paso 3 — Portada (10 min)
Diseñar la portada con placeholders:
```
{{nombre_modelo}}                    ← Title SMNYL
Model Development Documentation       ← Subtitle SMNYL
Template Type A                       ← Subtitle SMNYL

Preparado por: {{autor}}              ← Body SMNYL
Fecha: {{fecha_documentacion}}        ← Body SMNYL
Versión: {{version}}                  ← Body SMNYL

[Logo SMNYL grande centrado]
```

### Paso 4 — Tabla de atributos (sección 1.1) (10 min)
Crear tabla 2 columnas con bordes:
| Atributo | Valor |
|---|---|
| Model Name | `{{model_name}}` |
| Model ID | `{{model_id}}` |
| Model Class | `{{model_class}}` |
| Profit Center | `{{profit_center}}` |
| BU Executive (FAE) | `{{fae}}` |
| Model Owner | `{{model_owner}}` |
| Model Developer(s) | `{{model_developers}}` |
| Current Model Version | `{{current_version}}` |
| Implementation Platform | `{{platform}}` |
| Financial Impact | `{{financial_impact}}` |
| Model Status | `{{model_status}}` |
| Target Production Date | `{{target_prod_date}}` |
| Inherent Risk Tier | `{{inherent_risk_tier}}` |

Header row: fondo Blue `#0079c2`, texto blanco. Bordes Quartz `#bdc1c2` 0.5pt.

### Paso 5 — Tabla de Version Control (sección 1.2) (10 min)
Tabla con loop de docxtpl:
```
| Version No. | Date Changed | Updated By | Approved By | Description |
|-------------|--------------|------------|-------------|-------------|
| {%tr for v in version_history %} |
| {{v.version}} | {{v.date}} | {{v.updated_by}} | {{v.approved_by}} | {{v.description}} |
| {%tr endfor %} |
```

### Paso 6 — Estructura de secciones 1-9 con placeholders (45 min)
Para cada sección definida en `docs/TEMPLATE_MODEL_DEV.md`, insertar:
- Heading con número y nombre oficial (ej. "1.3 Problem Statement")
- Placeholder `{{seccion_1_3_problem_statement}}` debajo en estilo Body SMNYL

Mapeo completo de placeholders ↔ IDs de sección (32 placeholders en total — coincide con los IDs en `TEMPLATE_MODEL_DEV.md`):
- `{{seccion_1_3_problem_statement}}`
- `{{seccion_2_1_model_uses}}`
- `{{seccion_2_2_model_scope}}`
- `{{seccion_2_3_business_impact}}`
- `{{seccion_3_1_ancillary}}`
- `{{seccion_3_2_additional}}`
- `{{seccion_4_1_diagram}}` (con placeholder de imagen también)
- `{{seccion_4_2_theory}}`
- `{{seccion_4_3_risk_drivers}}`
- `{{seccion_4_4_assumptions}}`
- `{{seccion_5_1_raw_data}}`
- `{{seccion_5_2_upstream}}`
- `{{seccion_5_3_1_aggregations}}`
- `{{seccion_5_3_2_segmentations}}`
- `{{seccion_5_3_3_averages_proxies}}`
- `{{seccion_5_4_data_limitations}}`
- `{{seccion_5_5_input_changes}}` (loop tabla)
- `{{seccion_6_1_specification}}`
- `{{seccion_6_2_approach}}`
- `{{seccion_6_3_dev_testing}}`
- `{{seccion_6_4_limitations}}`
- `{{seccion_6_5_process_changes}}` (loop tabla)
- `{{seccion_7_1_platform}}`
- `{{seccion_7_2_runs}}`
- `{{seccion_7_3_perf_testing}}`
- `{{seccion_7_4_prod_limitations}}`
- `{{seccion_8_governance}}`
- `{{seccion_9_monitoring}}`

### Paso 7 — Validación visual (10 min)
- Abrir el `.docx` final junto al ejemplo real `M07.P07.S04.019.B Value of New Business.docx`.
- Comparar lado a lado: tipografía, colores, espaciado, tablas. Debe verse del mismo nivel (o mejor).

### Paso 8 — Test de templating (5 min)
Después de la sesión, Claude (modo código) ejecuta:
```python
from docxtpl import DocxTemplate
doc = DocxTemplate("src/docs/templates/model_development_smnyl.docx")
doc.render({
    "nombre_modelo": "Test Model XYZ",
    "autor": "Alberto Solano",
    "fecha_documentacion": "2026-05-05",
    "version": "1.0",
    "model_name": "Test Model XYZ",
    # ... resto de placeholders con texto dummy
    "version_history": [
        {"version": "1.0", "date": "2026-05-05",
         "updated_by": "Alberto", "approved_by": "—", "description": "Borrador inicial"},
    ],
})
doc.save("data/exports/test_render.docx")
```
Si renderiza sin errores y se ve igual de bien que la plantilla → plantilla validada.

---

## Tiempo total estimado: ~2 horas

Mejor distribuirlo en una sesión continua para mantener consistencia visual.

---

## Cómo arrancar la sesión

Cuando Alberto esté listo, abrir nueva sesión de Claude Code en este proyecto y decir:

> "Vamos a diseñar la plantilla maestra `.docx`. Lee `docs/TEMPLATE_DESIGN_SESSION.md` y guíame paso a paso."

Claude leerá este archivo, los archivos de contexto necesarios, y guiará la sesión.
