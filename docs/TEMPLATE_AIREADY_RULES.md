# Reglas de conversión: template humano → template AI-ready

> **Doble propósito de este documento:**
> 1. Es la **especificación del prompt** que usa el Template Studio cuando el LLM propone el catálogo de un template nuevo.
> 2. Es el **checklist de curación humana**: lo que el admin (o el usuario en Fase 2) verifica sección por sección antes de publicar.
>
> El lint de AI-readiness (`TEMPLATE_STUDIO_SPEC.md` §8) automatiza lo verificable de estas reglas; el criterio de fondo es humano.
>
> Los ejemplos "buenos" están tomados verbatim del catálogo real de Model Development (`src/core/template_catalog.py`) y de la Ficha Prophet (`src/core/template_catalog_prophet.py`) — los dos templates que ya funcionan en producción.

---

## La idea en una frase

Un template para humanos dice *dónde escribir*; un template AI-ready dice *qué conocimiento capturar, cómo preguntarlo y cómo reconocerlo*. La conversión consiste en agregar esa segunda capa a cada sección.

Cada sección AI-ready tiene siete atributos, y cada uno tiene su regla:

| # | Atributo | Regla |
|---|---|---|
| R1 | `id` | Un id estable por sección, para siempre |
| R2 | `intencion` | Qué conocimiento captura, no qué formato tiene |
| R3 | `preguntas_guia` | Las que haría un entrevistador experto del dominio |
| R4 | `aliases` | Cómo la gente nombra la sección en documentos reales |
| R5 | `obligatoria` | Con criterio, no por default |
| R6 | `tipo_contenido` | Texto, tabla o campos — y el esquema si es tabla |
| R7 | (estructura) | Granularidad correcta: una sección = una conversación |

---

## R1 — Una sección = un id estable

**Qué es.** Cada sección lleva un identificador tipo slug (`numero` + palabra clave semántica) que **nunca cambia** una vez asignado, aunque la sección se renombre, se traduzca o cambie de posición.

**Por qué importa.** El id es cómo el sistema "recuerda" una sección a través del tiempo: el contenido capturado, el estado de la entrevista, el audit trail y el mapeo en importaciones cuelgan del id. Si el id cambia, el sistema pierde la memoria de esa sección — contenido huérfano, entrevistas que arrancan de cero, trazabilidad rota.

**Ejemplo bueno** (catálogo MRM real):

```
id="4.4.assumptions"   →  sección "Key Assumptions"
id="9.monitoring"      →  sección "On-going Monitoring"
```

Slug corto, semántico, en minúsculas, anclado al número de sección.

**Ejemplo malo:**

```
id="seccion_7"          ← no dice nada; al reordenar, el "7" miente
id="Key Assumptions"    ← el nombre humano como id: se rompe al renombrar o traducir
id="4.4.assumptions_v2" ← versionar el id = cambiar el id = perder la memoria
```

**Regla operativa:** el id se asigna una vez, al crear la sección en el Studio. Reordenar cambia `numero`; renombrar cambia `nombre`; **nada** cambia `id`.

---

## R2 — Intención = qué conocimiento captura (no qué formato tiene)

**Qué es.** La `intencion` describe en una o dos frases **qué debe saberse** después de leer la sección: el conocimiento que captura, no su forma.

**Por qué importa.** La intención es el atributo más trabajador del catálogo: el motor de entrevista la usa para decidir qué preguntar; el analizador de brechas la usa para juzgar si el contenido realmente responde a lo que la sección pide (y no solo si hay texto); el redactor la usa para mantener el borrador enfocado. Una intención de formato ("aquí va una tabla") deja a los tres ciegos.

**Ejemplo bueno** (MRM, sección 1.3 Problem Statement):

> "Descripción de alto nivel del problema o necesidad que el modelo resuelve, incluyendo restricciones informacionales, computacionales o analíticas bajo las que se desarrolló."

Nombra el conocimiento (el problema que resuelve) **y** los matices que un experto esperaría (las restricciones de diseño).

**Ejemplo malo:**

> "Sección introductoria del documento."          ← describe posición, no conocimiento
> "Texto libre de aproximadamente dos párrafos."  ← describe formato
> "Descripción de la sección."                    ← circular; el lint lo marca (L7)

**Prueba rápida al curar:** tapa el nombre de la sección y lee solo la intención. ¿Un experto del dominio sabría qué contarte? Si no, reescríbela.

---

## R3 — Preguntas guía = las de un entrevistador experto del dominio

**Qué es.** De 2 a 4 preguntas que un especialista con años en el tema le haría al dueño del proceso para sacarle el conocimiento de esa sección — incluyendo lo que la gente olvida contar.

**Por qué importa.** Son el guion inicial de la entrevista. La diferencia entre una entrevista que se siente como hablar con un colega senior y una que se siente como llenar un formulario está aquí. Las buenas preguntas persiguen el "por qué" y las decisiones históricas — exactamente el conocimiento tácito que DocuMente existe para preservar.

