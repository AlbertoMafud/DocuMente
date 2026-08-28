# Template Studio — Especificación funcional y técnica

> **Estado:** especificación aprobada a nivel de diseño; pendiente de implementación.
> **Documento hermano:** [TEMPLATE_AIREADY_RULES.md](TEMPLATE_AIREADY_RULES.md) — las reglas de conversión humano→AI-ready que este módulo aplica.
> **Decisión de producto cerrada:** los usuarios NO cargan templates crudos. La conversión a AI-ready es el corazón del módulo. No relitigar.

---

## 1. El problema

DocuMente hoy soporta dos tipos de documento, ambos definidos en código:

| Tipo | Secciones | Archivo |
|---|---|---|
| `model_development` | 28 (congelado) | `src/core/template_catalog.py` |
| `prophet` | 12 | `src/core/template_catalog_prophet.py` |

Los usuarios piden documentar **otros** tipos: procedimientos operativos, políticas, metodologías, fichas de procesos, EUCs. Cada tipo nuevo necesita su propio template. Con el diseño actual, cada template nuevo implica escribir código Python, y **cada cambio de código exige una migración por ZIP a la instancia corporativa** — un ciclo caro y lento (ver `docs/MIGRATION_TO_EC2.md`).

### 1.1 Por qué no basta con "subir el template y ya"

Un template hecho para humanos (un `.docx` con encabezados y tablas vacías) le dice a una persona *dónde escribir*. No le dice a DocuMente *cómo entrevistar*.

Lo que hace funcionar la entrevista, el análisis de brechas y la importación de documentos existentes no es la lista de encabezados — es la **capa AI-ready** que hoy vive en `SeccionCatalogo`:

- **`id`** estable por sección — para que el sistema siga la pista de cada sección aunque cambie de nombre o de orden.
- **`intencion`** — qué conocimiento debe capturar la sección. Es lo que el motor de entrevista usa para saber *qué preguntar* y el analizador de brechas para saber *si ya está respondido*.
- **`preguntas_guia`** — las preguntas que haría un entrevistador experto del dominio.
- **`aliases`** — los nombres alternativos con los que la gente titula esa sección en documentos reales, para que la importación de un `.docx` existente mapee contenido a la sección correcta.
- **`obligatoria`** — qué secciones bloquean el avance del documento y cuáles son opcionales.
- **`tipo_contenido`** (texto / tabla / campos) — cómo se captura y se renderiza la sección.

Nada de eso viene en el `.docx` crudo. Un template sin esta capa produce entrevistas genéricas ("¿qué quieres escribir aquí?"), brechas mal detectadas e importaciones que no mapean nada. **El Template Studio existe para construir esa capa con asistencia del LLM y curación humana**, y publicar el resultado en un registro que el resto del sistema consume.

---

## 2. Conceptos clave (en lenguaje llano)

- **Catálogo**: la lista ordenada de secciones de un tipo de documento, cada una con su capa AI-ready. Es la "receta" que consume la entrevista, el gap analyzer y el reader.
- **Registro de templates**: el directorio único donde el sistema busca "¿qué tipos de documento existen y cuál es la receta de cada uno?". Unifica los templates de código (congelados) y los dinámicos (creados en el Studio).
- **Template dinámico**: un template creado en el Studio. Vive en la base de datos como datos, no como código. Por eso **viaja a la instancia corporativa sin migración de código**: la migración por ZIP lleva el código una vez; los templates se crean y editan del otro lado sin tocar el ZIP nunca más. Ésta es la razón crítica de la arquitectura.
- **Plantilla Word de export**: el `.docx` con placeholders (docxtpl) que da el formato visual institucional al documento exportado. Es una pieza distinta del catálogo — ver §9.

---

## 3. Roles y fases

| Fase | Quién crea templates | Gobernanza |
|---|---|---|
| **Fase 1 — admin-only** | Solo el administrador | El admin cura y publica directo |
| **Fase 2 — usuarios** | Cualquier usuario | El template del usuario queda `propuesto` (no usable) hasta aprobación del admin |

