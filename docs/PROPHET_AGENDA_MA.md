# PROPHET_AGENDA_MA — Agenda 1h para reunión con Modelos Actuariales

> Reunión propuesta: 1 hora. Objetivo = alinear sobre qué necesita MA
> para su governance de modelos Prophet y mapearlo a lo que DocuMente
> puede entregar en S17-S19. Esta agenda asume que ya leíste
> `PROPHET_FASE0_AUDIT.md`.

## Preparación previa

**Lo que DocuMente lleva a la mesa:**

1. **Demo en vivo (5 min)** — abrir DocuMente y mostrar:
   - Crear ficha Prophet desde cero (12 secciones).
   - Subir registro Excel de MA → detectar modelos → importar batch.
   - Vista previa del DOCX exportado actual.
   - **Importante**: aclarar desde el inicio que el template DOCX
     todavía NO está pulido — es Fase 0. La conversación es sobre
     **qué viene después**, no sobre el estado actual.

2. **Lo que YA está listo y le sirve a MA (S15+S16)**:
   - Importar PDFs/DOCX/Excel como fuentes adicionales — Claude lee
     instructivos y propone borradores automáticos por sección.
   - Visión Claude para describir screenshots en docs cargados
     (Prophet UI, flowcharts, diagramas). Caché por hash → no se
     re-paga.
   - Versionado funcional (ver, descargar DOCX de versión histórica,
     restaurar con snapshot automático previo).
   - Selector de idioma al exportar (ES/EN/bilingüe).
   - Markdown rendering en preview (tablas, bold, etc.).

**Lo que MA debería traer a la mesa:**

- Los templates en construcción (Word/Excel) para cambios de **bajo
  impacto** y **alto impacto**, aunque estén en borrador.
- Lista de modelos Prophet actuales clasificados por área dueña.
- Si hay un policy/framework escrito de governance — aún en borrador
  está bien.

---

## Agenda (60 min)

### Apertura (5 min)

- Contexto: DocuMente como plataforma agéntica de documentación.
  Tiene módulo Prophet Fase 0 funcional pero necesita evolucionar
  para servir el governance que MA está construyendo.
- Objetivo de hoy: alinear sobre alcance + cronograma de S17+.

### Bloque 1 — Tiering y clasificación de modelos (10 min)

**Preguntas concretas:**

1. **Tier 1 / 2 / 3 (alto / medio / bajo impacto)** — ¿cómo se
   clasifican? ¿qué métricas usan (impacto financiero, criticidad
   regulatoria, volumen de cálculo, dependencias)?
2. **¿Quién clasifica?** ¿MA solo o requiere visto bueno del área dueña?
3. **¿Qué documentación exige cada tier?** Tier 1 ≈ 100-300 pp en la
   industria; Tier 3 ≈ 15-30 pp. ¿MA tiene un estándar similar?
4. **¿La clasificación cambia con el tiempo?** ¿hay re-tiering anual?

**Output esperado:** definición de tier en DocuMente como atributo
estructurado del modelo, con reglas claras de cuándo aplica cada uno.

### Bloque 2 — Roles y responsables (5 min)

5. **¿Quién es Validator independiente?** En SR 11-7 estándar, el
   Validator NO puede ser del mismo equipo que desarrolló el modelo.
   ¿MA tiene ese rol formalmente? ¿Cómo se selecciona?
6. **Roles SR 11-7 / MRM: Model Owner, Developer, Validator, Reviewer,
   Approver** — ¿cuáles aplican en SMNYL y cuáles no?
7. **Attestation anual** — ¿quién firma y cuándo? ¿Cómo se evidencia?

**Output esperado:** modelo de roles claro que se refleje en la ficha
del modelo (sección 3 actual "Responsables y roles") y en la state
machine MRM (signoffs).

### Bloque 3 — Cambios de bajo vs alto impacto (15 min) — el más importante

8. **¿Qué define el umbral entre bajo y alto impacto?**
9. **¿Hay aprobaciones distintas?** Bajo impacto = aprobación del área
   dueña; alto = comité o C-level?
10. **¿Cómo se versiona Prophet hoy?** ¿Git? ¿Carpetas con sufijos
    `_v1`, `_v2`? ¿Backups manuales?
11. **Granularidad del change log**:
    - ¿Por release de modelo (`v2 → v3`)?
    - ¿Por cambio individual de variable?
    - ¿Por commit/ticket?
