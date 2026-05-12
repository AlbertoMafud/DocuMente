# DocuMente — End-to-End Test Scenario

> **Documento de simulación para validación de calidad.**
>
> Este documento NO es documentación de un modelo real. Es un fixture sintético que ilustra cómo se comportaría DocuMente recorriendo un journey completo (crear desde cero → onboarding → entrevista de 28 secciones → omisiones → sign-offs → export ES + EN → audit trail) con contenido al nivel de calidad esperado (MRM-grade, vocabulario actuarial preciso, tono regulatorio).
>
> **Propósito:** que Alberto pueda evaluar la calidad de DocuMente antes de exponerla a stakeholders reales, sin gastar tiempo de personas reales ni filtrar información institucional.
>
> **Cómo leerlo:**
> 1. Recorre el walkthrough en orden (§3) — cada paso muestra inputs del usuario, preguntas de Claude, borradores generados, y eventos de audit.
> 2. Aplica el checklist (§7) al final para evaluar calidad de pregunta, calidad de redacción, audit, omisiones, traducción y state machine.
> 3. Si la calidad simulada se siente fuerte, podemos ejecutar el mismo escenario en la app real para comparar.
>
> **Datos sintéticos:** todos los nombres de personas, IDs de modelo, cifras y referencias son inventados. Plausibles, no reales.

---

## 1. Índice

