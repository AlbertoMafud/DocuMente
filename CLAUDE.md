# CLAUDE.md

## Contexto general

Seguros Monterrey New York Life (SMNYL) es una institución financiera regulada que opera con múltiples políticas, procesos, procedimientos, sistemas y modelos críticos para la operación de la compañía.

Sin embargo, en muchos casos, especialmente para procesos, procedimientos y modelos, no se cuenta con documentación formal suficiente. Cuando existe documentación, suele ser principalmente operativa: describe los pasos a seguir, pero no explica el razonamiento detrás de esos pasos, las decisiones históricas que dieron forma al proceso, las dependencias con otros equipos o sistemas, ni los supuestos bajo los cuales fue diseñado el modelo, proceso o procedimiento.

Esto genera una brecha importante entre saber “qué hacer” y entender “por qué se hace así”.

## Problema a resolver

SMNYL enfrenta dos cambios relevantes de manera simultánea:

1. Un cambio generacional en su talento humano.
2. Una renovación de sistemas clave, incluyendo sistemas legados utilizados en procesos críticos.

Esta combinación genera un riesgo importante de pérdida de conocimiento institucional, especialmente en procesos antiguos, modelos complejos o actividades que dependen de sistemas legados y del conocimiento tácito de personas con muchos años de experiencia.

El talento nuevo que ingresa a la compañía debe aprender sobre la marcha, con documentación limitada, fragmentada o excesivamente operativa. Esto reduce su capacidad para comprender el “por qué” detrás de los procesos, limita la transferencia de conocimiento y disminuye el tiempo disponible para innovar, rediseñar procesos, mejorar modelos o migrar hacia sistemas más modernos.

La falta de documentación adecuada no solo representa un problema operativo. También implica un riesgo institucional, porque dificulta preservar conocimiento clave, asegurar continuidad operativa, facilitar auditorías, cumplir con marcos de gobierno y tomar mejores decisiones futuras.

Otro problema importante es que se está reforzando la gobernanza de modelos con MRM, por lo que la documentación es crítica y debe estar lista para auditoría.

## Documentación de modelos y Model Risk Management

En el caso particular de los modelos de la compañía, estos forman parte del marco de Model Risk Management, o MRM. Este marco establece lineamientos claros sobre la documentación, gobierno, validación, seguimiento y evidencia que deben existir para cada modelo.

Actualmente, el área de Riesgos opera este marco de gobierno y realiza un proceso anual de attestation de los modelos de la compañía.

Aunque se han realizado esfuerzos relevantes para contar con la documentación requerida, en la práctica documentar modelos suele percibirse como una actividad:

- Extenuante.
- Tediosa.
- De bajo valor agregado inmediato.
- Separada del trabajo analítico o técnico principal.
- Consumidora de tiempo para las personas que poseen el conocimiento clave.

Esto genera fricción, baja adopción y riesgo de que la documentación no capture adecuadamente el conocimiento técnico, histórico, metodológico y operativo necesario.

MRM es un caso de uso prioritario para DocuMente, pero el sistema debe diseñarse de forma suficientemente flexible para documentar también procesos, procedimientos, políticas operativas, metodologías internas y conocimiento institucional relevante.

---

# ¿Qué es DocuMente?

DocuMente es un sistema agéntico local de documentación institucional construido para SMNYL.

Su propósito principal es eliminar la fricción de documentar procesos, procedimientos y modelos, transformando una tarea percibida como tediosa en un flujo asistido, claro, estructurado y útil.

DocuMente debe ayudar a generar documentación:

- Estructurada.
- Estética.
- Estandarizada.
- Trazable.
- Fácil de actualizar.
- Útil para usuarios técnicos y no técnicos.
- Basada en información real provista por el usuario o por fuentes autorizadas.
- Preparada para revisión, aprobación y mantenimiento futuro.

El objetivo no es únicamente generar documentos. El objetivo es preservar conocimiento institucional, facilitar la transferencia de conocimiento, apoyar el cumplimiento de marcos de gobierno como MRM y habilitar mejores decisiones futuras.

Antes de proponer o ejecutar cualquier cambio de código, Claude Code debe evaluar si la modificación contribuye directamente al propósito principal del sistema:

> Reducir la fricción de documentar y convertir la documentación institucional en un activo vivo, confiable y útil para la organización.

Si una modificación no contribuye a este propósito, debe cuestionarse, justificarse o descartarse.

---

# Visión del producto

DocuMente debe convertirse en la plataforma interna de referencia para capturar, estructurar, mantener y consultar conocimiento institucional sobre modelos, procesos y procedimientos críticos de SMNYL.

El sistema debe sentirse como un copiloto de documentación: entrevista al usuario, organiza la información, identifica brechas, sugiere estructura, genera borradores, ayuda a mejorar la claridad del documento y permite revisión humana antes de aprobar cualquier contenido.

La experiencia debe ser suficientemente sencilla para que cualquier usuario pueda documentar sin sentir que está enfrentando una tarea burocrática, pero suficientemente robusta para cumplir con estándares institucionales, regulatorios y de gobierno interno.