12. **¿Qué campos OBLIGATORIOS debe tener cada entrada de change log?**
    Probables candidatos:
    - `fecha`, `variable_o_componente`, `tipo_cambio`,
      `razon`, `como_se_implementa`, `modelos_afectados`,
      `aprobador`, `evidencia` (link a ticket / email / documento).
13. **¿Quieren matriz de impactos cross-model?** ("Si cambio variable X,
    qué modelos se rompen.") — esto requiere modelo de datos con
    relaciones M:N, NO es trivial.

**Output esperado:** schema del módulo ChangeLog. Decisión de si va
adentro de cada ficha o como entidad separada con vinculación M:N a
modelos.

### Bloque 4 — Inventario centralizado (10 min)

14. **¿Inventario único centralizado por MA, o federado por área?**
    (Cada área mantiene su lista, MA agrega).
15. **¿Qué campos necesita el inventario para reporting?**
    Probables:
    - ID, nombre, área dueña, contabilidad (STAT/GAAP/MSTAT/IFRS17),
      propósito (Valuación/BP/Pricing/Capital/Inversiones), owner,
      tier, fecha última validación, status MRM, n_cambios_ultimos_X.
16. **¿Necesita exportable a Excel?** ¿Con qué frecuencia? ¿Para qué
    audiencia (CFO, CEO, regulador, auditor externo)?
17. **¿Hay riesgo de duplicados o modelos "huérfanos" sin owner?**
    ¿Cómo se identifican hoy?

**Output esperado:** spec de la vista `/prophet/inventario`.

### Bloque 5 — Variables compartidas y "one model" (5 min)

18. **¿Qué tan común es el problema de "misma variable, distinta
    metodología en distintos modelos"?**
19. **¿"One model" es visión de 2-3 años o más cercana?** ¿Hay piloto
    en curso o solo concepto?
20. **¿LLM-assisted clustering de variables ayudaría?** (DocuMente
    podría detectar variables semánticamente equivalentes con nombres
    distintos en distintas fichas.)

**Output esperado:** decisión si vista `/prophet/variables` global es
prioridad S17 o se difiere.

### Bloque 6 — Demo D.1.d (5 min)

21. **¿Con qué área hacemos la primera demo de DocuMente Prophet?**
    Candidatos del plan S14: Carmona / Cynthia Flores / Juan Carlos
    Magallanes.
22. **¿Con qué modelo específico?** Sugerido: uno de tier intermedio
    (no el más crítico ni el más trivial) para validar fit.
23. **¿Qué constituye una demo "exitosa"?** Métricas concretas:
    ¿reducción de tiempo de documentar? ¿calidad percibida del borrador?
    ¿% de secciones que el dueño acepta sin editar?

**Output esperado:** plan de demo con fecha tentativa y métricas claras.

### Cierre (5 min)

24. Confirmar prioridades S17 con MA. Las 3 cosas más urgentes en su
    opinión.
25. Acordar próxima reunión / checkpoint.
26. **Compromiso**: MA comparte los templates en construcción esta
    semana. DocuMente entrega un primer prototipo del módulo
    ChangeLog en 2 semanas (si las decisiones quedan claras hoy).

---

## Riesgos / banderas rojas durante la conversación

- **MA aún no tiene su framework definido**: si las respuestas a los
  bloques 1-4 son "todavía lo estamos definiendo", **no codear nada**
  de Prophet hasta tener claridad. Documentar lo discutido y agendar
  otra reunión con un working draft.

- **MA quiere algo más complejo que un sistema de documentación**: si
  en algún momento sale "queremos que DocuMente ejecute Prophet" o
  "queremos que DocuMente sea el sistema de versionado del código",
  marcar como **fuera de alcance**. DocuMente documenta; no reemplaza
  Prophet ni Git.

- **MA pide algo que está bloqueado por Vidal**: ej. integración con
  SharePoint, single sign-on con Cognito, deploy a EC2 — todo está
  pendiente de Vidal. No comprometer fechas sobre eso.

- **El template de MA es muy distinto al nuestro**: si el template
  word/excel que traen tiene muchas secciones distintas a las 12
  actuales, **no rediseñar a ojo en S17**. Hacer un mapping field-by-field
  documentado primero.

---

## Después de la reunión

1. **Notas estructuradas** dentro de 24h, compartidas con MA para
   confirmar entendimiento.
2. Actualizar `PROPHET_FASE0_AUDIT.md` con las decisiones tomadas.
3. Crear plan detallado S17 con scope cerrado.
4. **No empezar a codear** hasta que el plan S17 esté aprobado por MA.