**Ejemplo bueno** (MRM, sección 4.4 Key Assumptions):

> - "Para cada supuesto: ¿qué fuente lo respalda? ¿qué documento/study?"
> - "¿Cuáles son los rangos plausibles de cada supuesto?"
> - "¿Hay supuestos que se sospecha pueden necesitar revisión?"

Nótese la tercera: pregunta por la *duda* del experto — algo que nadie escribe espontáneamente y que vale oro en una auditoría.

Otro bueno (MRM, 4.2 Model Theory and Logic):

> - "¿Qué enfoques alternativos consideraste y por qué no los elegiste?"

Captura decisiones descartadas: el "por qué se hace así" que la documentación operativa nunca trae.

**Ejemplo malo:**

> - "Describe esta sección."                 ← no es una pregunta de experto, es un placeholder
> - "¿Qué quieres escribir aquí?"            ← delega el trabajo al entrevistado
> - "¿Cuáles son los supuestos?"             ← se queda en la superficie; falta fuente, rango, vigencia

**Regla operativa:** toda sección **obligatoria** lleva al menos 1 pregunta guía (lint L4). Las opcionales pueden apoyarse solo en la intención, pero una buena pregunta nunca sobra. Prueba al curar: ¿la pregunta la podría hacer alguien que *no* conoce el dominio? Si sí, no es de experto — profundízala.

---

## R4 — Aliases = cómo la gente nombra la sección en documentos reales

**Qué es.** La lista de títulos alternativos con los que esa sección aparece en documentos que ya existen en la institución: sinónimos, traducciones, variantes con numeración, nombres de la vieja plantilla.

**Por qué importa.** Cuando un usuario importa un documento existente, el sistema mapea cada encabezado del archivo contra los aliases del catálogo para saber a qué sección pertenece el contenido. Sin aliases, la importación solo reconoce el título exacto — y los documentos reales casi nunca usan el título exacto. Cada alias es una importación que funciona en lugar de una sección que queda vacía.

**Ejemplo bueno** (MRM, 1.3 Problem Statement):

```
aliases=("problem", "problema", "1. problem statement", "objetivo",
         "objetivo del modelo", "propósito")
```

Mezcla inglés/español, incluye la variante con numeración y los nombres con que los equipos realmente titulan esa sección ("Objetivo del modelo"). Otro bueno: la sección 9 On-going Monitoring incluye `"frecuencia de la revisión"` — así se llama esa sección en documentos legados reales, aunque el nombre oficial no se parezca en nada.

**Ejemplo malo:**

```
aliases=()                        ← importaciones frágiles (lint L9, advertencia)
aliases=("descripción", "general")  ← tan genéricos que colisionan con media docena
                                      de secciones (lint L5 si colisionan: error)
```

**Regla operativa:** un alias pertenece a **una sola** sección del catálogo (el lint bloquea colisiones). Fuente ideal de aliases: abre 2-3 documentos reales del tipo que se está templetizando y copia los encabezados tal como aparecen.

---

## R5 — Obligatoriedad con criterio

**Qué es.** `obligatoria=True` significa que el documento **no puede avanzar de estado** sin que esa sección esté completa u omitida con justificación explícita. No es una etiqueta decorativa: bloquea el flujo.

**Por qué importa.** Si todo es obligatorio, documentar se vuelve la tarea burocrática que DocuMente promete eliminar, y la gente rellena por rellenar. Si nada lo es, la completitud no significa nada y el documento no sirve para auditoría. La obligatoriedad bien puesta es lo que hace que "100% completo" sea una afirmación con valor.

**Ejemplo bueno** (catálogo MRM real): 22 de 28 secciones son obligatorias; las opcionales son exactamente las condicionales — 5.3.1 Data Aggregations, 5.3.2 Segmentations, 5.3.3 Use of Averages or Proxies ("si aplica"), 5.5 y 6.5 (bitácoras vivas), 3.2 Additional Documents. El patrón: **obligatorio lo que todo modelo tiene; opcional lo que solo algunos tienen.**

**Ejemplo malo:**

- Marcar las 14 secciones de un template como obligatorias "por si acaso" (lint L8, advertencia).
- Marcar opcional una sección que el marco de gobierno exige — la completitud reportará 100% sobre un documento inauditable.

**Regla operativa al curar:** por cada sección pregúntate "¿existe un caso legítimo de este tipo de documento donde esta sección no aplique?" Si sí → opcional. Si no → obligatoria. Recuerda que el usuario final siempre puede **omitir con motivo** una obligatoria que no aplique a su caso — la omisión justificada es una decisión documentada, no un hueco.

---

## R6 — Tipo de contenido: texto, tabla o campos

**Qué es.** Cada sección declara cómo se captura y se renderiza:

- **`texto`** — prosa: explicaciones, razonamiento, contexto.
- **`tabla`** — filas homogéneas con columnas fijas; exige declarar `schema_tabla` (las columnas).
- **`campos`** — pares etiqueta/valor: fichas de identificación, metadatos.

**Por qué importa.** El tipo decide tres cosas: cómo pregunta la entrevista (una tabla se entrevista fila por fila, no con prosa), cómo se valida (una tabla sin el esquema declarado no puede validarse), y cómo se exporta a Word (párrafos vs. tabla institucional vs. ficha de dos columnas). Un tipo mal elegido produce documentos donde la información correcta queda en el formato incorrecto — listas de responsables narradas en párrafos, imposibles de escanear.

**Ejemplo bueno** (Ficha Prophet real, sección 4 Corridas):

```
tipo_contenido="tabla",
schema_tabla=("numero", "detalle", "es_alm", "tiempo_ejecucion",
              "corrida_precedente", "outputs_principales", "responsable")
```

El esquema captura hasta la dependencia entre corridas (`corrida_precedente`) — conocimiento operativo que en prosa se perdería. Y la sección 1 (Identificación) usa `campos`, no tabla ni texto: nombre, área, encargado, frecuencia — pares etiqueta/valor puros.

**Ejemplo malo:**

```
tipo_contenido="tabla", schema_tabla=()      ← tabla sin columnas (lint L6: error)
tipo_contenido="texto"  para "Responsables y roles"  ← lista de personas narrada;
                                                        debería ser tabla (persona, rol, área)
```

**Regla operativa:** si al imaginar la sección llena ves renglones que se repiten con la misma estructura → `tabla`. Si ves una ficha de datos sueltos → `campos`. Solo si ves razonamiento y contexto → `texto`.

---

## R7 — Granularidad correcta: una sección = una conversación

**Qué es.** Cada sección debe cubrir **una unidad de conocimiento entrevistable de una sentada**: ni un capítulo entero comprimido, ni un párrafo inflado a sección.

**Por qué importa.** La entrevista opera sección por sección: una sección demasiado grande produce una conversación interminable que mezcla temas (y un gap analyzer que no puede decir *qué* falta, solo que "falta algo"); una demasiado chica produce decenas de micro-entrevistas burocráticas. La granularidad es el termostato de la fricción — y reducir fricción es el propósito del sistema.

**Ejemplo bueno** (catálogo MRM real): el tema "Datos" no es una sección — son seis (5.1 Raw Data, 5.2 Upstream Models, 5.3.1 Aggregations, 5.3.2 Segmentations, 5.3.3 Proxies, 5.4 Limitations), cada una con intención propia y entrevistable por separado. Para la navegación humana, las 28 secciones se agrupan en 9 capítulos — **la agrupación resuelve la UX; la separación resuelve la entrevista.** No hay que elegir.

**Ejemplo malo:**

- Sección "5. Datos" única con intención "todo lo relacionado con los datos del modelo" — la entrevista divaga, la brecha detectada es inservible ("los datos están incompletos" ¿qué parte?).
- Partir "Supuestos" en "Supuestos de mortalidad", "Supuestos de lapsos", "Supuestos de tasas", "Supuestos de gastos"… — si todas comparten las mismas preguntas guía, es **una** sección (quizá tipo tabla) con filas, no cuatro secciones.

**Prueba rápida al curar:**
- ¿La intención necesita la palabra "y" para unir dos temas que se preguntan distinto? → divídela.
- ¿Dos secciones contiguas tendrían las mismas preguntas guía? → fusiónalas.
- ¿La entrevista de esta sección tomaría más de ~15 minutos a un experto? → probablemente sobra granularidad hacia arriba.

---

## Checklist de curación (imprimible)

Antes de proponer o publicar un template, por **cada sección**:

- [ ] R1 — id slug estable, único, semántico; no cambiará jamás
- [ ] R2 — la intención dice qué conocimiento captura (prueba: tapa el nombre y léela)
- [ ] R3 — preguntas guía de nivel experto; ≥1 en toda obligatoria; alguna persigue el "por qué"
- [ ] R4 — aliases tomados de documentos reales; sin colisiones con otras secciones
- [ ] R5 — obligatoria solo si ningún documento legítimo del tipo puede omitirla
- [ ] R6 — tipo de contenido coherente con la forma natural de la información; tablas con esquema
- [ ] R7 — la sección se entrevista de una sentada; ni "y" en la intención ni gemelas contiguas

Y para el **template completo**:

- [ ] Numeración jerárquica coherente y en orden
- [ ] Mezcla razonable de obligatorias y opcionales (ni 0% ni 100% sin justificación)
- [ ] El dry-run del lint genera preguntas que sonarían naturales viniendo de un colega senior del área
- [ ] Nombre y descripción del template entendibles por alguien fuera del área dueña
