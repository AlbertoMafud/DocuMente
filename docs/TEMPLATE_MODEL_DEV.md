# Model Development Documentation Template — Estructura

> Descripción **estructurada y accionable** del *NYL Model Development Template* oficial, extraída verbatim de `SMNYL/Templates/NYL Model Development Template.docx` (Template Type A, fechado February 13, 2019).
>
> Este archivo es la **fuente única** que el motor de entrevista (`InterviewEngine`), el analizador de brechas (`GapAnalyzer`) y el generador de borradores (`Drafter`) consumen para saber:
> - Qué secciones existen
> - Qué información captura cada una
> - Cuáles son obligatorias vs opcionales
> - Qué preguntas hacer al usuario para completarlas
>
> Cuando el template oficial NYL se actualice, este archivo se re-sincroniza.

---

## Estructura general del documento

El template tiene **8 secciones principales** numeradas, más portada, control de versiones, y apéndices opcionales.

```
PORTADA
  ├── New York Life
  ├── Model Development Template
  ├── Template Type A
  ├── Name of model
  ├── Prepared by (Author)
  ├── Date

1. MODEL PROFILE
   ├── 1.1 Tabla de atributos (Model Name, ID, Class, FAE, Owner, Developer, ...)
   ├── 1.2 Version Control (bitácora de cambios)
   └── 1.3 Problem Statement

2. MODEL OVERVIEW
   ├── 2.1 Model Uses
   ├── 2.2 Model Scope
   └── 2.3 Business Impact of Model Usage

3. RELATED & SUPPORTING DOCUMENTS
   ├── 3.1 Ancillary document list
   └── 3.2 Additional Documents

4. MODEL DESCRIPTION & CONCEPT
   ├── 4.1 Schematic Diagram
   ├── 4.2 Model Theory and Logic
   ├── 4.3 Key Risk Drivers
   └── 4.4 Key Assumptions

5. INPUTS AND DATA
   ├── 5.1 Raw Data Sources and Data Quality
   ├── 5.2 Upstream Models & Company Determined Assumptions
   ├── 5.3 Key Data Pre-Processing Steps
   │     ├── 5.3.1 Data Aggregations
   │     ├── 5.3.2 Segmentations
   │     └── 5.3.3 Use of Averages or Proxies
   ├── 5.4 Known Input and Data Limitations
   └── 5.5 Record of Input Changes or Decisions Made

6. MODEL BUILD PROCESS
   ├── 6.1 Specification Process
   ├── 6.2 Approach Used
   ├── 6.3 Development Testing
   ├── 6.4 Limitations Revealed During Testing
   └── 6.5 Record of Process Changes

7. MODEL IMPLEMENTATION & PRODUCTION
   ├── 7.1 Platform
   ├── 7.2 Model Runs
   ├── 7.3 Performance Testing
   └── 7.4 Production and Performance Limitations

8. MODEL GOVERNANCE
   └── (gobernanza de software, datos, controles, signoff, escalación)

9. ON-GOING MONITORING
   └── (procedimientos de monitoreo de performance)

APÉNDICES (opcionales)
  ├── Test plans
  ├── Especificaciones técnicas
  └── Documentación de soporte
```

---

## Catálogo de secciones detallado

> Cada entrada incluye: ID, nombre oficial, intención (qué captura), si es obligatoria, y preguntas-guía que el `InterviewEngine` puede formular al usuario para completarla.

### 0. Portada (Cover Page)

**ID:** `0.cover`  
**Obligatoria:** Sí  
**Intención:** Identificar el documento.  
**Campos:**
- `nombre_modelo` (texto libre, ej. "UL Rebuild Model")
- `autor` (texto)
- `fecha_documentacion` (fecha)

---

### 1. Model Profile

#### 1.1 Tabla de atributos del modelo

**ID:** `1.1.attributes`  
**Obligatoria:** Sí  
**Intención:** Capturar metadata estructurada del modelo.  
**Campos** (extraídos verbatim de la Tabla 0 del template):
- Model Name
- Model ID
- Model Class
- Profit Center
- BU Executive
- Model Owner
- Model Developer(s)
- Current Model Version
- Financial Impact
- Model Status
- Target Production Date

**Preguntas-guía:**
- "¿Cuál es el nombre oficial del modelo y su ID en el inventario MRM?"
- "¿Qué Functional Area es la dueña? ¿Quién es el FAE responsable?"
- "¿Quién es el Model Owner y quiénes son los developers?"
- "¿Cuál es el estado actual: en desarrollo, en producción, o retirado?"

