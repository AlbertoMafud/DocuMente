# PROPHET_FASE0_AUDIT — qué cubre DocuMente hoy vs lo que necesita MA

> Documento de inventario para preparar la conversación con Modelos
> Actuariales (MA). NO modificar el código de Prophet hasta tener
> alineación con MA. Ver `PROPHET_AGENDA_MA.md` para la agenda.

## TL;DR

**Cubre hoy (~30%):** ficha por modelo individual con 12 secciones,
importar registro Excel de MA, exportar DOCX básico con marca SMNYL,
detectar múltiples modelos en un registro.

**No cubre (gap principal):** governance multi-modelo (inventario,
tiering, owner, contabilidad), matrices de cambios entre versiones,
extracción de código Prophet, integración con el process de attestation,
visión "one model" integrado.

**Conclusión**: el módulo Fase 0 sirve como punto de partida para
documentar UN modelo aislado. Lo que MA necesita para su governance
es una capa superior — un sistema de inventario + change logs + impact
analysis que orquesta múltiples fichas individuales.

---

## Lo que existe en código hoy

### Backend

| Archivo | Qué hace |
|---|---|
| `src/core/template_catalog_prophet.py` | Define 12 secciones del template Ficha Prophet (ver detalle abajo). |
| `src/core/usecases/importar_registro_prophet.py` | Lee un Excel "Registro de Modelos Actuariales" (formato MA actual) y extrae modelos detectados. |
| `src/core/usecases/detectar_modelos_prophet.py` | LLM-assisted: detecta qué hojas/rangos del Excel son modelos individuales. |
| `src/core/usecases/docx_writer_prophet.py` | Renderiza la ficha como DOCX con marca SMNYL (12 secciones, sin loops avanzados). |
| `src/docs/templates/prophet_model_doc_smnyl.docx` | Template DOCX base. Existe pero no está pulida ni tiene loops docxtpl avanzados (matrices de cambios, etc.). |
| `src/api/routers/prophet.py` | Endpoints: detectar, importar, listar modelos, ficha individual. |

### Frontend Next.js

| Ruta | Función |
|---|---|
| `/prophet` (Beta) | Página de upload de registro Excel → detecta modelos → importa |
| `/documentos/{id}` (cuando `tipo=prophet`) | Dashboard genérico con `SeccionesPlanas` (sin agrupar por capítulo) |
| `/documentos/crear` | Permite crear ficha Prophet desde cero (12 secciones vacías) |

### Las 12 secciones del template Ficha Prophet actual

| # | Sección | Tipo |
|---|---|---|
| 1 | Identificación del modelo | campos |
| 2 | Objetivo y alcance | texto |
| 3 | Responsables y roles | tabla (persona, rol, área) |
| 4 | Corridas (Runs) | tabla |
| 5 | Variables críticas | tabla |
| 6 | Inputs y dependencias | tabla |
| 7 | Supuestos relevantes | texto |
| 8 | Outputs y reportes | tabla |
| 9 | Componentes y librerías Prophet | texto |
| 10 | Historial de cambios | tabla |
| 11 | Limitaciones y riesgos | texto |
| 12 | Matriz de conocimiento técnico | tabla |

---

## Gap analysis — comparando contra lo que MA reportó

### B2.1 — Múltiples áreas dueñas, modelos heterogéneos

> "En Actuaría existen varios modelos de Prophet, cuyo owner es un área
> distinta: Valuación de Reservas tiene sus modelos propios para cada
> contabilidad (3: STAT, MSTAT, GAAP); Business Plan; Rentabilidad de
> Productos (NIL); Planeación Financiera (Capital); Inversiones; Pricing."

**Cubre hoy:** la ficha individual sí tiene campos de "Responsables y
roles" (sección 3) y de "Identificación" (sección 1).

**No cubre:**
- Concepto explícito de **contabilidad** (STAT / MSTAT / GAAP / IFRS17)
  como atributo del modelo. Hoy es texto libre en "Identificación".
- Concepto de **propósito/categoría del modelo** (Valuación / BP /
  Pricing / Capital / ALM / Inversiones) como atributo estructurado.
  Hoy es texto libre.