Debe de poder generar documentos en formato docx o pdf, desde cero o partiendo de la documentación ya existente, encontrando mejoras a esta.

---

# Usuarios objetivo

Los usuarios principales de DocuMente son:

- Analistas.
- Seniors.
- Gerentes.
- Dueños de procesos.
- Responsables de modelos.
- Áreas de Riesgos, Finanzas, Actuaría, Operaciones y Tecnología.

Algunos usuarios serán técnicos, pero otros no. Por lo tanto, la experiencia debe ser clara, rápida y entendible para cualquier nivel.

La aplicación debe evitar depender de lenguaje excesivamente técnico en la interfaz. Cuando existan conceptos técnicos, deben explicarse de forma breve, natural y accionable.

---

# Principios no negociables

## 1. Diseño visual excepcional

La aplicación debe verse y sentirse como un producto profesional de nivel enterprise, no como un prototipo básico de Streamlit.

El diseño visual forma parte central de la propuesta de valor, porque ayuda a que la organización perciba DocuMente como una herramienta seria, confiable y lista para uso institucional.

La interfaz debe ser limpia, moderna, consistente y fácil de usar. Cada pantalla debe transmitir claridad, orden y profesionalismo.

## 2. Documentación como activo vivo

La documentación no debe tratarse como un archivo estático que se genera una sola vez.

Los documentos deben tener estados explícitos de avance, por ejemplo:

# Información y documentos iniciales

En la carpeta /SMNYL se encuentra la información y documentos iniciales del proyecto como los estándares, políticas, ejemplos de documentaciones actuales de SMNYL, la identidad de marca y el logo. **Estos archivos son fuente, no se modifican** — solo se leen.

---

# Archivos de contexto del proyecto

Antes de hacer cualquier cambio relevante, consulta los siguientes archivos según el dominio del cambio:

| Archivo | Cuándo consultarlo |
|---|---|
| [docs/MRM_REQUIREMENTS.md](docs/MRM_REQUIREMENTS.md) | Cambios que afecten validación de modelos, completitud de secciones, roles, tiering, attestation |
| [docs/BRAND_GUIDELINES.md](docs/BRAND_GUIDELINES.md) | Cambios visuales (UI, DOCX export, paleta, tipografías, logo) |
| [docs/TEMPLATE_MODEL_DEV.md](docs/TEMPLATE_MODEL_DEV.md) | Cambios al motor de entrevista, gap analyzer, estructura de secciones del documento |
| [docs/UX_PRINCIPLES.md](docs/UX_PRINCIPLES.md) | Cambios a UI/UX, componentes, microinteracciones, lenguaje |
| [docs/MIGRATION_TO_EC2.md](docs/MIGRATION_TO_EC2.md) | **Actualizar después de cualquier feature** que pueda afectar la migración futura |
| [status.md](status.md) | Leer al iniciar sesión; actualizar al cerrar si hubo cambios significativos |

---

# Tech stack y decisiones técnicas

| Área | Elección | Razón |
|---|---|---|
| Lenguaje | Python 3.11+ | Stack del workspace; ecosistema docx/LLM maduro |
| UI | Streamlit + CSS custom + `streamlit-extras` | Velocidad de iteración; le aplicamos tema SMNYL para que no parezca prototipo |
| LLM | Claude API vía Anthropic SDK con prompt caching | Decisión del usuario; calidad máxima de generación |
| DOCX (motor) | `docxtpl` (template-driven) + `python-docx` (operaciones quirúrgicas) | Crítico: el `.docx` plantilla maestra se diseña en Word con marca SMNYL completa; `docxtpl` solo rellena placeholders. Garantiza calidad estética por construcción |
| Validación de datos | Pydantic v2 | Datos siempre con forma correcta; menos bugs |
| ORM / persistencia | SQLAlchemy + SQLite local (MVP) | Local-first sin servidor; migración a PostgreSQL post-MVP es swap de URI |
| Logs | `structlog` a stdout | Logs estructurados; compatibles con CloudWatch al migrar |
| Tests | pytest | Estándar; integration tests con docs reales como fixtures |
| Lint/format | `ruff` (lint+format) + `mypy --strict` | Calidad de código sin fricción |

**Política de dependencias:** evitar dependencias innecesarias. Antes de agregar una librería nueva, validar que no se puede resolver con stdlib o con una librería ya presente.

---

# Estructura del proyecto