#### 1.2 Version Control

**ID:** `1.2.version_control`  
**Obligatoria:** Sí  
**Intención:** Bitácora de cambios y aprobaciones (NYL exige `change log must be maintained to track changes and annual approvals`).  
**Estructura tabular:**

| Version No. | Date Changed | Updated By | Approved By | Description |
|---|---|---|---|---|
| 1.0 | YYYY-MM-DD | Nombre | Nombre | Descripción |

DocuMente debe poblar esta tabla automáticamente desde el `audit_trail` interno.

#### 1.3 Problem Statement

**ID:** `1.3.problem_statement`  
**Obligatoria:** Sí  
**Intención (verbatim):** "High-level verbal description of the problem or need that the model is designed to solve, including informational, computational, or analytic constraints under which this solution was developed."

**Sub-elementos esperados:**
- Inadecuaciones del modelo previo (si aplica) — listar
- Razones por las que el modelo previo era problemático
- Decisión de rebuild vs. enhancement y cuándo se tomó
- Constraints de plataforma (ej. "debe construirse en Prophet porque...")
- Si el modelo viejo existe: ¿se puede usar para parallel testing? Si no, ¿qué tests se planean?
- Propósitos principales y productos cubiertos

**Preguntas-guía:**
- "¿Cuál es el problema o necesidad que este modelo resuelve?"
- "¿Existe un modelo previo? ¿Por qué fue insuficiente?"
- "¿Hay restricciones (plataforma, regulatorias, computacionales) bajo las que tuvo que diseñarse?"
- "¿Cuáles son los productos o líneas de negocio que cubre?"

---

### 2. Model Overview

#### 2.1 Model Uses

**ID:** `2.1.model_uses`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Description of all the intended users and use frequency of the models. In some cases, it is useful to explicitly list uses not in scope (e.g., 'the model currently does not have stress testing capability')."

**Preguntas-guía:**
- "¿Quiénes son los usuarios intencionados del modelo?"
- "¿Con qué frecuencia se usa? (diaria, mensual, trimestral, ad-hoc)"
- "¿Qué usos están explícitamente fuera del alcance?"

#### 2.2 Model Scope

**ID:** `2.2.model_scope`  
**Obligatoria:** Sí  
**Intención (verbatim):** "This section describes the products modelled, including both high level description and detailed generation. Please provide as much information on the products covered as possible, including blocks and years of issuance: e.g., enumerate all main products, including information of size of each product."

Para cada tipo de producto, capturar:
- Features del producto
- Features que se reflejarán en el modelado
- Features que NO se reflejarán y por qué (con justificación de aproximaciones)

**Preguntas-guía:**
- "¿Qué productos cubre el modelo? Lista enumerada."
- "Para cada producto: ¿qué features modela y cuáles deja fuera? ¿por qué?"
- "¿Cuál es el tamaño de cada bloque (reservas, número de pólizas, montos)?"

#### 2.3 Business Impact of Model Usage

**ID:** `2.3.business_impact`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Information regarding how the model fits into the company business and how the result will be used for business decisions. It should also be documented if the model results are required by regulation."

**Preguntas-guía:**
- "¿Cómo encaja este modelo en las decisiones del negocio?"
- "¿Sus resultados son requeridos por alguna regulación? ¿Cuál?"
- "Si es posible, da contexto cuantitativo: ¿qué se decide con base en el output?"

---

### 3. Related & Supporting Documents

#### 3.1 Ancillary document list

**ID:** `3.1.ancillary`  
**Obligatoria:** Sí  
**Intención:** Lista de documentos relacionados con links/ubicaciones.  
**Sub-elementos esperados:**
- Project folder usado para el desarrollo
- Location of Model Specifications
- Descripción de sub-folders relevantes

#### 3.2 Additional Documents

**ID:** `3.2.additional`  
**Obligatoria:** No (recomendable)  
**Intención (verbatim):** "List of all additional documentation that may exist related to the products covered by this model and the modelling approach."

Tipos comunes: pricing memos, policy forms, valuation memos, assumption memos, methodology documents, conversation memos, 1st line validation memos, performance testing memos, documentation for additional data manipulation, documentation about rationale for relevant decisions.

---

### 4. Model Description & Concept

#### 4.1 Schematic Diagram

**ID:** `4.1.diagram`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Provide a diagram of the modelling system, including data sources, upstream models and assumptions, outputs, platform, and other system components as applicable."

