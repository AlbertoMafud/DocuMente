# MRM Requirements — Fuente única de verdad

> Este archivo destila los requerimientos de Model Risk Management (MRM) que DocuMente debe respetar. Es la **fuente única** que tanto el código (validación de completitud, alertas, plantillas) como los prompts de Claude (entrevista, drafting) consultan para garantizar que la documentación generada cumple con el marco de gobierno de SMNYL/NYL.
>
> **Origen:** extracción verbatim de los documentos oficiales:
> - *New York Life Model Risk Management Policy* — Versión 10.0, 16 de diciembre 2021 (`SMNYL/Politicas y estandares/MRM Policy.pdf`)
> - *New York Life Model Risk Management Standard* — Versión 1.1, 21 de abril 2025 (`SMNYL/Politicas y estandares/New York Life Model Risk Management Standard_2025_v1.1.pdf`)
>
> Cuando estos documentos se actualicen, este archivo debe re-sincronizarse.

---

## 1. Definición oficial de "modelo"

> "A model is a quantitative method, system, or approach based upon theories, techniques, and assumptions to process input data into quantitative results, estimates, or forecasts."  
> — *NYL MRM Standard 2025 §2.1*

Un modelo tiene **tres componentes**:
1. **Input component**: datos y supuestos.
2. **Processing component**: método cuantitativo que transforma inputs en resultados.
3. **Output (reporting) component**: información que apoya decisiones de negocio.

**Cobertura:**
- Aplica también a métodos cuyos inputs son parcial o totalmente cualitativos / juicio experto, **siempre que el output sea cuantitativo**.
- Cubre **modelos de terceros (vendor models)** y EUCs (End User Computing Tools, ej. spreadsheets de Excel) que cumplan la definición de modelo.
- Es agnóstica al ambiente, plataforma o controles: aplica igual si vive en un sistema IT o en una hoja de Excel.

---

## 2. Roles obligatorios y opcionales (Three Lines of Defense)

DocuMente debe permitir asignar al menos los roles obligatorios a cada documento de modelo.

### First Line of Defense (1ra línea — los que desarrollan y usan)

| Rol | Obligatorio | Responsabilidad clave |
|---|---|---|
| **Functional Area Executive (FAE)** | Sí | Acepta el riesgo del modelo dentro de su área. Asigna Model Owner y First Line Reviewer. Atestigua semestralmente la completitud del inventario. |
| **Model Owner** | Sí | Responsable del uso y desempeño del modelo. Asegura cumplimiento de Política/Standards a nivel del modelo. Identifica usuarios. Desarrolla plan de remediación post-validación. |
| **Model Developer** | Sí | Construye el modelo, gestiona datos de desarrollo, supuestos, metodología y testing. Documenta exhaustivamente el proceso de desarrollo. (Frecuentemente la misma persona que el Model Owner.) |
| **Model User** | Sí | Usa el modelo dentro de su contexto de negocio. Debe entender limitaciones e incertidumbres. |
| **First Line Model Reviewer** | Opcional (asignado caso por caso) | Realiza peer review del modelo. **No puede haber sido el Developer ni el Owner.** Debe tener skills suficientes. |
| **Model Architect** | Opcional | Diseña/mantiene sets de modelos complejos (ej. Prophet Modeling Center of Excellence). |
| **Model Steward** | Opcional | Asistente del Model Owner, especialmente en change management. |

### Second Line of Defense (2da línea — independiente)

| Rol | Obligatorio | Responsabilidad clave |
|---|---|---|
| **Head of Model Risk Management (HMRM)** | Sí (a nivel empresa) | Responsable ejecutivo del MRM Team. Aprueba reportes de validación. |
| **Independent Model Validator** | Sí (para modelos high-risk) | Análisis profundo independiente. **No puede ser Owner ni Developer ni afiliado.** |
| **Lead Model Validator** | Sí (cuando hay validadores) | Supervisa el trabajo de validadores y asegura effective challenge. |

