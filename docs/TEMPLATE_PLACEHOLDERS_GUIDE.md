# Guía paso a paso — Placeholders Jinja en plantilla maestra

> Esta guía te lleva por la edición manual de la plantilla maestra `.docx` que el `DocxWriter` rellenará en Fase 3. Toma ~30-45 minutos. **No requiere conocimientos técnicos** — solo Word.

---

## Antes de empezar

1. **Copia el archivo fuente** (NO edites el original):
   - Origen: `SMNYL/Templates/NYL Model Development Template.docx`
   - Destino: `src/docs/templates/model_development_smnyl.docx`
   - Crea la carpeta `templates/` si no existe.

2. **Abre la copia en Word.**

3. **Sintaxis básica de los placeholders:**
   - **Variables simples**: las escribes tal cual donde quieras que aparezca el valor. Ej. `{{ nombre_modelo }}`. Cuando exportes, esa cadena exacta se reemplaza con el valor.
   - **Loops en filas de tabla**: `{%tr for v in versiones %}` al inicio de la fila que se repite, y `{%tr endfor %}` al final. Estos van en una **fila propia** (Word: clic derecho → "Insertar fila arriba/abajo" para crear filas vacías solo para los marcadores).
   - **Importante**: los placeholders son **texto normal** que escribes con tu teclado. No son campos, ni código, ni nada especial. Solo texto. Word los respeta como cualquier otra palabra.

4. **Tip**: usa `Ctrl+F` (Buscar) en Word para encontrar rápidamente los textos que mencionamos abajo.

---

## Paso 1 — Portada (3 reemplazos)

Buscar en la portada y reemplazar **el texto entre comillas tipográficas** (no las comillas):

| Texto a buscar (aprox.) | Reemplazar con |
|---|---|
| `Name of model: e.g. "UL Rebuild Model"` → la parte de `"UL Rebuild Model"` | `{{ nombre_modelo }}` |
| `Prepared by: "Author"` → la parte de `"Author"` | `{{ preparado_por }}` |
| `Date: "Date of documentation completion"` → la parte entre comillas | `{{ fecha_export }}` |

También puedes borrar la línea `February 13, 2019` si quieres (no es necesaria — es la fecha del template).

---

## Paso 2 — Tabla 1.1 Model Profile (la tabla grande de la primera página)

Esta tabla tiene 2 columnas. La columna izquierda son etiquetas (`Model Name`, `Model ID`, etc.). La **derecha está vacía o con texto guía**: ahí van los placeholders.

En la columna derecha, **reemplaza el contenido de cada celda** con el placeholder correspondiente:

| Etiqueta (columna izquierda) | Placeholder (columna derecha) |
|---|---|
| Model Name | `{{ nombre_modelo }}` |
| Model ID | `{{ model_id }}` |
| Model Class | `{{ model_class }}` |
| Profit Center | `{{ profit_center }}` |
| BU Executive (FAE) | `{{ fae }}` |
| Model Owner | `{{ model_owner }}` |
| Model Developer(s) | `{{ model_developers }}` |
| Current Model Version | `{{ current_version }}` |
| Implementation Platform | `{{ implementation_platform }}` |
| Financial Impact | `{{ financial_impact }}` |
| Inherent Risk Tier | `{{ inherent_risk_tier }}` |

> Si la tabla tiene filas adicionales que no aparecen aquí (ej. *Model Status*, *Target Production Date*), agrégalas con: `{{ model_status }}`, `{{ target_production_date }}`, `{{ intended_use }}`, `{{ use_restrictions }}`. Si no las tiene, no pasa nada.

---

## Paso 3 — Tabla 1.2 Version Control (loop de filas)

La tabla de Version Control tiene **header** (Version No., Date Changed, Updated By, Approved By, Description) y filas de ejemplo abajo.

**Lo que vas a hacer:** convertir la fila de ejemplo en un loop que se repita por cada versión que el sistema registre.

1. Identifica la fila de **encabezado** (Version No. | Date Changed | etc.). **No la toques.**
2. Identifica la primera fila de datos (puede tener "1.0" o estar vacía).
3. **Inserta una fila arriba** de esa fila de datos (clic derecho → Insertar → Filas arriba). En la primera celda de esa nueva fila escribe:
   ```
   {%tr for v in versiones %}
   ```
4. En la fila de datos, reemplaza el contenido de las celdas:
   - Versión No. → `{{ v.version }}`
   - Date Changed → `{{ v.fecha }}`
   - Updated By → `{{ v.actor }}`
   - Approved By → `{{ v.aprobado_por }}`
   - Description → `{{ v.descripcion }}`
5. **Inserta otra fila debajo** de la fila de datos. En la primera celda escribe:
   ```
   {%tr endfor %}
   ```
6. Si había más filas de ejemplo después, **bórralas** — el loop se encarga de generar todas las que hagan falta.

**Resultado:** la tabla quedará con 1 header + 1 fila de loop start + 1 fila de placeholders + 1 fila de loop end. Cuando se exporte, docxtpl repetirá la fila intermedia tantas veces como versiones haya.