**Tratamiento en DocuMente:** placeholder para imagen + descripción textual del diagrama. El usuario puede subir imagen o describir verbalmente y Claude genera placeholder (con disclaimer).

#### 4.2 Model Theory and Logic

**ID:** `4.2.theory`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Describe what is the basic algorithm(s) of the model. If it is based on existing platform, describe the additional logic and/or theory you develop on top of the existing platform. Describe alternative (or prior) approaches that are not being used, and why not."

**Preguntas-guía:**
- "¿Cuál es el algoritmo o teoría central del modelo?"
- "¿Está construido sobre una plataforma existente (Prophet, GGY Axis)? ¿Qué lógica adicional añadiste?"
- "¿Qué enfoques alternativos consideraste y por qué no los elegiste?"

#### 4.3 Key Risk Drivers

**ID:** `4.3.risk_drivers`  
**Obligatoria:** Sí  
**Intención:** Lista y contexto de los principales drivers de riesgo del modelo.

**Ejemplos del template (verbatim):**
- Longevidad: "For the modeled products longevity is a main risk driver because... For this modeling approach we will model longevity as increasing with the time"
- Mortalidad
- Económicos: "Changes in economic environment may impact assumptions and underlying products."

**Preguntas-guía:**
- "¿Cuáles son los 3-5 drivers principales de riesgo del modelo?"
- "Para cada uno: ¿por qué es relevante y cómo está modelado?"

#### 4.4 Key Assumptions

**ID:** `4.4.assumptions`  
**Obligatoria:** Sí (crítica para tier high-risk)  
**Intención (verbatim):** "Describe all assumptions, economic or insurance and provide context for the sources and the modeling approaches."

**Categorías típicas a capturar:**
- Mortality assumptions (tabla SOA, study experience, año implementación)
- Economic assumptions (ESG, scenario generator, fuentes)
- Longevity assumptions
- Lapse assumptions (base, dynamic, fuentes)
- Otras según producto

**Preguntas-guía (importantes):**
- "Para cada supuesto: ¿qué fuente lo respalda? ¿qué documento/study?"
- "¿Cuáles son los rangos plausibles de cada supuesto?"
- "¿Hay supuestos que se sospecha pueden necesitar revisión?"

---

### 5. Inputs and Data

#### 5.1 Raw Data Sources and Data Quality

**ID:** `5.1.raw_data`  
**Obligatoria:** Sí  
**Intención (verbatim):** "List all providers and the location of the final specs for raw policy data being fed into the model."

Para cada fuente, capturar:
- **Data type** (ej. mortality, lapse, yield curve)
- **Data source** (cómo se adquiere: email, base de datos, etc.)
- **Team responsible** for data
- **Location** of the final data/assumption
- **Method** by which data is input (connector, manual upload, API)

Si los datos requieren manipulación adicional, documentar la ubicación post-manipulación.

Análisis de calidad: accuracy, completeness, conformity.

#### 5.2 Upstream Models & Company Determined Assumptions

**ID:** `5.2.upstream`  
**Obligatoria:** Sí  
**Intención (verbatim):** "List all upstream models and Company input assumptions. For Company input assumptions, the model used to supply proposed assumptions to the Assumptions Committee should be identified."

**Estructura tabular:**

| # | Upstream Model/Assumption | Key Contact | Inventory ID* |
|---|---|---|---|
| 1 | ... | ... | ... |

*Modelos no inventariados todavía pueden agregarse después.

#### 5.3 Key Data Pre-Processing Steps

##### 5.3.1 Data Aggregations

**ID:** `5.3.1.aggregations`  
**Obligatoria:** Si aplica  
**Intención:** Información sobre agregación de datos. ¿Bloques de pólizas homogéneos procesados como una unidad? ¿Bloques con features similares pero no idénticos tratados como idénticos?

##### 5.3.2 Segmentations

**ID:** `5.3.2.segmentations`  
**Obligatoria:** Si aplica  
**Intención (verbatim):** "Provide information on relevant segmentation."

**Preguntas-guía:**
- "¿Las tasas de lapse recibidas requieren conversión para fit a las agrupaciones del modelo?"
- "¿Qué bloques principales se procesan uniformemente? ¿Son product-driven?"
- "¿Qué segmentaciones son driven por feeder models? ¿Por estructura corporativa? ¿Por requisitos regulatorios?"

##### 5.3.3 Use of Averages or Proxies