- **Vista de inventario consolidada** — no hay pantalla que muestre
  "todos los modelos de Valuación STAT con owner X".

**Acción S17+:** agregar a `MetadataModelo` (o equivalente Prophet) los
campos `contabilidad` (enum) y `proposito_modelo` (enum). Crear vista
`/prophet/inventario` con filtros.

### B2.2 — Variables y metodologías difieren entre modelos del mismo concepto

> "Pueden modelar el mismo concepto pero con variables y metodologías
> diferentes, pues cada quien lo codificó como quiso."

**Cubre hoy:** la sección 5 "Variables críticas" es una tabla libre por
modelo — captura las variables de CADA modelo individualmente.

**No cubre:**
- **Comparación cross-model**: ¿cuántos modelos tienen una variable
  llamada "X"? ¿con qué metodologías distintas?
- **Diccionario global de variables** con sinónimos y mapping.
- **Detección de duplicados/inconsistencias** entre modelos.

**Acción S17+:** vista `/prophet/variables` con búsqueda global. Posible
LLM-assisted clustering de variables semánticamente equivalentes con
nombres distintos.

### B2.3 — Governance estricta: cambios, productos, variables, código, impacto

> "Tienen la idea de que registre cambios entre modelos, cambios a los
> propios productos, registro de nuevos productos y variables, cambios
> a variables registrando sus razones de cambio, los propios cambios en
> el código, a qué modelos impacta y las configuraciones necesarias."

**Cubre hoy:**
- Sección 10 "Historial de cambios" (tabla libre) en cada ficha.
- Audit trail general del documento (eventos del sistema).
- Versionado: snapshots inmutables (S16 funcional con ver/descargar/restaurar).

**No cubre:**
- **Change log estructurado** con campos: variable_afectada,
  metodologia_antes, metodologia_despues, razon, modelos_impactados,
  fecha_efectiva, aprobador.
- **Impact analysis matrix** (qué modelos comparten variables y qué se
  rompe si X cambia).
- **Linkeo de cambios entre fichas distintas** (un cambio en variable X
  afecta a modelos A, B y C — se debe reflejar en las 3 fichas).
- **Vinculación a tickets/aprobaciones** (Jira, ServiceNow, email).

**Acción S17+:** módulo separado `ChangeLog` con tabla relacional
(no JSON dentro de la ficha). Cada change tiene N modelos asociados
(M:N), categoría (variable/metodología/código/producto/configuración) y
estado (propuesto/aprobado/implementado/revertido).

### B2.4 — Visión "one model" integrado a largo plazo

> "A largo plazo, ellos absorber más el governance de los modelos y
> crear un 'one model' que sea un modelo integrado de todo."

**Cubre hoy:** Nada relacionado.

**No cubre:** Concepto enteramente fuera del alcance actual.

**Acción S17+:** explícitamente **no se trabaja en S16**. Cuando MA
defina mejor qué significa "one model" (¿una pantalla agregada?
¿un modelo Prophet real consolidado?), se diseña. Probablemente sea
una vista del inventario que mapea variables comunes + diferencias
metodológicas — no requiere cambios al modelo de datos central.

### B2.5 — Documentación rica: matrices, texto, capturas, código, impactos

> "La documentación puede incluir matrices de cambios, texto, razones,
> motivos, capturas de pantallas, extractos de código, registro de
> impactos."

**Cubre hoy:**
- Texto libre: ✅ (todas las secciones de tipo "texto")
- Tablas: ✅ (secciones "tabla" con schema fijo)
- **Capturas de pantalla**: ✅ ahora (S16) — visión Claude describe
  imágenes embebidas en PDFs/DOCX cargados como fuentes.
- **Apéndices** (PDFs, Excel multi-hoja, fórmulas LaTeX): ✅ desde S13.

**No cubre:**
- **Extractos de código Prophet** con tabla estructurada:
  `Variable / Definición / Fórmula / Dependencias / Comentarios`
- **Renderizado del código** preservando indentación / sintaxis Prophet.
- **Matriz de cambios** con loops docxtpl en el template DOCX
  (`{% for cambio in cambios %}...{% endfor %}`).