**Rol admin en el MVP:** hoy la autenticación es un token compartido pre-Cognito (`src/api/auth.py`). Para Fase 1 se propone un mecanismo mínimo y migrable: variable de entorno `DOCUMENTE_ADMIN_TOKEN`; quien presenta ese token es admin. Al llegar Cognito (Fase A.1.c), el rol admin se lee del grupo/claim del JWT y este mecanismo se retira. La API ya queda escrita contra una dependencia `RequireAdmin` para que el swap sea de un solo archivo.

---

## 4. Flujo UX — Fase 1 (admin)

Pantalla nueva "Template Studio", visible solo para admin. Cinco pasos con barra de progreso, mismo lenguaje visual del resto de la app (nada técnico crudo).

### Paso 1 — Subir el template

El admin sube el `.docx` del template "hecho para humanos" (o, alternativamente, un documento ejemplo ya lleno de ese tipo). Campos: nombre del tipo de documento, descripción de una línea, área dueña.

### Paso 2 — Extracción de estructura

El sistema recorre el `.docx` con `python-docx` (mismos cimientos que `src/docs/reader.py`): detecta encabezados por estilo y numeración, tablas y campos tipo formulario. Muestra el esqueleto detectado ("Encontré 14 secciones candidatas, 3 tablas") para una verificación visual rápida antes de gastar LLM.

### Paso 3 — Propuesta del LLM

El LLM recibe la estructura extraída + el texto del template y propone el **catálogo completo**: por cada sección, `id`, `numero`, `nombre`, `obligatoria`, `intencion`, `preguntas_guia`, `aliases` y `tipo_contenido` (con `schema_tabla` si es tabla). El prompt del sistema es, literalmente, el documento [TEMPLATE_AIREADY_RULES.md](TEMPLATE_AIREADY_RULES.md) — las mismas reglas que después verifica el lint.

> Nota de seguridad: el contenido del `.docx` subido se trata siempre como *datos*, nunca como instrucciones. El prompt lo encapsula como material a analizar; la curación humana del paso 4 es la segunda barrera.

### Paso 4 — Curación sección por sección

La pantalla central del Studio. Lista de secciones a la izquierda; al seleccionar una, panel de edición con todos los campos AI-ready. El admin puede:

- Editar cualquier campo (intención, preguntas, aliases…).
- Marcar obligatoria/opcional.
- Fusionar dos secciones o dividir una (el Studio regenera ids solo para secciones nuevas — ids ya asignados no cambian).
- Reordenar (renumera `numero`, **nunca** el `id`).
- Pedir al LLM "regenerar esta sección" con una instrucción libre ("hazla menos genérica", "agrega preguntas sobre riesgos").

Cada sección muestra un semáforo de lint en vivo (verde / advertencia / error) para que la curación sea guiada, no ciega.

### Paso 5 — Lint y publicación

Botón "Validar AI-readiness" que corre dos capas (detalle en §8):

1. **Checks determinísticos** — instantáneos, sin costo.
2. **Dry-run con LLM** — genera 1 pregunta de entrevista de muestra por sección y valida coherencia. El admin ve las preguntas generadas: es la mejor prueba de "¿así se sentirá la entrevista?".

Con lint en verde (o advertencias explícitamente aceptadas), botón **Publicar**. El template aparece de inmediato en "Crear documento" para todos los usuarios.

---

## 5. Flujo UX — Fase 2 (usuarios con gobernanza)

Mismo módulo, abierto a usuarios, con dos diferencias:

1. **El usuario no publica.** Su flujo termina en **Proponer**: el template pasa a estado `propuesto` y NO es usable para crear documentos.
2. **Bandeja del admin.** El admin ve los templates propuestos, con el mismo editor de curación y el resultado del lint ya corrido. Puede: **aprobar y publicar**, **devolver a borrador** con comentarios (el usuario ve los comentarios y reintenta), o **rechazar**.

### Ciclo de vida del template

```
borrador ──proponer──▶ propuesto ──aprobar──▶ aprobado/publicado ──retirar──▶ retirado
   ▲                       │
   └────devolver───────────┘
```