**ID:** `5.3.3.averages_proxies`  
**Obligatoria:** Si aplica  
**Intención:** Identificar dónde se usan promedios o proxies para llenar datos faltantes/incompletos/erróneos, o dónde se aplican promedios para suavizar datos y remover outliers.

#### 5.4 Known Input and Data Limitations

**ID:** `5.4.data_limitations`  
**Obligatoria:** Sí  
**Intención:** Lista de todas las limitaciones encontradas en datos o supuestos y las acciones tomadas para remediarlas.

#### 5.5 Record of Input Changes or Decisions Made

**ID:** `5.5.input_changes`  
**Obligatoria:** No (vivo, se actualiza con el tiempo)  
**Estructura tabular:**

| Date | Decision |
|---|---|
| YYYY-MM-DD | Ej.: "El último supuesto de lapse no se recibió, se usaron supuestos de 201X." |

---

### 6. Model Build Process

#### 6.1 Specification Process

**ID:** `6.1.specification`  
**Obligatoria:** Sí  
**Intención (verbatim, dos casos):**

- *Si es un cambio o upgrade*: "Describe the nature of the requests in the context of the pre-existing model. Is this based on an existing platform? What is new in the specs and how specs are translated into the modelling features."
- *Si es modelo nuevo*: "Are there business decisions, needs, or constraints that condition the specifications of the model or may favour one modelling approach over another? Explain business rationale for all additional constraint."

#### 6.2 Approach Used

**ID:** `6.2.approach`  
**Obligatoria:** Sí  
**Intención:** Metodología detallada del modelo finalmente seleccionado.

**Sub-elementos esperados:**
- Teoría y lógica de cómo funciona el modelo, risk drivers, variable selection
- Derivaciones de soluciones analíticas, métodos numéricos, choice de parámetros
- Supuestos implícitos en la estructura y su racional
- Aproximaciones o simplificaciones y su racional
- Comparación con enfoques alternativos: métricas, benchmarks, conclusiones (pros/cons)
- Racional de la elección final (performance metrics, robustness, implementation, data availability)
- Lenguaje de programación / herramientas usadas
- Estructura del código, cambios respecto al modelo predecesor, input mappings

#### 6.3 Development Testing

**ID:** `6.3.dev_testing`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Describe tests performed to evaluate that all model components and the overall model functions as intended."

**Tipos de tests esperados:**
- Evaluación de accuracy
- Evaluación de robustness y stability con rangos de inputs y supuestos
- Sensitivity analysis
- Limitaciones potenciales
- Scenario testing (especialmente extremos)
- Pre-development tests / evaluación de la solución preferida

Si hay test plan formal: incluirlo y documentar resultados de cada test.

#### 6.4 Limitations Revealed During Testing

**ID:** `6.4.limitations`  
**Obligatoria:** Sí  
**Intención:** Limitaciones del modelo descubiertas durante testing.

**Categorías:**
- Por la naturaleza/elección de supuestos (¿bajo qué condiciones falla?)
- Simplificaciones/aproximaciones implícitas o explícitas
- Procesos involucrados en producir resultados

#### 6.5 Record of Process Changes

**ID:** `6.5.process_changes`  
**Obligatoria:** No (vivo)  
**Intención:** Bitácora de todos los cambios de proceso y decisiones durante el build del modelo.

---

### 7. Model Implementation & Production

#### 7.1 Platform

**ID:** `7.1.platform`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Describe the platform where the model is using; E.g. Prophet, stand-alone C++ program, Excel spreadsheet etc., and how it is integrated with this platform."

**Sub-elementos:**
- Plataforma (Prophet, GGY Axis, R, Python, Excel, custom)
- Fuentes de datos en producción
- Proceso de transferencia (link directo, file exchange, manual)
- Outputs y dónde se almacenan o transmiten

#### 7.2 Model Runs

**ID:** `7.2.runs`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Provide instructions on how to run the model for different use cases, and what are the control model settings."

**Sub-elementos:**
- Instrucciones de ejecución por use case
- Settings de control (toggle de features)
- Periodicidad de runs por propósito
- Diferencias del proceso de producción por caso

#### 7.3 Performance Testing

**ID:** `7.3.perf_testing`  
**Obligatoria:** Sí  
**Intención:** Testing realizado para asegurar que el modelo refleja correctamente las specs y se desempeña como intended en producción y bajo rangos relevantes.

#### 7.4 Production and Performance Limitations