---

## Paso 4 — Las 28 secciones de contenido (lo más extenso)

Para **cada sección** del template (1.3, 2.1, 2.2, …, 9), busca el heading y **reemplaza el texto guía gris** (las descripciones tipo *"This section captures…"* o las instrucciones de qué llenar) con un placeholder único.

> **Mantén el heading intacto** (ej. `1.3 Problem Statement` se queda igual). Solo reemplazas el texto descriptivo/guía que viene **después** del heading.

| Heading en el .docx | Placeholder a colocar (después del heading) |
|---|---|
| 1.3 Problem Statement | `{{ s_1_3 }}` |
| 2.1 Model Uses | `{{ s_2_1 }}` |
| 2.2 Model Scope | `{{ s_2_2 }}` |
| 2.3 Business Impact of Model Usage | `{{ s_2_3 }}` |
| 3.1 Ancillary document list | `{{ s_3_1 }}` |
| 3.2 Additional Documents | `{{ s_3_2 }}` |
| 4.1 Schematic Diagram | `{{ s_4_1 }}` |
| 4.2 Model Theory and Logic | `{{ s_4_2 }}` |
| 4.3 Key Risk Drivers | `{{ s_4_3 }}` |
| 4.4 Key Assumptions | `{{ s_4_4 }}` |
| 5.1 Raw Data Sources and Data Quality | `{{ s_5_1 }}` |
| 5.2 Upstream Models & Company Determined Assumptions | `{{ s_5_2 }}` |
| 5.3.1 Data Aggregations | `{{ s_5_3_1 }}` |
| 5.3.2 Segmentations | `{{ s_5_3_2 }}` |
| 5.3.3 Use of Averages or Proxies | `{{ s_5_3_3 }}` |
| 5.4 Known Input and Data Limitations | `{{ s_5_4 }}` |
| 5.5 Record of Input Changes or Decisions Made | `{{ s_5_5 }}` |
| 6.1 Specification Process | `{{ s_6_1 }}` |
| 6.2 Approach Used | `{{ s_6_2 }}` |
| 6.3 Development Testing | `{{ s_6_3 }}` |
| 6.4 Limitations Revealed During Testing | `{{ s_6_4 }}` |
| 6.5 Record of Process Changes | `{{ s_6_5 }}` |
| 7.1 Platform | `{{ s_7_1 }}` |
| 7.2 Model Runs | `{{ s_7_2 }}` |
| 7.3 Performance Testing | `{{ s_7_3 }}` |
| 7.4 Production and Performance Limitations | `{{ s_7_4 }}` |
| 8 Model Governance | `{{ s_8 }}` |
| 9 On-going Monitoring | `{{ s_9 }}` |

> Si el template tiene tablas dentro de alguna sección (ej. tabla de upstream models en 5.2, tabla de input changes en 5.5), **déjalas tal cual** por ahora. El `DocxWriter` insertará el contenido textual de la sección como párrafos al lado, no las modifica. En la sesión de pulido formal de plantilla las reemplazaremos por loops.

---

## Paso 5 — Pie del documento (opcional pero recomendado)

Al final del documento, agrega una nota de status explícita. Esta línea ayuda a leerlo correctamente:

```
Estado del documento: {{ estado_documento }} · Generado: {{ fecha_export }}
```

Y, si quieres una nota de "borrador asistido":

```
Documento generado con asistencia de DocuMente. Revisión humana requerida antes de uso oficial.
```

---

## Paso 6 — Guarda y verifica

1. Guarda el archivo: `Ctrl+S`. Asegúrate que está en `src/docs/templates/model_development_smnyl.docx`.
2. **Verifica visualmente** que los placeholders quedaron escritos correctamente. Cada uno debe aparecer en el texto como `{{ nombre_modelo }}` (con las dobles llaves).
3. **No deben quedar placeholders rotos** del tipo `{ { x } }` o sin las dos llaves de cierre. docxtpl es estricto: si falta una llave, falla la generación.

---

## Lista de verificación final

- [ ] La copia está en `src/docs/templates/model_development_smnyl.docx`
- [ ] Portada: 3 reemplazos hechos (`nombre_modelo`, `preparado_por`, `fecha_export`)
- [ ] Tabla 1.1 Model Profile: al menos 11 placeholders en columna derecha
- [ ] Tabla 1.2 Version Control: filas de loop `{%tr for v in versiones %}` y `{%tr endfor %}` agregadas
- [ ] 28 secciones: cada una con su placeholder `{{ s_X_Y }}` después del heading
- [ ] (Opcional) Pie con estado/fecha
- [ ] Guardaste sin errores
- [ ] Visualmente las dobles llaves están bien escritas

---

## Cuando termines

Avísame y yo implemento `DocxWriter` + un test de exportación que valide que tu doc de prueba se renderiza correctamente. Si algún placeholder está mal escrito, el test te lo dirá con un mensaje claro y te indicaré exactamente cuál ajustar.