```
DocuMente/
├── CLAUDE.md                # ← este archivo
├── README.md
├── status.md                # estado actual; se actualiza al cerrar sesión
├── pyproject.toml           # dependencias, ruff, mypy, pytest config
├── .env / .env.example      # variables de entorno
├── .gitignore
├── app.py                   # entry point de Streamlit
│
├── src/
│   ├── ui/                  # Capa UI: páginas y componentes Streamlit
│   │   ├── pages/           # home.py, importar_documento.py, entrevista.py, ...
│   │   ├── components/      # header.py, seccion_card.py, chat_bubble.py, ...
│   │   └── theme.py         # paleta SMNYL aplicada a Streamlit (CSS custom)
│   │
│   ├── core/                # Capa Dominio + Aplicación (lógica pura)
│   │   ├── models/          # Pydantic: Documento, Seccion, Brecha, ...
│   │   ├── usecases/        # ImportarDocumento, IniciarEntrevista, ExportarDocx, ...
│   │   └── rules/           # Reglas MRM: validar tier, completitud, independencia
│   │
│   ├── llm/                 # Capa Infra: cliente Claude
│   │   ├── client.py        # wrapper Anthropic SDK con prompt caching
│   │   └── prompts/         # prompts de sistema por caso de uso
│   │
│   ├── docs/                # Capa Infra: lectura/escritura DOCX
│   │   ├── reader.py        # python-docx → estructura interna
│   │   ├── writer.py        # estructura interna → .docx con marca SMNYL (docxtpl)
│   │   └── templates/
│   │       └── model_development_smnyl.docx  # ← plantilla maestra diseñada en Word
│   │
│   └── storage/             # Capa Infra: persistencia
│       ├── db.py            # conexión SQLAlchemy
│       └── repositories.py  # DocumentoRepository, etc.
│
├── docs/                    # Documentación del proyecto (ver tabla arriba)
├── assets/                  # Logo, fuentes
├── data/                    # Datos locales (gitignore: db, exports)
├── SMNYL/                   # Material fuente — solo lectura
└── tests/
    ├── unit/
    └── integration/
```

**Regla de capas:** UI → Aplicación → Dominio. La capa de Infraestructura sirve a Aplicación e Infra. **Dominio nunca importa de UI ni de Infraestructura.** Si encuentras un import que rompe esto, repórtalo.

---

# Comandos comunes

```bash
# Setup inicial (una sola vez)
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"

# Correr la app
streamlit run app.py

# Tests
pytest                          # todos los tests
pytest tests/unit/              # solo unit tests
pytest -k "test_docx_reader"    # filtrar por nombre

# Calidad de código
ruff check src/ tests/          # lint
ruff format src/ tests/         # format
mypy src/                       # type checking estricto
```

---

# Identidad visual SMNYL (resumen accionable)

Detalle completo en [docs/BRAND_GUIDELINES.md](docs/BRAND_GUIDELINES.md). Resumen rápido:

- **Color primario:** New York Life Blue `#0079c2` (logo, botones primarios, acentos)
- **Texto:** Steel `#0a3c53` sobre White `#ffffff` (cumple AAA)
- **Texto secundario:** Iron `#565656` (cumple AA)
- **Tipografías:** Georgia (display) / Tahoma (body) — reemplazos oficialmente autorizados por el manual SMNYL p. 75; nativas de Windows/Mac, sin licencia adicional. Cuando se obtengan Alda Pro / Effra Pro, sustituir el primer ítem del stack.
- **Logo:** mínimo 2.5 cm, esquinas redondeadas, fondo blanco preferible.
- **Estados:** verde Pine `#4b8b7f` (success), naranja Sunset `#ce7046` (warning), rosa `#754a62` (danger), azul Rain `#2e86af` (info).

**Cualquier cambio visual debe pasar el checklist de marca** en `docs/BRAND_GUIDELINES.md` §9.

---

# Workflow de cambio

1. **Antes de codear:** consulta los archivos de contexto relevantes (tabla arriba). Si la tarea tiene >3 archivos modificados o >1 día de trabajo, escribe un plan corto antes.
2. **Implementa:** sigue separación de capas; no introduzcas dependencias innecesarias; comentarios solo para "por qué", nunca para "qué".
3. **Testea:** unit tests para lógica de dominio; integration tests para flujos completos. Tests con docs reales del repo `SMNYL/Ejemplos actuales/` como fixtures.
4. **Valida:** corre `ruff check`, `ruff format`, `mypy src/`, `pytest`. Todo debe pasar.
5. **Si tocaste algo migrable:** actualiza `docs/MIGRATION_TO_EC2.md` §3 con la nueva fila.
6. **Si tocaste UI:** valida contra `docs/UX_PRINCIPLES.md` y el checklist de marca en `docs/BRAND_GUIDELINES.md` §9.
7. **Al cerrar sesión:** pregunta al usuario si actualizar `status.md`.

---

# Reglas que NO son negociables

- **Calidad estética del DOCX exportado**: indistinguible de un documento corporativo SMNYL real. Tablas con bordes correctos, paleta exacta, tipografías corporativas. Si no se ve enterprise → no se exporta.
- **UX excepcional**: cero look "Streamlit default", cero texto técnico crudo visible al usuario.
- **Trazabilidad**: cada cambio en un documento se registra en `audit_trail` con who/when/what.
- **No alucinar contenido**: nunca afirmamos hechos no provistos por el usuario; el `.docx` final lleva marca de "Borrador asistido — requiere revisión humana".
- **Migrabilidad**: ningún feature del MVP rompe los principios de migración (ver `MIGRATION_TO_EC2.md` §6).