**ID:** `7.4.prod_limitations`  
**Obligatoria:** Sí  
**Intención:** Limitaciones conocidas debido a cómo se implementó en producción. ¿Bajo qué condiciones underlying/económicas el modelo podría desempeñarse inadecuadamente? ¿Hay aspectos del ambiente productivo que si cambian rompen el modelo?

---

### 8. Model Governance

**ID:** `8.governance`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Describe current governance around the software; e.g. version control, user access control, IT controls on hardware. Describe governance around the data."

**Sub-elementos esperados:**
- Controles para asegurar que input data es correcta y protegida de tampering
- Controles sobre transmisión de output a modelos upstream
- Checks, access control, signoff authority, escalation procedures cuando se detectan issues

---

### 9. On-going Monitoring

**ID:** `9.monitoring`  
**Obligatoria:** Sí  
**Intención (verbatim):** "Describe any on-going model performance monitoring procedures that are in place to ensure the model continues to meet business requirements over time."

**Preguntas-guía:**
- "¿Hay KPIs de performance del modelo? ¿Cuáles?"
- "¿Quién monitorea, con qué frecuencia, contra qué thresholds?"
- "¿Qué se hace cuando un threshold se rompe?"

---

## Resumen de obligatoriedad

| Sección | Obligatoria | Comentario |
|---|---|---|
| 0. Cover | ✅ | Default |
| 1.1 Attributes | ✅ | Metadata estructurada |
| 1.2 Version Control | ✅ | Auto-poblado desde audit trail |
| 1.3 Problem Statement | ✅ | Crítica para entender el "por qué" |
| 2.1 Model Uses | ✅ | |
| 2.2 Model Scope | ✅ | |
| 2.3 Business Impact | ✅ | |
| 3.1 Ancillary document list | ✅ | |
| 3.2 Additional Documents | ⚠️ | Recomendado |
| 4.1 Schematic Diagram | ✅ | Imagen + descripción |
| 4.2 Model Theory and Logic | ✅ | |
| 4.3 Key Risk Drivers | ✅ | |
| 4.4 Key Assumptions | ✅ | Crítica para tier high-risk |
| 5.1 Raw Data Sources | ✅ | |
| 5.2 Upstream Models | ✅ | |
| 5.3.1 Data Aggregations | ⚠️ | Si aplica |
| 5.3.2 Segmentations | ⚠️ | Si aplica |
| 5.3.3 Averages or Proxies | ⚠️ | Si aplica |
| 5.4 Known Data Limitations | ✅ | |
| 5.5 Input Changes Record | ⚠️ | Vivo, opcional al inicio |
| 6.1 Specification Process | ✅ | |
| 6.2 Approach Used | ✅ | |
| 6.3 Development Testing | ✅ | |
| 6.4 Limitations Revealed | ✅ | Crítica MRM |
| 6.5 Process Changes Record | ⚠️ | Vivo, opcional al inicio |
| 7.1 Platform | ✅ | |
| 7.2 Model Runs | ✅ | |
| 7.3 Performance Testing | ✅ | |
| 7.4 Production Limitations | ✅ | |
| 8. Governance | ✅ | |
| 9. On-going Monitoring | ✅ | |

**Reglas de completitud:**
- `Draft → In Review`: todas las secciones marcadas ✅ deben tener contenido sustancial (no solo el placeholder).
- `In Review → Approved`: además debe haber sign-off de un First Line Reviewer (independencia validada — ver `MRM_REQUIREMENTS.md` §12).

---

## Mapeo entrevista → secciones

El `InterviewEngine` recorre las secciones en este orden (priorizado por dependencias lógicas):

1. **Identificación**: Cover + 1.1 Attributes
2. **Contexto**: 1.3 Problem Statement → 2.1 Uses → 2.2 Scope → 2.3 Business Impact
3. **Metodología**: 4.2 Theory → 4.3 Risk Drivers → 4.4 Assumptions
4. **Datos**: 5.1 Raw Data → 5.2 Upstream → 5.3 Pre-processing → 5.4 Limitations
5. **Build**: 6.1 Specification → 6.2 Approach → 6.3 Testing → 6.4 Limitations Revealed
6. **Producción**: 7.1 Platform → 7.2 Runs → 7.3 Perf Testing → 7.4 Prod Limitations
7. **Gobernanza y monitoreo**: 8 → 9
8. **Soportes**: 3.1 Ancillary docs → 3.2 Additional docs → 4.1 Schematic Diagram

Las secciones con buckets `5.5` y `6.5` (records vivos) se pueblan automáticamente desde el audit trail de DocuMente.