**Acción S17+:** D.1.a en el plan original — rediseñar el template
DOCX Prophet con loops docxtpl. Diseñar el modelo de datos para
"extracto de código" (probablemente como un tipo de apéndice nuevo
con renderizado monospace).

### B2.6 — Templates en construcción (bajo/alto impacto)

> "Están desarrollando (y me compartirán) un template en word y excel
> para registrar los cambios de bajo impacto a los modelos y otro para
> los de alto impacto."

**Cubre hoy:** Nada explícito de tiering bajo/alto impacto.

**Esto es lo más importante en la conversación con MA**: sus templates
en construcción son el target real al que debe alinearse DocuMente.
Sin verlos primero, cualquier diseño es especulativo.

**Acción inmediata (no código):** pedir a MA los templates en estado
borrador (con tracked changes incluso) y mapear cada campo al modelo
de datos de DocuMente.

### B2.7 — Matrices de variables (ruta de tablas, razones, cómo)

> "Las matrices de cambios quieren que registren cada variable, la ruta
> de las tablas, las razones de cambio y el cómo."

**Cubre hoy:**
- Sección 5 "Variables críticas" — tabla simple.
- Sección 6 "Inputs y dependencias" — tabla.

**No cubre:**
- Schema enriquecido por variable: `ruta_tabla` (path en Prophet),
  `razon_cambio`, `como_se_implementa`, `version_modelo_antes`,
  `version_modelo_despues`.
- Esto es esencialmente un superset de la sección 5 actual, con
  campos adicionales y vinculación al ChangeLog (B2.3).

**Acción S17+:** extender schema de la tabla de variables. Confirmar
con MA qué campos van — probable diferencia entre Tier 1 (todos los
campos) y Tier 3 (solo nombre + definición).

### B2.8 — Inventario de todos los modelos Prophet

> "Generar un inventario de todos los modelos de Prophet."

**Cubre hoy:**
- Lista plana de documentos tipo Prophet en `/` (home).
- Importar registro Excel `/prophet` detecta múltiples modelos.

**No cubre:**
- **Vista de inventario dedicada** con columnas: nombre, área dueña,
  contabilidad, propósito, owner, tier, fecha última validación,
  estado MRM, n_cambios_ultimos_30d, etc.
- **Filtros y búsqueda** sobre el inventario.
- **Exportable a Excel** para reporting a stakeholders.

**Acción S17+:** crear `/prophet/inventario` como tabla virtualizada
(TanStack Table). Reusa los DocumentoListItem que ya existen, pero
filtrando `tipo=prophet` + agregando columnas Prophet-specific.

---

## Resumen — qué hacer en qué orden tras la reunión con MA

### Inmediato (post-reunión, S17)

1. **Recibir templates en construcción de MA**. Mapear cada campo al
   modelo de datos DocuMente. Identificar gaps.
2. **D.1.a** del plan S14: rediseñar template DOCX Prophet con marca
   SMNYL completa + 4 loops docxtpl (corridas, variables, cambios,
   matriz de conocimiento). Bloquea D.1.d (demo MA real).
3. **Agregar metadata Prophet estructurada**: contabilidad,
   proposito_modelo, tier — como enums. Migration aditiva.

### Medio plazo (S17-S19)

4. **Módulo ChangeLog** independiente con M:N a modelos.
5. **Vista `/prophet/inventario`** con filtros y búsqueda.
6. **Vista `/prophet/variables`** con búsqueda global.

### Largo plazo (S20+)

7. Concepto "one model" — diseño basado en lo que MA defina.
8. Integración con tickets externos (Jira) si así lo piden.

---

## Decisión técnica vigente

El módulo Prophet Fase 0 actual es funcional pero **NO se toca en S16**.
Las mejoras de S16 (markdown, idioma, sources con LLM, visión, versiones
funcionales) sí benefician a Prophet automáticamente porque comparten
infraestructura. El template DOCX Prophet específicamente queda
diferido hasta tener:

1. Los templates en construcción de MA en mano.
2. Decisión de tiering tomada con MA.
3. Lista de campos por sección consensuada.

Sin esos 3 inputs, rediseñar el template ahora desperdiciaría trabajo.