- En Fase 1 el admin salta directo `borrador → aprobado/publicado` (es su propia autoridad).
- `retirado`: el template deja de aparecer para crear documentos nuevos. **Los documentos existentes no se rompen**: cada documento copia su estructura de secciones al crearse (mismo patrón que `construir_secciones_vacias()` hoy), así que no depende del template vivo.
- Las transiciones se validan en una clase de dominio pura `TemplateStateMachine` (`src/core/rules/template_state_machine.py`), espejo del patrón `DocumentStateMachine` existente: mapa de transiciones permitidas + validaciones bloqueantes (ej. no se puede proponer con errores de lint) + `ResultadoTransicion` con razones legibles.

### Edición post-publicación

Un template publicado no se edita en caliente (los documentos en curso dependen de su estabilidad conceptual). El flujo es: **"Crear nueva versión"** → copia el catálogo a un borrador nuevo con `version + 1` → se cura → se publica → la versión anterior pasa a `retirado` automáticamente. Cada documento registra el `tipo` y la `template_version` con la que nació.

---

## 6. Modelo de datos

### 6.1 Entidades Pydantic nuevas (`src/core/models/template_dinamico.py`)

```python
TipoContenido = Literal["texto", "tabla", "campos"]
EstadoTemplate = Literal["borrador", "propuesto", "publicado", "retirado"]

class SeccionCatalogoDinamica(BaseModel):
    id: str                       # slug estable, ej. "4.controles_clave"
    numero: str                   # jerárquico, ej. "4" o "4.1"
    nombre: str
    obligatoria: bool
    intencion: str
    tipo_contenido: TipoContenido = "texto"
    schema_tabla: list[str] = []  # solo si tipo_contenido == "tabla"
    aliases: list[str] = []
    preguntas_guia: list[str] = []

class TemplateDinamico(BaseModel):
    id: UUID
    slug: str                     # identificador del tipo, ej. "procedimiento_operativo"
    nombre: str                   # nombre humano, ej. "Ficha de Procedimiento Operativo"
    descripcion: str
    area_duena: str
    version: int = 1
    estado: EstadoTemplate = "borrador"
    secciones: list[SeccionCatalogoDinamica]
    creado_por: str               # user_id
    archivo_origen: str | None    # .docx del que se extrajo
    resultado_lint: ResultadoLint | None
    audit_trail: list[EventoAuditoria]
    creado_en / actualizado_en: datetime
```

`SeccionCatalogoDinamica` es la unión de los campos de `SeccionCatalogo` (MRM) y `SeccionCatalogoProphet` — deliberadamente un superset, para que cualquier template existente sea expresable en el formato dinámico.

### 6.2 Tabla nueva — migración 100% aditiva

Misma filosofía que `documentos`: el Pydantic completo serializado a JSON en una columna de texto, con columnas planas solo para filtrar y listar.

```
templates_dinamicos
├── id            String(36) PK
├── slug          String(64)  index      (único por versión publicada)
├── nombre        String(256)
├── estado        String(32)  index
├── version       Integer
├── creado_por    String(64)  index
├── payload_json  Text                    (TemplateDinamico completo)
├── creado_en / actualizado_en  DateTime
```

- **No se altera ninguna tabla existente.** Solo `CREATE TABLE` nueva vía `Base.metadata.create_all` — el mecanismo de `_aplicar_migraciones_aditivas` de `src/storage/db.py` no necesita ni una entrada nueva.
- Repositorio `TemplateDinamicoRepository` en `src/storage/repositories.py`, calcado de `DocumentoRepository` (guardar/obtener/listar/borrar).

### 6.3 El único cambio a código existente que no es aditivo puro

`Documento.tipo` hoy es `Literal["model_development", "prophet"]` (`src/core/models/documento.py:26`). Debe ampliarse a `str`, validado contra el registro al crear el documento (no en el modelo — el modelo debe poder deserializar documentos cuyo template ya fue retirado). Es un cambio quirúrgico de una línea + validación en el use case `CrearDocumentoEnBlanco`. La columna `tipo` en BD ya es `String(32)` genérico — sin cambio de esquema. Se documentará en `MIGRATION_TO_EC2.md` §3.