### Third Line of Defense (3ra línea)

- **Corporate Audit Department (CAD)**: revisa periódicamente actividades de 1ra y 2da línea. No participa en la documentación operativa pero puede auditar.

### Reglas de independencia (críticas para DocuMente)
- First Line Reviewer ≠ Model Owner ni Model Developer del modelo en revisión.
- Independent Validator ≠ Owner, Developer, User ni afiliado.
- Model Owner, Developer, User pueden ser la misma persona.

---

## 3. Tiering de riesgo del modelo

DocuMente debe capturar el tier de cada modelo, ya que **la profundidad de la documentación escala con el riesgo**.

### Inherent Risk — Anchor Rating Matrix

> *NYL MRM Standard 2025 §3.6.1, Table 1*

Combina dos dimensiones: **Materiality** (tamaño del output relativo a la exposición de la compañía) y **Criticality** (importancia para el negocio).

| Materiality \ Criticality | Low | Medium | High | Very High | Critical |
|---|---|---|---|---|---|
| **Extreme** | Medium | High | Very High | Very High + | Critical |
| **Major** | Medium - | Medium | High | Very High | Very High + |
| **Material** | Low | Medium - | Medium | High | Very High |
| **Minor** | Low | Low | Medium - | Medium | High |
| **Minimal** | Low | Low | Low | Medium - | Medium |

Una tercera dimensión, **Likelihood (Uncertainty)**, ajusta hacia arriba o abajo según factores como complejidad estructural, riesgo de mal uso, exposición regulatoria.

### Niveles de tier resultantes
`Low → Medium- → Medium → High → Very High → Very High+ → Critical`

### Residual Risk
Es el riesgo que queda después de aplicar gobernanza y controles. Se evalúa contra completitud y efectividad de controles en: documentación, FLRT, inputs/supuestos, data governance, change management, performance review.

### Implicaciones para DocuMente
- Modelos `Critical` y `Very High`: documentación más detallada y prioritaria.
- DocuMente debe pedir el tier en la creación del documento y ajustar la entrevista en consecuencia.

---

## 4. Documentación obligatoria por fase del Model Lifecycle

> *NYL MRM Policy §3.5 + Standard §2.4 y §4*

Las 7 fases del ciclo de vida:

1. **Model Pre-Development** — establecimiento del business use case
2. **Model Development and Build** — construcción y testing
3. **Model Implementation and Production** — operacionalización
4. **First Line Review and Testing (FLRT)** — peer review de 1ra línea
5. **Second Line Independent Validation** — validación profunda independiente
6. **Model Use** — uso en producción
7. **Model Maintenance and Monitoring** — monitoreo continuo

### Tres documentos obligatorios

> "Key modeling activities that must be documented are: (1st Line) Model development including build, implementation, and use, plus 1st Line Review and Testing; (2nd Line) 2nd Line Independent Validation."  
> — *NYL MRM Standard 2025 §3.5*

| Documento | Quién lo produce | Plantilla oficial |
|---|---|---|
| **Model Development Documentation** | Model Developer (1ra línea) | `Model Development Documentation Template` |
| **First Line Review & Testing (FLRT) Report** | First Line Model Reviewer (1ra línea) | `First Line Review and Testing Template` |
| **Independent Validation Report** | Independent Model Validator (2da línea) | `Model Validation Templates` |

> **MVP de DocuMente** cubre únicamente el primer documento: Model Development Documentation Template.

### Requisito clave de calidad
> "Model documentation should enable an independent subject matter expert to assess and replicate model functionalities."  
> — *NYL MRM Standard 2025 §3.5*

Es decir: cualquier documentación generada debe permitir a un experto independiente **replicar** el modelo. Este es el estándar de calidad contra el cual DocuMente valida completitud.

---

## 5. Tiempos de cumplimiento basados en riesgo

> *NYL MRM Standard 2025 §4, Figure 6*