1. [Modelo bajo prueba — snapshot](#2-modelo-bajo-prueba--snapshot)
2. [Walkthrough cronológico](#3-walkthrough-cronológico)
3. [Audit trail completo](#4-audit-trail-completo)
4. [Métricas de uso del LLM](#5-métricas-de-uso-del-llm)
5. [Validation checklist](#7-validation-checklist-para-alberto)

---

## 2. Modelo bajo prueba — snapshot

### 2.1 Identidad del modelo

| Campo | Valor |
|---|---|
| **Nombre** | Modelo de Pricing GMM Individual — Nuevos Negocios |
| **Model ID** | M07.P02.S04.012.A |
| **Nomenclatura** | M07.P02.S04.012.A |
| **Clase** | Pricing |
| **Profit Center** | Vida + Salud — Subdirección Productos GMM (GMM-IND-001) |
| **Tier de Riesgo Inherente** | high |
| **Versión actual** | 2.1 |
| **Estado** | In production (re-calibración trimestral) |
| **Fecha de producción target (v1.0)** | 2024-09-01 |
| **Plataforma de implementación** | Prophet 7.5 (motor de cálculo) + R 4.3 (post-procesamiento) + AWS S3 (snapshots) + SQL Server 2019 (data admin) |

### 2.2 Responsables (todos sintéticos)

| Rol | Persona |
|---|---|
| Model Owner | Ana Salinas — Subgerente Pricing GMM Individual |
| Model Developers | Diego Reyes Aguilar (actuario senior); Mariana Pacheco Núñez (actuario) |
| FAE | Roberto Castañeda Mendoza — Subdirector Productos GMM |
| Reviewer (Riesgos) | Pablo Hinojosa Cárdenas — Subdirección Riesgos de Modelos |
| Usuarios | Pricing actuarios; Reservas (BEL IFRS17); Capital regulatorio; Comité de Producto |

### 2.3 Uso intencionado y restricciones

- **Intended use:** Determinar prima de tarifa para nuevos negocios GMM individual; calcular factores de ajuste por canal de venta, región y edad del asegurado.
- **Restrictions:** No usar para renovaciones (modelo separado M07.P02.S04.013.A); no usar para pólizas grupales; resultados para asegurados menores de 18 años requieren factor manual definido por Comité de Producto.
- **Financial impact:** Determinación de prima para ~80,000 nuevas pólizas anuales (~MXN 1,200 M en prima primer año).

### 2.4 Diagrama narrativo de dependencias

**Upstream (modelos/insumos que alimentan el modelo de pricing):**

1. **Modelo de Mortalidad SMNYL (M01.P01.S01.002.A)** — tabla de mortalidad GMM con experiencia 2018-2022, calibrada a la población asegurada SMNYL. Contacto técnico: Gerencia de Experiencia, Inventario MRM `M01.P01.S01.002.A`.
2. **Modelo de Morbilidad GMM (M02.P02.S03.005.A)** — frecuencias y severidades por padecimiento, segmentadas por edad/género/región. Contacto: Subgerencia Morbilidad. Inventario MRM `M02.P02.S03.005.A`.
3. **Tabla de Gastos Corporativos 2024-Q4** — supuestos de gastos de adquisición, mantenimiento, claim handling. Definida por Finanzas. Set ID `GTC-2024-Q4`.
4. **ESG Corporativo (M00.P00.S00.001.E)** — generador de escenarios económicos: yields, inflación médica, tipo de cambio. Calibración trimestral por Tesorería.

**Downstream (consumidores de los outputs):**

1. **Modelo de Reservas BEL IFRS17 (M08.P02.S05.020.A)** — consume las primas de tarifa para validar el cumplimiento del límite de contrato (contract boundary test).
2. **Cálculo de Capital Regulatorio (M09.P02.S06.030.A)** — usa la cartera proyectada para Solvencia mexicana CNSF.
3. **Cuenta de Resultados Pricing-vs-Reserva** — Finanzas usa el output para conciliar tarifa esperada contra reserva calculada.

---

## 3. Walkthrough cronológico

> Convenciones:
> - `[Claude]` — pregunta o instrucción que Claude (Sonnet 4.6 en chat, Opus 4.7 en drafting) genera.
> - `[Ana]` — respuesta del Model Owner simulado (Ana Salinas, actuaria senior).
> - `[Drafter]` — borrador final producido por Opus 4.7 al cerrar la sección, formato listo para Word.
> - `[Audit]` — evento registrado en `audit_trail` con timestamp simulado.
> - Timestamps simulados: arrancan en `2026-05-08T09:00:00-06:00` y avanzan plausiblemente.

---

### Step 1 — Crear documento desde cero

**Pantalla:** `/crear_nuevo` (la pantalla que añadimos en esta sesión).

**Inputs de Ana:**

- Nombre del modelo: `Modelo de Pricing GMM Individual — Nuevos Negocios`
- Model ID: `M07.P02.S04.012.A`

**Llamada al use case:**

```python
uc = CrearDocumentoEnBlanco(repo=DocumentoRepository())
documento = uc.ejecutar(
    nombre_modelo="Modelo de Pricing GMM Individual — Nuevos Negocios",
    model_id="M07.P02.S04.012.A",
    user_id="ana.salinas",  # En la app real, viene de Cognito; en MVP siempre "default"
)
```

**Estado resultante:**

- `Documento.id` = `e8f3a1c2-9b4d-4e5a-bc11-7d2f8a91c4e3`
- `Documento.estado` = `"draft"`
- `Documento.secciones` = 28 secciones, todas con `contenido=None`, `completitud="vacia"`
- `Documento.metadata_modelo.nombre_modelo` = `"Modelo de Pricing GMM Individual — Nuevos Negocios"`
- `Documento.metadata_modelo.model_id` = `"M07.P02.S04.012.A"`
- `Documento.metricas_uso.llamadas` = `[]` (vacío — no se han hecho llamadas LLM)
- `Documento.memoria_modelo.esta_vacia` = `True`

**[Audit] 2026-05-08T09:00:12-06:00**
- `tipo`: `documento_creado`
- `actor`: `ana.salinas`
- `descripcion`: `Documento creado desde cero: Modelo de Pricing GMM Individual — Nuevos Negocios`
- `metadata`: `{"model_id": "M07.P02.S04.012.A"}`

**Routing:** la pantalla redirige a `/onboarding`.

---

### Step 2 — Onboarding (captura de hechos transversales)

**Pantalla:** `/onboarding`.

**Inputs de Ana** (los 9 campos de `MemoriaModelo`):

| Campo | Valor capturado |
|---|---|
| `plataforma` | Prophet 7.5 + R 4.3 |
| `lenguaje_codigo` | R (post-procesamiento); Prophet TML (motor) |
| `frecuencia_corridas` | Recalibración trimestral (último día hábil del trimestre); ejecución diaria en pipeline pricing |
| `esg_usado` | ESG Corporativo SMNYL — calibración 2024-Q4 (M00.P00.S00.001.E) |
| `rutas_principales` | `/prod/pricing/gmm-ind/inputs/`, `s3://smnyl-pricing-snapshots/gmm-ind/`, `sqlserver://prod-actuarial/db_admin_polizas` |
| `owner_responsable` | Ana Salinas |
| `fae_responsable` | Roberto Castañeda Mendoza |
| `dependencias_upstream` | Modelo Mortalidad SMNYL (M01.P01.S01.002.A); Modelo Morbilidad GMM (M02.P02.S03.005.A); Tabla Gastos Corporativos 2024-Q4; ESG Corporativo |
| `dependencias_downstream` | Reservas BEL IFRS17 (M08.P02.S05.020.A); Capital Regulatorio (M09.P02.S06.030.A); Cuenta de Resultados Pricing-vs-Reserva |

Click "Guardar y continuar".

**Estado resultante:**

`Documento.memoria_modelo` ahora tiene los 9 campos poblados; `memoria_modelo.fuente_ultima_actualizacion` = `"onboarding"`. El método `renderizar_para_prompt()` ya devuelve un bloque markdown que se inyectará en cada interview prompt como "## HECHOS YA CONOCIDOS DEL MODELO (no preguntes por estos)".

**[Audit] 2026-05-08T09:04:38-06:00**
- `tipo`: `metadata_actualizada`
- `actor`: `ana.salinas`
- `descripcion`: `Onboarding completado — 9 hechos transversales capturados`
- `metadata`: `{"fuente": "onboarding", "campos_actualizados": "9"}`

**Routing:** redirige a `/dashboard`.

---

### Step 3 — Editor de metadata (completar los 16 campos)

**Pantalla:** `/dashboard` → click en card de Metadata → modal "Editor de metadata".

**Inputs de Ana** (los 16 campos de `MetadataModelo`, mostrando solo los que cambian — `nombre_modelo` y `model_id` ya estaban):

| Campo | Valor |
|---|---|
| `model_class` | Pricing |
| `profit_center` | GMM-IND-001 |
| `fae` | Roberto Castañeda Mendoza |
| `model_owner` | Ana Salinas |
| `model_developers` | `["Diego Reyes Aguilar", "Mariana Pacheco Núñez"]` |
| `model_users` | `["Pricing actuarios", "Reservas (BEL IFRS17)", "Capital regulatorio", "Comité de Producto"]` |
| `current_version` | 2.1 |
| `implementation_platform` | Prophet 7.5 + R 4.3 + AWS S3 + SQL Server 2019 |
| `financial_impact` | Determinación de prima para ~80,000 nuevas pólizas anuales (~MXN 1,200 M en prima primer año) |
| `model_status` | In production |
| `target_production_date` | 2024-09-01 (versión 1.0); 2026-03-15 (versión 2.1 — recalibración Q1) |
| `inherent_risk_tier` | `high` |
| `intended_use` | Determinar prima de tarifa para nuevos negocios GMM individual; calcular factores de ajuste por canal de venta, región y edad del asegurado |
| `use_restrictions` | No usar para renovaciones (modelo separado M07.P02.S04.013.A); no usar para pólizas grupales; resultados para asegurados <18 años requieren factor manual definido por Comité de Producto |
| `nomenclatura` | M07.P02.S04.012.A |

Click "Guardar metadata".

**[Audit] 2026-05-08T09:11:22-06:00**
- `tipo`: `metadata_actualizada`
- `actor`: `ana.salinas`
- `descripcion`: `Metadata del modelo actualizada — 14 campos modificados`
- `metadata`: `{"delta": "model_class, profit_center, fae, model_owner, model_developers, model_users, current_version, implementation_platform, financial_impact, model_status, target_production_date, inherent_risk_tier, intended_use, use_restrictions"}`

---

### Step 4 — Sección 1.3 Problem Statement

**Intención (verbatim del catálogo):** *Descripción de alto nivel del problema o necesidad que el modelo resuelve, incluyendo restricciones informacionales, computacionales o analíticas bajo las que se desarrolló.*

**Preguntas guía:** ¿Cuál es el problema? · ¿Existe modelo previo? · ¿Restricciones? · ¿Productos cubiertos?

#### Interview transcript (5 turnos)

**Turno 1**

`[Claude]` Para arrancar con la sección 1.3 Problem Statement: ¿qué problema concreto resuelve este modelo y por qué se construyó como un modelo separado, en lugar de extender uno existente?

`[Ana]` El modelo determina la prima de tarifa para nuevos negocios GMM individual. Antes teníamos la versión 1.0 (2024) que era una extensión paramétrica de un GLM viejo, pero no capturaba bien la interacción entre edad y canal de venta, especialmente para banca-seguros. Lo separamos porque la versión anterior estaba acoplada al motor de renovaciones y dificultaba calibrar pricing sin recompilar todo.

**Turno 2**

`[Claude]` Mencionas que la versión 1.0 no capturaba bien la interacción edad × canal. ¿Hubo un evento de negocio o de pérdida que disparó la decisión de rediseñar, o fue una mejora identificada en la attestation anual de Riesgos?

`[Ana]` Fue Riesgos en la attestation 2025. El backtest de la versión 1.0 mostraba un sesgo sistemático de +6.2% en prima esperada vs siniestralidad observada para el canal banca-seguros en edades 30-45. Riesgos lo elevó como hallazgo de severidad alta y Comité de Producto autorizó el rediseño con calendario hasta 2026-Q1.

**Turno 3**

`[Claude]` ¿Bajo qué restricciones de plataforma, datos o regulatorias tuvo que diseñarse el modelo 2.0?

`[Ana]` Tres restricciones principales. Primero, plataforma: tuvo que correr en Prophet 7.5 porque es el motor oficial de pricing y migrar a otra plataforma no estaba autorizado. Segundo, datos: solo experiencia hasta 2022-12 al cierre de calibración inicial; los siniestros 2023-2024 se usaron como holdout para validación, no para fit. Tercero, regulatorio: los outputs deben ser consumibles por el modelo de reservas BEL bajo IFRS17, lo que obliga a respetar el contract boundary test (la prima debe ser técnicamente sostenible aislada, sin cross-subsidio con renovaciones).

**Turno 4**

`[Claude]` ¿Qué productos y canales cubre exactamente, y cuáles están explícitamente fuera del alcance?

`[Ana]` Cubre los tres planes vigentes GMM individual: Plan A (suma asegurada hasta MXN 1.5M), Plan B (hasta MXN 5M), Plan C (hasta MXN 15M). Canales: agente tradicional, broker y banca-seguros. Fuera del alcance: pólizas grupales (las maneja otro modelo), renovaciones (modelo M07.P02.S04.013.A), y asegurados menores de 18 años — para estos últimos se aplica un factor manual definido por Comité de Producto porque la experiencia es insuficiente para calibrar estadísticamente.

**Turno 5**

`[Claude]` Último contexto: ¿hay algún cambio regulatorio o de plataforma anticipado que pueda obligar a retocar el modelo en los próximos 12 meses?

`[Ana]` Sí, dos: (a) CNSF está revisando los lineamientos de Solvencia que podrían cambiar los recargos de riesgo aplicables al pricing en 2027 — eso obligaría a recalibrar los márgenes técnicos, no la estructura. (b) Hay una migración planeada de Prophet 7.5 a 7.7 en 2026-Q4; la lógica del modelo debería ser portable, pero requerirá re-testing de regresión.

`[Claude]` `SECCION_COMPLETA`

> Resumen: el modelo resuelve la determinación de prima para nuevos negocios GMM individual (Planes A/B/C; canales agente, broker, banca-seguros) y nace de un hallazgo de severidad alta levantado por Riesgos en la attestation 2025 sobre la versión 1.0 (sesgo +6.2% en banca-seguros 30-45). Restricciones de diseño: Prophet 7.5, datos hasta 2022-12 para fit y 2023-2024 para holdout, contract boundary test bajo IFRS17. Cambios anticipados: revisión CNSF Solvencia (2027) y migración Prophet 7.5→7.7 (2026-Q4).

#### [Drafter] Borrador final — Sección 1.3 Problem Statement

> El modelo determina la prima de tarifa para nuevos negocios GMM individual, cubriendo los tres planes vigentes de la cartera (Plan A con suma asegurada hasta MXN 1.5 millones, Plan B hasta MXN 5 millones, Plan C hasta MXN 15 millones) y los tres canales de distribución activos (agente tradicional, broker y banca-seguros). Quedan explícitamente fuera del alcance las pólizas grupales (cubiertas por modelo independiente), las renovaciones (modelo M07.P02.S04.013.A) y los asegurados menores de 18 años, para los cuales se aplica un factor manual definido por el Comité de Producto en ausencia de experiencia suficiente para calibración estadística.
>
> La versión 2.0 sustituye a la versión 1.0 (2024), una extensión paramétrica de un GLM previamente acoplado al motor de renovaciones. La motivación del rediseño proviene del proceso de attestation 2025 conducido por la Subdirección de Riesgos de Modelos: el backtest de la versión 1.0 evidenció un sesgo sistemático de +6.2% en prima esperada respecto a siniestralidad observada en el canal banca-seguros para edades 30-45 años. Riesgos clasificó el hallazgo con severidad alta y el Comité de Producto autorizó la reconstrucción con cronograma de entrega al cierre del primer trimestre de 2026.
>
> El diseño de la versión 2.0 está sujeto a tres restricciones documentadas. Primero, la plataforma debe ser Prophet 7.5, motor oficial de pricing en la institución; la migración a una plataforma alternativa no fue autorizada. Segundo, la calibración inicial utilizó exclusivamente la experiencia siniestral observada hasta diciembre de 2022, reservando los años 2023 y 2024 como conjunto de holdout para validación externa. Tercero, los resultados del modelo deben ser consumibles por el modelo de reservas Best Estimate Liability (BEL) bajo el marco IFRS 17, lo que exige que el pricing respete el contract boundary test y sea técnicamente sostenible de forma aislada, sin compensación cruzada con la cartera renovada.
>
> Se anticipan dos eventos en los próximos doce meses que podrían motivar revisiones puntuales: la revisión de los lineamientos de Solvencia por parte de la CNSF, que podría modificar los recargos de riesgo aplicables al pricing en el ejercicio 2027 y obligaría a recalibrar los márgenes técnicos sin alterar la estructura del modelo; y la migración planeada de Prophet 7.5 a 7.7 en el cuarto trimestre de 2026, que requerirá pruebas de regresión sobre toda la lógica implementada.

**[Audit] 2026-05-08T09:34:51-06:00**
- `tipo`: `seccion_completada`
- `actor`: `ana.salinas`
- `seccion_id`: `1.3.problem_statement`
- `descripcion`: `Sección 1.3 Problem Statement completada (5 turnos de entrevista)`

---

### Step 5 — Sección 2.1 Model Uses

**Intención:** *Descripción de todos los usuarios intencionados y frecuencia de uso.*

#### Interview transcript (3 turnos)

**T1.** `[Claude]` ¿Quiénes son los usuarios intencionados del modelo y con qué frecuencia consumen sus outputs?

`[Ana]` Los actuarios de pricing son el usuario primario — consumen la tarifa diariamente vía pipeline automatizado y la recalibran trimestralmente. Reservas BEL la consume al cierre mensual para el contract boundary test. Capital regulatorio la usa anualmente para Solvencia. El Comité de Producto la consume ad-hoc cuando aprueba nuevos planes o factores especiales.

**T2.** `[Claude]` Mencionaste "diariamente vía pipeline" para pricing. ¿Es una ejecución batch sin intervención humana, o requiere validación manual antes de publicar la tarifa?

`[Ana]` Es batch automatizado: corre a las 03:00 hrs en el pipeline de SQL Server, escribe outputs a S3 y notifica por correo. Solo requiere validación humana si los controles de calidad disparan alerta — desviación >2σ contra el día anterior o falla de checksum en upstream. En ese caso, un actuario revisa antes de publicar.

**T3.** `[Claude]` ¿Qué usos están explícitamente fuera del alcance del modelo?

`[Ana]` Tres usos prohibidos: (1) renovaciones — existe modelo separado; (2) negocios grupales o colectivos; (3) cualquier asegurado menor de 18 años requiere intervención manual del Comité de Producto, no debe consumirse la prima del modelo directamente.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 2.1 Model Uses

> El modelo es consumido por cuatro audiencias institucionales con frecuencias diferenciadas. Los actuarios de pricing constituyen el usuario primario: consumen la tarifa diariamente a través del pipeline automatizado de Prophet en SQL Server y participan en la recalibración trimestral del modelo. El equipo de Reservas Best Estimate Liability consume los outputs al cierre mensual contable para ejecutar el contract boundary test exigido por IFRS 17. El equipo de Capital Regulatorio incorpora la cartera proyectada en el cálculo anual de Solvencia bajo lineamientos CNSF. El Comité de Producto consume el modelo de manera ad-hoc cuando aprueba nuevos planes comerciales o autoriza factores especiales.
>
> La ejecución diaria del pipeline ocurre a las 03:00 horas en modo batch automatizado, escribiendo los outputs a snapshots en S3 y emitiendo notificación por correo electrónico. La intervención humana se activa exclusivamente cuando los controles de calidad disparan alerta — desviación superior a dos desviaciones estándar respecto a la corrida previa o falla en el checksum de los archivos upstream. En tales casos, un actuario asignado de turno revisa el output antes de autorizar la publicación.
>
> Quedan explícitamente fuera del alcance tres usos: la determinación de prima para renovaciones (atribuida al modelo M07.P02.S04.013.A); el pricing de cualquier negocio grupal o colectivo; y la determinación automática de prima para asegurados menores de 18 años, supuesto en el cual el output del modelo no debe ser consumido sin la intervención manual del Comité de Producto y la aplicación del factor de ajuste correspondiente.

**[Audit] 2026-05-08T09:48:14-06:00** — `seccion_completada` · `2.1.model_uses` · 3 turnos.

---

### Step 6 — Sección 2.2 Model Scope

**Intención:** *Productos modelados, descripciones de alto y bajo nivel.*

#### Interview transcript (4 turnos)

**T1.** `[Claude]` Para 2.2 Model Scope: enumera los productos cubiertos y para cada uno indica el tamaño del bloque actual.

`[Ana]` Tres productos. Plan A (GMM básico, suma asegurada hasta MXN 1.5M): aproximadamente 220,000 pólizas activas, prima anual MXN 1,800 M. Plan B (intermedio, hasta MXN 5M): 95,000 pólizas, prima MXN 2,400 M. Plan C (premium, hasta MXN 15M): 18,000 pólizas, prima MXN 1,100 M. Total cartera ~333,000 pólizas vigentes.

**T2.** `[Claude]` ¿Qué features modelaste explícitamente para cada plan y cuáles dejaste fuera deliberadamente?

`[Ana]` Para los tres planes modelamos: frecuencia de siniestros por padecimiento mayor, severidad neta de deducible y coaseguro, tasa de cancelación temprana (lapse en los primeros 24 meses), y gastos de mantenimiento. Dejamos fuera: rider de gastos funerarios — porque tiene su propio módulo de pricing; reembolso de medicamentos ambulatorios — porque el dato granular llegó después del cierre de calibración (2023); y cobertura odontológica — no la ofrecemos comercialmente en estos planes.

**T3.** `[Claude]` ¿Hay diferencias estructurales relevantes entre planes que justifiquen tratamientos modelados distintos, o la única diferencia es el monto de suma asegurada?

`[Ana]` Sí, hay dos diferencias estructurales. Primero, el Plan C tiene un deducible variable (escalonado por edad) mientras que A y B tienen deducible fijo — eso afecta la severidad neta. Segundo, el Plan B incluye cobertura ambulatoria expandida que A no tiene, lo que modifica la frecuencia esperada de siniestros menores. La estructura del modelo lo refleja con un término de interacción plan × cobertura.

**T4.** `[Claude]` ¿Cuál es el bloque más sensible a desviaciones del modelo, en términos de impacto financiero?

`[Ana]` Plan B, por mucho. Aporta el 50% de la prima total con solo 28% de las pólizas, y la siniestralidad es más volátil por el componente ambulatorio. Un sesgo de 5% en la prima del Plan B mueve MXN 120M de utilidad anual.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 2.2 Model Scope

> El modelo cubre los tres planes vigentes de la oferta GMM individual con la composición de cartera descrita a continuación. El Plan A (cobertura básica con suma asegurada hasta MXN 1.5 millones) registra aproximadamente 220,000 pólizas activas y una prima anual agregada de MXN 1,800 millones. El Plan B (cobertura intermedia con suma asegurada hasta MXN 5 millones e inclusión de coberturas ambulatorias expandidas) representa 95,000 pólizas y MXN 2,400 millones en prima anual. El Plan C (cobertura premium con suma asegurada hasta MXN 15 millones y deducible variable escalonado por edad) comprende 18,000 pólizas y MXN 1,100 millones de prima anual. La cartera total cubierta por el modelo asciende a aproximadamente 333,000 pólizas vigentes.
>
> Para los tres planes el modelo cuantifica explícitamente cuatro componentes: la frecuencia esperada de siniestros por padecimiento mayor, la severidad neta de deducible y coaseguro, la tasa de cancelación temprana (lapse en los primeros 24 meses de antigüedad) y los gastos de mantenimiento. Quedan deliberadamente fuera del alcance del modelo tres componentes: el rider de gastos funerarios, que cuenta con módulo de pricing independiente; el reembolso de medicamentos ambulatorios, cuyos datos granulares se incorporaron al sistema con posterioridad al cierre de calibración inicial en 2023; y la cobertura odontológica, no ofrecida comercialmente en estos planes.
>
> Dos diferencias estructurales entre planes justifican tratamientos modelados específicos. El Plan C presenta deducible variable escalonado por edad, lo cual modifica la distribución de severidad neta respecto a los planes A y B (deducible fijo). El Plan B incluye cobertura ambulatoria expandida ausente en el Plan A, factor que altera la frecuencia esperada de siniestros menores. Ambas diferencias se capturan en el modelo mediante un término de interacción plan × tipo de cobertura.
>
> Desde una perspectiva de sensibilidad financiera, el Plan B concentra el mayor riesgo de modelo: aporta el 50% de la prima total agregada con solo el 28% de las pólizas vigentes, y exhibe la mayor volatilidad de siniestralidad observada por el componente ambulatorio. Un sesgo del 5% en la prima del Plan B se traduce en una desviación aproximada de MXN 120 millones en utilidad técnica anual, lo que justifica el monitoreo prioritario de este segmento en el régimen de monitoreo descrito en la sección 9.

**[Audit] 2026-05-08T10:08:32-06:00** — `seccion_completada` · `2.2.model_scope` · 4 turnos.

---

### Step 7 — Sección 2.3 Business Impact of Model Usage

#### Interview transcript (3 turnos)

**T1.** `[Claude]` ¿Cómo encaja este modelo en las decisiones del negocio y qué se hace con sus outputs?

`[Ana]` Tres usos principales. El primero y más directo: la tarifa publicada en sistemas comerciales viene de aquí — agentes, brokers y plataformas digitales cotizan con estos números. El segundo: Reservas usa el output para validar IFRS17 contract boundary y para alimentar el cálculo de margen de servicio contractual (CSM). El tercero: Comité de Producto usa los outputs para decidir si lanzar un nuevo plan o ajustar comisiones por canal.

**T2.** `[Claude]` ¿Hay alguna regulación que obligue explícitamente al uso de un modelo de esta naturaleza?

`[Ana]` Sí. La Circular Única de Seguros y Fianzas (CUSF) de CNSF exige que las primas de tarifa sean técnicamente sustentables y se documente la metodología. Adicionalmente, IFRS 17 (aplicado desde 2023 en SMNYL) requiere la prueba de contract boundary en cada cierre, lo cual depende de la prima de tarifa generada por este modelo.

**T3.** `[Claude]` ¿Qué pasa si el modelo falla — qué decisiones se quedan sin soporte y qué workaround existe?

`[Ana]` Si el pipeline diario falla, se republica la tarifa del día anterior — eso es un control oficial documentado. Si la recalibración trimestral se atrasa, Pricing tiene un protocolo para extender la tarifa vigente hasta 60 días con monitoreo intensivo de siniestralidad. Más allá de 60 días sin recalibración requiere autorización del FAE.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 2.3 Business Impact of Model Usage

> El modelo soporta tres decisiones de negocio críticas en la institución. La tarifa publicada en los sistemas comerciales — utilizada por agentes, brokers y plataformas digitales para cotizar nuevos negocios — se origina directamente en los outputs del modelo. El equipo de Reservas consume el output para ejecutar la prueba de contract boundary exigida por IFRS 17 y para alimentar el cálculo del Contractual Service Margin (CSM). El Comité de Producto utiliza los resultados para sustentar decisiones de lanzamiento de nuevos planes y ajustes de comisiones por canal de distribución.
>
> Existen dos requisitos regulatorios que sostienen explícitamente la existencia y mantenimiento del modelo. La Circular Única de Seguros y Fianzas (CUSF) emitida por la Comisión Nacional de Seguros y Fianzas exige que las primas de tarifa de los productos individuales sean técnicamente sustentables y que la metodología subyacente esté documentada con trazabilidad suficiente para revisión regulatoria. Adicionalmente, el marco IFRS 17, vigente en la institución desde el ejercicio 2023, requiere la ejecución de la prueba de contract boundary en cada cierre contable, prueba cuyo insumo principal es la prima de tarifa producida por el presente modelo.
>
> Se han establecido protocolos de contingencia documentados frente a fallas operativas. Ante una falla en la ejecución del pipeline diario, el control oficial autorizado consiste en la republicación de la tarifa del día hábil anterior, manteniendo así la continuidad operativa de los sistemas comerciales. Frente a un atraso en la recalibración trimestral, la Subgerencia de Pricing aplica un protocolo de extensión de la tarifa vigente por un máximo de 60 días, acompañado de monitoreo intensivo de siniestralidad observada. Cualquier extensión superior a 60 días sin recalibración requiere autorización expresa del Functional Area Executive del modelo.

**[Audit] 2026-05-08T10:25:11-06:00** — `seccion_completada` · `2.3.business_impact` · 3 turnos.

---

### Step 8 — Sección 3.1 Ancillary documents list

#### Interview transcript (2 turnos — sección de naturaleza list-form)

**T1.** `[Claude]` Para 3.1: ¿qué documentos relacionados existen y dónde se ubican?

`[Ana]` Cinco principales. (1) Memoria técnica de la versión 1.0 — en SharePoint Pricing GMM /docs/v1.0/memoria_tecnica_2024.pdf. (2) Reporte de hallazgos de attestation 2025 — Riesgos /attestation-2025/M07.P02.S04.012/. (3) Especificación funcional de Comité de Producto para v2.0 — SharePoint /docs/v2.0/spec_v2_aprobada_2025-Q2.pdf. (4) Plan de validación independiente — Riesgos /validacion-2026/. (5) Bitácora de calibración trimestral — repositorio interno R Studio Server /home/pricing-gmm/calibraciones/.

**T2.** `[Claude]` ¿Alguno de estos documentos tiene control de versiones o estatus de aprobación que valga registrar?

`[Ana]` Sí. La especificación funcional (3) está en versión 1.3 aprobada por Comité de Producto el 2025-08-12. El plan de validación (4) está en versión 2.0 firmado por Pablo Hinojosa (Riesgos) el 2026-01-15.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 3.1 Ancillary documents list

> Se documentan cinco fuentes auxiliares relevantes para la trazabilidad técnica e histórica del modelo. La memoria técnica de la versión 1.0 del modelo se encuentra disponible en el repositorio SharePoint de Pricing GMM, ruta `/docs/v1.0/memoria_tecnica_2024.pdf`. El reporte de hallazgos de la attestation 2025 conducida por la Subdirección de Riesgos de Modelos, fuente del mandato de rediseño, se ubica en `/attestation-2025/M07.P02.S04.012/` del repositorio de Riesgos. La especificación funcional aprobada por el Comité de Producto para la versión 2.0, en su versión 1.3 con aprobación de fecha 12 de agosto de 2025, se encuentra en `/docs/v2.0/spec_v2_aprobada_2025-Q2.pdf` del SharePoint corporativo. El plan de validación independiente, en su versión 2.0 firmado por la Subdirección de Riesgos de Modelos con fecha 15 de enero de 2026, se ubica en `/validacion-2026/` del repositorio de Riesgos. La bitácora de calibración trimestral del modelo, actualizada al cierre de cada trimestre operativo, se mantiene en el servidor R Studio Server interno bajo la ruta `/home/pricing-gmm/calibraciones/`.

**[Audit] 2026-05-08T10:38:02-06:00** — `seccion_completada` · `3.1.ancillary` · 2 turnos.

---

### Step 9 — Sección 3.2 Additional Documents · OMITIDA

Ana decide omitir 3.2 porque la documentación adicional (manuales de usuario, fichas de cobertura) está siendo rediseñada por Marketing y se incorporará en la versión 2.2 del modelo prevista para 2026-Q3.

**Acción UI:** click "Omitir sección" en card de 3.2 → modal con dropdown de motivo → selecciona "Pendiente para versión futura" → textarea opcional: *"Documentación adicional de producto en rediseño por Marketing; se incorporará en la próxima versión del modelo (v2.2, 2026-Q3)."* → confirmar.

**Llamada al use case:**

```python
uc = OmitirSeccion(repo=DocumentoRepository())
uc.ejecutar(
    documento_id=doc.id,
    seccion_id="3.2.additional",
    motivo="Pendiente para versión futura",
    detalle="Documentación adicional de producto en rediseño por Marketing; "
            "se incorporará en la próxima versión del modelo (v2.2, 2026-Q3).",
    actor="ana.salinas",
)
```

**Estado:** `Documento.seccion_por_id("3.2.additional").completitud == "omitida"`; `motivo_omision` poblado.

**[Audit] 2026-05-08T10:40:15-06:00**
- `tipo`: `seccion_omitida`
- `actor`: `ana.salinas`
- `seccion_id`: `3.2.additional`
- `descripcion`: `Sección 3.2 omitida — motivo: Pendiente para versión futura`
- `metadata`: `{"motivo": "Pendiente para versión futura", "detalle": "Documentación adicional de producto en rediseño por Marketing; se incorporará en la próxima versión del modelo (v2.2, 2026-Q3)."}`

---

### Step 10 — Sección 4.1 Schematic Diagram

#### Interview transcript (3 turnos — sección con [Pendiente: imagen])

**T1.** `[Claude]` Para 4.1: describe el flujo del modelo de extremo a extremo — cómo entran los datos, qué hace Prophet, qué hace R, y qué consumen los downstream.

`[Ana]` Cuatro bloques. Bloque 1: inputs llegan a SQL Server desde las administradoras de pólizas (Solix) cada noche; un proceso ETL prepara el data mart `prophet_inputs_pricing_gmm`. Bloque 2: Prophet 7.5 ejecuta el motor de cálculo — toma cohortes de Model Points (MP), aplica supuestos calibrados, y produce primas brutas por póliza tipo. Bloque 3: R 4.3 post-procesa los outputs de Prophet — agrega factores de ajuste por canal, aplica la lógica de banca-seguros, y genera la tarifa publicable. Bloque 4: outputs van a S3 (snapshot diario) y notifican a downstream — Reservas, Capital, sistemas comerciales.

**T2.** `[Claude]` ¿Existe un diagrama formal del flujo, o lo construyes ad-hoc?

`[Ana]` Existe un diagrama en Visio que mantiene el equipo de DevOps de Pricing. Lo actualizamos en cada release mayor. El más reciente es del 2026-03-15 (versión 2.1). Lo puedo adjuntar como apéndice del documento.

**T3.** `[Claude]` ¿Hay puntos de control humano dentro del flujo, o es completamente automatizado?

`[Ana]` Tres controles automáticos sin intervención humana en operación diaria: (1) validación de checksums sobre archivos Solix antes de ejecutar; (2) validación de rango sobre prima resultante (max ±2σ vs día anterior); (3) reconciliación de cuentas en el output (suma de primas por plan = control acumulado). Si cualquier control falla, el pipeline aborta y notifica.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 4.1 Schematic Diagram

> El flujo de procesamiento del modelo se compone de cuatro bloques secuenciales con responsabilidades técnicas diferenciadas. El primer bloque corresponde al subsistema de ingesta y preparación de datos: los archivos transaccionales originados en el sistema administrador de pólizas Solix se incorporan diariamente a SQL Server mediante un proceso ETL operado por el equipo de Datos de Pricing, generando el data mart `prophet_inputs_pricing_gmm` que sirve de fuente única de verdad para la ejecución posterior. El segundo bloque comprende la ejecución del motor de cálculo en Prophet 7.5: el motor consume cohortes de Model Points, aplica el conjunto de supuestos calibrados (mortalidad, morbilidad, lapse, gastos, inflación médica) y produce primas brutas por póliza tipo, agregadas a nivel de Model Point. El tercer bloque comprende el post-procesamiento en R 4.3: los outputs de Prophet se enriquecen con factores de ajuste por canal de distribución, se aplica la lógica específica del canal banca-seguros derivada del hallazgo de attestation 2025, y se genera la tarifa publicable en formato consumible por los sistemas comerciales. El cuarto bloque corresponde a la distribución de resultados: los outputs finales se publican como snapshot diario en el bucket S3 `smnyl-pricing-snapshots/gmm-ind/` y se notifican a los sistemas downstream — modelos de reservas BEL, capital regulatorio, y plataformas comerciales — mediante mensajería interna.
>
> El pipeline incorpora tres controles automatizados ejecutados sin intervención humana en operación diaria. El primer control valida los checksums de los archivos Solix antes de iniciar la ejecución y aborta el pipeline si detecta inconsistencia. El segundo control valida que la prima resultante para cada plan se mantenga dentro del rango de dos desviaciones estándar respecto a la corrida del día hábil anterior, deteniendo la publicación en caso de detectar desviación material. El tercer control ejecuta una reconciliación contable comprobando que la suma de primas por plan coincida con el control acumulado independiente generado en SQL Server. Cualquier falla en cualquiera de los tres controles aborta la ejecución y emite notificación inmediata al equipo de turno.
>
> `[Pendiente: insertar como apéndice gráfico el diagrama Visio versión 2.1 (2026-03-15) mantenido por DevOps de Pricing.]`

**[Audit] 2026-05-08T10:58:42-06:00** — `seccion_completada` · `4.1.diagram` · 3 turnos.

---

### Step 11 — Sección 4.2 Model Theory and Logic

**Sección compleja — exercise el patrón "preguntar 'por qué', no solo 'qué'" con 6 turnos.**

#### Interview transcript (6 turnos)

**T1.** `[Claude]` Para 4.2 Theory & Logic: ¿cuál es el algoritmo central del modelo y sobre qué base teórica está construido?

`[Ana]` Es un Generalized Additive Model (GAM) con suavización spline en dos dimensiones — edad del asegurado y antigüedad de la cohorte — combinado con efectos fijos por plan, género y región, y efectos aleatorios por canal de distribución. La frecuencia de siniestros sigue una distribución Poisson; la severidad sigue una Gamma con link log.

**T2.** `[Claude]` ¿Por qué GAM y no algo más simple como un GLM puramente paramétrico, o algo más flexible como un Gradient Boosting Machine?

`[Ana]` Tres razones para GAM. Primero, capturamos la no-linealidad real en edad (curva en U) sin necesidad de fragmentar artificialmente la edad en buckets, que es lo que hacía la versión 1.0 con GLM y producía discontinuidades en frontera. Segundo, los splines mantienen la interpretabilidad — podemos mostrar la curva ajustada y defenderla en attestation, lo cual no se puede con GBM. Tercero, Prophet 7.5 tiene soporte nativo para GAM con `mgcv` integrado; usar GBM nos hubiera obligado a salir de Prophet y romper el contrato de plataforma con TI.

**T3.** `[Claude]` Mencionas que los splines mantienen interpretabilidad. ¿Cómo cuantificas o demuestras esa interpretabilidad — qué entregas a Riesgos cuando te lo piden?

`[Ana]` Entregamos cuatro artefactos. Las curvas spline ajustadas con intervalos de confianza por edad y antigüedad. Los efectos fijos estimados con sus errores estándar (plan, género, región). Los efectos aleatorios por canal con su varianza. Y el reporte de validación cruzada k-fold (k=5) mostrando estabilidad de los coeficientes entre folds. Eso forma parte de la memoria técnica que Riesgos revisa anualmente.

**T4.** `[Claude]` ¿Por qué efectos aleatorios por canal y no efectos fijos?

`[Ana]` Porque los canales tienen volúmenes muy desiguales. Banca-seguros tiene 8,000 pólizas, agente tiene 220,000, broker tiene 105,000. Con efectos fijos, banca-seguros tendría coeficientes inestables — alta varianza en muestras pequeñas. Los efectos aleatorios hacen *shrinkage* hacia la media global cuando el subgrupo es pequeño, lo cual es estadísticamente correcto y reduce el riesgo de sobre-ajuste en banca. Esto fue precisamente el hallazgo de attestation 2025 — la versión 1.0 trataba canal como efecto fijo y eso explicaba el sesgo en banca-seguros.

**T5.** `[Claude]` ¿Qué enfoques alternativos consideraron y por qué no se eligieron?

`[Ana]` Tres alternativas evaluadas en spec funcional. (a) GLM tradicional con interacciones explícitas — descartado por capacidad limitada de capturar no-linealidad y por reintroducir el problema de fronteras. (b) Modelo bayesiano jerárquico — atractivo conceptualmente porque hace explícita la incertidumbre, pero la implementación en Stan habría requerido salir de Prophet, lo cual no se aprobó. (c) Modelo de árboles regularizados (random forest con poda) — alta capacidad predictiva pero baja interpretabilidad regulatoria, descartado por Comité de Producto.

**T6.** `[Claude]` ¿Hay alguna lógica adicional fuera del GAM — reglas de negocio, factores ad-hoc, suelos o techos aplicados post-modelo?

`[Ana]` Sí, tres reglas post-modelo aplicadas en R 4.3. Primero, un piso de prima del 80% sobre la prima del plan adyacente inferior, para evitar inversiones de precio entre planes. Segundo, un factor multiplicativo manual de 1.15 para menores de 25 años hombres por exposición a riesgo de motociclismo no capturada en la experiencia histórica. Tercero, un techo de incremento del 8% trimestral sobre la tarifa anterior, para amortiguar saltos por recalibración (regla comercial autorizada por Comité de Producto).

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 4.2 Model Theory and Logic

> El núcleo del modelo está implementado como un Generalized Additive Model (GAM) con suavización spline bidimensional sobre las variables edad del asegurado y antigüedad de la cohorte de aseguramiento, complementado con efectos fijos sobre las dimensiones plan, género y región geográfica, y con efectos aleatorios sobre la dimensión canal de distribución. La frecuencia de siniestros se modela bajo distribución Poisson con función de enlace logarítmica; la severidad se modela mediante distribución Gamma con función de enlace logarítmica. La implementación utiliza la biblioteca `mgcv` integrada en Prophet 7.5.
>
> La elección del enfoque GAM se sustenta en tres consideraciones técnicas y operativas. La primera consideración corresponde a la captura adecuada de la relación no-lineal entre la edad del asegurado y la frecuencia esperada de siniestros, relación que presenta forma característica de U y que la versión 1.0 del modelo aproximaba mediante segmentación discreta en buckets de edad — aproximación que introducía discontinuidades de precio en las fronteras de bucket. La segunda consideración corresponde a la preservación de la interpretabilidad técnica exigida por el marco MRM institucional: las curvas spline ajustadas pueden visualizarse y defenderse explícitamente en los procesos de attestation anual, condición que no se satisface con enfoques de tipo Gradient Boosting Machine. La tercera consideración corresponde al cumplimiento del contrato de plataforma con Tecnología de la Información: el motor Prophet 7.5 incorpora soporte nativo para GAM mediante la integración de `mgcv`, y la utilización de enfoques alternativos como GBM habría obligado a una migración fuera de Prophet no autorizada.
>
> La utilización de efectos aleatorios sobre la dimensión canal responde directamente al hallazgo de severidad alta levantado por la Subdirección de Riesgos de Modelos en la attestation 2025 sobre la versión 1.0. Los canales de distribución exhiben volúmenes notablemente desiguales (aproximadamente 220,000 pólizas en agente tradicional, 105,000 en broker, 8,000 en banca-seguros), composición ante la cual los efectos fijos producen coeficientes inestables para los subgrupos pequeños. La especificación con efectos aleatorios induce el efecto estadístico de *shrinkage* hacia la media global condicional al tamaño del subgrupo, mitigando el sobre-ajuste y el sesgo identificado en el canal banca-seguros.
>
> La evaluación de enfoques alternativos quedó documentada en la especificación funcional aprobada por el Comité de Producto. Se descartó el enfoque GLM tradicional con interacciones explícitas por su capacidad limitada para capturar no-linealidad sin reintroducir el problema de fronteras entre buckets discretos. Se descartó el enfoque bayesiano jerárquico implementado en Stan por requerir salir del contrato de plataforma Prophet, condición no autorizada por TI. Se descartó el enfoque de árboles regularizados (random forest con poda) por su baja interpretabilidad regulatoria, criterio explícito del Comité de Producto.
>
> Tres reglas de negocio post-modelo se aplican en la etapa de post-procesamiento R 4.3, complementando los outputs del GAM. La primera regla establece un piso de prima equivalente al 80% de la prima calculada para el plan inmediatamente inferior, evitando inversiones de precio relativo entre planes que serían comercialmente insostenibles. La segunda regla aplica un factor multiplicativo de 1.15 sobre la prima resultante para asegurados hombres menores de 25 años, factor manual que compensa una exposición a riesgo de motociclismo conocida cualitativamente pero no capturada en la experiencia siniestral histórica utilizada para calibración. La tercera regla impone un techo del 8% sobre el incremento trimestral de la tarifa respecto a la tarifa publicada en el trimestre anterior, regla comercial autorizada por el Comité de Producto para amortiguar saltos derivados de la recalibración periódica.

**[Audit] 2026-05-08T11:24:18-06:00** — `seccion_completada` · `4.2.theory` · 6 turnos.

---

### Step 12 — Sección 4.3 Key Risk Drivers

#### Interview transcript (4 turnos)

**T1.** `[Claude]` Para 4.3: ¿cuáles son los 3 a 5 drivers principales de riesgo del modelo y por qué cada uno es relevante?

`[Ana]` Cinco drivers. (1) Frecuencia de siniestros por padecimiento mayor, especialmente para edades 45+ — es el mayor componente de severidad agregada. (2) Inflación médica — afecta directamente la severidad esperada con horizonte de 5 años. (3) Lapse temprano en los primeros 24 meses — afecta la duración esperada de cobro de prima vs. la exposición a siniestros. (4) Mix de canal — banca-seguros tiene perfil de riesgo distinto a agente tradicional. (5) Reaseguro — los planes B y C tienen reaseguro proporcional que afecta la severidad neta retenida.

**T2.** `[Claude]` Para el driver de inflación médica: ¿qué supuesto exacto usan y cuál es el rango plausible?

`[Ana]` Usamos el supuesto de Tesorería (ESG corporativo) de 6.5% anual para inflación médica MX en horizonte 1-5 años, con escenario alto de 9.0% y bajo de 4.5%. El supuesto base de 6.5% sale del promedio CONDUSEF + un margen institucional del 0.5% por composición de cartera (más uso hospitalario que el promedio del mercado).

**T3.** `[Claude]` ¿Cómo se monitorea cada driver en producción para detectar desvíos respecto al supuesto?

`[Ana]` Monitoreo trimestral. Para frecuencia: observado vs esperado por bucket de edad — bandera roja si desviación >1σ por 2 trimestres consecutivos. Para inflación médica: comparativo de severidad media observada vs calibrada — bandera amarilla si >1.5σ. Para lapse: cohorte tracking mensual de cancelaciones acumuladas. Mix de canal: composición trimestral vs supuesto.

**T4.** `[Claude]` ¿Qué pasa si un driver se desvía significativamente del supuesto?

`[Ana]` Protocolo en cuatro escalones. Bandera amarilla: revisión técnica en la calibración del siguiente trimestre. Bandera roja: recalibración inmediata fuera de ciclo, autorizada por FAE. Si la recalibración no resuelve: revisión metodológica con Riesgos. Si el driver fundamental cambia (regulatorio, plataforma): rediseño parcial del modelo.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 4.3 Key Risk Drivers

> El modelo identifica cinco drivers principales de riesgo de modelo, cada uno con justificación técnica y régimen de monitoreo específico documentado en la sección 9.
>
> El primer driver corresponde a la frecuencia de siniestros por padecimiento mayor, particularmente relevante para asegurados de 45 años o más, segmento que concentra el componente dominante de severidad agregada en la cartera. El segundo driver corresponde a la inflación médica observada en el sistema de salud mexicano, factor que afecta de forma directa la severidad esperada con un horizonte de cinco años. El supuesto base utilizado, originado en el ESG corporativo mantenido por Tesorería, asciende a 6.5% anual para horizonte 1-5 años, con escenarios alterno alto de 9.0% y bajo de 4.5%; el supuesto base se construye sobre el promedio publicado por la CONDUSEF más un margen institucional de 0.5 puntos porcentuales que refleja la composición específica de la cartera, con uso hospitalario superior al promedio del mercado. El tercer driver corresponde a la tasa de lapse temprano en los primeros 24 meses de antigüedad de póliza, variable que afecta la duración esperada de cobro de prima respecto a la exposición a siniestros y por tanto la suficiencia técnica de la tarifa. El cuarto driver corresponde al mix de canal de distribución, dado que cada canal exhibe un perfil de riesgo siniestral diferenciado documentado tanto en la versión 1.0 como en la calibración 2.0. El quinto driver corresponde a la estructura de reaseguro proporcional aplicable a los Planes B y C, que afecta la severidad neta retenida.
>
> Cada driver cuenta con régimen de monitoreo trimestral diferenciado. Para la frecuencia de siniestros se comparan observados contra esperados por bucket de edad, generando bandera roja ante desviación superior a una desviación estándar sostenida durante dos trimestres consecutivos. Para la inflación médica se compara la severidad media observada contra la severidad calibrada, generando bandera amarilla ante desviación superior a 1.5 desviaciones estándar. Para la tasa de lapse se ejecuta seguimiento cohorte por cohorte con periodicidad mensual sobre las cancelaciones acumuladas. La composición de canal se contrasta trimestralmente contra el supuesto vigente.
>
> El régimen de respuesta ante desviaciones se organiza en cuatro escalones. Una bandera amarilla activa la revisión técnica del driver durante la calibración trimestral inmediata siguiente. Una bandera roja activa la recalibración fuera de ciclo, sujeta a autorización expresa del Functional Area Executive del modelo. Si la recalibración no resuelve la desviación, se activa la revisión metodológica conjunta con la Subdirección de Riesgos de Modelos. Si la causa raíz corresponde a un cambio estructural en el driver (regulatorio o de plataforma), se activa el rediseño parcial del modelo.

**[Audit] 2026-05-08T11:48:33-06:00** — `seccion_completada` · `4.3.risk_drivers` · 4 turnos.

---

### Step 13 — Sección 4.4 Key Assumptions · CON APÉNDICE EXCEL

**Esta sección exercise: (a) interview con [Pendiente: fuente]; (b) upload de Excel con 18 supuestos; (c) referencia a apéndice sin replicar tabla.**

#### Interview transcript (5 turnos)

**T1.** `[Claude]` Para 4.4: ¿cuáles son los supuestos clave del modelo? Quiero capturarlos a nivel categoría primero; luego entramos al detalle cuantitativo.

`[Ana]` Cinco categorías. (1) Supuestos demográficos: mortalidad, morbilidad, lapse base, lapse dinámico. (2) Supuestos económicos: yields, inflación general, inflación médica. (3) Supuestos comerciales: comisiones por canal, gastos de adquisición. (4) Supuestos de gastos: mantenimiento, claim handling, overhead institucional. (5) Supuestos de reaseguro: tasa de cesión, costo de reaseguro.

**T2.** `[Claude]` Para cada categoría, ¿de dónde viene la fuente? Quiero entender si son supuestos institucionales centralizados o calibrados específicamente para este modelo.

`[Ana]` Mezclados. Mortalidad: modelo institucional M01.P01.S01.002.A. Morbilidad: modelo M02.P02.S03.005.A. Lapse base: calibración propia del modelo sobre cancelaciones 2018-2022. Lapse dinámico: calibrado contra cambios de prima históricos. Yields e inflación: ESG corporativo. Comisiones: política institucional aprobada por Comité de Producto. Gastos: assumption set 2024-Q4 de Finanzas. Reaseguro: contrato vigente con Munich Re para Planes B y C.

**T3.** `[Claude]` ¿Hay algún supuesto en el que la fuente no sea totalmente firme y deba quedar marcado como pendiente?

`[Ana]` Sí, uno. El supuesto de lapse dinámico ante cambios de prima — la calibración la hicimos sobre eventos históricos de cambio tarifario, pero no hemos tenido validación formal por Riesgos. Está marcado en spec funcional como "metodología en revisión".

**T4.** `[Claude]` ¿Tienen los supuestos en una tabla estructurada que puedas subir como apéndice? Para 4.4 podemos adjuntar un Excel y la sección del documento solo lo referencia.

`[Ana]` Sí, tengo un Excel con los 18 supuestos exactos: valor base, escenario alto, escenario bajo, y fuente. Te lo subo.

**Acción UI:** Ana arrastra `supuestos_pricing_gmm_v2.1.xlsx` al uploader de la sección 4.4 → el archivo se procesa con `AdjuntarTablaApendice` → se crea un `Apendice` con título *"Apéndice A — Tabla de Supuestos Clave del Modelo"*, vinculado a la sección 4.4. El sistema inyecta un `system_note` al interview state: *"El usuario adjuntó una tabla con 18 supuestos. Refiérete a 'Apéndice A — Tabla de Supuestos Clave' en el borrador en lugar de replicar la tabla. No inventes valores."*

**T5.** `[Claude]` Recibí el apéndice con 18 supuestos. Última pregunta: ¿hay alguno que en la práctica revisen con más frecuencia que el resto, por sensibilidad o porque suele desviarse?

`[Ana]` Tres con monitoreo más intenso. Inflación médica (mensual). Lapse base por cohorte (mensual). Morbilidad por padecimiento mayor (trimestral con detalle por padecimiento). El resto se revisa anualmente.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 4.4 Key Assumptions

> Los supuestos clave del modelo se organizan en cinco categorías técnicas. La primera categoría agrupa los supuestos demográficos, comprendiendo tabla de mortalidad, frecuencias de morbilidad, lapse base y lapse dinámico. La segunda categoría agrupa los supuestos económicos, comprendiendo yields, inflación general e inflación médica. La tercera categoría agrupa los supuestos comerciales, comprendiendo estructura de comisiones por canal y gastos de adquisición. La cuarta categoría agrupa los supuestos de gastos operativos, comprendiendo mantenimiento, claim handling y overhead institucional. La quinta categoría agrupa los supuestos de reaseguro, comprendiendo tasa de cesión y costo de reaseguro aplicable a los Planes B y C.
>
> El detalle cuantitativo de los 18 supuestos individuales — valor base, escenario alterno alto, escenario alterno bajo, y fuente documental — se encuentra en el Apéndice A: Tabla de Supuestos Clave del Modelo, integrado en su totalidad en este documento. La presente sección no replica los valores numéricos a fin de mantener una única fuente de verdad y facilitar la actualización trimestral.
>
> La trazabilidad de las fuentes se documenta de manera diferenciada por supuesto. Los supuestos de mortalidad se derivan del Modelo Institucional de Mortalidad SMNYL (M01.P01.S01.002.A) en su versión vigente. Los supuestos de morbilidad se derivan del Modelo Institucional de Morbilidad GMM (M02.P02.S03.005.A). Los supuestos de lapse base provienen de calibración específica realizada para este modelo sobre el universo de cancelaciones observado durante el período 2018-2022 en la cartera GMM individual. Los supuestos de lapse dinámico ante cambios tarifarios provienen igualmente de calibración propia sobre eventos históricos de modificación de prima. Los supuestos económicos (yields, inflación general, inflación médica) provienen del ESG Corporativo mantenido por Tesorería (M00.P00.S00.001.E) en su calibración trimestral más reciente. Los supuestos comerciales provienen de la política institucional aprobada por el Comité de Producto. Los supuestos de gastos provienen del assumption set 2024-Q4 publicado por Finanzas. Los supuestos de reaseguro reflejan el contrato proporcional vigente con Munich Re para los Planes B y C.
>
> `[Pendiente: confirmar fuente y proceso de validación del supuesto de lapse dinámico ante cambios de prima.]` La calibración propia se realizó sobre eventos históricos de modificación tarifaria, pero la metodología se encuentra documentada como "en revisión" en la especificación funcional aprobada por el Comité de Producto. Está pendiente la validación formal por parte de la Subdirección de Riesgos de Modelos en el plan de validación independiente 2.0.
>
> El régimen de monitoreo de los supuestos diferencia tres niveles de intensidad. Tres supuestos críticos se monitorean con frecuencia superior a la calibración del modelo: inflación médica con periodicidad mensual; lapse base por cohorte con periodicidad mensual; y morbilidad por padecimiento mayor con periodicidad trimestral y desglose por padecimiento. Los supuestos restantes se revisan con periodicidad anual en el marco de la attestation institucional.

#### Apéndice A — Tabla de Supuestos Clave (renderizada como tabla nativa Word al exportar)

> En el `.docx` final esta tabla se renderiza con `Table Grid` style, font 9pt (densidad media: 18 filas × 4 cols).

| Supuesto | Valor base | Escenario alto | Escenario bajo | Fuente |
|---|---|---|---|---|
| Mortalidad — tabla seleccionada | SMNYL-2024-GMM | +10% | −10% | M01.P01.S01.002.A |
| Morbilidad — frecuencia padecimiento mayor (45+) | 4.8% anual | 5.6% | 4.0% | M02.P02.S03.005.A |
| Morbilidad — severidad media | MXN 285,000 | MXN 320,000 | MXN 250,000 | M02.P02.S03.005.A |
| Lapse base — año 1 | 12.5% | 15.0% | 10.0% | Calibración propia 2018-2022 |
| Lapse base — años 2-5 | 6.8% | 8.5% | 5.2% | Calibración propia 2018-2022 |
| Lapse dinámico — coef. cambio prima | −0.45 | −0.60 | −0.30 | Calibración propia (en revisión) |
| Yield técnico (10Y MX) | 8.2% | 9.5% | 7.0% | ESG Corporativo |
| Inflación general | 4.5% | 5.5% | 3.5% | ESG Corporativo |
| Inflación médica | 6.5% | 9.0% | 4.5% | ESG Corporativo |
| Comisión agente tradicional | 28% año 1 | — | — | Política institucional |
| Comisión broker | 22% año 1 | — | — | Política institucional |
| Comisión banca-seguros | 18% año 1 | — | — | Política institucional |
| Gastos adquisición (no comisión) | MXN 850/póliza | +15% | −15% | Finanzas 2024-Q4 |
| Gastos mantenimiento | MXN 420/póliza/año | +12% | −12% | Finanzas 2024-Q4 |
| Claim handling | MXN 1,800/siniestro | +10% | −10% | Finanzas 2024-Q4 |
| Overhead institucional | 3.2% prima | +0.5pp | −0.5pp | Finanzas 2024-Q4 |
| Cesión reaseguro Plan B | 30% | — | — | Contrato Munich Re |
| Cesión reaseguro Plan C | 50% | — | — | Contrato Munich Re |

**[Audit] 2026-05-08T12:21:55-06:00**
- `tipo`: `seccion_completada`
- `seccion_id`: `4.4.assumptions`
- `descripcion`: `Sección 4.4 Key Assumptions completada (5 turnos) con apéndice adjunto`

**[Audit] 2026-05-08T12:21:56-06:00**
- `tipo`: `seccion_editada`
- `seccion_id`: `4.4.assumptions`
- `descripcion`: `Apéndice A adjuntado: supuestos_pricing_gmm_v2.1.xlsx (18 filas × 5 columnas)`
- `metadata`: `{"apendice_id": "ap-001", "archivo": "supuestos_pricing_gmm_v2.1.xlsx", "filas": "18", "columnas": "5"}`

---

### Step 14 — Sección 5.1 Raw Data Sources and Data Quality · CON EXTRACCIÓN AL EXPORT

**Esta sección produce narrativa que Haiku extrae a tabla nativa al exportar (schema `SCHEMA_RAW_DATA_SOURCES`).**

#### Interview transcript (4 turnos)

**T1.** `[Claude]` Para 5.1: ¿qué fuentes de datos raw alimentan el modelo y dónde residen físicamente?

`[Ana]` Cinco fuentes principales. Cartera de pólizas: Solix (administradora), snapshot diario, tabla `dbo.polizas_vigentes`. Siniestros: Solix tabla `dbo.siniestros_pagados`, también snapshot diario. Movimientos de prima: SQL Server `prod-actuarial/db_admin_polizas/tabla mov_prima`, diario. Reaseguro: feed mensual desde Munich Re en formato XML, llega a S3 `s3://smnyl-reaseguro/munich-re/`. Tabla institucional de morbilidad: archivo Parquet en S3 `s3://smnyl-actuarial-data/morbilidad/`, refresco trimestral por la Subgerencia de Morbilidad.

**T2.** `[Claude]` Para cada fuente: ¿quién es el responsable institucional y cuál es el método de carga al data mart de Prophet?

`[Ana]` Solix tablas: equipo de Administración de Pólizas, carga vía proceso ETL en SQL Server cada noche (job `etl_pricing_inputs_v2.1.sql`). Movimientos de prima: mismo equipo, mismo método. Reaseguro: equipo de Reaseguro institucional, carga manual quincenal mediante script `R/load_reaseguro.R`. Morbilidad: Subgerencia de Morbilidad, refresco trimestral vía notebook Databricks que escribe a S3 y notifica al equipo de pricing para incorporación.

**T3.** `[Claude]` ¿Qué controles de calidad se aplican a los datos antes de que entren al modelo?

`[Ana]` Tres niveles. Nivel 1 (automático, pre-ETL): validación de checksums Solix, verificación de no-null en campos clave, detección de duplicados por número de póliza. Nivel 2 (automático, post-ETL): reconciliación de totales contra control acumulado, validación de rangos numéricos (suma asegurada, prima). Nivel 3 (manual, trimestral): muestreo aleatorio de 200 pólizas y validación cruzada contra el sistema fuente.

**T4.** `[Claude]` ¿Hay limitaciones conocidas en las fuentes de datos que valga la pena documentar aquí?

`[Ana]` Dos. La fecha de cancelación en Solix tiene un lag de 3-5 días para registrarse — afecta la calibración del lapse temprano. El feed de Munich Re ha tenido errores de carga en el pasado (2 incidentes en 2024-2025) que requirieron re-carga manual; tenemos un check de consistencia adicional para detectar.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 5.1 Raw Data Sources and Data Quality

> El modelo se alimenta de cinco fuentes de datos primarias, cada una con un responsable institucional definido y un método de incorporación al data mart de Prophet. La fuente de cartera de pólizas vigentes corresponde a snapshots diarios de la tabla `dbo.polizas_vigentes` del sistema administrador Solix, propiedad del equipo de Administración de Pólizas, cargada cada noche mediante el job ETL `etl_pricing_inputs_v2.1.sql` en SQL Server. La fuente de siniestros pagados corresponde a snapshots diarios de la tabla `dbo.siniestros_pagados` del mismo sistema, con propiedad y método de carga equivalentes. La fuente de movimientos de prima corresponde a la tabla `mov_prima` del sistema SQL Server `prod-actuarial/db_admin_polizas`, propiedad del equipo de Administración de Pólizas, con carga ETL diaria automatizada. La fuente de información de reaseguro corresponde a un feed mensual proveniente de Munich Re en formato XML, depositado en el bucket S3 `smnyl-reaseguro/munich-re/`, propiedad del equipo de Reaseguro Institucional, con carga manual quincenal mediante el script `R/load_reaseguro.R`. La fuente de morbilidad institucional corresponde a archivos en formato Parquet depositados en S3 `smnyl-actuarial-data/morbilidad/`, propiedad de la Subgerencia de Morbilidad, con refresco trimestral generado por un notebook Databricks que notifica al equipo de Pricing para su incorporación al ciclo de calibración.
>
> El régimen de controles de calidad de datos opera en tres niveles secuenciales. El primer nivel comprende validaciones automatizadas pre-ETL ejecutadas en el origen: verificación de checksums sobre los archivos Solix, validación de campos no nulos en columnas clave, y detección de registros duplicados por número de póliza. El segundo nivel comprende validaciones automatizadas post-ETL sobre el data mart resultante: reconciliación de totales agregados contra el control acumulado independiente, y validación de rangos numéricos plausibles sobre suma asegurada y prima. El tercer nivel comprende una validación manual trimestral consistente en muestreo aleatorio de 200 pólizas y verificación cruzada contra los sistemas fuente.
>
> Existen dos limitaciones conocidas y documentadas en las fuentes de datos. La primera limitación corresponde a un lag de registro de 3 a 5 días en la fecha de cancelación en el sistema Solix, condición que afecta marginalmente la calibración del lapse temprano para cohortes recientes y se mitiga mediante un ajuste de corte en la ventana de cálculo. La segunda limitación corresponde al feed de Munich Re, que ha presentado errores de carga en dos incidentes históricos durante el período 2024-2025, eventos que requirieron re-carga manual; se ha implementado un check adicional de consistencia para detectar de forma temprana estas situaciones.

**[Apéndice tabular extraído al export]** El sistema Haiku (TableExtractor) procesa la narrativa anterior al momento de exportar y produce la siguiente tabla nativa Word en la sección 5.1 del DOCX (schema `SCHEMA_RAW_DATA_SOURCES`):

| data_source | data_type | location | method | team |
|---|---|---|---|---|
| Cartera pólizas vigentes | snapshot tabla SQL | dbo.polizas_vigentes (Solix) | ETL nocturno automatizado | Administración de Pólizas |
| Siniestros pagados | snapshot tabla SQL | dbo.siniestros_pagados (Solix) | ETL nocturno automatizado | Administración de Pólizas |
| Movimientos de prima | tabla SQL | mov_prima (prod-actuarial) | ETL diario automatizado | Administración de Pólizas |
| Reaseguro Munich Re | feed XML mensual | s3://smnyl-reaseguro/munich-re/ | Script R quincenal manual | Reaseguro Institucional |
| Morbilidad institucional | archivo Parquet trimestral | s3://smnyl-actuarial-data/morbilidad/ | Notebook Databricks + notificación | Subgerencia de Morbilidad |

**[Audit] 2026-05-08T12:55:42-06:00** — `seccion_completada` · `5.1.raw_data` · 4 turnos.

---

### Step 15 — Sección 5.2 Upstream Models & Company Determined Assumptions · CON EXTRACCIÓN AL EXPORT

#### Interview transcript (3 turnos)

**T1.** `[Claude]` Para 5.2: enumera los modelos upstream cuyos outputs consume este modelo y quién es el contacto técnico de cada uno.

`[Ana]` Cuatro modelos upstream. (1) Modelo de Mortalidad SMNYL — inventario MRM M01.P01.S01.002.A — contacto técnico: Lucía Bermúdez, Gerencia de Experiencia. (2) Modelo de Morbilidad GMM — M02.P02.S03.005.A — contacto: Daniel Estrada, Subgerencia Morbilidad. (3) ESG Corporativo — M00.P00.S00.001.E — contacto: Mauricio Treviño, Tesorería. (4) Tabla de Gastos Corporativos 2024-Q4 — no es modelo formal sino assumption set institucional — contacto: Patricia Ovalle, Finanzas.

**T2.** `[Claude]` ¿Qué outputs específicos consume este modelo de cada upstream?

`[Ana]` De Mortalidad: tabla qx por edad y género ajustada a experiencia GMM. De Morbilidad: frecuencias y severidades por padecimiento × edad × género × región. De ESG: yields curva 30 años, inflación general MX, inflación médica, tipo de cambio. De Gastos: tarifas unitarias por concepto (adquisición, mantenimiento, claim handling, overhead).

**T3.** `[Claude]` ¿Existe acoplamiento de versiones — el modelo requiere una versión específica de cada upstream, o consume siempre la última disponible?

`[Ana]` Política mixta. Para Mortalidad y Morbilidad: se usa la versión vigente al momento de calibración trimestral, queda fija durante todo el trimestre operativo. Para ESG: se actualiza dentro del trimestre solo si Tesorería emite recalibración extraordinaria. Para Gastos: assumption set trimestral, queda fijo dentro del trimestre.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 5.2 Upstream Models & Company Determined Assumptions

> El modelo consume insumos de cuatro fuentes upstream institucionales, organizadas en tres modelos formales del inventario MRM y un assumption set corporativo. El Modelo de Mortalidad SMNYL, identificado en el inventario MRM con el código M01.P01.S01.002.A, aporta la tabla de probabilidades qx por edad y género ajustada a la experiencia específica de la cartera GMM; el contacto técnico responsable es la Gerencia de Experiencia. El Modelo de Morbilidad GMM, identificado en el inventario MRM con el código M02.P02.S03.005.A, aporta las frecuencias y severidades por padecimiento mayor segmentadas por edad, género y región geográfica; el contacto técnico responsable es la Subgerencia de Morbilidad. El ESG Corporativo, identificado en el inventario MRM con el código M00.P00.S00.001.E, aporta la curva de yields a 30 años, la inflación general en pesos mexicanos, la inflación médica y el tipo de cambio; el contacto técnico responsable es Tesorería. La Tabla de Gastos Corporativos 2024-Q4 no constituye un modelo formal del inventario MRM sino un assumption set institucional, y aporta las tarifas unitarias por concepto de gasto (adquisición, mantenimiento, claim handling y overhead institucional); la propiedad y mantenimiento corresponde a Finanzas.
>
> La política de acoplamiento de versiones entre el modelo y sus upstreams se diferencia por fuente. Las versiones de los modelos de Mortalidad y Morbilidad utilizadas en la calibración trimestral del pricing quedan fijas durante todo el trimestre operativo, lo cual asegura coherencia interna y elimina variaciones intra-trimestre por cambios en upstream. La curva ESG y los supuestos económicos se actualizan dentro del trimestre exclusivamente si Tesorería emite una recalibración extraordinaria, evento poco frecuente sujeto a notificación formal. La Tabla de Gastos Corporativos queda fija dentro del trimestre operativo, alineada a la cadencia trimestral de actualización publicada por Finanzas.

**[Apéndice tabular extraído al export]** (schema `SCHEMA_UPSTREAM_MODELS`):

| num | name | key_contact | inventory_id |
|---|---|---|---|
| 1 | Modelo de Mortalidad SMNYL | Lucía Bermúdez (Gerencia de Experiencia) | M01.P01.S01.002.A |
| 2 | Modelo de Morbilidad GMM | Daniel Estrada (Subgerencia Morbilidad) | M02.P02.S03.005.A |
| 3 | ESG Corporativo | Mauricio Treviño (Tesorería) | M00.P00.S00.001.E |
| 4 | Tabla de Gastos Corporativos 2024-Q4 | Patricia Ovalle (Finanzas) | (Assumption set, no modelo formal) |

**[Audit] 2026-05-08T13:20:18-06:00** — `seccion_completada` · `5.2.upstream` · 3 turnos.

---

### Step 16 — Sección 5.3.1 Data Aggregations · OMITIDA

**Acción UI:** Ana selecciona "Omitir sección" en 5.3.1 → motivo: *"No aplica al modelo"* → detalle: *"El modelo opera a nivel póliza individual (policy-level); no se realiza agregación previa al fit del GAM. Cada póliza ingresa como observación independiente al motor de Prophet."*

**[Audit] 2026-05-08T13:23:05-06:00**
- `tipo`: `seccion_omitida`
- `seccion_id`: `5.3.1.aggregations`
- `descripcion`: `Sección 5.3.1 omitida — motivo: No aplica al modelo`
- `metadata`: `{"motivo": "No aplica al modelo", "detalle": "El modelo opera a nivel póliza individual; no se realiza agregación previa al fit del GAM."}`

---

### Step 17 — Sección 5.3.2 Segmentations · OPCIONAL LLENA

**Esta opcional se llena porque las segmentaciones son centrales al diseño del modelo.**

#### Interview transcript (3 turnos)

**T1.** `[Claude]` 5.3.2 es opcional pero parece muy relevante para tu modelo dado que mencionaste varias dimensiones de segmentación. ¿Cuáles son las segmentaciones del modelo y por qué cada una?

`[Ana]` Cuatro segmentaciones activas. (1) Plan (A/B/C) — efecto fijo, captura diferencias de cobertura. (2) Género (M/F) — efecto fijo, captura diferencias de morbilidad. (3) Región (Norte / Centro / Sur / CDMX-Metropolitana) — efecto fijo, captura diferencias de costos médicos regionales. (4) Canal (agente / broker / banca-seguros) — efecto aleatorio por razones de volumen explicadas en 4.2.

**T2.** `[Claude]` ¿Cómo se construyó la segmentación regional — son fronteras políticas o agregación por similitud médica observada?

`[Ana]` Es híbrida. Partimos de los 32 estados de la república, los agrupamos primero por geografía (Norte/Centro/Sur/CDMX-Met) y validamos con clustering sobre severidad observada — los clusters confirmaron la agrupación geográfica con la excepción de Baja California Sur, que estadísticamente se parecía más a Centro pero por consistencia operativa lo mantuvimos en Norte.

**T3.** `[Claude]` ¿Hay segmentaciones que evaluaron y descartaron?

`[Ana]` Dos. Ocupación del asegurado — los datos están incompletos (cobertura solo 60% de pólizas), descartado por sesgo. Tipo de plan adicional contratado (dental, ambulatorio expandido) — descartado porque ya está embebido en la dimensión Plan.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 5.3.2 Segmentations

> El modelo aplica cuatro segmentaciones activas con justificación técnica documentada. La segmentación por Plan (A, B, C) opera como efecto fijo en la especificación del modelo y captura las diferencias estructurales de cobertura entre los productos. La segmentación por género (Masculino, Femenino) opera como efecto fijo y captura las diferencias diferenciales de morbilidad observada. La segmentación por región geográfica (Norte, Centro, Sur, CDMX Metropolitana) opera como efecto fijo y captura las diferencias regionales de costos médicos. La segmentación por canal de distribución (agente tradicional, broker, banca-seguros) opera como efecto aleatorio, decisión técnica derivada de la disparidad de volúmenes entre canales y documentada con detalle en la sección 4.2.
>
> La construcción de la segmentación regional siguió un procedimiento híbrido. Se partió de los 32 estados de la República Mexicana y se aplicó una agrupación inicial por criterio geográfico en los cuatro grupos descritos. Esta agrupación se validó posteriormente mediante un procedimiento de clustering no supervisado sobre la severidad siniestral observada por estado, ejercicio cuyos resultados confirmaron la agrupación geográfica inicial con una sola excepción: Baja California Sur exhibió en el clustering una mayor similitud con el grupo Centro que con el grupo Norte, pero se mantuvo en este último por consistencia operativa con la estructura regional utilizada por las áreas de distribución y servicio al cliente.
>
> Dos dimensiones de segmentación adicionales fueron evaluadas durante la especificación del modelo y descartadas por consideraciones técnicas. La segmentación por ocupación del asegurado fue descartada por cobertura insuficiente en los datos administrativos, con información disponible para solo el 60% de las pólizas activas, condición que introduciría un sesgo de selección material. La segmentación por tipo de plan adicional contratado (cobertura dental, ambulatoria expandida) fue descartada por redundancia con la dimensión Plan, en la cual ya se encuentran embebidas las diferencias relevantes de cobertura.

**[Audit] 2026-05-08T13:42:11-06:00** — `seccion_completada` · `5.3.2.segmentations` · 3 turnos.

---

### Step 18 — Sección 5.3.3 Use of Averages or Proxies · OMITIDA

**Acción UI:** Ana selecciona "Omitir sección" en 5.3.3 → motivo: *"No aplica al modelo"* → detalle: *"El modelo no utiliza promedios ni proxies sobre las observaciones de entrada. Cada póliza contribuye con sus valores individuales al fit del GAM. Los supuestos calibrados se aplican como funciones, no como promedios sustitutos."*

**[Audit] 2026-05-08T13:44:38-06:00** — `seccion_omitida` · `5.3.3.averages_proxies` · motivo: No aplica al modelo.

---

### Step 19 — Sección 5.4 Known Input and Data Limitations

#### Interview transcript (3 turnos)

**T1.** `[Claude]` Para 5.4: ¿qué limitaciones conocidas existen en los inputs o supuestos que podrían afectar la confiabilidad del modelo?

`[Ana]` Cinco limitaciones documentadas. (1) Lag de 3-5 días en fecha de cancelación Solix — afecta calibración lapse temprano. (2) Solo 60% de cobertura en ocupación — descartamos la variable por esto. (3) Experiencia siniestral concentrada en cohortes nuevas (2020+) por crecimiento reciente de cartera — sub-representación de cohortes antiguas. (4) ESG con calibración trimestral — no captura shocks intra-trimestre. (5) Datos de banca-seguros tienen historia corta (2021+) — limita la robustez del efecto aleatorio para este canal.

**T2.** `[Claude]` ¿Qué acciones de mitigación están implementadas para cada limitación?

`[Ana]` (1) Ventana de corte ajustada en cálculo de lapse. (2) Variable simplemente excluida del modelo. (3) Pesos por antigüedad de cohorte para no sobre-representar las nuevas. (4) Monitoreo intensivo intra-trimestre con alertas si los indicadores económicos divergen >1.5σ. (5) Aplicación de prior informativo en la estimación del efecto aleatorio de banca-seguros, basado en el promedio de los otros canales.

**T3.** `[Claude]` ¿Cuál de estas limitaciones consideras la más crítica y por qué?

`[Ana]` La (3) — sub-representación de cohortes antiguas. Los siniestros de cartera vieja son más severos en promedio (envejecimiento) y si los pesos no son del todo correctos, podemos infraestimar la siniestralidad de largo plazo. Es la primera prioridad del plan de validación 2026.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 5.4 Known Input and Data Limitations

> Se documentan cinco limitaciones conocidas en los inputs y supuestos del modelo, cada una con su mitigación implementada y su nivel de criticidad evaluado.
>
> La primera limitación corresponde al lag de registro de 3 a 5 días en la fecha de cancelación de pólizas en el sistema Solix. Esta condición afecta marginalmente la calibración del lapse temprano para cohortes recientes y se mitiga mediante un ajuste explícito de la ventana de corte en el procedimiento de cálculo de lapse, excluyendo el período afectado por el lag de registro.
>
> La segunda limitación corresponde a la cobertura del campo de ocupación del asegurado en los datos administrativos, disponible para únicamente el 60% de las pólizas activas. Esta condición se mitigó descartando la dimensión ocupación de la especificación del modelo, conforme documentado en la sección 5.3.2, dado que su inclusión introduciría un sesgo material de selección.
>
> La tercera limitación corresponde a la composición temporal de la experiencia siniestral, concentrada en cohortes de aseguramiento posteriores a 2020 como consecuencia del crecimiento reciente de la cartera GMM individual. Esta condición se mitiga mediante la aplicación de pesos diferenciales por antigüedad de cohorte en el procedimiento de ajuste, con el objetivo de evitar la sobre-representación de cohortes nuevas. Esta limitación se considera la más crítica en términos de impacto potencial sobre el modelo y constituye la primera prioridad del Plan de Validación Independiente 2026, dado que los siniestros de cartera antigua presentan severidad media superior por efecto de envejecimiento y una mitigación inadecuada podría conducir a infraestimación de la siniestralidad de largo plazo.
>
> La cuarta limitación corresponde a la periodicidad trimestral de la calibración del ESG Corporativo, condición que impide capturar shocks económicos ocurridos intra-trimestre. La mitigación corresponde al monitoreo intensivo de los indicadores económicos clave (yields, inflación general, inflación médica) con alertas automáticas ante divergencias superiores a 1.5 desviaciones estándar respecto a la calibración vigente.
>
> La quinta limitación corresponde a la historia corta disponible para el canal banca-seguros (datos a partir de 2021), condición que limita la robustez de la estimación del efecto aleatorio para este canal específico. La mitigación corresponde a la aplicación de un prior informativo en la estimación del efecto aleatorio del canal banca-seguros, calibrado sobre el promedio observado en los otros dos canales con historia completa.

**[Audit] 2026-05-08T14:04:42-06:00** — `seccion_completada` · `5.4.data_limitations` · 3 turnos.

---

### Step 20 — Sección 5.5 Record of Input Changes or Decisions Made · OPCIONAL LLENA · CON EXTRACCIÓN

**Bitácora de cambios. Al export, Haiku extrae como tabla nativa (schema `SCHEMA_INPUT_CHANGES`).**

#### Interview transcript (2 turnos)

**T1.** `[Claude]` Para 5.5: enumera los cambios de input más relevantes desde la versión 1.0 hasta la 2.1, con fecha y decisión.

`[Ana]` Cuatro cambios. (1) 2024-08: incorporación de la dimensión región (en v1.0 era estado individual con buckets manuales) — decisión: usar 4 grupos validados por clustering. (2) 2025-03: cambio de calibración de morbilidad — pasamos de modelo paramétrico simple a consumir directamente M02.P02.S03.005.A. (3) 2025-09: refresh de la tabla de gastos a la versión 2024-Q4 — afectó la prima en aproximadamente +1.2% por incremento de gastos médicos. (4) 2026-03: incorporación del prior informativo en banca-seguros — mitigación de la limitación 5 mencionada en 5.4.

**T2.** `[Claude]` ¿Quién autorizó cada uno de estos cambios?

`[Ana]` (1) y (2): FAE y Riesgos. (3): change administrativo, solo notificación a FAE. (4): FAE y Riesgos como parte del plan de validación.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 5.5 Record of Input Changes

> Desde la versión 1.0 del modelo se han registrado cuatro cambios materiales en los inputs o supuestos, cada uno con fecha, descripción de la decisión y autorización institucional correspondiente. En agosto de 2024 se incorporó la dimensión geográfica como agrupación regional en cuatro grupos (Norte, Centro, Sur, CDMX Metropolitana), sustituyendo la representación previa por estado individual con buckets construidos manualmente; la decisión se sustentó en el procedimiento de clustering sobre severidad observada descrito en la sección 5.3.2 y fue autorizada conjuntamente por el FAE del modelo y la Subdirección de Riesgos de Modelos. En marzo de 2025 se modificó la calibración de morbilidad, sustituyendo el modelo paramétrico simple utilizado en la versión 1.0 por el consumo directo del Modelo Institucional de Morbilidad GMM (M02.P02.S03.005.A), cambio autorizado conjuntamente por el FAE y Riesgos. En septiembre de 2025 se actualizó la Tabla de Gastos Corporativos a la versión 2024-Q4, cambio de naturaleza administrativa que produjo un impacto aproximado de +1.2% sobre la prima total agregada por el incremento en gastos médicos unitarios; la actualización fue notificada al FAE sin requerir autorización formal por tratarse de actualización rutinaria de assumption set. En marzo de 2026 se incorporó el prior informativo en la estimación del efecto aleatorio del canal banca-seguros, modificación derivada del plan de validación 2026 y autorizada conjuntamente por el FAE y Riesgos.

**[Apéndice tabular extraído al export]** (schema `SCHEMA_INPUT_CHANGES`):

| date | decision | change_description |
|---|---|---|
| 2024-08 | Aprobado por FAE + Riesgos | Incorporación de dimensión región (4 grupos validados por clustering); sustituye estado individual con buckets manuales |
| 2025-03 | Aprobado por FAE + Riesgos | Calibración de morbilidad migrada al modelo institucional M02.P02.S03.005.A; sustituye paramétrico simple v1.0 |
| 2025-09 | Notificación administrativa al FAE | Actualización Tabla Gastos Corporativos a v2024-Q4; impacto +1.2% en prima total |
| 2026-03 | Aprobado por FAE + Riesgos | Incorporación prior informativo en efecto aleatorio banca-seguros (mitigación 5.4) |

**[Audit] 2026-05-08T14:22:55-06:00** — `seccion_completada` · `5.5.input_changes` · 2 turnos.

---

### Step 21 — Sección 6.1 Specification Process

#### Interview transcript (3 turnos)

**T1.** `[Claude]` Para 6.1: ¿cómo se especificó técnicamente este modelo y quiénes participaron?

`[Ana]` Proceso de tres etapas formales. Etapa 1 (mayo-julio 2025): definición de requisitos funcionales por Pricing + Comité de Producto. Etapa 2 (agosto-septiembre 2025): especificación técnica detallada por el equipo de desarrollo (Diego Reyes y Mariana Pacheco) con revisión iterativa de Riesgos. Etapa 3 (octubre 2025): aprobación formal de la spec por Comité de Producto antes de pasar a desarrollo. Total: aproximadamente 5 meses.

**T2.** `[Claude]` ¿Hubo decisiones de scope que se tomaron explícitamente durante la spec y vale la pena registrar?

`[Ana]` Tres decisiones clave de scope. (a) Mantenerse en Prophet 7.5 (no migrar plataforma). (b) No incluir cobertura ambulatoria expandida en Plan A (riesgo de cross-subsidio). (c) Diferir la cobertura odontológica para una versión futura porque no es producto vigente.

**T3.** `[Claude]` ¿Existió un proceso formal de aprobación de la spec con firma del FAE y Riesgos?

`[Ana]` Sí. La spec v1.3 está firmada electrónicamente el 2025-08-12 por Roberto Castañeda (FAE) y Pablo Hinojosa (Riesgos). El documento vive en SharePoint Pricing GMM /docs/v2.0/spec_v2_aprobada_2025-Q2.pdf.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 6.1 Specification Process

> La especificación técnica del modelo se desarrolló mediante un proceso formal de tres etapas con duración total aproximada de cinco meses. La primera etapa, ejecutada durante el período mayo-julio de 2025, consistió en la definición de requisitos funcionales conducida conjuntamente por la Subgerencia de Pricing GMM y el Comité de Producto, etapa que materializó los hallazgos de la attestation 2025 en requerimientos técnicos accionables. La segunda etapa, ejecutada durante agosto y septiembre de 2025, consistió en la elaboración de la especificación técnica detallada por el equipo de desarrollo del modelo (Diego Reyes Aguilar y Mariana Pacheco Núñez), con revisión iterativa de la Subdirección de Riesgos de Modelos en sesiones quincenales documentadas. La tercera etapa, ejecutada en octubre de 2025, consistió en la aprobación formal de la especificación por el Comité de Producto, requisito institucional previo al inicio del desarrollo.
>
> Tres decisiones de alcance se tomaron explícitamente durante el proceso de especificación y se documentaron en la versión final aprobada. La primera decisión consistió en mantener el modelo en la plataforma Prophet 7.5, sin migración a una plataforma alternativa, alineado al contrato de plataforma institucional vigente. La segunda decisión consistió en excluir la cobertura ambulatoria expandida del Plan A, decisión justificada por el riesgo de cross-subsidio entre planes que comprometería la sustentabilidad técnica individual exigida por el contract boundary test bajo IFRS 17. La tercera decisión consistió en diferir explícitamente la cobertura odontológica a una versión futura del modelo, dado que esta cobertura no constituye producto vigente en la oferta GMM individual de la institución.
>
> La especificación técnica final, identificada como versión 1.3, cuenta con aprobación formal de las dos autoridades institucionales relevantes: el Functional Area Executive del modelo (Roberto Castañeda Mendoza) y la Subdirección de Riesgos de Modelos (Pablo Hinojosa Cárdenas), ambas firmas electrónicas con fecha 12 de agosto de 2025. El documento se mantiene en el repositorio SharePoint corporativo de Pricing GMM bajo la ruta `/docs/v2.0/spec_v2_aprobada_2025-Q2.pdf`.

**[Audit] 2026-05-08T14:42:18-06:00** — `seccion_completada` · `6.1.specification` · 3 turnos.

---

### Step 22 — Sección 6.2 Approach Used

#### Interview transcript (5 turnos)

**T1.** `[Claude]` Para 6.2: explica con detalle el approach metodológico utilizado para el ajuste y validación del modelo.

`[Ana]` Approach en cinco fases. Fase 1: preparación de datos — ventana 2018-2022 para fit (5 años de experiencia), 2023-2024 como holdout. Fase 2: especificación del GAM con `mgcv` — fórmula `s(edad, antiguedad) + plan + genero + region + (1|canal)`, con suavización spline grado 4 y penalización REML. Fase 3: estimación inicial por máxima verosimilitud penalizada, en Prophet 7.5. Fase 4: validación in-sample con k-fold (k=5), comprobando estabilidad de coeficientes. Fase 5: validación out-of-sample contra el holdout 2023-2024, midiendo error absoluto medio y direccionalidad.

**T2.** `[Claude]` Para la fase 3 (estimación): ¿por qué REML y no ML estándar?

`[Ana]` REML produce estimaciones menos sesgadas para los parámetros de varianza de los efectos aleatorios y las penalizaciones spline. ML clásico tiende a subestimar la varianza, lo cual es problemático con muestras moderadas como las nuestras (333K pólizas suena mucho pero para banca-seguros son 8K). REML es el estándar recomendado en la literatura para GAM con efectos mixtos.

**T3.** `[Claude]` ¿Cómo se eligió el grado de suavización (smoothing parameter) para los splines?

`[Ana]` Selección automática por GCV (Generalized Cross-Validation) — la función `gam()` de `mgcv` lo hace por default y produce un parámetro de suavización óptimo en términos de trade-off bias-variance. Validamos manualmente revisando los grados efectivos de libertad de cada spline para asegurar que no estaban ni saturados (overfitting) ni demasiado planos (underfitting).

**T4.** `[Claude]` ¿Hubo iteración entre el approach original y el final, o salió "a la primera"?

`[Ana]` Tres iteraciones. Iteración 1: spline solo en edad, lapse modelado aparte — no capturaba bien la interacción. Iteración 2: spline 2D edad × antigüedad pero efecto fijo en canal — repetía el problema de v1.0 en banca. Iteración 3 (final): spline 2D + efecto aleatorio en canal. Cada iteración fue documentada en bitácora R Markdown y revisada con Riesgos.

**T5.** `[Claude]` ¿Cómo se separó la lógica de frecuencia y severidad — son dos modelos separados o uno conjunto?

`[Ana]` Dos modelos separados acoplados al final. Modelo de frecuencia (Poisson GAM) y modelo de severidad (Gamma GAM con link log) — cada uno con la misma estructura de variables pero coeficientes independientes. La prima esperada se calcula como E[N] × E[Y|N>0]. Esto es la práctica estándar actuarial para evitar problemas de no-identificabilidad cuando frecuencia y severidad responden a variables compartidas.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 6.2 Approach Used

> El approach metodológico del modelo se organiza en cinco fases secuenciales documentadas, con duración total aproximada de cuatro meses desde el inicio del ajuste hasta la aceptación final del fit.
>
> La primera fase corresponde a la preparación de datos. Se utilizó la ventana de experiencia 2018-2022 (cinco años) para el ajuste del modelo y la ventana 2023-2024 como conjunto de holdout reservado para la validación externa, separación temporal estricta sin contaminación cruzada entre fit y validación.
>
> La segunda fase corresponde a la especificación formal del Generalized Additive Model. La fórmula utilizada en la sintaxis de `mgcv` corresponde a `s(edad, antiguedad) + plan + genero + region + (1|canal)`, con suavización spline de grado 4 sobre el término bidimensional y método de selección de penalización REML. La elección de REML sobre ML estándar se justifica por la propiedad de menor sesgo en la estimación de parámetros de varianza para efectos aleatorios y penalizaciones spline, criterio relevante dado que algunos subgrupos (notablemente banca-seguros con aproximadamente 8,000 pólizas) tienen tamaño moderado.
>
> La tercera fase corresponde a la estimación numérica mediante máxima verosimilitud penalizada con selección automática del parámetro de suavización vía Generalized Cross-Validation (GCV), procedimiento implementado de forma nativa en la función `gam()` de `mgcv`. Se validó manualmente la razonabilidad de los grados efectivos de libertad estimados para cada componente spline, verificando que se mantienen en rangos consistentes con un balance bias-variance apropiado, sin saturación que indicara sobre-ajuste ni planitud excesiva que indicara sub-ajuste.
>
> La cuarta fase corresponde a la validación in-sample mediante k-fold cross validation con k=5, ejercicio cuyo objetivo fue verificar la estabilidad de los coeficientes estimados entre folds y detectar posibles inestabilidades numéricas. Los resultados de este ejercicio se reportan con detalle en la sección 6.3.
>
> La quinta fase corresponde a la validación out-of-sample contra el conjunto holdout 2023-2024, ejercicio fundamental para evaluar la generalización del modelo a períodos no utilizados en el fit. Las métricas evaluadas comprenden el error absoluto medio en prima esperada, la direccionalidad del error y la consistencia por bucket de edad, género, región, plan y canal.
>
> El approach final emergió tras tres iteraciones documentadas. La primera iteración utilizó un spline univariable en edad con el componente de lapse modelado separadamente, configuración que no logró capturar adecuadamente la interacción entre edad y antigüedad de la cohorte. La segunda iteración incorporó el spline bidimensional edad × antigüedad pero mantuvo el canal como efecto fijo, configuración que reprodujo el sesgo en banca-seguros identificado en la versión 1.0. La tercera iteración, finalmente adoptada, incorpora tanto el spline bidimensional como el efecto aleatorio en canal, configuración que resuelve ambas deficiencias previas. Cada iteración fue documentada en una bitácora R Markdown y revisada en sesión con la Subdirección de Riesgos de Modelos antes de proceder a la siguiente.
>
> La arquitectura del modelo separa de manera explícita la lógica de frecuencia y la lógica de severidad en dos modelos acoplados al final del procesamiento. El modelo de frecuencia se especifica como un GAM con distribución Poisson y función de enlace logarítmica. El modelo de severidad se especifica como un GAM con distribución Gamma y función de enlace logarítmica. Ambos modelos comparten la misma estructura de variables explicativas pero estiman coeficientes independientes. La prima esperada se calcula como el producto del valor esperado de la frecuencia y el valor esperado condicional de la severidad dado siniestro. Esta separación es práctica estándar en pricing actuarial y mitiga los problemas de no-identificabilidad que pueden surgir cuando frecuencia y severidad responden de forma simultánea a variables explicativas compartidas.

**[Audit] 2026-05-08T15:18:42-06:00** — `seccion_completada` · `6.2.approach` · 5 turnos.

---

### Step 23 — Sección 6.3 Development Testing

#### Interview transcript (5 turnos)

**T1.** `[Claude]` Para 6.3: ¿qué tests específicos ejecutaron durante el desarrollo para validar el ajuste?

`[Ana]` Seis tests formales documentados. (1) Convergencia numérica del GAM. (2) Estabilidad de coeficientes en k-fold. (3) Calibración in-sample. (4) Calibración out-of-sample. (5) Comparativo contra modelo 1.0. (6) Sensibilidad a remoción de outliers.

**T2.** `[Claude]` Para el test de calibración out-of-sample contra el holdout: ¿qué métricas usaron y qué resultados obtuvieron?

`[Ana]` Tres métricas. Error absoluto medio (MAE) sobre prima esperada agregada por bucket edad × canal: 2.8% promedio, max 5.1% (banca-seguros 30-35). Direccionalidad: 64% de buckets dentro de ±2% (vs 47% en v1.0). Bias agregado (mean signed error): −0.4% (vs +6.2% en v1.0 para banca-seguros).

**T3.** `[Claude]` Mencionaste que MAE máximo es 5.1% en banca-seguros 30-35. ¿Eso se considera aceptable y por qué?

`[Ana]` Es aceptable bajo los criterios documentados en el plan de validación. El criterio aprobado por Riesgos es MAE <7% por bucket con n>500 pólizas. El bucket banca 30-35 tiene n=1,200, por lo que aplica el umbral 7%. El 5.1% está dentro de tolerancia, aunque marcado para monitoreo intensivo en el primer año de producción.

**T4.** `[Claude]` ¿Hicieron algún test de robustez frente a cambios en supuestos económicos?

`[Ana]` Sí, sensibilidad económica. Re-corrimos el modelo con los escenarios alto y bajo de inflación médica del ESG y observamos el impacto: +1% en inflación médica produce +0.9% en prima esperada, prácticamente lineal. Riesgos lo validó como consistente con la teoría.

**T5.** `[Claude]` ¿Qué tests fallaron o produjeron resultados que requirieron ajuste antes de aprobar?

`[Ana]` Dos. Primer fallo: la calibración inicial mostraba bias positivo en cohorte de antigüedad >5 años (sobreestimación de siniestralidad de cartera vieja). Lo corregimos con los pesos por antigüedad mencionados en 5.4. Segundo fallo: la primera versión tenía discontinuidad en la frontera Plan B / Plan C a edades 50+ (precio de Plan C podía caer por debajo de Plan B). Lo corregimos con la regla de piso post-modelo documentada en 4.2.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 6.3 Development Testing

> El régimen de testing de desarrollo del modelo comprendió seis tests formales documentados, cada uno con criterios de aceptación predefinidos en el plan de validación independiente acordado con la Subdirección de Riesgos de Modelos.
>
> El primer test corresponde a la convergencia numérica del GAM en el procedimiento de ajuste mediante REML. La verificación de convergencia se realizó comprobando la estabilidad del valor de la función objetivo en las iteraciones finales y la ausencia de warnings emitidos por la librería `mgcv`. El segundo test corresponde a la estabilidad de los coeficientes estimados mediante k-fold cross validation con k=5, ejercicio en el cual se evaluó la desviación máxima de cada coeficiente entre folds; los resultados se mantuvieron dentro de tolerancia con desviación máxima inferior al 3% en todos los coeficientes principales.
>
> El tercer test corresponde a la calibración in-sample sobre el conjunto de fit 2018-2022, ejercicio cuyos resultados se reportan en el repositorio de calibración trimestral. El cuarto test, el de mayor relevancia para la aceptación final, corresponde a la calibración out-of-sample contra el conjunto holdout 2023-2024. Las tres métricas evaluadas arrojaron los siguientes resultados: el error absoluto medio sobre prima esperada agregada por bucket edad × canal se ubicó en 2.8% promedio, con máximo de 5.1% observado en el bucket banca-seguros 30-35 años. La direccionalidad del error, medida como porcentaje de buckets con error dentro de la banda de ±2%, alcanzó el 64% (frente al 47% observado bajo la versión 1.0 del modelo). El bias agregado, medido como el error medio con signo, se ubicó en −0.4% (frente al sesgo de +6.2% identificado en banca-seguros bajo la versión 1.0).
>
> El criterio de aceptación documentado en el plan de validación independiente establece un umbral máximo de error absoluto medio de 7% por bucket con tamaño muestral superior a 500 pólizas. El bucket banca-seguros 30-35 años, con tamaño muestral de 1,200 pólizas y MAE de 5.1%, se mantiene dentro del umbral aprobado; sin embargo, ha sido marcado para monitoreo intensivo durante el primer año de operación de la versión 2.0.
>
> El quinto test corresponde al ejercicio comparativo formal contra la versión 1.0 del modelo, evaluando diferencias en prima esperada por segmento y validando que las mejoras observadas en banca-seguros no se obtienen a costa de degradación en otros canales. El sexto test corresponde al ejercicio de sensibilidad mediante remoción de outliers, en el cual se eliminaron observaciones con residuales superiores a tres desviaciones estándar y se re-estimó el modelo, verificando que los coeficientes principales se mantuvieron estables.
>
> Adicionalmente se ejecutó un ejercicio de sensibilidad económica con los escenarios alterno alto y bajo del supuesto de inflación médica documentados en el ESG Corporativo. Un incremento de un punto porcentual en la inflación médica produce un incremento aproximadamente lineal de 0.9% en la prima esperada agregada, resultado validado por la Subdirección de Riesgos como consistente con la teoría de pricing actuarial.
>
> Dos fallos materiales se identificaron durante el régimen de testing y fueron corregidos antes de la aprobación final del modelo. El primer fallo correspondió a un sesgo positivo sistemático observado en cohortes con antigüedad superior a cinco años, condición que reflejaba la sub-representación de cartera antigua documentada en la sección 5.4 y que se corrigió mediante la incorporación de pesos diferenciales por antigüedad de cohorte. El segundo fallo correspondió a una discontinuidad de precio en la frontera entre Plan B y Plan C para asegurados de 50 años o más, condición que producía instancias en las que el precio del Plan C podía caer por debajo del precio del Plan B para el mismo asegurado; esta discontinuidad se corrigió mediante la regla de piso post-modelo documentada en la sección 4.2.

**[Audit] 2026-05-08T15:54:11-06:00** — `seccion_completada` · `6.3.dev_testing` · 5 turnos.

---

### Step 24 — Sección 6.4 Limitations Revealed During Testing

#### Interview transcript (3 turnos)

**T1.** `[Claude]` Para 6.4: ¿qué limitaciones del modelo se evidenciaron durante el testing y son inherentes al diseño, no solo a los datos?

`[Ana]` Tres limitaciones de diseño. (1) El GAM no captura interacciones múltiples más complejas que dos variables simultáneas — un random forest sí lo haría pero ya descartamos esa ruta. (2) La estimación del efecto aleatorio para canales con muy pocas pólizas (banca-seguros) sigue siendo menos robusta que para canales grandes, aun con el prior informativo. (3) El modelo asume independencia entre pólizas; no modela contagios o eventos masivos como una pandemia.

**T2.** `[Claude]` ¿Hay mitigaciones operativas para cada limitación?

`[Ana]` (1) Aceptada como trade-off por interpretabilidad. (2) Monitoreo intensivo trimestral del canal banca-seguros con alertas al 1σ en lugar del 2σ habitual. (3) Plan de respuesta documentado a nivel institucional para pandemia — el modelo no entra en operación normal durante un evento sistémico.

**T3.** `[Claude]` ¿Cómo se planea revisar estas limitaciones en futuras versiones?

`[Ana]` Para (1): re-evaluar en la versión 3.0 (estimada 2027) considerando si vale la pena un modelo ensemble. Para (2): re-evaluar el prior informativo cuando banca-seguros llegue a 20K pólizas, estimado 2027. Para (3): no hay plan de versión.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 6.4 Limitations Revealed During Testing

> El régimen de testing reveló tres limitaciones inherentes al diseño del modelo, distinguibles de las limitaciones de datos documentadas en la sección 5.4.
>
> La primera limitación corresponde a la incapacidad del Generalized Additive Model para capturar interacciones múltiples de orden superior entre variables explicativas. La estructura del GAM permite interacciones bivariadas explícitas (en este modelo, la interacción edad × antigüedad de cohorte representada como spline bidimensional) pero no permite modelar de forma natural interacciones simultáneas entre tres o más variables sin proliferación de términos. Esta limitación constituye un trade-off explícitamente aceptado durante la especificación del modelo, dado que el objetivo institucional de interpretabilidad regulatoria descarta el uso de enfoques de aprendizaje automático con mayor capacidad de captura de interacciones complejas pero menor capacidad de explicación.
>
> La segunda limitación corresponde a la robustez subóptima de la estimación del efecto aleatorio para el canal banca-seguros, debido a su tamaño muestral moderado (aproximadamente 8,000 pólizas activas frente a 220,000 en agente tradicional). Aun con la incorporación del prior informativo documentada en la sección 5.4, la varianza de la estimación del efecto aleatorio de este canal se mantiene mayor que la observada para los demás canales. La mitigación operativa consiste en un régimen de monitoreo trimestral más intenso para este canal, con activación de alertas ante desviaciones superiores a una desviación estándar en lugar del umbral habitual de dos desviaciones estándar aplicado al resto de los canales.
>
> La tercera limitación corresponde al supuesto de independencia entre pólizas implícito en la formulación del modelo, supuesto que no captura eventos sistémicos con potencial de generar correlación entre observaciones individuales, como una pandemia. La mitigación operativa institucional consiste en el plan de respuesta documentado a nivel corporativo para eventos sistémicos, plan que suspende la operación normal del modelo durante períodos de evento sistémico declarado.
>
> Las dos primeras limitaciones se encuentran calendarizadas para reevaluación. La primera limitación será reevaluada en la versión 3.0 del modelo, prevista para el ejercicio 2027, considerando la conveniencia de migrar a una arquitectura de tipo ensemble que combine la interpretabilidad del GAM con elementos de captura de interacciones complejas. La segunda limitación será reevaluada cuando el canal banca-seguros alcance un volumen estimado de 20,000 pólizas, hito proyectado para el ejercicio 2027. La tercera limitación no cuenta con plan de revisión a nivel de modelo dado que su mitigación es de naturaleza institucional, no técnica.

**[Audit] 2026-05-08T16:14:38-06:00** — `seccion_completada` · `6.4.limitations` · 3 turnos.

---

### Step 25 — Sección 6.5 Record of Process Changes · OPCIONAL LLENA · CON EXTRACCIÓN

#### Interview transcript (2 turnos)

**T1.** `[Claude]` Para 6.5 (bitácora de procesos): ¿qué cambios en el proceso de construcción se registraron a lo largo del desarrollo?

`[Ana]` Cuatro. (1) 2025-08: cambio de método de selección de smoothing parameter (de UBRE a GCV). (2) 2025-10: incorporación de k-fold cross validation al pipeline de testing automatizado. (3) 2025-12: ajuste del criterio de aceptación MAE de 5% a 7% (negociado con Riesgos por consideración del trade-off bias-variance). (4) 2026-02: incorporación de bitácora R Markdown obligatoria por iteración.

**T2.** `[Claude]` ¿Quién aprobó cada uno?

`[Ana]` Todos: FAE y Riesgos. El (3) requirió debate más extenso documentado en minuta de Comité de Validación.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 6.5 Record of Process Changes

> A lo largo del desarrollo del modelo se registraron cuatro cambios materiales en el proceso de construcción, cada uno con autorización formal de las autoridades institucionales relevantes. En agosto de 2025 se modificó el método de selección del parámetro de suavización spline, sustituyendo el criterio UBRE (Un-Biased Risk Estimator) por el criterio GCV (Generalized Cross-Validation), modificación autorizada conjuntamente por el FAE y la Subdirección de Riesgos de Modelos. En octubre de 2025 se incorporó la ejecución sistemática de k-fold cross validation al pipeline automatizado de testing, modificación autorizada por las mismas autoridades. En diciembre de 2025 se ajustó el criterio cuantitativo de aceptación del error absoluto medio por bucket, modificándolo del 5% original al 7% finalmente aprobado, ajuste sustentado en consideraciones de trade-off bias-variance y documentado en la minuta del Comité de Validación. En febrero de 2026 se incorporó la obligación de mantenimiento de bitácora R Markdown por cada iteración del modelo, modificación de proceso autorizada por las mismas autoridades.

**[Apéndice tabular extraído al export]** (schema `SCHEMA_PROCESS_CHANGES`):

| date | decision | change_description |
|---|---|---|
| 2025-08 | Aprobado por FAE + Riesgos | Smoothing parameter: cambio de UBRE a GCV |
| 2025-10 | Aprobado por FAE + Riesgos | Incorporación de k-fold CV al pipeline de testing |
| 2025-12 | Aprobado por FAE + Riesgos (minuta Comité Validación) | Ajuste criterio MAE de 5% a 7% por trade-off bias-variance |
| 2026-02 | Aprobado por FAE + Riesgos | Bitácora R Markdown obligatoria por iteración |

**[Audit] 2026-05-08T16:32:18-06:00** — `seccion_completada` · `6.5.process_changes` · 2 turnos.

---

### Step 26 — Sección 7.1 Platform

#### Interview transcript (4 turnos)

**T1.** `[Claude]` Para 7.1: ¿en qué plataforma corre el modelo en producción y cómo se integra con los sistemas adyacentes?

`[Ana]` El motor de cálculo es Prophet 7.5 ejecutándose en una instancia dedicada Windows Server 2019 con 32 GB RAM y 8 cores virtuales. El post-procesamiento es R 4.3 ejecutándose en un servidor R Studio Server Linux RHEL 8. La orquestación es vía SQL Server Agent en el servidor de SQL Server 2019 prod-actuarial. El almacenamiento de snapshots es AWS S3 con cifrado SSE-S3 y versionado activo.

**T2.** `[Claude]` ¿Cuál es la latencia típica de una corrida completa end-to-end?

`[Ana]` 45 minutos en promedio: 30 minutos para Prophet (carga datos, ajuste y predicción) y 15 minutos para R post-procesamiento y publicación. El pipeline está calendarizado a las 03:00 hrs y termina alrededor de 03:45 hrs. La hora pico de consultas comerciales empieza a las 07:00 hrs.

**T3.** `[Claude]` ¿Cómo se controla el acceso a la plataforma — quién puede modificar el modelo, los inputs, los outputs?

`[Ana]` Tres niveles de acceso documentados. Acceso desarrollo: Diego, Mariana y Ana — pueden modificar código del modelo en branch separado, requiere PR aprobado por Ana para merge a producción. Acceso operativo: equipo de DevOps Pricing — pueden ejecutar ad-hoc el pipeline en producción para testing pero no modificar lógica. Acceso solo-lectura: Riesgos, Reservas, Capital, Comité de Producto — pueden consultar outputs pero no modificar.

**T4.** `[Claude]` ¿Existe ambiente de pruebas separado de producción?

`[Ana]` Sí, dos ambientes adicionales. Desarrollo: corre en laptops + servidor compartido R Studio. Pre-producción (staging): réplica completa del ambiente de producción usada para validar releases — copia diaria de datos production-like con anonimización parcial. Cada release pasa por staging antes de promoción a producción.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 7.1 Platform

> El modelo opera en una arquitectura de cuatro componentes tecnológicos integrados. El motor de cálculo corresponde a Prophet 7.5 ejecutándose en una instancia Windows Server 2019 dedicada, con 32 GB de RAM y 8 núcleos virtuales asignados. El componente de post-procesamiento corresponde a R 4.3 ejecutándose en un servidor R Studio Server bajo sistema operativo Linux RHEL 8. La capa de orquestación del pipeline corresponde a SQL Server Agent ejecutándose en el servidor de SQL Server 2019 identificado como `prod-actuarial`. El subsistema de almacenamiento persistente de snapshots corresponde a AWS S3 con cifrado en reposo bajo esquema SSE-S3 y versionado activo sobre el bucket institucional.
>
> La latencia de procesamiento end-to-end del pipeline completo es de aproximadamente 45 minutos por ejecución, con la distribución siguiente: 30 minutos corresponden a la fase Prophet (carga de datos desde SQL Server, ejecución del ajuste GAM y generación de predicciones por póliza tipo) y 15 minutos corresponden a la fase R (post-procesamiento, aplicación de reglas de negocio y publicación de outputs). El pipeline diario se encuentra calendarizado para inicio a las 03:00 horas y finalización aproximada a las 03:45 horas, completando ampliamente antes del inicio del horario pico de consultas comerciales a las 07:00 horas.
>
> El control de acceso a la plataforma se organiza en tres niveles diferenciados con responsabilidades documentadas. El nivel de acceso de desarrollo comprende a la Subgerente de Pricing GMM y a los dos developers asignados (Diego Reyes Aguilar y Mariana Pacheco Núñez), quienes pueden modificar el código del modelo en branches separados con requisito de Pull Request aprobado por la propietaria del modelo para promoción a la rama de producción. El nivel de acceso operativo comprende al equipo de DevOps de Pricing, autorizado para ejecutar el pipeline en producción de forma ad-hoc con fines de testing operativo pero sin facultades para modificar la lógica del modelo. El nivel de acceso de solo lectura comprende a las áreas consumidoras del modelo (Subdirección de Riesgos de Modelos, Reservas, Capital Regulatorio, Comité de Producto), autorizadas para consultar los outputs publicados sin facultades de modificación.
>
> La arquitectura institucional incorpora dos ambientes complementarios al ambiente de producción. El ambiente de desarrollo opera sobre estaciones de trabajo individuales de los developers y un servidor R Studio Server compartido para experimentación colaborativa. El ambiente de pre-producción (staging) constituye una réplica funcional completa del ambiente productivo, alimentada con copias diarias de datos production-like sometidos a procedimientos de anonimización parcial. La política institucional exige que todo release del modelo transite por el ambiente de pre-producción para validación antes de su promoción al ambiente de producción.

**[Audit] 2026-05-08T16:51:42-06:00** — `seccion_completada` · `7.1.platform` · 4 turnos.

---

### Step 27 — Sección 7.2 Model Runs

#### Interview transcript (3 turnos)

**T1.** `[Claude]` Para 7.2: describe las modalidades de ejecución del modelo en producción.

`[Ana]` Tres modalidades. (1) Corrida diaria automatizada — 03:00 hrs, sin intervención humana, produce tarifa del día. (2) Recalibración trimestral — último día hábil del trimestre, ejecutada por developers con validación de FAE, actualiza los coeficientes y pesos del modelo. (3) Corrida ad-hoc — bajo demanda, ejecutada por DevOps Pricing para responder consultas específicas (ej. cotización de plan especial), no actualiza tarifa publicada.

**T2.** `[Claude]` ¿Qué parámetros de control hay en cada modalidad?

`[Ana]` Diaria: ninguno editable, completamente parametrizada por el último release. Trimestral: ventana de datos (configurable), criterios de aceptación (heredados de plan de validación), método de selección de hiperparámetros (configurable bajo aprobación). Ad-hoc: input personalizado, modelo en modo "lectura" sin modificar tarifa publicada.

**T3.** `[Claude]` ¿Cómo se documenta cada corrida — hay registro de qué versión del modelo, qué datos, qué parámetros?

`[Ana]` Cada corrida genera un manifest YAML con: versión del modelo, hash del código (Git SHA), versión de los inputs (timestamp + checksum), versión de los supuestos (referencia al assumption set), parámetros de ejecución, y hora de inicio/fin. El manifest se almacena junto al snapshot de outputs en S3. Esto permite reproducir cualquier corrida histórica.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 7.2 Model Runs

> El modelo opera en producción bajo tres modalidades de ejecución diferenciadas con propósito y régimen de control específicos. La modalidad de corrida diaria automatizada se ejecuta a las 03:00 horas sin intervención humana y produce la tarifa publicable del día operativo subsecuente; esta modalidad opera con la totalidad de parámetros heredados del último release autorizado, sin facultad de modificación durante la ejecución. La modalidad de recalibración trimestral se ejecuta en el último día hábil del trimestre operativo, conducida por los developers del modelo con validación previa del FAE, y tiene por objeto la actualización de los coeficientes estimados y los pesos de cohorte; los parámetros configurables en esta modalidad comprenden la ventana de datos utilizada, los criterios cuantitativos de aceptación heredados del plan de validación independiente, y el método de selección de hiperparámetros sujeto a aprobación formal. La modalidad de corrida ad-hoc se ejecuta bajo demanda específica por el equipo de DevOps de Pricing para responder a consultas puntuales tales como la cotización de planes especiales o escenarios de sensibilidad; esta modalidad opera al modelo en estado de solo-lectura sin modificar en ningún caso la tarifa publicada en sistemas comerciales.
>
> El régimen de trazabilidad documental aplicable a toda corrida del modelo en cualquiera de las tres modalidades consiste en la generación automática de un manifest en formato YAML que captura los siguientes atributos: identificador de versión del modelo, hash del código fuente correspondiente al commit Git utilizado para la ejecución, identificador de versión de los inputs procesados (timestamp de generación y checksum de integridad), identificador del assumption set vigente, parámetros operativos de ejecución, y marcas temporales de inicio y finalización de la corrida. El manifest se almacena con persistencia indefinida en el bucket S3 conjuntamente con el snapshot de outputs correspondiente, permitiendo la reproducción exacta de cualquier corrida histórica del modelo para propósitos de auditoría, validación o análisis retrospectivo.

**[Audit] 2026-05-08T17:08:14-06:00** — `seccion_completada` · `7.2.runs` · 3 turnos.

---

### Step 28 — Sección 7.3 Performance Testing

#### Interview transcript (5 turnos)

**T1.** `[Claude]` Para 7.3: ¿qué tests de desempeño se ejecutaron sobre el modelo en producción para validar que refleja las specs?

`[Ana]` Cinco tests. (1) UAT funcional con casos de prueba documentados por Pricing. (2) Pruebas de regresión contra modelo 1.0 en escenarios canónicos. (3) Pruebas de carga: 50,000 pólizas simultáneas. (4) Pruebas de integridad de datos end-to-end (entrada vs salida). (5) Prueba de recuperación frente a fallas controladas.

**T2.** `[Claude]` Para el UAT funcional: ¿cuántos casos de prueba se ejecutaron y cuál fue el resultado?

`[Ana]` 87 casos de prueba documentados. 84 pasaron al primer intento. 3 fallaron y requirieron ajuste: dos por error en regla post-modelo (umbral incorrecto de piso de prima) y uno por edge case de edad 99+ que producía división por cero. Los tres se corrigieron y re-pasaron el UAT.

**T3.** `[Claude]` ¿Cómo se construyeron los casos canónicos para la comparación contra v1.0?

`[Ana]` 24 casos canónicos cubriendo combinaciones de plan (3) × género (2) × edad-bucket (4: 18-30, 31-45, 46-60, 61-75). Para cada caso se compara prima v1.0 vs prima v2.1 y se documenta la diferencia. La diferencia media absoluta es 4.3%, dirección esperada (v2.1 más alta en banca-seguros, más equilibrada en agente).

**T4.** `[Claude]` ¿Las pruebas de carga simularon cuántas pólizas y qué resultado tuvieron?

`[Ana]` 50,000 pólizas simultáneas — máximo previsto en pico operativo. Tiempo total: 8 minutos para esta carga sintética, dentro del SLA de 15 minutos. Uso de memoria peak 22 GB de los 32 GB disponibles. CPU al 78% peak. Sin errores.

**T5.** `[Claude]` ¿La prueba de recuperación cubrió qué escenarios de falla?

`[Ana]` Tres escenarios. (a) Falla de archivos de input — recuperación con re-publicación de tarifa día anterior. (b) Falla en Prophet (crash de proceso) — detección por timeout, alerta a equipo de turno, rollback automático al snapshot anterior. (c) Falla en post-procesamiento R — alerta y publicación de outputs Prophet sin post-proceso como contingencia (con flag en metadata).

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 7.3 Performance Testing

> El régimen de performance testing aplicado al modelo previo a su autorización para operación productiva comprendió cinco tests formales documentados, cada uno con criterios de aceptación predefinidos y resultados archivados en el repositorio de validación correspondiente.
>
> El primer test corresponde al User Acceptance Test (UAT) funcional, ejecutado sobre un conjunto de 87 casos de prueba documentados por la Subgerencia de Pricing GMM. De los 87 casos, 84 pasaron exitosamente en el primer intento. Los tres casos restantes requirieron corrección antes de la aprobación final: dos casos identificaron un error en una regla post-modelo correspondiente a un umbral incorrecto del piso de prima, y un caso identificó una situación de borde para asegurados de 99 años o más que producía división por cero en una etapa intermedia del procesamiento. Los tres errores se corrigieron y los casos correspondientes se re-ejecutaron exitosamente.
>
> El segundo test corresponde a las pruebas de regresión contra la versión 1.0 del modelo sobre un conjunto de 24 casos canónicos construidos como producto cartesiano de las dimensiones plan (3 niveles), género (2 niveles) y bucket de edad (4 niveles: 18-30, 31-45, 46-60, 61-75 años). Para cada caso se calculó la prima bajo ambas versiones del modelo y se documentó la diferencia porcentual. La diferencia absoluta media en prima entre versiones se ubicó en 4.3%, con direccionalidad consistente con las expectativas técnicas: la versión 2.1 produce primas superiores en el canal banca-seguros (donde se corrige el sesgo previo) y produce primas más equilibradas en el canal agente.
>
> El tercer test corresponde a las pruebas de carga sintética, ejecutadas con un volumen de 50,000 pólizas simultáneas correspondiente al máximo previsto en el pico operativo trimestral. El tiempo total de procesamiento end-to-end para esta carga sintética se ubicó en 8 minutos, dentro del SLA documentado de 15 minutos. El consumo máximo de memoria observado durante la prueba se ubicó en 22 GB de los 32 GB disponibles en el servidor Prophet. La utilización máxima de CPU se ubicó en 78%. La prueba se completó sin errores ni warnings emitidos por el motor.
>
> El cuarto test corresponde a las pruebas de integridad de datos end-to-end, verificando la consistencia entre los inputs originales y los outputs publicados mediante reconciliación contable y muestreo aleatorio. El quinto test corresponde a las pruebas de recuperación frente a fallas controladas, ejecutadas sobre tres escenarios documentados. El primer escenario consistió en la simulación de falla en los archivos de input proveniente del sistema Solix, sobre el cual se validó el comportamiento del control de contingencia consistente en la re-publicación de la tarifa del día hábil anterior. El segundo escenario consistió en la simulación de falla del motor Prophet mediante terminación controlada del proceso, sobre el cual se validó el funcionamiento del mecanismo de detección por timeout, la emisión correcta de la alerta operativa al equipo de turno, y el rollback automático al snapshot del día anterior. El tercer escenario consistió en la simulación de falla en la fase de post-procesamiento R, sobre el cual se validó el comportamiento del mecanismo de contingencia consistente en la publicación de los outputs directos de Prophet sin la capa de post-procesamiento, acompañados de un flag explícito en la metadata del snapshot.

**[Audit] 2026-05-08T17:42:55-06:00** — `seccion_completada` · `7.3.perf_testing` · 5 turnos.

---

### Step 29 — Sección 7.4 Production and Performance Limitations

#### Interview transcript (3 turnos)

**T1.** `[Claude]` Para 7.4: ¿qué limitaciones específicas tiene el modelo en producción derivadas de la implementación?

`[Ana]` Tres limitaciones operativas. (1) Latencia: la corrida diaria de 45 minutos no permite tarifa intra-día — si hay un evento que afecte siniestralidad después de las 03:00 hrs, no se refleja hasta el día siguiente. (2) Capacidad: el server Prophet maneja bien hasta 60K pólizas simultáneas, después degrada significativamente. (3) Dependencia upstream: si Solix falla en el ETL nocturno, el pipeline aborta sin tarifa fresca del día.

**T2.** `[Claude]` ¿Hay mitigaciones planeadas para estas limitaciones?

`[Ana]` Para (1): no hay plan a corto plazo, la cadencia diaria es suficiente para el negocio. Para (2): upgrade de servidor planeado 2026-Q4 (64 GB / 16 cores) cuando proyectamos llegar a 70K pólizas. Para (3): se solicitó a TI feed alternativo desde réplica de Solix para evitar single-point-of-failure; en evaluación.

**T3.** `[Claude]` ¿Hay algún caso donde el modelo se haya degradado en producción y se haya tenido que intervenir manualmente?

`[Ana]` Sí, uno. En enero 2026, el feed de Munich Re tuvo un retraso de 4 días por incidente del lado del reasegurador. El pipeline detectó la inconsistencia y abortó. Se ejecutó el protocolo de contingencia (republicación tarifa día anterior) durante 4 días, hasta normalizar. Se reportó como incidente operativo Tier 2 al Comité de Riesgos Operativos.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 7.4 Production and Performance Limitations

> La implementación productiva del modelo presenta tres limitaciones operativas conocidas, cada una con su impacto evaluado y su régimen de mitigación documentado.
>
> La primera limitación corresponde a la latencia del pipeline diario. La duración aproximada de 45 minutos para la ejecución end-to-end impide la generación de tarifas con frecuencia intra-día: cualquier evento operativo o de siniestralidad que ocurra con posterioridad a las 03:00 horas del día operativo no se refleja en la tarifa publicada hasta la ejecución del ciclo subsecuente, con horizonte mínimo de 24 horas. No se contempla plan de mitigación en el corto plazo dado que la cadencia diaria de actualización es considerada suficiente para los requerimientos del negocio.
>
> La segunda limitación corresponde a la capacidad de procesamiento del servidor Prophet asignado al modelo. El servidor maneja con desempeño aceptable cargas de hasta 60,000 pólizas simultáneas, después de las cuales se observa una degradación material del tiempo de respuesta. La mitigación corresponde al upgrade de infraestructura ya planeado para el cuarto trimestre de 2026, consistente en una migración a un servidor con 64 GB de RAM y 16 núcleos virtuales, dimensionada para soportar la proyección de 70,000 pólizas simultáneas estimada para el cierre del año 2027.
>
> La tercera limitación corresponde a la dependencia operativa del proceso ETL nocturno proveniente del sistema Solix. Una falla en este proceso aborta automáticamente el pipeline del modelo y resulta en la imposibilidad de generar tarifa fresca para el día subsecuente. La mitigación operativa corresponde al control de contingencia documentado consistente en la republicación de la tarifa del día hábil anterior. Como mitigación estructural se ha elevado a TI una solicitud de habilitación de un feed alternativo desde la réplica de Solix con el objetivo de eliminar el punto único de falla, solicitud que se encuentra en evaluación al cierre de esta versión del documento.
>
> Durante el período de operación de la versión 2.1 del modelo se registró un incidente operativo material correspondiente al retraso de cuatro días en el feed de Munich Re durante enero de 2026, evento originado por un incidente del lado del reasegurador. El pipeline del modelo detectó automáticamente la inconsistencia derivada del retraso y procedió al aborto de la ejecución. Durante el período de afectación se aplicó el protocolo de contingencia documentado, consistente en la republicación de la tarifa del día hábil anterior, hasta la normalización del feed. El incidente se documentó y reportó como incidente operativo de Tier 2 al Comité de Riesgos Operativos institucional.

**[Audit] 2026-05-08T18:02:33-06:00** — `seccion_completada` · `7.4.prod_limitations` · 3 turnos.

---

### Step 30 — Sección 8 Model Governance

#### Interview transcript (5 turnos)

**T1.** `[Claude]` Para 8 Governance: describe el marco de gobernanza institucional aplicable a este modelo, incluyendo roles, responsabilidades y procesos formales.

`[Ana]` Cuatro elementos. (1) Marco MRM institucional con tres líneas de defensa: Pricing (1L), Riesgos (2L), Auditoría Interna (3L). (2) Roles formales: Model Owner, FAE, Reviewer, Developer documentados con responsabilidades RACI. (3) Comités: Comité de Validación trimestral, Comité de Riesgos de Modelos mensual, Comité de Producto ad-hoc. (4) Procesos formales: attestation anual obligatoria, revisión metodológica trianual, plan de validación independiente anual.

**T2.** `[Claude]` Sobre el marco MRM: ¿qué versión del estándar institucional aplica y dónde está documentado?

`[Ana]` Aplica el MRM Standard SMNYL versión 3.2 (vigente desde 2024-Q1), publicado en SharePoint Riesgos /standards/mrm-v3.2.pdf. Sustituye las versiones 2.x y se alinea con el framework de SR 11-7 de la Fed adaptado al contexto regulatorio mexicano.

**T3.** `[Claude]` ¿Qué controles de software y datos aplican específicamente a este modelo?

`[Ana]` Cinco controles. (a) Control de versiones de código en Azure DevOps con políticas de PR obligatorio. (b) Code review obligatorio por al menos un segundo developer. (c) Pipeline CI/CD con tests unitarios automáticos. (d) Inmutabilidad de snapshots productivos en S3 (versionado + lock). (e) Logging estructurado de cada corrida con retención de 7 años.

**T4.** `[Claude]` Sobre los procesos de escalación: ¿cómo se escalan los hallazgos materiales?

`[Ana]` Proceso de escalación documentado en el MRM Standard sección 5.4. Hallazgo severidad baja: notificación al FAE y resolución en siguiente ciclo trimestral. Severidad media: notificación al FAE + Comité Validación, resolución en máximo 60 días. Severidad alta: notificación al Comité de Riesgos de Modelos + suspensión potencial del modelo según evaluación, resolución urgente. El hallazgo de attestation 2025 que motivó la versión 2.0 fue de severidad alta.

**T5.** `[Claude]` ¿Hay obligaciones regulatorias específicas de gobernanza más allá del marco interno?

`[Ana]` Dos. CNSF puede solicitar la documentación del modelo en cualquier inspección — el documento debe estar actualizado y firmado. IFRS 17 requiere que la metodología de pricing sea consistente con la metodología de reservas; consistency check anual está formalizado.

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 8 Model Governance

> El marco de gobernanza aplicable al modelo se estructura sobre cuatro componentes institucionales formalmente documentados, alineados al MRM Standard SMNYL versión 3.2 vigente desde el primer trimestre de 2024 y publicado en el repositorio SharePoint de la Subdirección de Riesgos de Modelos bajo la ruta `/standards/mrm-v3.2.pdf`. El estándar institucional se alinea conceptualmente al framework SR 11-7 de la Reserva Federal de Estados Unidos, adaptado al contexto regulatorio mexicano supervisado por la Comisión Nacional de Seguros y Fianzas.
>
> El primer componente del marco corresponde al esquema de tres líneas de defensa institucional. La primera línea (1L) corresponde al equipo de Pricing GMM como propietario y operador del modelo, responsable de su construcción, calibración y operación cotidiana. La segunda línea (2L) corresponde a la Subdirección de Riesgos de Modelos como revisor independiente, responsable de la validación metodológica y del proceso anual de attestation. La tercera línea (3L) corresponde a Auditoría Interna, responsable de validar el funcionamiento del marco de gobernanza en su conjunto. Las tres líneas operan con independencia funcional y reportan a través de cadenas de mando separadas.
>
> El segundo componente corresponde a los roles formales institucionales asignados al modelo, cada uno con responsabilidades definidas en matriz RACI. El Model Owner es responsable de la construcción técnica, operación y mantenimiento del modelo. El Functional Area Executive (FAE) es responsable de la aceptación del riesgo de modelo en nombre de la unidad de negocio y de la autorización formal de las versiones liberadas a producción. El Reviewer, perteneciente a la Subdirección de Riesgos de Modelos, es responsable de la validación independiente y debe afirmar su independencia respecto al equipo de construcción. Los Developers son responsables de la implementación técnica bajo la supervisión del Model Owner.
>
> El tercer componente corresponde a los comités institucionales con jurisdicción sobre el modelo. El Comité de Validación opera con periodicidad trimestral y revisa los resultados de recalibración y monitoreo. El Comité de Riesgos de Modelos opera con periodicidad mensual y supervisa el portafolio institucional de modelos, incluyendo hallazgos materiales. El Comité de Producto opera de manera ad-hoc para decisiones de alcance comercial que requieren autorización formal.
>
> El cuarto componente corresponde a los procesos formales que rigen el modelo a lo largo de su ciclo de vida. El proceso de attestation anual es obligatorio y constituye el ejercicio en el cual la Subdirección de Riesgos certifica formalmente la conformidad del modelo con el marco MRM. La revisión metodológica trianual evalúa la pertinencia conceptual del enfoque adoptado y la necesidad de evolución estructural. El plan de validación independiente anual define los ejercicios específicos de validación que la Subdirección de Riesgos ejecutará durante el ejercicio.
>
> El régimen de controles operativos sobre software y datos aplicable al modelo comprende cinco controles formales. Primero, el control de versiones del código fuente se mantiene en Azure DevOps con políticas obligatorias de Pull Request para cualquier modificación. Segundo, se exige code review obligatorio por al menos un developer adicional al autor de la modificación antes de la integración. Tercero, el pipeline de integración continua y despliegue continuo ejecuta automáticamente la batería de tests unitarios sobre cada commit. Cuarto, los snapshots productivos almacenados en S3 cuentan con versionado activo y políticas de inmutabilidad mediante Object Lock, impidiendo modificaciones retroactivas. Quinto, el logging estructurado de cada corrida del modelo se conserva durante un período de siete años conforme a la política institucional de retención documental.
>
> El régimen de escalación de hallazgos se encuentra documentado en la sección 5.4 del MRM Standard institucional y se estratifica en tres niveles. Un hallazgo de severidad baja se notifica al Functional Area Executive del modelo y se resuelve en el ciclo trimestral subsecuente. Un hallazgo de severidad media se notifica al FAE y al Comité de Validación con plazo máximo de resolución de 60 días naturales. Un hallazgo de severidad alta se eleva al Comité de Riesgos de Modelos y puede activar la suspensión del modelo según evaluación específica del Comité, requiriendo resolución urgente. El hallazgo de attestation 2025 que motivó la reconstrucción del modelo en la versión 2.0 fue clasificado con severidad alta.
>
> Adicionalmente al marco interno de gobernanza, el modelo está sujeto a dos obligaciones regulatorias específicas. La Comisión Nacional de Seguros y Fianzas puede solicitar la documentación técnica del modelo en cualquier inspección, condición que exige el mantenimiento continuo de la documentación actualizada y formalmente firmada por las autoridades institucionales correspondientes. El marco IFRS 17 exige consistencia metodológica entre el modelo de pricing y el modelo de reservas BEL, condición cuya verificación se encuentra formalizada mediante un consistency check anual ejecutado conjuntamente por las Subgerencias de Pricing GMM y Reservas BEL.

**[Audit] 2026-05-08T18:32:48-06:00** — `seccion_completada` · `8.governance` · 5 turnos.

---

### Step 31 — Sección 9 On-going Monitoring

#### Interview transcript (5 turnos)

**T1.** `[Claude]` Para 9 Monitoring: describe el régimen de monitoreo continuo del modelo en producción.

`[Ana]` Tres tipos de monitoreo. (1) Operativo: pipeline diario, success rate, latencia, alertas técnicas. (2) Estadístico: predicciones vs observado por bucket, residuales, estabilidad de coeficientes en recalibraciones. (3) De negocio: contribución al margen, market share, retención.

**T2.** `[Claude]` ¿Quién consume cada tipo de monitoreo y con qué frecuencia?

`[Ana]` Operativo: equipo de DevOps Pricing, monitoreo continuo, dashboard 24/7. Estadístico: Pricing actuarios (semanal) + Riesgos (mensual). De negocio: Comité de Producto (mensual) + Comité Validación (trimestral). El reporte trimestral consolidado lo presenta Ana al Comité de Validación.

**T3.** `[Claude]` ¿Qué KPIs específicos rastrean en el monitoreo estadístico?

`[Ana]` Cinco KPIs principales. (a) Loss ratio observado vs esperado por bucket (target ±5%). (b) Frecuencia siniestros observada vs esperada por edad-canal (target ±10%). (c) Severidad media observada vs esperada (target ±8%). (d) Lapse observado vs esperado por cohorte (target ±15%). (e) Estabilidad de coeficientes entre recalibraciones trimestrales (target desviación <10% en coef. principales).

**T4.** `[Claude]` ¿Qué activa una recalibración fuera de ciclo?

`[Ana]` Cuatro disparadores. (1) Bandera roja sostenida en cualquiera de los 5 KPIs por 2 trimestres consecutivos. (2) Cambio material en upstream model (notificado por contacto). (3) Evento de mercado (cambio regulatorio, shock económico) que afecte supuestos económicos materialmente. (4) Solicitud explícita de FAE o Comité Validación.

**T5.** `[Claude]` ¿Cómo se documenta cada ciclo de monitoreo trimestral?

`[Ana]` Reporte estructurado en R Markdown que se entrega al Comité de Validación. Contiene: resultados de los 5 KPIs por bucket, análisis de desviaciones materiales, comparativo trimestre actual vs anterior, recomendaciones operativas, y action items con fecha de cierre. El reporte se firma electrónicamente por Ana (Owner) y Pablo Hinojosa (Riesgos).

`[Claude]` `SECCION_COMPLETA`

#### [Drafter] Borrador final — Sección 9 On-going Monitoring

> El régimen de monitoreo continuo aplicable al modelo se organiza en tres líneas complementarias con propósito y audiencia diferenciados.
>
> La primera línea corresponde al monitoreo operativo del pipeline productivo, cuyo propósito es garantizar la disponibilidad y desempeño técnico del modelo en operación cotidiana. Las métricas observadas incluyen la tasa de éxito de las corridas diarias automatizadas, la latencia de procesamiento end-to-end, y la totalidad de alertas técnicas emitidas por los controles automatizados. El consumo de este monitoreo corresponde al equipo de DevOps de Pricing mediante un dashboard de disponibilidad continua 24/7, con alertas push ante eventos materiales.
>
> La segunda línea corresponde al monitoreo estadístico del desempeño predictivo del modelo, cuyo propósito es detectar de manera temprana cualquier desviación material entre el comportamiento observado de la cartera y las expectativas del modelo. Las métricas observadas se organizan en cinco indicadores clave de desempeño con tolerancias documentadas. El primer indicador corresponde al loss ratio observado contra el loss ratio esperado, evaluado por bucket de segmentación con tolerancia objetivo de ±5%. El segundo indicador corresponde a la frecuencia de siniestros observada contra la frecuencia esperada, evaluado por combinación edad-canal con tolerancia objetivo de ±10%. El tercer indicador corresponde a la severidad media observada contra la severidad esperada con tolerancia objetivo de ±8%. El cuarto indicador corresponde a la tasa de lapse observada contra la tasa esperada, evaluado por cohorte de aseguramiento con tolerancia objetivo de ±15%. El quinto indicador corresponde a la estabilidad de los coeficientes estimados entre recalibraciones trimestrales sucesivas, con tolerancia objetivo de desviación inferior al 10% para los coeficientes principales. El consumo de este monitoreo corresponde a los actuarios de Pricing con cadencia semanal y a la Subdirección de Riesgos de Modelos con cadencia mensual.
>
> La tercera línea corresponde al monitoreo de impacto de negocio, cuyo propósito es evaluar la contribución del modelo a los objetivos comerciales y financieros de la institución. Las métricas observadas incluyen la contribución del modelo al margen técnico de la cartera, la evolución del market share de la institución en el segmento GMM individual, y los indicadores de retención y crecimiento de la cartera asegurada. El consumo de este monitoreo corresponde al Comité de Producto con cadencia mensual y al Comité de Validación con cadencia trimestral.
>
> El régimen de respuesta ante desviaciones identificadas durante el monitoreo se estructura mediante cuatro disparadores formales para la activación de recalibraciones fuera del ciclo trimestral regular. El primer disparador corresponde a la observación de una bandera roja sostenida en cualquiera de los cinco indicadores clave de desempeño durante dos trimestres consecutivos. El segundo disparador corresponde a un cambio material reportado en cualquiera de los modelos upstream que alimentan el modelo, notificación que debe provenir del contacto técnico institucional asignado. El tercer disparador corresponde a un evento de mercado o regulatorio con afectación material esperada sobre los supuestos económicos, tales como cambios sustanciales en los lineamientos de Solvencia emitidos por la CNSF o shocks económicos sistémicos que afecten la curva de yields o la inflación médica. El cuarto disparador corresponde a una solicitud explícita emitida por el Functional Area Executive del modelo o por el Comité de Validación.
>
> La documentación del ciclo trimestral de monitoreo se materializa en un reporte estructurado generado en formato R Markdown que se presenta formalmente al Comité de Validación. El reporte incorpora los resultados cuantitativos de los cinco indicadores clave de desempeño desglosados por bucket de segmentación, el análisis cualitativo de las desviaciones materiales observadas con sus causas raíz identificadas, el comparativo entre el trimestre actual y el inmediato anterior para evaluación de tendencias, las recomendaciones operativas para el ciclo subsecuente, y los action items específicos con fechas de cierre asignadas. El reporte trimestral se firma electrónicamente por la Subgerente Owner del modelo y por el Subdirector de Riesgos de Modelos, formalizando la trazabilidad institucional.

**[Audit] 2026-05-08T19:08:22-06:00** — `seccion_completada` · `9.monitoring` · 5 turnos.

---

### Step 32 — Verificación de completitud

**Estado del documento al cierre de las 28 secciones:**

| Categoría | Conteo |
|---|---|
| Mandatorias completas | 22 / 22 |
| Opcionales completas | 3 (5.3.2, 5.5, 6.5) |
| Opcionales omitidas | 3 (3.2, 5.3.1, 5.3.3) |
| Mandatorias omitidas | 0 |
| **`porcentaje_resuelto`** | **100%** |
| **`porcentaje_completitud`** | **100%** (22/22 mandatorias completas) |

La state machine valida que `porcentaje_resuelto == 1.0` antes de permitir la transición `draft → in_review`. Condición satisfecha. ✓

---

### Step 33 — Transición `draft → in_review`

**Pantalla:** `/dashboard` → card Gobernanza → botón "Enviar a revisión" (habilitado porque completitud = 100%).

**Click → confirmación → llamada:**

```python
uc = CambiarEstadoDocumento(repo=DocumentoRepository(), state_machine=DocumentStateMachine())
resultado = uc.ejecutar(
    documento_id=doc.id,
    estado_destino="in_review",
    actor="ana.salinas",
    razon="Cierre de versión 2.1 — todas las secciones obligatorias completas y opcionales no aplicables omitidas con justificación."
)
# resultado.permitida == True
# resultado.razones == []
```

**Estado resultante:** `Documento.estado` = `"in_review"`.

**[Audit] 2026-05-08T19:14:55-06:00**
- `tipo`: `transicion_estado`
- `actor`: `ana.salinas`
- `descripcion`: `Documento enviado a revisión por el Owner`
- `metadata`: `{"origen": "draft", "destino": "in_review", "razon": "Cierre de versión 2.1 — todas las secciones obligatorias completas y opcionales no aplicables omitidas con justificación."}`

---

### Step 34 — Sign-off del Reviewer (afirmación de independencia)

**Pantalla:** Pablo Hinojosa Cárdenas (Riesgos) accede al documento → card Gobernanza muestra expander "Sign-off Reviewer" porque el estado es `in_review`.

**Inputs de Pablo:**

- Checkbox: **"Afirmo que actúo de forma independiente al equipo de construcción del modelo (Pricing GMM) y que mi revisión ha sido conducida bajo los lineamientos del MRM Standard SMNYL versión 3.2."** ✓ marcado
- Textarea (opcional): *"Revisión metodológica conducida sobre la especificación funcional v1.3 y los entregables del plan de validación independiente 2.0. Los hallazgos materiales identificados en attestation 2025 (sesgo en banca-seguros 30-45) se confirman corregidos en versión 2.1. Recomendación: aprobar con monitoreo intensivo del bucket banca-seguros 30-35 durante el primer año de operación."*

**Llamada:**

```python
uc = RegistrarSignoff(repo=DocumentoRepository())
uc.ejecutar(
    documento_id=doc.id,
    rol="reviewer",
    actor="pablo.hinojosa",
    notas="Revisión metodológica conducida sobre la especificación funcional v1.3 y los entregables del plan de validación independiente 2.0. Los hallazgos materiales identificados en attestation 2025 (sesgo en banca-seguros 30-45) se confirman corregidos en versión 2.1. Recomendación: aprobar con monitoreo intensivo del bucket banca-seguros 30-35 durante el primer año de operación.",
    afirmacion_independencia=True,
)
```

**[Audit] 2026-05-08T20:42:11-06:00**
- `tipo`: `signoff_reviewer`
- `actor`: `pablo.hinojosa`
- `descripcion`: `Sign-off del Reviewer registrado con afirmación de independencia`
- `metadata`: `{"rol": "reviewer", "afirmacion_independencia": "true", "notas_resumen": "Revisión metodológica completa; recomienda aprobar con monitoreo intensivo de bucket banca-seguros 30-35."}`

---

### Step 35 — Sign-off del FAE (aceptación de riesgo)

**Pantalla:** Roberto Castañeda Mendoza (FAE) accede al documento → card Gobernanza muestra ahora expander "Sign-off FAE" (habilitado porque ya hay sign-off del Reviewer).

**Inputs de Roberto:**

- Checkbox: **"Acepto el riesgo de modelo asociado a la versión 2.1 del Modelo de Pricing GMM Individual — Nuevos Negocios en mi rol de Functional Area Executive, conforme al MRM Standard SMNYL versión 3.2."** ✓ marcado
- Textarea (opcional): *"Aceptación de riesgo otorgada con base en la revisión del Reviewer Independiente (Pablo Hinojosa, Riesgos) y los entregables del plan de validación 2.0. Tomo nota de la recomendación de monitoreo intensivo del bucket banca-seguros 30-35 e instruyo a la Owner mantener reporte adicional mensual sobre este segmento durante 12 meses operativos."*

**Llamada:**

```python
uc.ejecutar(
    documento_id=doc.id,
    rol="fae",
    actor="roberto.castaneda",
    notas="Aceptación de riesgo otorgada con base en la revisión del Reviewer Independiente y los entregables del plan de validación 2.0. Instruyo monitoreo adicional mensual del bucket banca-seguros 30-35 durante 12 meses operativos.",
    afirmacion_aceptacion_riesgo=True,
)
```

**[Audit] 2026-05-08T21:18:33-06:00**
- `tipo`: `signoff_fae`
- `actor`: `roberto.castaneda`
- `descripcion`: `Sign-off del FAE registrado con aceptación de riesgo`
- `metadata`: `{"rol": "fae", "afirmacion_aceptacion_riesgo": "true", "instruccion_adicional": "Monitoreo mensual adicional sobre bucket banca-seguros 30-35 durante 12 meses operativos."}`

---

### Step 36 — Transición `in_review → approved`

**Pantalla:** Ana o el FAE accede al dashboard → card Gobernanza → botón "Aprobar" (habilitado porque ambos sign-offs están registrados).

**Llamada:**

```python
resultado = uc_cambiar.ejecutar(
    documento_id=doc.id,
    estado_destino="approved",
    actor="roberto.castaneda",
    razon="Aprobación final v2.1 — sign-offs Reviewer y FAE completos."
)
# resultado.permitida == True
```

**Estado resultante:** `Documento.estado` = `"approved"`.

**[Audit] 2026-05-08T21:22:14-06:00**
- `tipo`: `transicion_estado`
- `actor`: `roberto.castaneda`
- `descripcion`: `Documento aprobado tras sign-offs de Reviewer y FAE`
- `metadata`: `{"origen": "in_review", "destino": "approved", "razon": "Aprobación final v2.1 — sign-offs Reviewer y FAE completos."}`

---

### Step 37 — Export DOCX en Español

**Pantalla:** `/dashboard` → card Gobernanza → botón "Exportar DOCX" → modal con radio Idioma → "Español" seleccionado por default → click "Generar".

**Llamada:**

```python
uc_exportar = ExportarDocumento(
    repo=DocumentoRepository(),
    writer=DocxWriter(template_path="src/docs/templates/model_development_smnyl_final.docx"),
    extractor=TableExtractor(llm_client=AnthropicClient()),
    translator=None,  # No translation
)
resultado = uc_exportar.ejecutar(
    documento_id=doc.id,
    idioma_objetivo="es",
    actor="roberto.castaneda",
)
# resultado.contenido: bytes del .docx
# resultado.nombre_archivo: "Modelo_Pricing_GMM_Individual_Nuevos_Negocios_v2_1_2026-05-08.docx"
```

**Spinner UI:** "Extrayendo tablas tabulares con Haiku… Generando documento…" (~12 segundos).

**Streamlit `st.download_button` ofrece el archivo al usuario.**

**[Audit] 2026-05-08T21:25:42-06:00**
- `tipo`: `exportado`
- `actor`: `roberto.castaneda`
- `descripcion`: `Documento exportado a DOCX en español`
- `metadata`: `{"idioma": "es", "archivo": "Modelo_Pricing_GMM_Individual_Nuevos_Negocios_v2_1_2026-05-08.docx", "tamano_bytes": "184320"}`

#### Estructura del DOCX exportado (aproximación markdown)

> En el documento Word real cada sección rendera con: encabezados Heading 1/2 estilo SMNYL (azul `#0079c2`, Georgia 14pt), prosa en Tahoma 10pt sobre fondo blanco, tablas con `Table Grid` y font 9pt adaptable, negritas reales (no asteriscos), bullets con prefijo `•`, marca de pie de página *"Borrador asistido — requiere revisión humana"*.

```
═══════════════════════════════════════════════════════════════════
PORTADA
═══════════════════════════════════════════════════════════════════

                    [Logo SMNYL — esquinas redondeadas]


              NEW YORK LIFE — MODEL DEVELOPMENT TEMPLATE

                            Template Type A


    Modelo de Pricing GMM Individual — Nuevos Negocios

           M07.P02.S04.012.A · Versión 2.1


              Preparado por: Ana Salinas
              Fecha de generación: 8 de mayo de 2026

           Documento de gobernanza interno — Confidencial


═══════════════════════════════════════════════════════════════════
PÁGINA DE CONTROL DE VERSIONES (Sección 1.2)
═══════════════════════════════════════════════════════════════════

Version History (tabla nativa Word)

| Version | Date       | Author       | Status     | Notes                                                |
|---------|------------|--------------|------------|------------------------------------------------------|
| 1.0     | 2024-09-01 | Pricing GMM  | Retired    | Versión inicial publicada en producción              |
| 2.0     | 2025-Q4    | D. Reyes     | Superseded | Rediseño post-attestation 2025 (efectos aleatorios)  |
| 2.1     | 2026-03-15 | D. Reyes     | Approved   | Recalibración Q1 2026 + incorporación prior banca    |


═══════════════════════════════════════════════════════════════════
ÍNDICE
═══════════════════════════════════════════════════════════════════

1. Model Profile
   1.1 Attribute table .................................. p.3
   1.2 Version Control .................................. p.4
   1.3 Problem Statement ................................ p.5
2. Model Overview
   2.1 Model Uses ....................................... p.7
   2.2 Model Scope ...................................... p.9
   2.3 Business Impact of Model Usage ................... p.11
3. Related & Supporting Documents
   3.1 Ancillary documents .............................. p.13
   3.2 Additional Documents [SECCIÓN OMITIDA] ........... p.14
4. Model Description & Concept
   4.1 Schematic Diagram ................................ p.15
   4.2 Model Theory and Logic ........................... p.16
   4.3 Key Risk Drivers ................................. p.19
   4.4 Key Assumptions .................................. p.21
5. Inputs and Data
   5.1 Raw Data Sources and Data Quality ................ p.23
   5.2 Upstream Models & Company Assumptions ............ p.25
   5.3 Key Data Pre-Processing Steps
       5.3.1 Aggregations [SECCIÓN OMITIDA] ............. p.26
       5.3.2 Segmentations .............................. p.27
       5.3.3 Averages or Proxies [SECCIÓN OMITIDA] ...... p.28
   5.4 Known Input and Data Limitations ................. p.29
   5.5 Record of Input Changes .......................... p.31
6. Model Build Process
   6.1 Specification Process ............................ p.32
   6.2 Approach Used .................................... p.33
   6.3 Development Testing .............................. p.36
   6.4 Limitations Revealed During Testing .............. p.38
   6.5 Record of Process Changes ........................ p.39
7. Model Implementation & Production
   7.1 Platform ......................................... p.40
   7.2 Model Runs ....................................... p.42
   7.3 Performance Testing .............................. p.43
   7.4 Production and Performance Limitations ........... p.45
8. Model Governance .................................... p.46
9. On-going Monitoring ................................. p.49

APÉNDICES
   A. Tabla de Supuestos Clave (vinculado a 4.4) ........ p.52
   B. Sign-offs (Reviewer + FAE) ........................ p.54


═══════════════════════════════════════════════════════════════════
SECCIÓN 1.1 — Attribute Table (tabla nativa Word)
═══════════════════════════════════════════════════════════════════

| Attribute                  | Value                                              |
|----------------------------|----------------------------------------------------|
| Model Name                 | Modelo de Pricing GMM Individual — Nuevos Negocios |
| Model ID                   | M07.P02.S04.012.A                                  |
| Model Class                | Pricing                                            |
| Profit Center              | GMM-IND-001 (Vida + Salud — Productos GMM)         |
| FAE                        | Roberto Castañeda Mendoza                          |
| Model Owner                | Ana Salinas                                        |
| Model Developers           | Diego Reyes Aguilar; Mariana Pacheco Núñez         |
| Model Users                | Pricing actuarios; Reservas BEL; Capital; Comité   |
| Current Version            | 2.1                                                |
| Implementation Platform    | Prophet 7.5 + R 4.3 + AWS S3 + SQL Server 2019     |
| Financial Impact           | ~80,000 nuevas pólizas/año · ~MXN 1,200M prima Y1  |
| Model Status               | In production                                      |
| Target Production Date     | 2024-09-01 (v1.0); 2026-03-15 (v2.1)               |
| Inherent Risk Tier         | HIGH                                               |
| Nomenclatura               | M07.P02.S04.012.A                                  |


═══════════════════════════════════════════════════════════════════
SECCIÓN 1.3 — Problem Statement
═══════════════════════════════════════════════════════════════════

(Render del borrador final de la sección 1.3, ver Step 4)

[Texto completo: 4 párrafos · ~480 palabras · tono regulatorio formal]
[Negritas reales en: "+6.2% en banca-seguros 30-45", "IFRS 17",
 "Prophet 7.5", "contract boundary test"]


═══════════════════════════════════════════════════════════════════
SECCIÓN 2.1 — Model Uses
═══════════════════════════════════════════════════════════════════

(Borrador del Step 5 · 3 párrafos · ~280 palabras)


═══════════════════════════════════════════════════════════════════
SECCIÓN 2.2 — Model Scope
═══════════════════════════════════════════════════════════════════

(Borrador del Step 6 · 4 párrafos · ~440 palabras)


═══════════════════════════════════════════════════════════════════
SECCIÓN 2.3 — Business Impact of Model Usage
═══════════════════════════════════════════════════════════════════

(Borrador del Step 7 · 3 párrafos · ~310 palabras)


═══════════════════════════════════════════════════════════════════
SECCIÓN 3.1 — Ancillary documents list
═══════════════════════════════════════════════════════════════════

(Borrador del Step 8 · 1 párrafo · ~180 palabras · list-form)


═══════════════════════════════════════════════════════════════════
SECCIÓN 3.2 — Additional Documents
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ SECCIÓN OMITIDA — Pendiente para versión futura             │
│                                                             │
│ Documentación adicional de producto en rediseño por        │
│ Marketing; se incorporará en la próxima versión del         │
│ modelo (v2.2, 2026-Q3).                                     │
└─────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
SECCIÓN 4.1 — Schematic Diagram
═══════════════════════════════════════════════════════════════════

(Borrador del Step 10 · 3 párrafos · ~420 palabras)
[Pendiente: insertar como apéndice gráfico el diagrama Visio
 versión 2.1 (2026-03-15)]


═══════════════════════════════════════════════════════════════════
SECCIÓN 4.2 — Model Theory and Logic
═══════════════════════════════════════════════════════════════════

(Borrador del Step 11 · 5 párrafos · ~720 palabras · sección
 más densa metodológicamente)
[Subtítulo bold: "Reglas post-modelo aplicadas en R 4.3"
 antes del último párrafo]


═══════════════════════════════════════════════════════════════════
SECCIÓN 4.3 — Key Risk Drivers
═══════════════════════════════════════════════════════════════════

(Borrador del Step 12 · 4 párrafos · ~520 palabras)


═══════════════════════════════════════════════════════════════════
SECCIÓN 4.4 — Key Assumptions
═══════════════════════════════════════════════════════════════════

(Borrador del Step 13 · 5 párrafos · ~650 palabras)

> Marca [Pendiente: confirmar fuente y proceso de validación
  del supuesto de lapse dinámico ante cambios de prima.]
  visible en el render final, en negritas.

Referencia a tabla: "El detalle cuantitativo de los 18 supuestos
individuales se encuentra en el Apéndice A: Tabla de Supuestos
Clave del Modelo."


═══════════════════════════════════════════════════════════════════
SECCIÓN 5.1 — Raw Data Sources and Data Quality
═══════════════════════════════════════════════════════════════════

(Borrador del Step 14 · 3 párrafos · ~420 palabras)

Tabla nativa Word generada al export por TableExtractor (Haiku)
con 5 filas — schema RAW_DATA_SOURCES — Table Grid font 9pt:

| Data Source | Type | Location | Method | Team |
|...|...|...|...|...|
(5 filas como las del Step 14)


═══════════════════════════════════════════════════════════════════
SECCIÓN 5.2 — Upstream Models & Company Determined Assumptions
═══════════════════════════════════════════════════════════════════

(Borrador del Step 15 · 2 párrafos · ~350 palabras)

Tabla nativa Word generada al export (schema UPSTREAM_MODELS)
con 4 filas — Table Grid font 10pt:

| # | Name | Key Contact | Inventory ID |
|...|...|...|...|
(4 filas)


═══════════════════════════════════════════════════════════════════
SECCIÓN 5.3.1 — Data Aggregations
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ SECCIÓN OMITIDA — No aplica al modelo                       │
│                                                             │
│ El modelo opera a nivel póliza individual (policy-level);   │
│ no se realiza agregación previa al fit del GAM.             │
└─────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
SECCIÓN 5.3.2 — Segmentations
═══════════════════════════════════════════════════════════════════

(Borrador del Step 17 · 3 párrafos · ~330 palabras)


═══════════════════════════════════════════════════════════════════
SECCIÓN 5.3.3 — Use of Averages or Proxies
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ SECCIÓN OMITIDA — No aplica al modelo                       │
│                                                             │
│ El modelo no utiliza promedios ni proxies sobre las         │
│ observaciones de entrada.                                   │
└─────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
SECCIÓN 5.4 — Known Input and Data Limitations
═══════════════════════════════════════════════════════════════════

(Borrador del Step 19 · 5 párrafos · ~510 palabras)


═══════════════════════════════════════════════════════════════════
SECCIÓN 5.5 — Record of Input Changes
═══════════════════════════════════════════════════════════════════

(Borrador del Step 20 · 1 párrafo · ~280 palabras)

Tabla nativa Word (schema INPUT_CHANGES) con 4 filas.


═══════════════════════════════════════════════════════════════════
SECCIONES 6.1 a 6.5
═══════════════════════════════════════════════════════════════════

6.1 Specification Process .... (Step 21 · 3 párrafos · ~340 pal.)
6.2 Approach Used ............ (Step 22 · 6 párrafos · ~780 pal.)
6.3 Development Testing ...... (Step 23 · 6 párrafos · ~720 pal.)
6.4 Limitations Revealed ..... (Step 24 · 5 párrafos · ~430 pal.)
6.5 Record of Process Changes  (Step 25 · 1 párrafo  · ~190 pal.)
                               + tabla nativa PROCESS_CHANGES (4 filas)


═══════════════════════════════════════════════════════════════════
SECCIONES 7.1 a 7.4
═══════════════════════════════════════════════════════════════════

7.1 Platform ................. (Step 26 · 4 párrafos · ~480 pal.)
7.2 Model Runs ............... (Step 27 · 2 párrafos · ~360 pal.)
7.3 Performance Testing ...... (Step 28 · 5 párrafos · ~690 pal.)
7.4 Production Limitations ... (Step 29 · 4 párrafos · ~440 pal.)


═══════════════════════════════════════════════════════════════════
SECCIÓN 8 — Model Governance
═══════════════════════════════════════════════════════════════════

(Borrador del Step 30 · 7 párrafos · ~970 palabras)
[Sección más larga del documento]


═══════════════════════════════════════════════════════════════════
SECCIÓN 9 — On-going Monitoring
═══════════════════════════════════════════════════════════════════

(Borrador del Step 31 · 5 párrafos · ~680 palabras)


═══════════════════════════════════════════════════════════════════
APÉNDICE A — Tabla de Supuestos Clave del Modelo
═══════════════════════════════════════════════════════════════════

[Heading 1 estilo SMNYL · vinculado a sección 4.4]

> Tabla nativa Word con 18 filas × 5 columnas, Table Grid style,
> font 9pt (densidad media), bordes negros 0.5pt, encabezados
> de columna en negritas reales.

(Las 18 filas listadas en Step 13 — Apéndice A)


═══════════════════════════════════════════════════════════════════
APÉNDICE B — Sign-offs
═══════════════════════════════════════════════════════════════════

REVIEWER SIGN-OFF
─────────────────
Nombre:               Pablo Hinojosa Cárdenas
Rol:                  Subdirector de Riesgos de Modelos
Fecha:                2026-05-08 20:42:11 (UTC-6)
Afirmación:           ✓ Independencia respecto al equipo
                      de construcción del modelo
Notas:                Revisión metodológica conducida...
                      [texto completo del Step 34]

FAE SIGN-OFF
────────────
Nombre:               Roberto Castañeda Mendoza
Rol:                  Subdirector de Productos GMM (FAE)
Fecha:                2026-05-08 21:18:33 (UTC-6)
Afirmación:           ✓ Aceptación del riesgo de modelo
                      en nombre de la unidad de negocio
Notas:                Aceptación de riesgo otorgada con base...
                      [texto completo del Step 35]


═══════════════════════════════════════════════════════════════════
PIE DE PÁGINA (en cada página, Tahoma 8pt color Iron #565656)
═══════════════════════════════════════════════════════════════════

Modelo de Pricing GMM Individual — Nuevos Negocios · v2.1
Borrador asistido — requiere revisión humana · Página N de M
```

**Tamaño estimado del DOCX renderizado:** 56 páginas A4 · ~180 KB.

---

### Step 38 — Export DOCX en Inglés (U.S. corporate)

**Pantalla:** Usuario abre el dialog "Exportar DOCX" → cambia el toggle de Idioma a "English (U.S. corporate)" → click "Generar".

**Llamada:**

```python
uc_exportar = ExportarDocumento(
    repo=DocumentoRepository(),
    writer=DocxWriter(template_path="src/docs/templates/model_development_smnyl_final.docx"),
    extractor=TableExtractor(llm_client=AnthropicClient()),
    translator=TraductorDocumento(llm_client=AnthropicClient()),  # Activado
)
resultado = uc_exportar.ejecutar(
    documento_id=doc.id,
    idioma_objetivo="en",
    actor="roberto.castaneda",
)
# resultado.nombre_archivo: "Pricing_Model_GMM_Individual_New_Business_v2_1_2026-05-08.docx"
```

**Comportamiento:** el `TraductorDocumento` recorre el documento sección por sección y apéndice por apéndice, traduciendo `contenido` y `contenido_md` con un prompt específico de U.S. corporate English. La traducción es **efímera** — muta el `Documento` en memoria pero **no persiste** la versión traducida; el documento en español queda intacto en BD.

**Spinner UI:** "Traduciendo a U.S. corporate English… Extrayendo tablas… Generando documento…" (~95 segundos para 28 secciones + apéndice).

**[Audit] 2026-05-08T21:30:18-06:00**
- `tipo`: `exportado`
- `actor`: `roberto.castaneda`
- `descripcion`: `Documento exportado a DOCX en inglés (U.S. corporate)`
- `metadata`: `{"idioma": "en", "archivo": "Pricing_Model_GMM_Individual_New_Business_v2_1_2026-05-08.docx", "tamano_bytes": "189440"}`

---

#### Selecciones representativas del DOCX en inglés

A continuación se muestran cinco secciones traducidas y un apéndice para validar la calidad de la traducción. **Validar especialmente:** vocabulario actuarial preservado (BEL, MP, IFRS 17, ESG, GAM); identifiers verbatim (M07.P02.S04.012.A); tono American corporate formal sin contracciones.

---

#### EN · Section 1.3 — Problem Statement

> The model determines the tariff premium for new business GMM individual policies, covering the three product plans currently offered (Plan A with sum insured up to MXN 1.5 million; Plan B up to MXN 5 million; Plan C up to MXN 15 million) and the three active distribution channels (traditional agent, broker, and bancassurance). The following items are explicitly out of scope: group policies (covered by an independent model), renewals (model M07.P02.S04.013.A), and insureds under 18 years of age, for whom a manual factor defined by the Product Committee is applied in the absence of sufficient experience for statistical calibration.
>
> Version 2.0 supersedes version 1.0 (2024), a parametric extension of a Generalized Linear Model previously coupled to the renewals engine. The motivation for the redesign originates from the 2025 attestation conducted by the Model Risk Management subdivision: the backtest of version 1.0 evidenced a systematic bias of +6.2% in expected premium versus observed loss experience for the bancassurance channel within the 30-45 age bracket. Risk Management classified the finding with high severity, and the Product Committee authorized the rebuild with a delivery timeline through the first quarter of 2026.
>
> The design of version 2.0 is subject to three documented constraints. First, the platform must be Prophet 7.5, the institutional pricing engine; migration to an alternative platform was not authorized. Second, the initial calibration utilized loss experience observed through December 2022 exclusively, reserving years 2023 and 2024 as a holdout set for external validation. Third, the model outputs must be consumable by the Best Estimate Liability (BEL) reserve model under the IFRS 17 framework, which requires that pricing satisfy the contract boundary test and remain technically sustainable on a standalone basis, without cross-subsidization with the renewed portfolio.
>
> Two events are anticipated within the next twelve months that may motivate targeted revisions: the review of Solvency guidelines by the National Insurance and Surety Commission (CNSF), which could modify the risk loadings applicable to pricing in fiscal year 2027 and would require recalibration of technical margins without altering the model structure; and the planned migration from Prophet 7.5 to 7.7 in the fourth quarter of 2026, which will require regression testing of all implemented logic.

---

#### EN · Section 4.2 — Model Theory and Logic (key paragraphs)

> The core of the model is implemented as a Generalized Additive Model (GAM) with two-dimensional spline smoothing over the variables insured age and aseguramiento cohort tenure, complemented by fixed effects on the dimensions plan, gender, and geographic region, and random effects on the distribution channel dimension. Claim frequency is modeled under a Poisson distribution with logarithmic link function; severity is modeled through a Gamma distribution with logarithmic link function. The implementation uses the `mgcv` library integrated within Prophet 7.5.
>
> The choice of the GAM approach is supported by three technical and operational considerations. The first consideration corresponds to the adequate capture of the non-linear relationship between insured age and expected claim frequency, a relationship that exhibits a characteristic U-shape and that version 1.0 of the model approximated through discrete age bucket segmentation — an approximation that introduced price discontinuities at bucket boundaries. The second consideration corresponds to the preservation of technical interpretability required by the institutional MRM framework: the fitted spline curves can be explicitly visualized and defended in the annual attestation processes, a condition that is not satisfied by Gradient Boosting Machine-type approaches. The third consideration corresponds to compliance with the platform contract maintained with Information Technology: the Prophet 7.5 engine incorporates native support for GAM through the integration of `mgcv`, and the use of alternative approaches such as GBM would have required a non-authorized migration outside of Prophet.
>
> The use of random effects on the channel dimension responds directly to the high-severity finding raised by the Model Risk Management subdivision in the 2025 attestation regarding version 1.0. Distribution channels exhibit notably uneven volumes (approximately 220,000 policies in traditional agent, 105,000 in broker, 8,000 in bancassurance), a composition under which fixed effects produce unstable coefficients for the smaller subgroups. The specification with random effects induces the statistical *shrinkage* effect toward the global mean conditional on subgroup size, mitigating overfitting and the bias identified in the bancassurance channel.

*[Remaining paragraphs of section 4.2 follow the same register and translate the alternatives evaluation and the post-model rules consistently.]*

---

#### EN · Section 4.4 — Key Assumptions (full)

> The model's key assumptions are organized into five technical categories. The first category groups the demographic assumptions, comprising mortality table, morbidity frequencies, base lapse, and dynamic lapse. The second category groups the economic assumptions, comprising yields, general inflation, and medical inflation. The third category groups the commercial assumptions, comprising commission structure by channel and acquisition expenses. The fourth category groups the operating expense assumptions, comprising maintenance, claim handling, and institutional overhead. The fifth category groups the reinsurance assumptions, comprising cession rate and reinsurance cost applicable to Plans B and C.
>
> The quantitative detail of the 18 individual assumptions — base value, alternative high scenario, alternative low scenario, and documentary source — is contained in Appendix A: Table of Key Assumptions of the Model, integrated in full within this document. The present section does not replicate the numerical values in order to maintain a single source of truth and to facilitate quarterly updating.
>
> Source traceability is documented differentially by assumption. Mortality assumptions are derived from the SMNYL Institutional Mortality Model (M01.P01.S01.002.A) in its current version. Morbidity assumptions are derived from the GMM Institutional Morbidity Model (M02.P02.S03.005.A). Base lapse assumptions originate from a specific calibration performed for this model over the universe of cancellations observed during the period 2018-2022 in the GMM individual portfolio. Dynamic lapse assumptions in response to tariff changes likewise originate from in-house calibration over historical premium modification events. The economic assumptions (yields, general inflation, medical inflation) originate from the Corporate ESG maintained by Treasury (M00.P00.S00.001.E) in its most recent quarterly calibration. Commercial assumptions originate from the institutional policy approved by the Product Committee. Expense assumptions originate from the 2024-Q4 assumption set published by Finance. Reinsurance assumptions reflect the proportional contract currently in force with Munich Re for Plans B and C.
>
> `[Pending: confirm source and validation process for the dynamic lapse assumption in response to premium changes.]` In-house calibration was performed over historical tariff modification events, but the methodology is documented as "under review" in the functional specification approved by the Product Committee. Formal validation by the Model Risk Management subdivision in the Independent Validation Plan 2.0 is pending.
>
> The assumption monitoring regime differentiates three levels of intensity. Three critical assumptions are monitored at a frequency higher than the model recalibration cadence: medical inflation on a monthly basis; base lapse by cohort on a monthly basis; and morbidity by major condition on a quarterly basis with breakdown by condition type. The remaining assumptions are reviewed on an annual basis within the institutional attestation framework.

---

#### EN · Section 5.1 — Raw Data Sources and Data Quality (key paragraphs)

> The model is fed by five primary data sources, each with a defined institutional owner and an incorporation method to the Prophet data mart. The active policy portfolio data source corresponds to daily snapshots of the `dbo.polizas_vigentes` table of the Solix administrative system, owned by the Policy Administration team and loaded each night through the ETL job `etl_pricing_inputs_v2.1.sql` in SQL Server. The paid claims data source corresponds to daily snapshots of the `dbo.siniestros_pagados` table of the same system, with equivalent ownership and loading method. The premium movements data source corresponds to the `mov_prima` table of the `prod-actuarial/db_admin_polizas` SQL Server system, owned by the Policy Administration team, with daily automated ETL loading. The reinsurance information data source corresponds to a monthly feed from Munich Re in XML format, deposited in the S3 bucket `smnyl-reaseguro/munich-re/`, owned by the Institutional Reinsurance team, with biweekly manual loading through the `R/load_reaseguro.R` script. The institutional morbidity data source corresponds to Parquet-format files deposited in S3 `smnyl-actuarial-data/morbilidad/`, owned by the Morbidity subdivision, with quarterly refresh generated by a Databricks notebook that notifies the Pricing team for incorporation into the calibration cycle.
>
> The data quality control regime operates in three sequential levels. The first level comprises pre-ETL automated validations executed at the source: checksum verification on Solix files, validation of non-null values in key fields, and detection of duplicate records by policy number. The second level comprises post-ETL automated validations on the resulting data mart: reconciliation of aggregated totals against the independent accumulated control, and validation of plausible numerical ranges on sum insured and premium. The third level comprises a quarterly manual validation consisting of random sampling of 200 policies and cross-validation against source systems.

*[Tables and remaining paragraphs continue in the same register; the SCHEMA_RAW_DATA_SOURCES table in the Word document renders with English column headers: Data Source, Type, Location, Method, Team.]*

---

#### EN · Section 8 — Model Governance (key paragraphs)

> The governance framework applicable to the model is structured on four formally documented institutional components, aligned with the SMNYL MRM Standard version 3.2 effective since the first quarter of 2024 and published in the Model Risk Management SharePoint repository under the path `/standards/mrm-v3.2.pdf`. The institutional standard is conceptually aligned with the SR 11-7 framework of the United States Federal Reserve, adapted to the Mexican regulatory context supervised by the National Insurance and Surety Commission (CNSF).
>
> The first component of the framework corresponds to the institutional three-lines-of-defense scheme. The first line (1L) corresponds to the GMM Pricing team as the owner and operator of the model, responsible for its construction, calibration, and daily operation. The second line (2L) corresponds to the Model Risk Management subdivision as the independent reviewer, responsible for methodological validation and the annual attestation process. The third line (3L) corresponds to Internal Audit, responsible for validating the functioning of the governance framework as a whole. The three lines operate with functional independence and report through separate reporting chains.
>
> The second component corresponds to the formal institutional roles assigned to the model, each with responsibilities defined in a RACI matrix. The Model Owner is responsible for the technical construction, operation, and maintenance of the model. The Functional Area Executive (FAE) is responsible for accepting the model risk on behalf of the business unit and for formally authorizing the versions released to production. The Reviewer, belonging to the Model Risk Management subdivision, is responsible for the independent validation and must affirm independence with respect to the construction team. Developers are responsible for technical implementation under the supervision of the Model Owner.

*[Remaining paragraphs translate committees, formal processes, software/data controls, escalation procedures, and regulatory obligations with the same register.]*

---

#### EN · Appendix A — Table of Key Assumptions of the Model (translated)

> Native Word table rendered in the English export. Column headers translated; identifiers (model IDs, vendor names) preserved verbatim; technical terms (qx, BEL, ESG) preserved.

| Assumption | Base Value | High Scenario | Low Scenario | Source |
|---|---|---|---|---|
| Mortality — selected table | SMNYL-2024-GMM | +10% | −10% | M01.P01.S01.002.A |
| Morbidity — major condition frequency (age 45+) | 4.8% annual | 5.6% | 4.0% | M02.P02.S03.005.A |
| Morbidity — average severity | MXN 285,000 | MXN 320,000 | MXN 250,000 | M02.P02.S03.005.A |
| Base lapse — year 1 | 12.5% | 15.0% | 10.0% | In-house calibration 2018-2022 |
| Base lapse — years 2-5 | 6.8% | 8.5% | 5.2% | In-house calibration 2018-2022 |
| Dynamic lapse — premium change coefficient | −0.45 | −0.60 | −0.30 | In-house calibration (under review) |
| Technical yield (10Y MX) | 8.2% | 9.5% | 7.0% | Corporate ESG |
| General inflation | 4.5% | 5.5% | 3.5% | Corporate ESG |
| Medical inflation | 6.5% | 9.0% | 4.5% | Corporate ESG |
| Traditional agent commission | 28% year 1 | — | — | Institutional policy |
| Broker commission | 22% year 1 | — | — | Institutional policy |
| Bancassurance commission | 18% year 1 | — | — | Institutional policy |
| Acquisition expenses (non-commission) | MXN 850/policy | +15% | −15% | Finance 2024-Q4 |
| Maintenance expenses | MXN 420/policy/yr | +12% | −12% | Finance 2024-Q4 |
| Claim handling | MXN 1,800/claim | +10% | −10% | Finance 2024-Q4 |
| Institutional overhead | 3.2% of premium | +0.5pp | −0.5pp | Finance 2024-Q4 |
| Plan B reinsurance cession | 30% | — | — | Munich Re contract |
| Plan C reinsurance cession | 50% | — | — | Munich Re contract |

> **Validation notes for translation quality:**
> - "Best Estimate Liability" → preserved as English term + acronym BEL (no Spanish equivalent used)
> - "GAM (Generalized Additive Model)" → preserved (technical acronym)
> - "Lapse" → preserved (industry-standard English term used unchanged in Spanish original)
> - "MP (Model Point)", "ESG (Economic Scenario Generator)", "IFRS 17" → all preserved verbatim
> - Identifiers `M07.P02.S04.012.A`, `mgcv`, `dbo.polizas_vigentes` → preserved verbatim (technical references)
> - Person names → not translated (Ana Salinas, Roberto Castañeda Mendoza, etc.)
> - Currency MXN → preserved (no conversion); amount notation preserved (`MXN 1,200 M`)
> - Dates → ISO format preserved (`2026-03-15`); textual date "8 de mayo de 2026" → "May 8, 2026"

**Final state of source document:** the Spanish version remains intact in the database — the translation existed only in memory for export purposes.

---

## 4. Audit trail completo

> Tal como se vería en la pantalla `/auditoria` — timeline vertical con marcadores coloreados por tipo de evento. 43 eventos en total. Filtrable por tipo.

| # | Timestamp (UTC-6) | Tipo | Actor | Sección | Descripción |
|---|---|---|---|---|---|
| 01 | 2026-05-08 09:00:12 | `documento_creado` | ana.salinas | — | Documento creado desde cero |
| 02 | 2026-05-08 09:04:38 | `metadata_actualizada` | ana.salinas | — | Onboarding completado — 9 hechos transversales |
| 03 | 2026-05-08 09:11:22 | `metadata_actualizada` | ana.salinas | — | Metadata del modelo — 14 campos modificados |
| 04 | 2026-05-08 09:18-09:34 | `seccion_editada` × 4 | ana.salinas | 1.3 | (4 turnos intermedios) |
| 05 | 2026-05-08 09:34:51 | `seccion_completada` | ana.salinas | 1.3 | Sección 1.3 completada (5 turnos) |
| 06 | 2026-05-08 09:40-09:48 | `seccion_editada` × 2 | ana.salinas | 2.1 | (2 turnos intermedios) |
| 07 | 2026-05-08 09:48:14 | `seccion_completada` | ana.salinas | 2.1 | Sección 2.1 completada (3 turnos) |
| 08 | 2026-05-08 09:55-10:08 | `seccion_editada` × 3 | ana.salinas | 2.2 | (3 turnos intermedios) |
| 09 | 2026-05-08 10:08:32 | `seccion_completada` | ana.salinas | 2.2 | Sección 2.2 completada (4 turnos) |
| 10 | 2026-05-08 10:15-10:25 | `seccion_editada` × 2 | ana.salinas | 2.3 | (2 turnos intermedios) |
| 11 | 2026-05-08 10:25:11 | `seccion_completada` | ana.salinas | 2.3 | Sección 2.3 completada (3 turnos) |
| 12 | 2026-05-08 10:32-10:38 | `seccion_editada` × 1 | ana.salinas | 3.1 | (1 turno intermedio) |
| 13 | 2026-05-08 10:38:02 | `seccion_completada` | ana.salinas | 3.1 | Sección 3.1 completada (2 turnos) |
| 14 | 2026-05-08 10:40:15 | `seccion_omitida` | ana.salinas | 3.2 | Omitida — Pendiente para versión futura |
| 15 | 2026-05-08 10:47-10:58 | `seccion_editada` × 2 | ana.salinas | 4.1 | (2 turnos intermedios) |
| 16 | 2026-05-08 10:58:42 | `seccion_completada` | ana.salinas | 4.1 | Sección 4.1 completada (3 turnos · contiene [Pendiente: imagen]) |
| 17 | 2026-05-08 11:05-11:24 | `seccion_editada` × 5 | ana.salinas | 4.2 | (5 turnos intermedios — sección densa) |
| 18 | 2026-05-08 11:24:18 | `seccion_completada` | ana.salinas | 4.2 | Sección 4.2 completada (6 turnos) |
| 19 | 2026-05-08 11:32-11:48 | `seccion_editada` × 3 | ana.salinas | 4.3 | (3 turnos intermedios) |
| 20 | 2026-05-08 11:48:33 | `seccion_completada` | ana.salinas | 4.3 | Sección 4.3 completada (4 turnos) |
| 21 | 2026-05-08 11:55-12:18 | `seccion_editada` × 4 | ana.salinas | 4.4 | (4 turnos intermedios + adjunción de apéndice) |
| 22 | 2026-05-08 12:21:55 | `seccion_completada` | ana.salinas | 4.4 | Sección 4.4 completada con apéndice (5 turnos) |
| 23 | 2026-05-08 12:21:56 | `seccion_editada` | ana.salinas | 4.4 | Apéndice A adjuntado (18 filas × 5 cols) |
| 24 | 2026-05-08 12:30-12:55 | `seccion_editada` × 3 | ana.salinas | 5.1 | (3 turnos intermedios) |
| 25 | 2026-05-08 12:55:42 | `seccion_completada` | ana.salinas | 5.1 | Sección 5.1 completada (4 turnos) |
| 26 | 2026-05-08 13:02-13:20 | `seccion_editada` × 2 | ana.salinas | 5.2 | (2 turnos intermedios) |
| 27 | 2026-05-08 13:20:18 | `seccion_completada` | ana.salinas | 5.2 | Sección 5.2 completada (3 turnos) |
| 28 | 2026-05-08 13:23:05 | `seccion_omitida` | ana.salinas | 5.3.1 | Omitida — No aplica al modelo |
| 29 | 2026-05-08 13:30-13:42 | `seccion_editada` × 2 | ana.salinas | 5.3.2 | (2 turnos intermedios) |
| 30 | 2026-05-08 13:42:11 | `seccion_completada` | ana.salinas | 5.3.2 | Sección 5.3.2 completada (3 turnos) |
| 31 | 2026-05-08 13:44:38 | `seccion_omitida` | ana.salinas | 5.3.3 | Omitida — No aplica al modelo |
| 32 | 2026-05-08 13:51-14:04 | `seccion_editada` × 2 | ana.salinas | 5.4 | (2 turnos intermedios) |
| 33 | 2026-05-08 14:04:42 | `seccion_completada` | ana.salinas | 5.4 | Sección 5.4 completada (3 turnos) |
| 34 | 2026-05-08 14:12-14:22 | `seccion_editada` × 1 | ana.salinas | 5.5 | (1 turno intermedio) |
| 35 | 2026-05-08 14:22:55 | `seccion_completada` | ana.salinas | 5.5 | Sección 5.5 completada (2 turnos) |
| 36 | 2026-05-08 14:30-14:42 | `seccion_editada` × 2 | ana.salinas | 6.1 | (2 turnos intermedios) |
| 37 | 2026-05-08 14:42:18 | `seccion_completada` | ana.salinas | 6.1 | Sección 6.1 completada (3 turnos) |
| 38 | 2026-05-08 14:50-15:18 | `seccion_editada` × 4 | ana.salinas | 6.2 | (4 turnos intermedios) |
| 39 | 2026-05-08 15:18:42 | `seccion_completada` | ana.salinas | 6.2 | Sección 6.2 completada (5 turnos) |
| 40 | 2026-05-08 15:26-15:54 | `seccion_editada` × 4 | ana.salinas | 6.3 | (4 turnos intermedios) |
| 41 | 2026-05-08 15:54:11 | `seccion_completada` | ana.salinas | 6.3 | Sección 6.3 completada (5 turnos) |
| 42 | 2026-05-08 16:02-16:14 | `seccion_editada` × 2 | ana.salinas | 6.4 | (2 turnos intermedios) |
| 43 | 2026-05-08 16:14:38 | `seccion_completada` | ana.salinas | 6.4 | Sección 6.4 completada (3 turnos) |
| 44 | 2026-05-08 16:24-16:32 | `seccion_editada` × 1 | ana.salinas | 6.5 | (1 turno intermedio) |
| 45 | 2026-05-08 16:32:18 | `seccion_completada` | ana.salinas | 6.5 | Sección 6.5 completada (2 turnos) |
| 46 | 2026-05-08 16:40-16:51 | `seccion_editada` × 3 | ana.salinas | 7.1 | (3 turnos intermedios) |
| 47 | 2026-05-08 16:51:42 | `seccion_completada` | ana.salinas | 7.1 | Sección 7.1 completada (4 turnos) |
| 48 | 2026-05-08 17:00-17:08 | `seccion_editada` × 2 | ana.salinas | 7.2 | (2 turnos intermedios) |
| 49 | 2026-05-08 17:08:14 | `seccion_completada` | ana.salinas | 7.2 | Sección 7.2 completada (3 turnos) |
| 50 | 2026-05-08 17:16-17:42 | `seccion_editada` × 4 | ana.salinas | 7.3 | (4 turnos intermedios) |
| 51 | 2026-05-08 17:42:55 | `seccion_completada` | ana.salinas | 7.3 | Sección 7.3 completada (5 turnos) |
| 52 | 2026-05-08 17:50-18:02 | `seccion_editada` × 2 | ana.salinas | 7.4 | (2 turnos intermedios) |
| 53 | 2026-05-08 18:02:33 | `seccion_completada` | ana.salinas | 7.4 | Sección 7.4 completada (3 turnos) |
| 54 | 2026-05-08 18:10-18:32 | `seccion_editada` × 4 | ana.salinas | 8 | (4 turnos intermedios) |
| 55 | 2026-05-08 18:32:48 | `seccion_completada` | ana.salinas | 8 | Sección 8 Governance completada (5 turnos) |
| 56 | 2026-05-08 18:42-19:08 | `seccion_editada` × 4 | ana.salinas | 9 | (4 turnos intermedios) |
| 57 | 2026-05-08 19:08:22 | `seccion_completada` | ana.salinas | 9 | Sección 9 Monitoring completada (5 turnos) |
| 58 | 2026-05-08 19:14:55 | `transicion_estado` | ana.salinas | — | `draft` → `in_review` |
| 59 | 2026-05-08 20:42:11 | `signoff_reviewer` | pablo.hinojosa | — | Sign-off del Reviewer con afirmación de independencia |
| 60 | 2026-05-08 21:18:33 | `signoff_fae` | roberto.castaneda | — | Sign-off del FAE con aceptación de riesgo |
| 61 | 2026-05-08 21:22:14 | `transicion_estado` | roberto.castaneda | — | `in_review` → `approved` |
| 62 | 2026-05-08 21:25:42 | `exportado` | roberto.castaneda | — | DOCX exportado en español |
| 63 | 2026-05-08 21:30:18 | `exportado` | roberto.castaneda | — | DOCX exportado en inglés (U.S. corporate) |

**Total: 63 eventos** (eventos `seccion_editada` intermedios consolidados por sección — en producción cada turno de interview genera un evento individual; el conteo real estaría cerca de 110 eventos individuales).

**Distribución por tipo (conteo real esperado en producción):**

- `documento_creado`: 1
- `metadata_actualizada`: 2
- `seccion_editada`: 76 (uno por turno de interview)
- `seccion_completada`: 25
- `seccion_omitida`: 3
- `transicion_estado`: 2
- `signoff_reviewer`: 1
- `signoff_fae`: 1
- `exportado`: 2

**Total ~113 eventos.** Todos inmutables. Todos consultables vía pantalla `/auditoria` con filtros por tipo y por sección.

---

## 5. Métricas de uso del LLM

> Lo que se mostraría en el widget de costo del dashboard al cierre del flujo.

### 5.1 Llamadas LLM realizadas

| Modelo | Tarea | Llamadas | Input tokens | Output tokens | Cache read | Cache creation | Costo USD |
|---|---|---:|---:|---:|---:|---:|---:|
| `claude-sonnet-4-6` | chat (interview) | 76 | 95,200 | 41,800 | 832,000 | 12,200 | $4.12 |
| `claude-opus-4-7` | drafting (final) | 25 | 51,000 | 84,300 | 305,000 | 12,200 | $9.74 |
| `claude-haiku-4-5` | extraction (export ES) | 4 | 18,000 | 4,200 | 0 | 0 | $0.04 |
| `claude-haiku-4-5` | knowledge_extractor | 22 | 35,200 | 6,400 | 198,000 | 11,800 | $0.21 |
| `claude-sonnet-4-6` | translation (export EN) | 28 | 64,400 | 58,100 | 280,000 | 12,200 | $1.92 |
| `claude-haiku-4-5` | extraction (export EN) | 4 | 18,000 | 4,200 | 0 | 0 | $0.04 |

### 5.2 Totales

| Métrica | Valor |
|---|---|
| Total llamadas | 159 |
| Total input tokens (no-cached) | 281,800 |
| Total output tokens | 199,000 |
| Total cache read tokens | 1,615,000 |
| Total cache creation tokens | 48,400 |
| **Costo total USD** | **$16.07** |
| **Cache hit rate** | **0.831** (83.1%) |

### 5.3 Interpretación

- **Cache hit rate de 83.1%** confirma que el prompt caching del contexto fijo (~12K tokens: template + MRM + brand + tono) está funcionando. Sin caching, el costo sería ~3.5× mayor (~$56 USD).
- **Opus 4.7 representa 61% del costo total** ($9.74 / $16.07) aunque solo 16% de las llamadas (25/159). Es el costo justificado — el Drafter produce el output que el usuario realmente lee.
- **Sonnet 4.6 representa 38% del costo** ($6.04 incluyendo entrevista + traducción), 65% de las llamadas — buen valor.
- **Haiku 4.5 representa <1% del costo** ($0.29) y 19% de las llamadas — eficientísimo para extraction.
- **Costo unitario** del documento completo (creación + 28 secciones + export ES + export EN): **$16.07 USD**. Dentro del rango esperado ($10–20 USD por documento).

---

## 6. Cómo iterar si el simulado revela gaps

Si al recorrer el documento detectas que algún output no cumple la calidad esperada, los lugares donde iterar son:

| Gap detectado | Archivo a tocar | Tipo de cambio |
|---|---|---|
| Preguntas de Claude genéricas, no específicas | `src/llm/prompts/interview.py` | Endurecer instrucciones (más ejemplos de buena/mala pregunta) |
| Claude no pregunta "por qué" | `src/llm/prompts/interview.py` | Agregar regla explícita "demand reasons for every methodological choice" |
| Drafter usa coloquialismos | `src/llm/prompts/drafting.py` | Endurecer lista de prohibiciones léxicas |
| Drafter introduce `**markdown**` literal | `src/llm/prompts/drafting.py` | Reforzar prohibición de markdown visual + agregar ejemplos negativos |
| Marca `[Pendiente: ...]` no aparece donde debería | `src/llm/prompts/drafting.py` | Endurecer regla "if source missing, mark `[Pendiente: ...]`" |
| Traducción ES → EN pierde vocabulario técnico | `src/llm/prompts/traduccion_corporate_en.j2` | Ampliar la lista de términos a preservar verbatim |
| Tabla nativa Word con dimensiones malas en DOCX | `src/core/usecases/docx_writer.py` (función `font_size_para_tabla`) | Ajustar reglas de adaptación de font |
| Tabla extraída por Haiku con campos vacíos | `src/core/usecases/table_extractor.py` (schemas) | Mejorar prompt de extracción + tolerancia |
| Sign-off no se persiste correctamente | `src/core/usecases/cambiar_estado.py` | Revisar el método `RegistrarSignoff.ejecutar()` |
| Audit trail sin metadata útil | `src/core/models/auditoria.py` + use cases que generan eventos | Enriquecer `metadata` dict |

---

## 7. Validation checklist para Alberto

Aplica esta checklist al recorrer el documento de simulación. Cada ítem tiene `Pass / Fail / Marginal` para que puedas marcarlo:

### 7.1 Calidad de pregunta (Interview)

- [ ] **Q-01.** ¿Las preguntas son específicas, no genéricas? (Buen ejemplo: "¿De qué tabla de mortalidad parten los supuestos y de qué año?". Mal ejemplo: "¿Qué supuestos tiene el modelo?")
- [ ] **Q-02.** ¿Claude pregunta "por qué", no solo "qué"? (Ver Step 11 Sección 4.2 — busca "¿por qué GAM y no...?" y "¿por qué efectos aleatorios y no fijos?")
- [ ] **Q-03.** ¿Hay follow-ups cuando la respuesta es vaga? (Ver Step 4 Sección 1.3 turnos 1-2 — Claude pide aclaración sobre la attestation)
- [ ] **Q-04.** ¿1 pregunta por turno, nunca apiladas?
- [ ] **Q-05.** ¿Las preguntas siguen el orden de la `preguntas_guia` del catálogo o adaptan inteligentemente?
- [ ] **Q-06.** ¿El cierre con `SECCION_COMPLETA` aparece solo cuando la sección realmente captura suficiente material?

### 7.2 Calidad de redacción (Drafter)

- [ ] **D-01.** ¿3a persona impersonal en todos los drafts? ("Se utiliza...", "El modelo asume...", "Las pruebas mostraron...")
- [ ] **D-02.** ¿Vocabulario actuarial preciso? (BEL, MP, calibración, GAM, REML, GCV, validación cruzada k-fold, contract boundary test, etc.)
- [ ] **D-03.** ¿Cero asteriscos markdown literales en el output del Drafter? (Texto de la simulación los usa en este `.md` como aproximación visual; en el DOCX real no deben aparecer.)
- [ ] **D-04.** ¿`[Pendiente: ...]` aparece donde realmente falta info, no como muleta? (Ver 4.4 — pendiente sobre lapse dinámico)
- [ ] **D-05.** ¿Cada decisión metodológica tiene justificación? (Ver 4.2 — cada elección técnica tiene "por qué")
- [ ] **D-06.** ¿Cada supuesto tiene fuente identificada? (Ver 4.4 — cada supuesto del apéndice referencia un modelo institucional o assumption set)
- [ ] **D-07.** ¿Párrafos compactos (4-5 líneas), no muros de texto?
- [ ] **D-08.** ¿Cero phrases prohibidas? ("Como se mencionó", "Es importante notar", "En conclusión", "Cabe señalar", "Vale la pena mencionar")
- [ ] **D-09.** ¿Cero hedging? (No "creemos que", "decidimos", "podría decirse", "me parece")

### 7.3 Audit trail

- [ ] **A-01.** ¿Cada acción material genera un evento? (~110 eventos esperados; consolidados en 63 filas)
- [ ] **A-02.** ¿Sign-offs son eventos inmutables, no flags?
- [ ] **A-03.** ¿State transitions registran origen + destino en metadata?
- [ ] **A-04.** ¿Las omisiones registran motivo + detalle?
- [ ] **A-05.** ¿El timeline en la UI sería legible — orden cronológico, marcadores coloreados por tipo, filtros funcionales?
- [ ] **A-06.** ¿El export registra el idioma en metadata?

### 7.4 Apéndices y tablas

- [ ] **T-01.** ¿La tabla de assumptions de 4.4 se renderiza como tabla nativa Word con bordes y font 9pt? (No como lista markdown)
- [ ] **T-02.** ¿Las 4 tablas tabulares (5.1, 5.2, 5.5, 6.5) se ven como tablas nativas Word, no como prosa narrativa?
- [ ] **T-03.** ¿Los apéndices se referencian desde el cuerpo principal sin replicar la tabla?
- [ ] **T-04.** ¿El font de la tabla de assumptions (18 filas) es ~9pt — ni demasiado grande ni ilegible?

### 7.5 Omisiones

- [ ] **O-01.** ¿Las 3 secciones omitidas (3.2, 5.3.1, 5.3.3) muestran "Sección omitida — {motivo}" en el DOCX?
- [ ] **O-02.** ¿El motivo seleccionado es uno de los 4 oficiales del MVP (`No aplica` / `Información no disponible` / `Pendiente para versión futura` / `Otro`)?
- [ ] **O-03.** ¿En el DOCX, las omitidas aparecen en el índice marcadas como [OMITIDA]?
- [ ] **O-04.** ¿La state machine consideró las 3 omitidas como "resueltas" para el cálculo de `porcentaje_resuelto`?

### 7.6 Traducción ES → EN

- [ ] **L-01.** ¿Vocabulario técnico preservado verbatim? (BEL, MP, IFRS 17, ESG, GAM, REML, GCV)
- [ ] **L-02.** ¿Identifiers no traducidos? (M07.P02.S04.012.A, mgcv, dbo.polizas_vigentes)
- [ ] **L-03.** ¿Tono American corporate? (Third-person, no contractions, formal regulatory register)
- [ ] **L-04.** ¿Markdown formatting preservado? (Negritas se mantienen en lugares equivalentes)
- [ ] **L-05.** ¿Nombres de personas, currency MXN, fechas — manejados consistentemente?
- [ ] **L-06.** ¿El documento original en español permaneció **intacto** en BD post-traducción?

### 7.7 State machine y sign-offs

- [ ] **S-01.** ¿`draft → in_review` solo se permitió tras 100% resuelto?
- [ ] **S-02.** ¿`in_review → approved` solo se permitió tras los 2 sign-offs?
- [ ] **S-03.** ¿La afirmación de independencia del Reviewer está en el audit como evento, no como flag?
- [ ] **S-04.** ¿La aceptación de riesgo del FAE está en el audit como evento, no como flag?
- [ ] **S-05.** ¿En el DOCX, los sign-offs aparecen en un apéndice formal (Apéndice B)?

### 7.8 Apariencia general del DOCX

- [ ] **V-01.** ¿La portada tiene logo SMNYL, paleta azul `#0079c2`, tipografía Georgia para títulos?
- [ ] **V-02.** ¿Los headings de sección están en formato Heading 1/2 con estilo SMNYL?
- [ ] **V-03.** ¿La prosa está en Tahoma 10pt sobre fondo blanco?
- [ ] **V-04.** ¿Aparece el pie de página "Borrador asistido — requiere revisión humana" en cada página?
- [ ] **V-05.** ¿El documento se ve indistinguible de un doc corporativo real SMNYL? (Sin look "Streamlit default", sin tablas markdown, sin asteriscos)

---

## 8. Próximos pasos sugeridos

Una vez completada la validación:

### Si todo Pass o casi todo Pass

→ **Opción A:** Dejar este documento como referencia de calidad y arrancar la validación real con stakeholders (Vidal, Comité Validación).

→ **Opción B:** Ejecutar este escenario en la app real (operación tuya en navegador con respuestas guía de este doc) para comparar la calidad real-LLM vs la simulada. Tiempo estimado: 2-3 horas. Validamos contra esta referencia.

### Si hay gaps materiales detectados

→ **Iteración sobre prompts** según la tabla §6 ("Cómo iterar si el simulado revela gaps"). Después de cada iteración, regeneramos las secciones afectadas en este `.md` y re-evaluamos.

### Si quieres un fixture técnico permanente

→ **Opción C:** Crear un script de tests automatizados que reproduzca este escenario usando respuestas canned y mocks del LLM. Eso quedaría como integration test del flujo end-to-end. Tiempo estimado: 1-2 días.

---

## 9. Notas sobre el contenido del simulado

- **Plausibilidad:** todos los nombres de personas, ID de modelo (M07.P02.S04.012.A y M01/M02/M00 referenciados), nombres de áreas, vendors (Munich Re, Solix) y cifras (volúmenes de cartera, primas, costos) son **sintéticos**. La estructura del template, el vocabulario actuarial, las referencias regulatorias (CUSF, IFRS 17, SR 11-7) y los procesos institucionales (attestation, sign-off, MRM Standard) **sí son reales en su forma**.
- **Realismo del flujo:** las cinco fases del Drafter (Specification → Approach → Testing → Limitations → Process Changes) y los cinco indicadores de monitoreo siguen la práctica actuarial estándar. Un revisor real con experiencia en MRM debería sentir que el documento podría haber sido escrito en SMNYL.
- **Sesgo intencional:** el contenido se diseñó para exercise **todos** los features no triviales de DocuMente. No es necesariamente representativo de un caso "promedio" — es un fixture deliberadamente diseñado para ejercer la herramienta al máximo (sección densa con 6 turnos, sección con appendix Excel, secciones omitidas con 2 motivos diferentes, opcionales llenas, etc.).
- **Limitaciones de la simulación:** este `.md` aproxima lo que la app real produciría, pero (a) las llamadas LLM reales pueden producir variaciones de redacción, (b) la calidad del Drafter depende del prompt actual en `src/llm/prompts/drafting.py`, (c) la traducción real puede tener variaciones de Sonnet 4.6.

---

**Fin del documento de simulación.**

*Documento generado el 2026-05-08 como parte de la sesión 9 de DocuMente. Mantener para referencia de calidad en iteraciones futuras de prompts y plantilla.*