---

## 7. Registro de templates (TemplateSpec)

Pieza central de integración: `src/core/template_registry.py`.

```python
@dataclass(frozen=True)
class TemplateSpec:
    id: str                                   # "model_development", "prophet", o slug dinámico
    nombre: str
    version: int
    origen: Literal["codigo", "dinamico"]
    catalogo: tuple[SeccionCatalogoDinamica, ...]
    ruta_plantilla_word: Path                 # plantilla docxtpl para export
    writer: str                               # id del writer: "mrm" | "prophet" | "generico"
    reglas_completitud: ReglasCompletitud     # umbrales/heurísticas del gap analyzer
```

- **Los templates de código quedan congelados como código.** El registro los adapta al vuelo: `model_development` y `prophet` se registran envolviendo sus catálogos actuales (los archivos `template_catalog*.py` no se tocan). Cero riesgo de regresión sobre lo que ya funciona.
- **Los dinámicos se cargan desde BD** (estado `publicado`) al resolver el registro.
- Función única de resolución: `resolver_template(tipo: str) -> TemplateSpec`. Todo consumidor (crear documento, entrevista, gap analyzer, export, importación) pasa por aquí en lugar de hacer `if tipo == "prophet"`. Los `if` existentes se reemplazan gradualmente; para v1 basta con que **crear documento, entrevista y export** resuelvan por registro.

### Integración con flujos actuales

| Flujo | Cambio |
|---|---|
| `POST /documentos` (crear) | Acepta cualquier `tipo` registrado; construye secciones vacías desde `spec.catalogo` |
| `GET /templates` | Devuelve códigos + dinámicos publicados (la UI de "Crear documento" se vuelve dinámica sola) |
| Entrevista (`InterviewEngine`) | Ya opera sobre `Seccion.intencion` y `preguntas_guia` — funciona sin cambios; solo recibe las secciones del nuevo tipo |
| Gap analyzer | Usa `reglas_completitud` del spec; default v1: mismas heurísticas actuales sobre `obligatoria` |
| Export | Resuelve `writer` + `ruta_plantilla_word` del spec (ver §9) |
| Importar `.docx` existente | v1: soportado para dinámicos vía `aliases` con el reader genérico; el realineado avanzado de estructura queda para v2 |

---

## 8. Lint de AI-readiness

Se corre bajo demanda en el Studio y es **bloqueante para proponer/publicar** (errores bloquean; advertencias exigen aceptación explícita, que queda en el audit trail).

### Capa 1 — Checks determinísticos (sin LLM, instantáneos)

| # | Check | Severidad |
|---|---|---|
| L1 | `id` únicos, formato slug estable, nunca vacíos | Error |
| L2 | Numeración coherente: jerárquica, sin duplicados, orden consistente con la lista | Error |
| L3 | `intencion` no vacía en **todas** las secciones | Error |
| L4 | ≥1 pregunta guía en toda sección obligatoria | Error |
| L5 | Aliases sin colisión entre secciones (un alias no puede apuntar a dos) | Error |
| L6 | `tipo_contenido` válido; si es `tabla`, `schema_tabla` no vacío | Error |
| L7 | Intención sospechosamente corta (<15 caracteres) o genérica ("descripción de la sección") | Advertencia |
| L8 | 0% o 100% de secciones obligatorias (huele a criterio no aplicado) | Advertencia |
| L9 | Sección sin aliases (la importación de docs existentes será frágil) | Advertencia |

Implementación: `src/core/rules/template_lint.py`, lógica pura de dominio, testeable sin BD ni LLM.

### Capa 2 — Dry-run con LLM

Por cada sección, el LLM genera **1 pregunta de entrevista de muestra** usando exactamente el prompt del motor de entrevista real, y un segundo paso valida coherencia: ¿la pregunta es específica del dominio o genérica? ¿es respondible por el dueño del proceso? ¿es consistente con la intención declarada? Resultado por sección: `ok` / `revisar` con razón. Las llamadas se paralelizan con `AsyncAnthropic` (mismo patrón que `SugerenciasMultiFuente`), acotando costo y latencia a una sola pasada por publicación.