### Modelos nuevos (alto impacto)
| Tier | Documentación de desarrollo | Validación independiente |
|---|---|---|
| Critical | Antes de uso | Antes de uso |
| Very High | 1 año post-producción | 1 año post-producción |
| High | 1 año post-producción | 18 meses post-producción |

### Modelos existentes (cambiados)
Misma prioridad que modelos nuevos. Profundidad depende de la magnitud del cambio.

### Modelos existentes (residual risk evaluado)
- **Tier 1**: remediación dentro de 1 año
- **Tier 2**: remediación dentro de 18 meses

### Re-validación
- Modelos high-risk: evaluar necesidad cada 2-3 años.

### Monitoreo
- Frecuencia depende del uso y de la frecuencia de corridas. El MRM Procedures provee guía detallada.

---

## 6. Proceso de Attestation (semestral)

> *NYL MRM Standard 2025 §3.4.2*

El MRM Team conduce un proceso formal de attestation **semestral**. Los FAEs deben atestiguar a la fecha de attestation:

- Completitud del inventario (todos los modelos en uso o en desarrollo bajo su área están inventariados)
- Completitud y precisión de la metadata de cada modelo
- **Completitud de toda la documentación del modelo**
- Que el uso intencionado de cada modelo está especificado

**Implicación para DocuMente:** los documentos generados deben llegar a un estado verificable de "Approved" antes de la fecha de attestation. La app debe poder reportar completitud por modelo y exportar evidencia para attestation.

---

## 7. Inventario de Modelos (Model Inventory)

> *NYL MRM Standard 2025 §3.4*

El Model Inventory vive en el **MRM System** (web-based interno de NYL/SMNYL). Cada modelo debe registrarse **tan pronto como se confirma para desarrollo**.

DocuMente no es el MRM System, pero debe:
- Capturar metadata mínima alineable con el inventario (Model Name, Model ID, FA, Owner, Developer, Tier, Status).
- Permitir export de esta metadata para alimentar el MRM System externamente.

---

## 8. Tabla de campos obligatorios mínimos en metadata del modelo

Derivado del template oficial NYL Model Development y de los attributes del FLRT Template:

| Campo | Tipo | Notas |
|---|---|---|
| Model Name | texto | Ej. "UL Rebuild Model" |
| Model ID | texto | Asignado por el MRM System; en MVP puede ser tentativo |
| Model Class | texto | Categoría (actuarial, investment, statistical, etc.) |
| Profit Center / Functional Area | texto | FA al que pertenece |
| BU Executive (FAE) | persona | Nombre y rol |
| Model Owner | persona | Nombre y línea de negocio |
| Model Developer(s) | personas | Pueden ser múltiples |
| Model Users | personas | Pueden ser múltiples |
| Current Model Version | texto | Ej. "v3.0" |
| Implementation Platform | texto | Ej. "GGY Axis", "Prophet", "R" |
| Projection Start Date | fecha | Aplicable a modelos actuariales |
| Financial Impact | enum | Reservas, GAAP earnings, etc. |
| Model Status | enum | In Development / In Production / Retired |
| Target Production Date | fecha | Si está en desarrollo |
| Inherent Risk Tier | enum | Low / Medium- / Medium / High / Very High / Critical |
| Residual Risk Tier | enum | Tier 1 / Tier 2 / N/A |
| Intended Use | texto | Descripción explícita del uso aprobado |
| Use Restrictions | texto | Limitaciones explícitas |

---

## 9. Bitácora de cambios y aprobaciones (Version Control)

> Tomado del *NYL Model Development Template* — sección *Version Control*

Cada documento debe mantener una tabla con:

| Version No. | Date Changed | Updated By | Approved By | Description |
|---|---|---|---|---|
| 1.0 | YYYY-MM-DD | Nombre | Nombre | Descripción del cambio |

DocuMente registra esto automáticamente en su `audit_trail` y lo materializa en la bitácora del DOCX exportado.

