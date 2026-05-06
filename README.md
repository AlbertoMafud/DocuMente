# DocuMente

Sistema agéntico local de documentación institucional para modelos, procesos y procedimientos bajo el marco **Model Risk Management (MRM)**.

DocuMente entrevista al usuario, estructura la información según templates oficiales, identifica brechas de cumplimiento, genera borradores trazables y exporta documentos profesionales (DOCX/PDF). Diseñado para reducir la fricción de documentar y convertir la documentación en un activo vivo, confiable y auditable.

---

## Estado del MVP

| Fase | Descripción | Estado |
|---|---|:---:|
| 0 | Setup, archivos de contexto, marca, app branded | ✅ |
| 1 | Lectura de DOCX, análisis de brechas vs template MRM | ✅ |
| 2 | Motor de entrevista con Claude (chat + drafting) | ✅ |
| 2.5 | Memoria del modelo, apéndices Excel/CSV, drafter institucional, costo, vista previa, estrategia tiered de modelos | ✅ |
| 3 | Generación DOCX con marca corporativa | Pendiente |
| 4 | Estados del documento + audit trail UI | Pendiente |
| 5 | Pulido UX + demo interna | Pendiente |
| 6 | Cierre del plan de migración a EC2 | Pendiente |

**Tests:** 75/75 pasan · **Lint:** ruff clean

---

## Arquitectura

Capas separadas siguiendo el patrón hexagonal:

```
src/
├── ui/              # Streamlit pages + components (capa de presentación)
├── core/
│   ├── models/      # Pydantic v2 — modelos de dominio
│   └── usecases/    # Orquestadores de aplicación
├── llm/             # LLMClient Protocol + AnthropicClient (Infra)
├── docs/            # Lectura/escritura .docx, .xlsx, .csv (Infra)
└── storage/         # Repository pattern + SQLAlchemy (Infra)
```

### Decisiones técnicas clave

- **LLM tiered (Anthropic)**: Sonnet 4.6 para chat, Opus 4.7 para drafting final, Haiku 4.5 para extracción de hechos. Reduce costo ~50-65% vs todo-Opus sin sacrificar calidad.
- **Prompt caching agresivo**: contexto institucional (~12K tokens) se cachea en cada llamada. Cache hit rate típico ≥ 90% después del primer turno.
- **DOCX vía `docxtpl` + plantilla maestra**: la plantilla se diseña manualmente en Word con marca completa; el código solo rellena placeholders Jinja. Garantiza calidad estética por construcción.
- **Local-first, multi-user-ready**: corre 100% local con SQLite. Arquitectura ya soporta migración a PostgreSQL + S3 + EC2 sin reescribir lógica de negocio.
- **Persistencia abstraída**: lógica de negocio depende de `Repository` y `Storage` interfaces, nunca de implementaciones concretas.

---

## Stack técnico

| Área | Elección |
|---|---|
| Lenguaje | Python 3.11+ |
| UI | Streamlit + CSS custom |
| LLM | Anthropic SDK (Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5) |
| DOCX | `docxtpl` + `python-docx` |
| Excel/CSV | `openpyxl` + `pandas` |
| Validación | Pydantic v2 |
| Persistencia | SQLAlchemy + SQLite (PostgreSQL-ready) |
| Tests | pytest |
| Lint/Format | ruff + mypy |

---

## Setup local

```bash
# 1. Clonar
git clone <url-del-repo>
cd DocuMente

# 2. Entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# 3. Instalar dependencias
pip install -e ".[dev]"

# 4. Configurar credenciales
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY

# 5. Correr la app
python -m streamlit run app.py
```

La app abre en `http://localhost:8501`.

---

## Comandos comunes

```bash
# Tests
pytest                          # todos
pytest tests/unit/              # solo unitarios
pytest -k "test_drafter"        # filtro por nombre

# Calidad de código
ruff check src/ tests/ app.py   # lint
ruff format src/ tests/ app.py  # format
mypy src/                       # type checking
```

---

## Estructura del proyecto

```
DocuMente/
├── app.py                      # Entry point Streamlit
├── pyproject.toml
├── CLAUDE.md                   # Instrucciones del proyecto para Claude Code
├── status.md                   # Estado vivo del proyecto
├── docs/
│   ├── MRM_REQUIREMENTS.md     # Reglas MRM (extracción de standards oficiales)
│   ├── BRAND_GUIDELINES.md     # Identidad visual aplicada
│   ├── TEMPLATE_MODEL_DEV.md   # 28 secciones del template oficial
│   ├── UX_PRINCIPLES.md        # Principios UX no-negociables
│   ├── MIGRATION_TO_EC2.md     # Plan vivo de migración a la nube
│   └── TEMPLATE_DESIGN_SESSION.md  # Guía para diseñar plantilla maestra .docx
├── src/
│   ├── ui/                     # Capa UI
│   ├── core/                   # Dominio + casos de uso
│   ├── llm/                    # Cliente Claude + prompts
│   ├── docs/                   # Lectores/escritores de documentos
│   └── storage/                # Persistencia
├── tests/
│   ├── unit/
│   └── integration/
└── data/                       # Datos locales (gitignored)
    ├── documente.db
    ├── uploads/
    ├── exports/
    └── backups/
```

---

## Tipos de documento soportados

**MVP**: Model Development Documentation Template (28 secciones).

**v2 (futuro)**: First Line Review & Testing, Independent Validation, procesos genéricos, procedimientos operativos.

---

## Licencia y uso

Proyecto de uso interno. Los archivos `docs/*.md` contienen interpretaciones derivadas de marcos regulatorios públicos (NAIC, NY DFS, AAA, SOA) y de estándares MRM. La aplicación de estos a casos de uso específicos requiere revisión legal y compliance.

---

## Contacto

Alberto Solano · `albertosm08@gmail.com`