Los criterios de fondo de ambas capas están definidos en [TEMPLATE_AIREADY_RULES.md](TEMPLATE_AIREADY_RULES.md).

---

## 9. Export DOCX de templates dinámicos — honestidad por delante

La calidad estética del `.docx` exportado es no negociable, y se logra **por construcción**: la plantilla maestra se diseña a mano en Word con la marca completa de la institución, y docxtpl solo rellena placeholders. Esa parte es trabajo humano de diseño y **no se puede generar automáticamente con la misma calidad**. Esta spec no pretende lo contrario.

**Default v1:** se diseña *una vez* una **plantilla Word genérica institucional** (`src/docs/templates/generico_institucional.docx`): portada con logo y metadatos, encabezado/pie institucional, estilos de título por nivel, estilo de tabla de marca, y la marca de agua "Borrador asistido — requiere revisión humana". Un `DocxWriterGenerico` recorre las secciones en orden y las rinde según `tipo_contenido`:

- `texto` → párrafos con estilos de la plantilla.
- `tabla` → tabla institucional con las columnas de `schema_tabla`.
- `campos` → tabla de dos columnas etiqueta/valor.

El resultado es sobrio, correcto y de marca — no tan a la medida como la plantilla MRM, y eso es aceptable y explícito. Cuando un tipo de documento lo amerite, se diseña su plantilla Word específica en Word y se registra en `TemplateSpec.ruta_plantilla_word` — **ese paso sigue siendo manual por diseño**. La plantilla genérica viaja en el ZIP de código una sola vez; sirve a todos los templates dinámicos presentes y futuros.

---

## 10. Gobernanza y audit trail

Todo el ciclo de vida del template genera `EventoAuditoria` (mismo modelo inmutable existente), almacenados en el `audit_trail` del propio `TemplateDinamico`. Tipos de evento nuevos (ampliación aditiva de `TipoEvento` o Literal paralelo `TipoEventoTemplate`):

`template_creado`, `template_extraido` (con archivo origen), `catalogo_propuesto_llm`, `seccion_catalogo_editada`, `lint_ejecutado` (con resumen de resultados), `advertencias_aceptadas`, `template_propuesto`, `template_devuelto` (con comentarios del admin), `template_publicado`, `template_retirado`, `nueva_version_creada`.

Con esto, ante una auditoría se puede responder: quién creó el template, qué propuso el LLM, qué corrigió el humano, quién lo aprobó y cuándo — el mismo espíritu de trazabilidad MRM aplicado a la infraestructura de documentación misma.

---

## 11. Endpoints API propuestos

Router nuevo `src/api/routers/studio.py`, consistente con los existentes (FastAPI + DTOs Pydantic + `CurrentUser`; los marcados 🔒 exigen `RequireAdmin` en Fase 1 — en Fase 2, los de creación/edición se abren a usuarios y solo aprobación/publicación queda 🔒).

```
POST   /studio/templates/extraer          — sube .docx, devuelve estructura + propuesta LLM   🔒F1
POST   /studio/templates                  — crea borrador desde la propuesta curada           🔒F1
GET    /studio/templates                  — lista (admin: todos; usuario F2: propios)
GET    /studio/templates/{id}             — detalle completo
PATCH  /studio/templates/{id}             — metadata (nombre, descripción, área)
PUT    /studio/templates/{id}/secciones   — reemplaza el catálogo curado completo
POST   /studio/templates/{id}/regenerar-seccion — LLM re-propone una sección con instrucción
POST   /studio/templates/{id}/lint        — corre lint (query ?dry_run=true incluye capa LLM)
POST   /studio/templates/{id}/estado      — transición (proponer/publicar/devolver/retirar)   🔒 publicar
POST   /studio/templates/{id}/nueva-version — copia a borrador v+1                            🔒F1
DELETE /studio/templates/{id}             — solo en estado borrador
```

Cambios aditivos a routers existentes:

```
GET /templates                    — incluye templates dinámicos publicados
GET /templates/{tipo}/secciones   — genérico vía registro (los paths /mrm y /prophet se conservan)
POST /documentos                  — acepta tipo dinámico registrado
```

---

## 12. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| **Catálogo de mala calidad publicado** → entrevistas genéricas, usuarios pierden confianza | Lint bloqueante + dry-run visible ("así se sentirá la entrevista") + curación humana obligatoria; en F2, doble filtro (usuario + admin) |
| **Proliferación de templates casi duplicados** (F2) | Aprobación admin obligatoria; el Studio muestra templates publicados similares por nombre/slug antes de crear |
| **Regresión en tipos congelados** al ampliar `Documento.tipo` | Los catálogos de código no se tocan; el registro los envuelve; tests de regresión sobre crear/entrevistar/exportar MRM y Prophet |
| **Prompt injection vía el .docx subido** (texto que intenta instruir al LLM) | El contenido del archivo se trata como datos en el prompt; el output es solo una propuesta que el humano cura; el lint no ejecuta nada del contenido |
| **Costo/latencia del dry-run LLM** | 1 pregunta por sección, paralelizado, solo bajo demanda y en publicación — no en cada edición |
| **Template retirado con documentos vivos** | Los documentos copian su estructura al crearse; retirar solo bloquea creación nueva |
| **Export genérico percibido como "menos premium"** | Plantilla genérica diseñada con el mismo rigor de marca; expectativa explícita en la UI ("formato institucional estándar"); ruta clara para plantilla específica cuando el tipo lo amerite |
| **Admin por env var es débil** | Aceptado como puente pre-Cognito, igual que el gate actual; el diseño con `RequireAdmin` hace el swap trivial |

---

## 13. Alcance v1 vs explícitamente fuera

**Dentro de v1 (Fase 1):**
- Extracción DOCX + propuesta LLM + curación + lint (ambas capas) + publicar.
- Registro unificado; crear documento y entrevista funcionando con tipos dinámicos.
- Export con plantilla Word genérica institucional.
- Audit trail completo del template.

**Dentro de v1.5 (Fase 2):**
- Estados borrador/propuesto/publicado/retirado con `TemplateStateMachine`.
- Studio abierto a usuarios + bandeja de aprobación del admin + comentarios de devolución.

**Explícitamente fuera (no es "después lo vemos" — es "no en esta versión"):**
- Diseño de plantillas Word de export desde la UI (sigue siendo trabajo manual en Word).
- Editar los catálogos congelados (`model_development`, `prophet`) desde el Studio.
- Reglas de completitud personalizadas por template más allá de `obligatoria` (v1 usa las heurísticas actuales).
- Derivar un template desde varios documentos ejemplo a la vez (v2 interesante).
- Realineado estructural avanzado en importación de docs existentes hacia templates dinámicos.
- Multi-idioma del catálogo; permisos granulares por área.

---

## 14. Estimación por fase (sesiones de trabajo)

| Sesión | Entregable | Fase |
|---|---|---|
| S-A | Modelos Pydantic + tabla + repositorio + registro `TemplateSpec` envolviendo códigos existentes + tests | 1 |
| S-B | Extracción DOCX + prompt de propuesta LLM (basado en TEMPLATE_AIREADY_RULES.md) + endpoint `extraer` | 1 |
| S-C | UI del Studio: wizard de 5 pasos + editor de curación sección por sección | 1 |
| S-D | Lint determinístico + dry-run LLM + semáforos en UI + publicar; integración con `POST /documentos` y `GET /templates` | 1 |
| S-E | Plantilla Word genérica (diseño en Word) + `DocxWriterGenerico` + export end-to-end + pruebas de regresión MRM/Prophet | 1 |
| S-F | `TemplateStateMachine` + eventos de gobernanza + endpoints de transición | 2 |
| S-G | UI usuario (proponer) + bandeja admin (aprobar/devolver con comentarios) + pruebas E2E | 2 |

**Total: ~5 sesiones Fase 1, ~2 sesiones Fase 2.** La sesión S-E incluye tiempo de diseño manual en Word — no es solo código.