---

## 10. Estados del documento en DocuMente (alineados con MRM)

| Estado | Significado MRM | Reglas de transición |
|---|---|---|
| **Draft** | Documento en construcción | Default al crear |
| **In Review** | Listo para 1st Line Reviewer | Requiere completitud >= 100% de secciones obligatorias |
| **Approved** | First Line Reviewer aprobó | Requiere sign-off del rol Reviewer (registrado en audit trail) |
| **Published** | Aprobado por FAE / listo para attestation | Requiere sign-off del rol FAE |
| **Retired** | Modelo retirado | Solo desde Approved/Published; no se puede reabrir |

**Regla:** una vez en `Retired`, el documento es inmutable y solo lectura.

---

## 11. Documentos relacionados (catálogo de standards y templates suplementarios)

> *NYL MRM Standard 2025 §7.1*

Standards y plantillas adicionales que NYL/MRM mantiene:
- Model Documentation Guidelines
- Model Development Documentation Templates ← **este es el que cubre DocuMente MVP**
- First Line Review and Testing Standards
- First Line Review and Testing Template
- Model Validation Templates
- Independent Validation Standards
- Model Inventory and MRM System Standards

Y documentos de referencia: MRM Policy, MRM Procedures, Model Risk Assessment Methodology, Guidance on Model Identification and EUC Models, MRM System User Guide, FAQ.

---

## 12. Reglas de validación que DocuMente debe aplicar al documento

Estas reglas se traducen a tests automáticos en `src/core/rules/`:

1. **Independencia del Reviewer**: si se intenta poner un usuario como First Line Reviewer y aparece como Owner o Developer del mismo modelo → bloquear con mensaje claro.
2. **Completitud por sección obligatoria**: ninguna sección obligatoria del template puede quedar vacía antes de transición a `In Review`.
3. **Tier coherente**: si se declara `Critical` o `Very High`, validar que las secciones de "Limitations", "Key Assumptions" y "Development Testing" tengan contenido sustancial (no solo un párrafo).
4. **Bitácora de cambios poblada**: la tabla Version Control no puede estar vacía al pasar a `Approved`.
5. **Audit trail completo**: cada transición de estado y cada edición tiene who/when/what/why.
6. **Use restrictions explícitas**: si el modelo se usa para reporting regulatorio (Stat, GAAP, tax), validar que `Use Restrictions` no esté vacío.
7. **Reviewer firmó antes de Approved**: validar que existe evento de sign-off por rol Reviewer en el audit trail antes de permitir `Approved`.

---

## 13. Glosario rápido (jerga MRM)

| Término | Significado |
|---|---|
| **MRM** | Model Risk Management |
| **MRC** | Model Risk Committee |
| **ORC** | Operational Risk Committee |
| **RSC** | Risk Steering Committee |
| **FAE** | Functional Area Executive |
| **FA** | Functional Area |
| **FAWG** | Functional Area Working Group |
| **FLRT** | First Line Review and Testing |
| **LoD** | Line of Defense |
| **EUC** | End User Computing Tool |
| **HMRM** | Head of Model Risk Management |
| **CAD** | Corporate Audit Department |
| **Effective Challenge** | Capacidad real (independencia + expertise) de cuestionar el modelo |
| **Anchor Rating** | Combinación de Materiality + Criticality que determina inherent risk |
| **Effective Validation** | Validación que asegura que supuestos y limitaciones están identificados y evaluados |

---

## Notas de mantenimiento

- Cualquier actualización a `MRM Policy.pdf` o `MRM Standard.pdf` requiere re-sincronizar este archivo.
- Cuando se incorporen otros tipos de documentos a DocuMente (FLRT, Independent Validation), agregar secciones específicas.
- El equipo de Riesgos / MRM de SMNYL es la autoridad final sobre interpretación. Cualquier conflicto entre este archivo y los PDFs originales se resuelve a favor de los PDFs.
