# DOCUMENTE — Technical Architecture Document
## Institutional Documentation Assistant — Data & Infrastructure Architecture

**Prepared for:** Vidal (Data Architect)
**Prepared by:** Alberto Solano (Chief of Staff CFO)
**Date:** May 2026
**Version:** 1.0
**Classification:** Internal Technical Documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Data Architecture](#3-data-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Data Flow (End-to-End)](#5-data-flow-end-to-end)
6. [Core Modules](#6-core-modules)
7. [Storage & Persistence](#7-storage--persistence)
8. [Scalability Roadmap (MVP → Production)](#8-scalability-roadmap-mvp--production)
9. [Architectural Decisions](#9-architectural-decisions)
10. [Non-Functional Requirements](#10-non-functional-requirements)
11. [Security & Access Control](#11-security--access-control)
12. [Performance & Monitoring](#12-performance--monitoring)
13. [Disaster Recovery & Backup](#13-disaster-recovery--backup)
14. [Infrastructure on AWS](#14-infrastructure-on-aws)
15. [API Contracts & Data Interfaces](#15-api-contracts--data-interfaces)

---

## 1. Executive Summary

**DocuMente** is a Python-based agentic documentation assistant for SMNYL. It addresses a structural problem in the institution: documenting models, processes, and procedures under the MRM (Model Risk Management) framework is perceived as tedious, low-value work that gets postponed and ends up incomplete. DocuMente turns that work into a guided, conversational flow that produces audit-ready, branded `.docx` deliverables.

The system interviews the model owner section by section using Claude (Sonnet for chat, Opus for final drafting, Haiku for extraction), persists every change in an immutable audit trail, validates completeness against the official NYL Model Development Template (28 sections), and exports a Word document indistinguishable from a real corporate SMNYL deliverable.

### Key architectural principles

| Principle | Implication |
|---|---|
| **Layer separation** | UI → Application → Domain → Infrastructure. Domain depends on nothing; infrastructure is swappable. |
| **Auditability** | Every change to a document is recorded as an immutable `EventoAuditoria` event with actor, timestamp, type, and metadata. |
| **Migration-readiness** | Every MVP design decision is evaluated against "does this block migration to EC2?" Storage URI, LLM provider, file storage are all behind interfaces. |
| **Provider-neutral LLM interface** | `LLMClient` is a Python `Protocol`. `AnthropicClient` is the only implementation today; `BedrockClient` is a swap-not-rewrite if Compliance requires data residency. |
| **Aesthetic quality non-negotiable** | The exported `.docx` must be indistinguishable from a corporate SMNYL document. The master template is designed in Word; code only fills placeholders via `docxtpl`. |
| **No hallucination** | DocuMente never asserts facts not provided by the user or an authorized source. The exported `.docx` carries an explicit "Borrador asistido — requiere revisión humana" mark. |

### Current state (May 2026)

- **MVP closed for internal pilot** — Phases 0, 1, 2, 2.5, 3, 4, and 6 complete. Only Phase 5 (UX collateral) pending.
- **182 unit + integration tests passing** in this worktree (174 baseline + 5 from `template_catalog` refactor + 10 from `CrearDocumentoEnBlanco` use case + a few internal). Ruff clean. Mypy strict on new files.
- **2 document creation flows live:** import an existing `.docx` (with gap analysis) or create from scratch (28-section skeleton).
- **3-tier Anthropic strategy** (Sonnet 4.6 / Opus 4.7 / Haiku 4.5) with aggressive prompt caching (~12K-token fixed context).
- **Single-user, local-only** — runs on the project owner's laptop, persists to local SQLite + filesystem.
- **Estimated cost per export:** USD 0.10–0.20 (dominated by Opus drafting passes).

### Scope for AWS deployment

- Transition from single-laptop to multi-user web-accessible system.
- Preserve all data integrity, audit, and aesthetic guarantees of the local version.
- Containerize, then provision EC2 + RDS PostgreSQL + S3 + Cognito + ALB.
- Decision pending with Compliance: Anthropic API direct vs. Bedrock (data residency).
- Estimated infrastructure cost: USD 125–300/month at pilot scale.

---

## 2. System Overview

### 2.1 Conceptual layers

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  Streamlit Web App (single-user MVP)                        │
│  ├─ Home (entry: import or create-from-scratch)             │
│  ├─ Import flow (upload .docx → gap analysis)               │
│  ├─ Create-from-scratch flow (form → 28-section skeleton)   │
│  ├─ Onboarding (transversal model facts)                    │
│  ├─ Dashboard (sections + governance + export)              │
│  ├─ Interview (split chat ↔ live preview)                   │
│  └─ Audit timeline (immutable event log)                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  APPLICATION LAYER                          │
│  Use Cases (orchestrators)                                  │
│  ├─ ImportarDocumento, CrearDocumentoEnBlanco               │
│  ├─ IniciarEntrevista, ResponderPregunta, Drafter           │
│  ├─ OmitirSeccion, CambiarEstadoDocumento, RegistrarSignoff │
│  ├─ AdjuntarTablaApendice, KnowledgeExtractor               │
│  └─ ExportarDocumento, TraductorDocumento                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    DOMAIN LAYER (pure)                      │
│  Pydantic v2 models + business rules                        │
│  ├─ Documento (root entity)                                 │
│  ├─ Seccion, MetadataModelo, MemoriaModelo                  │
│  ├─ Apendice, EventoAuditoria, MetricasUso                  │
│  ├─ EstadoEntrevista, MensajeEntrevista                     │
│  ├─ DocumentStateMachine (5 states + transitions)           │
│  ├─ TEMPLATE_MODEL_DEVELOPMENT catalog (28 sections)        │
│  └─ GapAnalyzer (completeness heuristics)                   │
│  Imports nothing from UI or Infrastructure.                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                INFRASTRUCTURE LAYER                         │
│  External adapters                                          │
│  ├─ AnthropicClient (LLMClient Protocol)                    │
│  ├─ DocxReader (python-docx) → Documento                    │
│  ├─ DocxWriter (docxtpl + python-docx) → .docx              │
│  ├─ TableExtractor (Haiku-backed JSON extraction)           │
│  ├─ DocumentoRepository (SQLAlchemy → SQLite/PostgreSQL)    │
│  ├─ EstadoEntrevistaRepository                              │
│  └─ FilesystemStorage (Storage interface) → local/S3-ready  │
└─────────────────────────────────────────────────────────────┘
```

**Layer rule:** UI calls Application; Application calls Domain and Infrastructure; Infrastructure may import Domain types but never depends on UI or Application. Domain is fully pure (no I/O, no global state).

### 2.2 Data flow overview

```
INPUT                    PROCESSING                    OUTPUT
──────────────────────────────────────────────────────────────

Existing .docx  ─┐
                 ├─→  Document creation     ─→  Documento (28 sections,
Form input       ─┘   (Import OR FromScratch)    populated or empty)
(name + ID)

User answers  ─→ Interview Engine ─────────→ Section content
                 (Sonnet 4.6 + cached
                  12K-token system prompt)

Section content ─→ Drafter ──────────────────→ Final draft
                  (Opus 4.7, adaptive thinking)   (markdown w/ tables)

Tabular text  ─→ TableExtractor ────────────→ Structured JSON
               (Haiku 4.5)                      (for native Word tables)

Documento     ─→ DocxWriter ─────────────────→ .docx (branded)
              (docxtpl + master template)       Optional ES → EN
                                                 translation pass
                                                 (Sonnet)

All actions   ─→ EventoAuditoria ────────────→ Immutable audit_trail
              (registered in Documento)         (timeline UI)
```

---

## 3. Data Architecture

### 3.1 Core entities and schemas

**All schemas defined in `src/core/models/` using Pydantic v2.**

#### Documento (Root entity)

```python
class Documento(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str = "default"           # Multi-user-ready from day 1
    tipo: TipoDocumento = "model_development"
    estado: EstadoDocumento = "draft"  # draft | in_review | approved | published | retired
    metadata_modelo: MetadataModelo
    secciones: list[Seccion]           # Always 28 (canonical NYL template)
    audit_trail: list[EventoAuditoria]
    creado_en: datetime
    actualizado_en: datetime
    archivo_origen: str | None         # Path to imported .docx (if any)
    memoria_modelo: MemoriaModelo      # Transversal facts
    apendices: list[Apendice]          # Excel/CSV attachments
    metricas_uso: MetricasUso          # LLM token + cost accounting
```

**Persistence:** stored as serialized JSON in `documentos.payload_json` (TEXT column). Index columns for filter/sort: `user_id`, `estado`, `nombre_modelo`, `actualizado_en`.

---

#### Seccion (Document section)

```python
class Seccion(BaseModel):
    id: str                            # e.g., "4.4.assumptions"
    nombre: str                        # e.g., "Key Assumptions"
    numero: str                        # e.g., "4.4"
    obligatoria: bool
    contenido: str | None              # None = never touched
    completitud: Completitud           # vacia | parcial | completa | omitida
    intencion: str                     # What this section captures
    preguntas_guia: list[str]          # Questions the InterviewEngine uses
    motivo_omision: str | None         # Justification if completitud == "omitida"
```

The 28 sections come from the canonical `TEMPLATE_MODEL_DEVELOPMENT` tuple in `src/core/template_catalog.py`. This is the single source of truth consumed by `DocxReader`, `GapAnalyzer`, `Drafter`, `InterviewEngine`, and `CrearDocumentoEnBlanco`.

---

#### MetadataModelo (Structured model attributes)

```python
class MetadataModelo(BaseModel):
    nombre_modelo: str
    model_id: str
    model_class: str                   # e.g., "Statistical / Stochastic"
    profit_center: str
    fae: str                           # Functional Area Executive
    model_owner: str
    model_developers: list[str]
    model_users: list[str]
    current_version: str
    implementation_platform: str       # Prophet, GGY Axis, R+AWS, etc.
    financial_impact: str
    model_status: str
    target_production_date: str
    inherent_risk_tier: TierRiesgo | None  # low | medium_minus | medium | high | very_high | very_high_plus | critical
    intended_use: str
    use_restrictions: str
    nomenclatura: str                  # SMNYL institutional code (e.g., "M07.P07.S03.006.D")
```

Renders as the section 1.1 attribute table in the `.docx` export.

---

#### MemoriaModelo (Transversal facts)

```python
class MemoriaModelo(BaseModel):
    plataforma: str                    # Prophet, GGY Axis, R+AWS
    lenguaje_codigo: str               # R, Python, SQL
    frecuencia_corridas: str           # monthly, quarterly, ad-hoc
    esg_usado: str                     # Economic Scenario Generator
    rutas_principales: list[str]       # File paths the model reads/writes
    owner_responsable: str
    fae_responsable: str
    dependencias_upstream: list[str]   # Upstream models
    dependencias_downstream: list[str] # Downstream models
    hechos_libres: list[str]           # Free-form facts
    actualizada_en: datetime
    fuente_ultima_actualizacion: str   # "onboarding" | "extraccion:4.4" | "edicion_manual"
```

**Why this exists:** without it, Claude re-asked basic facts (platform, frequency, paths) in every section interview. `MemoriaModelo` is captured once via the onboarding screen or extracted automatically by the `KnowledgeExtractor` (Haiku-backed) post-section-close, and injected into every subsequent interview prompt as "Facts already known about the model — don't ask about these."

---

#### EventoAuditoria (Immutable event)

```python
class EventoAuditoria(BaseModel):
    timestamp: datetime
    actor: str                         # user_id (always "default" in MVP)
    tipo: TipoEvento                   # 10 known types — see below
    descripcion: str                   # Human-readable
    seccion_id: str | None
    metadata: dict[str, str]           # Origin/destination state, etc.

# Frozen Pydantic model. Once registered in audit_trail, never mutates.
```

Event types:

```
documento_creado          documento_importado
seccion_editada           seccion_completada       seccion_omitida
transicion_estado         metadata_actualizada
exportado
signoff_reviewer          signoff_fae
```

**Sign-offs are events, not flags.** This is intentional: an auditor querying "who approved this model and when?" gets a definitive answer from the timeline, not a boolean.

---

#### Apendice (Attached supporting data)

```python
class Apendice(BaseModel):
    id: UUID
    seccion_origen_id: str             # Which section refers to this appendix
    titulo: str
    tipo: TipoApendice                 # tabla_excel | tabla_csv | imagen | otros
    contenido_md: str                  # Markdown rendering (tables → native Word tables on export)
    archivo_id_storage: str | None     # Reference to Storage (Excel/CSV file)
    creado_en: datetime
```

Appendices are first-class citizens: the section in the main body references them by title, the appendix renders at the end of the `.docx` as a native Word table (font-size adaptive 7–10pt depending on density).

---

#### MetricasUso + LlamadaLLM (Cost accounting)

```python
class LlamadaLLM(BaseModel):
    modelo: str                        # claude-sonnet-4-6 | claude-opus-4-7 | claude-haiku-4-5
    tarea: str                         # chat | drafting | extraction
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    costo_usd: float

class MetricasUso(BaseModel):
    llamadas: list[LlamadaLLM]
    # Properties: total_input_tokens, total_output_tokens,
    # total_cache_read_tokens, costo_total_usd, cache_hit_rate
```

`cache_hit_rate < 0.5` after several calls is a red flag for a silent prompt-cache invalidator and shows up in the dashboard cost widget.

---

#### EstadoEntrevista (Conversational state)

Persisted in a separate table (`estados_entrevista`). One row per `(documento_id, seccion_id)`. Stores the full chat history, the "closed" flag (interview finished for that section), and metadata (turns count, last activity).

Modeled separately from `Documento` because:
1. It changes much more frequently (every chat turn).
2. It's not part of the `.docx` output.
3. It would bloat the document JSON unnecessarily.

---

### 3.2 Configuration (canonical sources of truth)

| File | Purpose |
|---|---|
| `src/core/template_catalog.py` | The 28 NYL sections — IDs, names, numbers, obligatoriness, intent text, guide questions, name aliases for the reader |
| `docs/MRM_REQUIREMENTS.md` | Plain-English MRM standard reference (sections, sign-off rules, completeness criteria) |
| `docs/TEMPLATE_MODEL_DEV.md` | Verbatim section structure from the official `.docx` template |
| `docs/BRAND_GUIDELINES.md` | SMNYL palette, typography, logo rules |
| `src/docs/templates/model_development_smnyl_final.docx` | The master Word template that `docxtpl` populates |
| `src/llm/prompts/` | System prompts (tone, interview, drafting, fixed context) |
| `.env` | Runtime configuration (API keys, DATABASE_URL, paths) — loaded via `pydantic-settings` |

---

### 3.3 Document lifecycle

```
                     ┌──────────────┐
                     │    DRAFT     │ ← Created (import or from scratch)
                     └───┬────────┬─┘
                         │        ↑
       100% sections     │        │  rejected
       completed/omitted ↓        │
                     ┌──────────────┐
                     │  IN_REVIEW   │
                     └───┬────────┬─┘
                         │        ↑
                signoff  │        │  retracted
                reviewer ↓        │
                     ┌──────────────┐
                     │   APPROVED   │
                     └───┬──────────┘
                         │
                signoff  ↓
                fae      │
                     ┌──────────────┐
                     │  PUBLISHED   │ ← Document considered "live"
                     └───┬──────────┘
                         │
                         ↓
                     ┌──────────────┐
                     │   RETIRED    │ ← Terminal (immutable)
                     └──────────────┘
```

State transition validation lives in `src/core/rules/state_machine.py` — pure domain logic, no I/O.

---

## 4. Technology Stack

### 4.1 Core runtime

| Component | Technology | Version | Why |
|---|---|---|---|
| **Language** | Python | 3.11–3.12 | Mature for AI + data; mandated `>=3.11,<3.13` in `pyproject.toml`. |
| **UI framework** | Streamlit | ≥1.36 | Single-developer-friendly UI; ~10× faster iteration than React. SMNYL theming via injected CSS. |
| **UI extras** | streamlit-extras | ≥0.4.7 | Microinteractions and components Streamlit lacks natively. |
| **Data validation** | Pydantic | ≥2.7 | Type-safe domain models; auto-serialization to JSON for persistence. |
| **Settings** | pydantic-settings | ≥2.3 | Typed loading of `.env`. |
| **Templating** | Jinja2 | ≥3.1 | Used for prompt assembly; not for HTML. |
| **Logs** | structlog | ≥24.2 | JSON-structured logs to stdout; CloudWatch-ready. |
| **Env file loader** | python-dotenv | ≥1.0 | Loads `.env` into `os.environ`. |

### 4.2 LLM SDK

| Component | Library | Version | Why |
|---|---|---|---|
| **Anthropic Claude SDK** | `anthropic` | ≥0.40 | Official client. Supports prompt caching, adaptive thinking, effort tiering. |

**Provider strategy (tiered):**

| Task | Model | Why |
|---|---|---|
| `chat` (interview Q&A) | `claude-sonnet-4-6` | Excellent conversational quality; ~3× cheaper than Opus. Adaptive thinking + medium effort. |
| `drafting` (final draft generation) | `claude-opus-4-7` | Highest writing quality (institutional tone). Adaptive thinking + high effort. |
| `extraction` (structured data from prose) | `claude-haiku-4-5` | Very fast, very cheap. Used for table extraction (4 tabular sections) and post-interview knowledge extraction. Thinking disabled (Haiku 4.5 limitation). |

Switching providers (Anthropic → Bedrock or other) means implementing a new class that satisfies the `LLMClient` Protocol. Use cases don't change.

### 4.3 Document processing

| Component | Library | Version | Use |
|---|---|---|---|
| **`.docx` reader** | python-docx | ≥1.1.2 | Parses imported Word files; reads paragraphs, headings, tables. |
| **`.docx` writer (template-driven)** | docxtpl | ≥0.18 | Fills the master template's `{{ placeholders }}` and `{% for %}` loops. Critical for aesthetic quality. |
| **Subdoc + RichText** | docxtpl | ≥0.18 | Real bold, italics, native tables embedded inline (not just markdown text). |
| **Document compose** | docxcompose | (transitive) | Glues subdoc fragments into the main document. |
| **Prompt assembly** | Jinja2 | ≥3.1 | Template-rendered system prompts (tone, interview flow, drafting instructions). |

### 4.4 Data persistence

| Component | Library | Version | Use |
|---|---|---|---|
| **ORM** | SQLAlchemy | ≥2.0 | Maps `DocumentoRow` and `EstadoEntrevistaRow` to SQL. Declarative base. |
| **DB (MVP)** | SQLite | (stdlib) | Local file-based DB. Zero config for laptop. |
| **DB (Production)** | PostgreSQL | 15+ (planned) | Swap by changing `DATABASE_URL` env var. SQLAlchemy abstracts the rest. |

### 4.5 Testing & QA

| Component | Tool | Version | Use |
|---|---|---|---|
| **Test framework** | pytest | ≥8.2 | Unit + integration tests. 182 currently passing. |
| **Coverage** | pytest-cov | ≥5.0 | Used for tracking coverage on new modules. |
| **Linter + formatter** | ruff | ≥0.5 | Fast lint + format. Replaces black + flake8 + isort. |
| **Type checker** | mypy | ≥1.10 (strict mode) | Catches type errors before runtime. Strict mode enforced. |

**Current tests:** 182 passing in worktree. 7 pre-existing integration failures are due to missing `SMNYL/Ejemplos actuales/*.docx` fixtures in agent worktrees (non-regressive — same failures on baseline).

### 4.6 Deployment (target AWS)

| Service | Role | MVP target spec |
|---|---|---|
| **EC2** | Application server | t3.medium (2 vCPU, 4 GB RAM) |
| **RDS PostgreSQL** | Persistent database | db.t3.micro (single AZ initially; Multi-AZ for production) |
| **S3** | Object storage (uploaded `.docx`, exported `.docx`, master template, daily backups) | Standard tier |
| **Cognito** | User authentication (SSO with SMNYL Active Directory if available; password+MFA otherwise) | User Pool |
| **Application Load Balancer** | TLS termination, HTTPS only, health checks | Single ALB |
| **Secrets Manager** | API key storage (`ANTHROPIC_API_KEY`, others) | Managed |
| **CloudWatch** | Logs (FastAPI/Streamlit stdout via Docker), metrics, alarms | Managed |
| **Route 53** | Internal DNS (`documente.internal.smnyl`) | Hosted Zone |
| **(Optional) Bedrock** | Claude access through AWS instead of Anthropic API | Decision pending with Compliance |

---

## 5. Data Flow (End-to-End)

### 5.1 Document creation — two flows that converge

```
┌─────────────────────────────────────────────────────────────┐
│   FLOW A: IMPORT EXISTING .docx                             │
│                                                             │
│   User uploads .docx                                        │
│        ↓                                                    │
│   FilesystemStorage saves the file (UUID as id)             │
│        ↓                                                    │
│   DocxReader parses paragraphs + tables                     │
│        ↓ (matches headings against template_catalog)        │
│   Documento (28 sections, some with content from the docx)  │
│        ↓                                                    │
│   GapAnalyzer flags missing sections + low-content ones     │
│        ↓                                                    │
│   DocumentoRepository.guardar(documento)                    │
│        ↓                                                    │
│   Audit event: documento_importado                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────────────────┐
│   FLOW B: CREATE FROM SCRATCH                               │
│                                                             │
│   User enters nombre_modelo + model_id                      │
│        ↓                                                    │
│   CrearDocumentoEnBlanco use case                           │
│        ↓ (calls construir_secciones_vacias() from catalog)  │
│   Documento (28 empty sections, metadata pre-filled)        │
│        ↓                                                    │
│   DocumentoRepository.guardar(documento)                    │
│        ↓                                                    │
│   Audit event: documento_creado                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
              ─── CONVERGENCE ───
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│   ONBOARDING (transversal facts capture, ~2 min, optional)  │
│   ↓                                                         │
│   DASHBOARD (sections grid + governance + export)           │
│   ↓                                                         │
│   INTERVIEW per section → DRAFTER → section.contenido       │
│   ↓                                                         │
│   STATE TRANSITION draft → in_review → approved → published │
│   ↓                                                         │
│   EXPORT (.docx with optional ES → EN translation)          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Interview flow (per section)

```
User clicks "Entrevistar" on section X
   ↓
IniciarEntrevista use case:
   ├─ Load Documento + Seccion + MemoriaModelo
   ├─ Build system prompt (Jinja2 template):
   │   ├─ Fixed: tone + MRM standard + brand guidelines (~12K tokens, CACHED)
   │   ├─ Section-specific: intencion + preguntas_guia
   │   └─ Document context: MemoriaModelo facts + previously closed sections
   ├─ LLMClient.chat(tarea="chat", system_blocks=[...], messages=[])
   │   └─ Sonnet 4.6, adaptive thinking, medium effort
   └─ Save EstadoEntrevista (turn 1)
   ↓
Streamlit renders split panel: chat (left) ↔ live preview (right)
   ↓
User answers (turn 2..N):
   ├─ ResponderPregunta use case adds turn to EstadoEntrevista
   ├─ LLMClient.chat with full conversation history
   └─ Updates section.contenido incrementally (live preview)
   ↓
User clicks "Finalizar entrevista":
   ├─ Drafter use case (LLMClient.chat with tarea="drafting"):
   │   ├─ Opus 4.7, adaptive thinking, high effort
   │   ├─ Input: full interview transcript + section context
   │   └─ Output: institutional-tone markdown (with bold, bullets, tables)
   ├─ section.contenido = drafter output
   ├─ section.completitud = "completa"
   ├─ KnowledgeExtractor (Haiku 4.5):
   │   ├─ Reads the closed section
   │   ├─ Extracts new transversal facts (platform, paths, etc.)
   │   └─ Merges into MemoriaModelo (deduplicating)
   └─ Audit event: seccion_completada
   ↓
Documento + EstadoEntrevista persisted
```

### 5.3 Export flow

```
User clicks "Exportar DOCX" on dashboard
   ↓
Modal: select language (Español | English)
   ↓
ExportarDocumento use case:
   ├─ Load Documento (full state)
   │
   ├─ IF English selected:
   │   └─ TraductorDocumento (Sonnet 4.6, single-pass):
   │       ├─ Prompt: "Translate to U.S. corporate English, preserve markdown
   │       │           formatting, preserve actuarial vocabulary verbatim
   │       │           (BEL, MP, ESG, IFRS), preserve identifiers"
   │       ├─ Mutates the in-memory Documento (does NOT persist)
   │       └─ Audit metadata: idioma_objetivo="en"
   │
   ├─ TableExtractor (Haiku 4.5) for 4 tabular sections (5.1, 5.2, 5.5, 6.5):
   │   ├─ Input: section.contenido (narrative text)
   │   ├─ Schema: list[dict] (raw_data_sources, upstream_models, etc.)
   │   └─ Output: structured rows for docxtpl loops
   │
   ├─ markdown_blocks.separar_bloques on each section.contenido:
   │   └─ Splits content into BloqueProsa + BloqueTabla (markdown tables)
   │
   ├─ DocxWriter:
   │   ├─ Loads master template (docxtpl Document)
   │   ├─ Builds context: metadata + sections + appendices + version_history
   │   ├─ Subdocs with RichText (bold/italic real, headings, bullet prefix)
   │   ├─ Native Word tables for markdown tables (Table Grid style, 7–10pt
   │   │   font adaptive based on row × col density)
   │   ├─ Renders the template with context
   │   └─ Returns binary content + filename
   │
   ├─ Audit event: exportado (with language metadata)
   └─ Streamlit st.download_button serves the file
```

---

## 6. Core Modules

### 6.1 UI layer (`src/ui/`)

```
src/ui/
├── theme.py                          # SMNYL_COLORS palette + apply_smnyl_theme()
│
├── components/
│   ├── header.py                     # Branded header with breadcrumbs
│   ├── empty_state.py                # Reusable empty-state visual
│   ├── timeline.py                   # Vertical audit timeline w/ event markers
│   ├── seccion_card.py               # Section card (status, actions)
│   └── ...
│
└── pages/
    ├── home.py                       # Entry point (in app.py)
    ├── importar.py                   # Upload .docx
    ├── crear_nuevo.py                # Create-from-scratch form
    ├── onboarding.py                 # Transversal facts capture
    ├── dashboard.py                  # 28-section grid + governance + export
    ├── entrevista.py                 # Split chat ↔ preview
    ├── auditoria.py                  # Full audit timeline w/ filters
    └── vista_previa.py               # HTML preview before export
```

**Routing:** `st.session_state["pagina"]` drives a simple `if/elif` ladder in `app.py:main()`. Each page exposes `def render() -> None`.

### 6.2 Application layer (`src/core/usecases/`)

```
src/core/usecases/
├── importar_documento.py            # Storage + Reader + Repo + Analyzer orchestration
├── crear_documento.py               # NEW: empty Documento from canonical catalog
├── interview_engine.py              # State management for interviews
├── entrevista_uc.py                 # IniciarEntrevista + ResponderPregunta
├── drafter.py                       # Final-draft generation (Opus)
├── knowledge_extractor.py           # Haiku-backed transversal-fact extractor
├── omitir_seccion.py                # Mark section as not applicable + reason
├── adjuntar_tabla.py                # Excel/CSV → Apendice
├── table_extractor.py               # Haiku-backed prose → structured JSON
├── cambiar_estado.py                # State transitions + sign-off registration
├── markdown_cleanup.py              # Cleans markdown artifacts before docx render
├── markdown_blocks.py               # Splits content into prose + native tables
├── richtext_render.py               # Bold/italic/heading parsing for RichText
├── traductor.py                     # ES → EN translation (Sonnet)
├── exportar_documento.py            # Orchestrator: TableExtractor + DocxWriter + audit
├── docx_writer.py                   # docxtpl + master template renderer
└── gap_analyzer.py                  # Heuristic completeness analysis
```

**Pattern:** each use case is a `@dataclass` (or class with `__init__`) with injected dependencies. UI builds it with concrete adapters; tests build it with mocks.

### 6.3 Domain layer (`src/core/`)

```
src/core/
├── models/                          # Pydantic models (see §3)
├── rules/
│   └── state_machine.py             # DocumentStateMachine (pure logic)
└── template_catalog.py              # TEMPLATE_MODEL_DEVELOPMENT (28 sections)
                                     # + construir_secciones_vacias()
```

**Imports here:** stdlib only + pydantic. Zero infrastructure dependencies.

### 6.4 Infrastructure layer

```
src/llm/
├── client.py                        # LLMClient Protocol + AnthropicClient
├── prompts/                         # System prompts (Jinja2 templates)
└── pricing.py                       # Per-model token pricing for cost calc

src/docs/
├── reader.py                        # python-docx → Documento
└── templates/
    └── model_development_smnyl_final.docx  # Master template

src/storage/
├── db.py                            # SQLAlchemy engine + session + tables
├── repositories.py                  # DocumentoRepository, EstadoEntrevistaRepository
└── storage.py                       # Storage interface + FilesystemStorage
                                     # (S3Storage to be added at M3)

src/config.py                        # pydantic-settings: load .env into Settings
```

---

## 7. Storage & Persistence

### 7.1 SQLite schema (current MVP)

#### Table: `documentos`

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` | UUID, primary key |
| `user_id` | `String(64)` | Indexed; always `"default"` in MVP |
| `tipo` | `String(32)` | `"model_development"` (only type today) |
| `estado` | `String(32)` | Indexed; `draft`/`in_review`/`approved`/`published`/`retired` |
| `nombre_modelo` | `String(256)` | Denormalized for quick listing |
| `payload_json` | `Text` | **The full Pydantic Documento serialized as JSON** |
| `creado_en` | `DateTime` | |
| `actualizado_en` | `DateTime` | |

#### Table: `estados_entrevista`

| Column | Type | Notes |
|---|---|---|
| `id` | `String(128)` | Composite: `"{documento_id}::{seccion_id}"` |
| `documento_id` | `String(36)` | Indexed |
| `seccion_id` | `String(64)` | Indexed |
| `cerrada` | `Boolean` | True once interview is finalized |
| `payload_json` | `Text` | Serialized `EstadoEntrevista` (chat history + metadata) |
| `actualizada_en` | `DateTime` | |

**Why JSON-blob and not normalized tables:**
- Domain model evolves frequently (new fields added in Phase 2.5, 3, 4 — backward compatible via Pydantic optional fields).
- Maintaining a parallel relational schema alongside the Pydantic model = double maintenance.
- Querying internals of `payload_json` in MVP is rare; when needed, PostgreSQL JSON operators handle it natively.
- When the schema stabilizes (post-pilot), specific fields can be denormalized to indexed columns for analytical queries.

**Trade-offs accepted:**
- ⚠ No transactional concurrent writes within a single document (single-user MVP makes this irrelevant).
- ⚠ Cannot query "give me all sections marked omitida across all documents" without scanning. Acceptable: such queries are rare; when needed, we can add a denormalized `documento_secciones` view in Phase 2.

### 7.2 Filesystem layout (current MVP)

```
data/
├── documente.db                     # SQLite database
├── uploads/                         # Imported .docx originals
│   └── {file_id}.docx               # File ID is the Storage UUID
├── exports/                         # Generated .docx exports
│   └── {documento_id}_{ts}.docx
├── apendices/                       # Excel/CSV files attached as appendices
│   └── {file_id}.{xlsx|csv}
└── backups/                         # Manual backups (pre-risky operations)
    └── documente_{ts}.db
```

**Total size growth:** dominated by `uploads/` and `exports/`. Estimated 5–20 MB per document. At 100 documents/year, ~1–2 GB/year. Not a concern in EC2 EBS or S3.

### 7.3 Storage interface (migration-ready)

```python
class Storage(Protocol):
    def guardar_upload(self, archivo: IO[bytes], nombre_original: str) -> str: ...
    def guardar_export(self, contenido: bytes, nombre_archivo: str) -> str: ...
    def obtener(self, file_id: str) -> bytes: ...
    def ruta_local(self, file_id: str) -> Path: ...  # For libs that need a real path

class FilesystemStorage:
    """MVP implementation — writes to data/ on local disk."""

class S3Storage:
    """Phase 2 implementation — writes to S3 bucket. Not implemented yet."""
```

When S3Storage lands, the only change in the rest of the codebase is the dependency injection in the UI's use-case factories.

---

## 8. Scalability Roadmap (MVP → Production)

### 8.1 Current state and bottlenecks

| Bottleneck | Current MVP | Impact at scale | Mitigation |
|---|---|---|---|
| **Single-user** | No auth, no `user_id` partitioning enforced | Cannot expose to multiple users | Cognito + enforce `user_id` filter in repository (M4) |
| **SQLite** | Single-writer, no network access | Cannot serve from EC2 | Swap to PostgreSQL via `DATABASE_URL` (M2) |
| **Local filesystem** | EC2 single-node | If instance dies, data lost | S3 with EC2 IAM role (M3) |
| **In-process LLM calls** | Synchronous, blocks Streamlit | At scale, long requests stall the UI | Background worker (Celery or AWS Step Functions) — Phase 3 |
| **No request rate limiting** | None | Could burst Anthropic API | Token-bucket rate limiter — Phase 2 |
| **Cost monitoring** | Per-document cost widget only | No org-level visibility | CloudWatch dashboard + cost alarms — Phase 2 |

### 8.2 Phased scaling plan

#### Phase 1 — MVP (current)

- Compute: laptop (single-user)
- Storage: SQLite + local FS
- Concurrency: 1 user, sequential operations
- Users: 1 (Alberto)
- **Cost:** USD 0–10/month (Anthropic API only, ~5–20 doc generations during testing)

#### Phase 2 — Pilot deployment (M1–M7, ~3 weeks)

- Compute: EC2 t3.medium with Docker
- Database: RDS PostgreSQL db.t3.micro
- Storage: S3 (uploads + exports + master template + daily backups)
- Auth: Cognito (5–10 pilot users, JWT tokens, 1-hour TTL)
- Logs: CloudWatch from container stdout
- Backups: RDS automated daily + S3 lifecycle rules
- **Cost:** USD 125–300/month (EC2 + RDS + S3 + ALB + Anthropic API for 30–50 docs)

#### Phase 3 — Production (12+ months)

- Compute: t3.large or autoscaling group
- Database: RDS Multi-AZ for HA
- Background processing: AWS Step Functions or Celery + SQS for long-running drafter jobs
- Document warehouse: parquet exports of SoV-like longitudinal metrics in S3 + Athena
- Integration with internal SMNYL document repositories
- **Cost:** USD 400–800/month (depends on document volume)

### 8.3 Concurrency at pilot scale (Phase 2)

Streamlit is fundamentally a single-process server. For 5–10 concurrent users with infrequent long-running operations (draft generation), a single t3.medium is sufficient. The bottleneck is the LLM call duration (~5–60 seconds) blocking that user's session, not contention across users.

If concurrent demand grows beyond ~20 simultaneous users, options:

1. **Vertical scale:** t3.large or t3.xlarge.
2. **Horizontal scale:** multiple EC2 instances behind ALB. Stateful sessions are stored in RDS, so this works as long as we use sticky sessions OR move EstadoEntrevista entirely to the DB (already done).
3. **Background workers:** offload Drafter and TableExtractor to a Celery worker pool, freeing the Streamlit process.

---

## 9. Architectural Decisions

### Decision 1 — Layered architecture with strict dependency direction

**Context:** the system has UI, domain logic, persistence, and external services.

**Chosen:** UI → Application (use cases) → Domain (pure) ← Infrastructure.

**Rule:** the domain layer (`src/core/models`, `src/core/rules`, `src/core/template_catalog`) NEVER imports from infrastructure (`src/storage`, `src/llm`, `src/docs`) or UI (`src/ui`).

**Benefit:** domain rules are testable without I/O. Infrastructure can be swapped (SQLite → PostgreSQL, Anthropic → Bedrock, FilesystemStorage → S3Storage) without touching domain or use cases.

**Enforcement:** code review + import linting (planned: a custom ruff rule or simple grep-based test).

---

### Decision 2 — Document persistence as JSON blob (vs. normalized schema)

**Context:** the `Documento` entity has nested structure (sections, audit_trail, memoria, apendices, métricas). Mapping all of this to relational tables would be ~6 join tables.

**Chosen:** serialize the Pydantic Documento as JSON in `payload_json: Text`. Index columns for filtering: `user_id`, `estado`, `nombre_modelo`, `actualizado_en`.

**Trade-offs:**

| Pro | Con |
|---|---|
| Domain model evolves freely (Pydantic optional fields → backward compat) | Cannot query inside `payload_json` without full table scan in SQLite |
| Single source of truth (no schema drift) | Loses some referential integrity guarantees |
| Atomic save of entire document | Bigger row size |

**Mitigation in Phase 2 (PostgreSQL):** PG's JSON operators (`->`, `->>`, `jsonb_path_ops`) make queries inside the payload efficient. If specific analytical queries become hot, denormalize to materialized views.

---

### Decision 3 — Provider-neutral LLM interface

**Context:** today we use Anthropic API directly. Compliance might require AWS Bedrock for data residency.

**Chosen:** define `LLMClient` as a Python `Protocol`. `AnthropicClient` implements it. Use cases depend on the Protocol, not the concrete class.

```python
class LLMClient(Protocol):
    def chat(self, *, tarea: Tarea, system_blocks: list[TextBlockParam],
             messages: list[MessageParam], max_tokens: int = 4096) -> LLMResponse: ...
```

**Implementations:**
- `AnthropicClient` — direct API calls, prompt caching via `cache_control`.
- `BedrockClient` (planned) — same Claude models via AWS Bedrock; enables data-residency compliance.

**Switching cost:** ~1–2 days to implement BedrockClient + 0 days of use-case changes.

---

### Decision 4 — Three-tier model strategy (Sonnet/Opus/Haiku)

**Context:** Opus is great but costs ~3× Sonnet and ~10× Haiku. Using Opus for everything is wasteful.

**Chosen:** route each task to its appropriate tier:

| Task | Model | Reasoning |
|---|---|---|
| Interview turn-taking | Sonnet 4.6 | Conversational; users wait. Quality "good enough" at 1/3 cost. |
| Final draft generation | Opus 4.7 | One-shot, quality matters more than cost or latency. |
| Table extraction, knowledge extraction | Haiku 4.5 | Fast structured-output extraction; cheap and fast. |

**Result:** ~3–5× lower cost per document vs. Opus-everywhere, with no quality degradation in practice (validated end-to-end).

**Override mechanism:** `AnthropicClient(modelos_override={...})` for tests or special configurations.

---

### Decision 5 — Master Word template (vs. generating styling in code)

**Context:** the exported `.docx` must be indistinguishable from a corporate SMNYL document.

**Chosen:** the master template is designed in Word with all styles, palette, typography, headers, table styles, footers, and cover page. Code only fills `{{ placeholders }}` and runs `{% for %}` loops via `docxtpl`.

**Benefits:**
- Brand designer can edit the template in Word without touching code.
- Aesthetic quality is guaranteed by construction — no chance of mismatched styling.
- Adding a new section means editing the template and adding a placeholder.

**Drawbacks accepted:**
- Word splits placeholder text into "runs" when typing pauses, which can break `{{ name_with_underscore }}` patterns. Mitigated by a guide (`docs/TEMPLATE_PLACEHOLDERS_GUIDE.md`) and an XML repair script.
- Programmatic edits (adding a new placeholder mid-cycle) require coordination with the template owner.

---

### Decision 6 — Aggressive prompt caching for fixed context

**Context:** every interview/drafting/extraction call sends ~12K tokens of fixed context (template structure, MRM standard excerpt, brand guidelines, tone rules).

**Chosen:** mark these blocks with `cache_control={"type": "ephemeral"}` so Anthropic caches them after the first call in a session.

**Effect:**
- First call: regular cost.
- Subsequent calls within the cache window: ~10% of input cost for cached blocks.
- After 30+ calls in a single session: cache_hit_rate >0.6, cost reduction ~50% vs. uncached.

**Monitoring:** `MetricasUso.cache_hit_rate` is computed per document. <0.5 after several calls is a red flag for a silent cache invalidator.

---

### Decision 7 — Sign-offs as immutable audit events (not booleans)

**Context:** MRM requires evidence of "who approved this and when?"

**Chosen:** sign-offs are recorded as `EventoAuditoria` events with type `signoff_reviewer` or `signoff_fae`. The state machine reads these events to validate the next transition.

**Code:**
```python
class DocumentStateMachine:
    def transitar(self, doc, destino):
        if destino == "approved" and not _tiene_evento(doc, "signoff_reviewer"):
            return ResultadoTransicion(permitida=False,
                                       razones=["Falta sign-off del Reviewer"])
        ...
```

**Benefit:** complete answer to audit questions. A boolean flag would tell us "yes" but not "by whom or when."

**Trade-off:** transitions cost an extra event lookup. Negligible for 28-section documents.

---

### Decision 8 — Multi-user-ready data model from day 1

**Context:** MVP is single-user but eventual deployment is multi-user.

**Chosen:** every persisted entity has a `user_id` field. In MVP it's always `"default"`. When Cognito lands in Phase 2, the field is populated from the JWT claim.

**Result:** zero schema migration needed for multi-user. All repository methods already accept `user_id` filtering.

---

## 10. Non-Functional Requirements

### 10.1 Reliability

| Requirement | Target | Mechanism |
|---|---|---|
| Document data integrity | 100% (audit_trail immutable) | Pydantic frozen events + atomic SQL transactions |
| LLM call success rate | ≥95% | Retry on transient errors (network, 5xx); explicit error UI on hard failures |
| Application uptime (Phase 2) | 99% (non-critical) | ALB health checks + systemd auto-restart on container exit |
| Backup recoverability | 100% within RTO | RDS automated daily snapshots + S3 lifecycle (30-day retention) |

### 10.2 Auditability (MRM requirement)

| Requirement | Implementation |
|---|---|
| Every change traced to actor + time | `EventoAuditoria` with `actor`, `timestamp`, `tipo`, `seccion_id`, `metadata` |
| Sign-offs verifiable | Sign-off events are immutable; state machine validates against them |
| State transitions logged | Every state change is a `transicion_estado` event with origen/destino in metadata |
| Export tracking | Every export is an `exportado` event with language metadata |
| Methodology transparency | Each section has `intencion` (what it captures); the Drafter's prompts are versioned in `src/llm/prompts/` |

### 10.3 Reproducibility

| Requirement | Implementation |
|---|---|
| Same documento → same .docx | DocxWriter is deterministic; only TableExtractor (Haiku) introduces stochasticity in 4 sections |
| Prompt versioning | Prompts live in `src/llm/prompts/*.j2` with explicit version comments |
| Model versioning | `target_model` is captured in `LlamadaLLM` for every call |
| Cache version invalidation | Changing fixed-context content automatically invalidates the cache (different tokens → different cache hash) |

### 10.4 Aesthetic compliance (non-negotiable)

| Requirement | Implementation |
|---|---|
| Exported `.docx` indistinguishable from corporate doc | Master template designed in Word + `docxtpl` placeholder fill |
| Brand palette adherence | `BRAND_GUIDELINES.md` codifies palette + typography; `theme.py` applies to UI; template encodes the same in `.docx` |
| Typography (Georgia/Tahoma) | Master template uses these fonts (officially authorized substitutes per SMNYL manual p.75) |
| Table aesthetics | Native Word `Table Grid` style + adaptive font sizing (7–10pt depending on density) |
| Bold/italic real (not asterisks) | Subdoc + RichText parser; markdown `**foo**` becomes a `bold=True` run |

### 10.5 Maintainability

| Requirement | Implementation |
|---|---|
| Test coverage | 182 passing tests; behavior-driven (TDD strict from Phase 1) |
| Type safety | mypy strict mode on `src/`; Pydantic v2 validates at runtime |
| Code style consistency | ruff lint + format; enforced pre-commit |
| Documentation | Inline Spanish docstrings + `docs/` for architecture, MRM, brand, template, migration, UX principles |

---

## 11. Security & Access Control

### 11.1 Authentication & authorization (Phase 2)

| Control | Phase 1 (MVP) | Phase 2 (AWS) |
|---|---|---|
| User auth | None (laptop-only) | AWS Cognito (SSO with SMNYL AD if available; password+MFA otherwise) |
| Session management | N/A | JWT tokens, 1-hour TTL, refresh on activity |
| Role-based access | N/A | Roles: `producer` (create/edit), `reviewer` (sign-off Reviewer), `fae` (sign-off FAE), `admin` (manage users + secrets) |
| User identity in audit | Hardcoded `"default"` | Populated from Cognito JWT `sub` claim |

### 11.2 Data classification

| Data type | Classification | Handling |
|---|---|---|
| Model documentation content | Internal (Confidential) | Stored in RDS (encrypted at rest); transmitted over HTTPS only |
| Model metadata | Internal | Same as above |
| Audit trail | Internal | Same; immutable |
| API keys (Anthropic, etc.) | Confidential / Restricted | AWS Secrets Manager; rotated every 90 days |
| Master `.docx` template | Internal | S3 with restricted IAM access |

### 11.3 Network security (Phase 2)

| Control | Implementation |
|---|---|
| Transport encryption | HTTPS only (ALB terminates TLS 1.2+); HTTP redirected to HTTPS |
| Ingress | Security group: ALB allows 443 from internet; EC2 allows ALB only |
| Egress | EC2 SG: 443 to Anthropic API + AWS service endpoints; DENY all else |
| NAT gateway | Single egress IP for audit/whitelisting at Anthropic |
| Internal DNS | `documente.internal.smnyl` via Route 53 |

### 11.4 LLM data handling

| Concern | Mitigation |
|---|---|
| Sensitive content sent to LLM | DocuMente sends ONLY model documentation content the user explicitly enters or imports. No other system data. |
| Anthropic data retention | Anthropic API claims 30-day retention by default; opt-out available. Bedrock keeps data within AWS region (under evaluation). |
| API key leakage | Stored in Secrets Manager; loaded via IAM role; never written to logs |
| Prompt injection (user input → LLM) | Low risk: prompts are constructed server-side, user input is treated as data not instructions; mitigations possible if needed (input sanitization, role separation) |

### 11.5 Data residency decision (pending)

Two paths for Claude access:

| Option | Pros | Cons |
|---|---|---|
| **Anthropic API direct** | ~10–20% cheaper; mature prompt caching; first-party features land here first | Data leaves AWS region (transmitted to Anthropic infrastructure) |
| **AWS Bedrock** | Data stays within AWS account/region; same Claude model versions | Slightly higher cost; some features lag (caching, batching) |

**Decision pending with SMNYL Compliance.** The codebase is designed to make this swap cheap (~1–2 days) at any time.

---

## 12. Performance & Monitoring

### 12.1 Latency targets

| Operation | Target | Notes |
|---|---|---|
| Page load (any Streamlit screen) | <2 s | 95th percentile |
| Import a `.docx` (parse + persist) | <10 s | For typical 30–50 page model docs |
| Create from scratch (form submit) | <2 s | Just persists an empty Documento |
| Interview turn round-trip | 3–8 s | Sonnet + adaptive thinking + ~12K cached prompt |
| Drafter (final section draft) | 15–60 s | Opus + adaptive thinking + high effort |
| Export `.docx` (no translation) | 10–30 s | Dominated by Haiku TableExtractor calls (4 sections) |
| Export `.docx` (English translation) | 60–180 s | Adds Sonnet translation pass over full document |

### 12.2 Metrics to monitor (Phase 2)

| Metric | Source | Alert threshold |
|---|---|---|
| EC2 CPU utilization | CloudWatch | >80% sustained 5 min |
| EC2 memory utilization | CloudWatch agent | >85% sustained 2 min |
| RDS connection count | CloudWatch | >50% of max_connections |
| RDS storage utilization | CloudWatch | >75% |
| Anthropic API error rate | Application logs | >5% over 10 min |
| Anthropic cost per day | CloudWatch custom metric | >USD 20/day |
| Cache hit rate (per document avg) | Application logs | <0.4 (silent invalidator) |
| Application errors (Streamlit unhandled) | CloudWatch | >1% of sessions |
| ALB 5xx response rate | ALB metrics | >1% |
| Cognito auth failures | Cognito + CloudWatch | >5% sustained |

### 12.3 Observability stack

| Signal | Tool | Notes |
|---|---|---|
| Application logs | CloudWatch Logs | structlog → JSON → CloudWatch via Docker logging driver |
| Infrastructure metrics | CloudWatch (default + agent) | CPU, memory, disk, network |
| Custom application metrics | CloudWatch (boto3) | Per-document cost, cache hit rate, generation duration |
| Distributed tracing | (Future, Phase 3) AWS X-Ray | Useful when background workers are introduced |
| Cost tracking | AWS Cost Explorer + tags | Tag all resources `Project=documente`; daily review |
| Alerts | CloudWatch Alarms → SNS → email/Slack | Tier alerts (P1/P2/P3) for response priority |

---

## 13. Disaster Recovery & Backup

### 13.1 Recovery objectives

| Scenario | RTO | RPO | Method |
|---|---|---|---|
| EC2 instance failure | 15 min | 5 min | ALB unhealthy detection + ASG launch from latest AMI |
| RDS corruption / accidental drop | 1 h | 24 h | Point-in-time restore from automated backups (5-min granularity) |
| S3 object accidental delete | 1 h | 0 (versioning) | Restore previous version; bucket versioning enabled |
| Region-wide AWS outage | 24 h | 24 h | Manual failover to secondary region (cross-region S3 + RDS snapshots — Phase 3) |
| Total AWS account loss | 7 days | 24 h | Rebuild from Terraform/CloudFormation IaC + last off-account backup |

### 13.2 Backup strategy

#### Phase 1 (MVP — local)

- Manual: copy `data/documente.db` to `data/backups/` before risky operations.
- No automated schedule.

#### Phase 2 (AWS)

- **RDS:** automated daily snapshots, 30-day retention.
- **S3:** versioning enabled on the documents bucket; lifecycle rule transitions versions older than 90 days to Glacier.
- **EC2 AMI:** weekly AMI snapshot of the application server (for disaster recovery only — application code is in container image).
- **Code:** GitHub private repo (already in place); Terraform/CloudFormation modules in repo.

#### Phase 3 (Production)

- Cross-region replication of S3 bucket and RDS snapshots.
- Disaster recovery runbook tested quarterly.

---

## 14. Infrastructure on AWS

### 14.1 Target architecture (Phase 2)

```
┌──────────────────────────────────────────────────────────────┐
│                       INTERNET                               │
│  SMNYL Internal Users (5–10 in pilot, 30–40 at MRM peak)     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │  Route 53 (private DNS) │
            │ documente.internal.smnyl│
            └────────────┬────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │ Application Load        │
            │ Balancer (HTTPS 443)    │
            │ ACM TLS cert            │
            │ Health check on :8501   │
            └────────────┬────────────┘
                         │
                         ▼
            ┌────────────────────────────┐
            │ AWS Cognito User Pool      │
            │ - SSO with SMNYL AD (TBD)  │
            │ - JWT 1h TTL               │
            │ - Roles: producer/reviewer/│
            │   fae/admin                │
            └────────────┬───────────────┘
                         │
                         ▼
       ┌─────────────────────────────────────┐
       │   EC2 instance (t3.medium)          │
       │   ├─ Docker container running:      │
       │   │   ├─ Streamlit + uvicorn        │
       │   │   ├─ DocuMente application      │
       │   │   └─ structlog → stdout         │
       │   ├─ IAM role: Secrets Manager      │
       │   │   read, S3 read/write, RDS,     │
       │   │   Bedrock (if used)             │
       │   └─ Security Group:                │
       │      ├─ Ingress: ALB only           │
       │      └─ Egress: 443 only            │
       └──────┬───────────┬──────────────────┘
              │           │           │
       ┌──────▼─────┐ ┌───▼────────┐ ┌▼──────────────┐
       │    RDS     │ │     S3     │ │   Secrets     │
       │ PostgreSQL │ │  Buckets   │ │   Manager     │
       │ db.t3.micro│ │            │ │               │
       │            │ │ - uploads  │ │ ANTHROPIC_KEY │
       │ Encrypted  │ │ - exports  │ │ (rotated 90d) │
       │ at rest    │ │ - template │ │               │
       │            │ │ - backups  │ │               │
       │ Backups:   │ │            │ │               │
       │ daily, 30d │ │ Versioned  │ │               │
       └────────────┘ └────────────┘ └───────────────┘
              │           │           │
              └───────────┼───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │   CloudWatch        │
                │   Logs + Metrics    │
                │   + Alarms → SNS    │
                └─────────────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │   NAT Gateway       │
                │   (single egress)   │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Internet (TLS)    │
                │   Anthropic API     │
                │   (or Bedrock — TBD)│
                └─────────────────────┘
```

### 14.2 AWS resource checklist

| Service | Resource | Configuration |
|---|---|---|
| **VPC** | 1 VPC, 2 AZs | 2 private subnets (EC2 + RDS), 2 public (ALB + NAT) |
| **EC2** | 1 instance, t3.medium | Ubuntu 22.04 LTS; 50 GB EBS gp3; Docker + Compose |
| **RDS PostgreSQL** | db.t3.micro | 20 GB, encrypted at rest (KMS), automated backup 30d |
| **S3** | 4 buckets | `documente-uploads`, `documente-exports`, `documente-templates`, `documente-backups` |
| **Cognito** | 1 User Pool | 5–10 pilot users initially; SSO config TBD |
| **ALB** | 1 ALB | TLS 1.2+, ACM cert for `documente.internal.smnyl` |
| **Secrets Manager** | 1–2 secrets | ANTHROPIC_API_KEY (+ others as needed) |
| **CloudWatch** | Log groups + alarms | Per-component log groups; ~6 alarms initially |
| **Route 53** | 1 hosted zone | Private zone for `*.internal.smnyl` |
| **IAM** | 2 roles, 1 instance profile | EC2 role (Secrets/S3/RDS/CloudWatch/Bedrock); deployment role for CI/CD |
| **NAT Gateway** | 1 NAT (single AZ in MVP) | Promote to multi-AZ at Phase 3 |
| **(Optional) ECR** | 1 repository | If using ECR for Docker images instead of public registry |

### 14.3 Migration milestones (recap from `MIGRATION_TO_EC2.md`)

| Milestone | Scope | Effort |
|---|---|---|
| **M1 — Containerize** | Dockerfile + docker-compose; validate parity with `streamlit run app.py` | 1–2 days |
| **M2 — Database swap** | Change `DATABASE_URL` to PostgreSQL; data migration script | 1–2 days |
| **M3 — Object storage swap** | Implement `S3Storage`; configure IAM | 1–2 days |
| **M4 — Authentication** | Cognito User Pool + ALB integration | 3–5 days |
| **M5 — Provisioning** | Terraform/CloudFormation for all resources above | 2–3 days |
| **M6 — CI/CD** | GitHub Actions: build image → push to ECR → deploy via SSM | 2–3 days |
| **M7 — Observability** | CloudWatch dashboards, alarms, log aggregation | 1–2 days |
| **(M8 — Bedrock, optional)** | Implement `BedrockClient`; switch via env var | 1–2 days |

**Total estimated effort:** 12–22 working days (~3 weeks calendar), including testing and review cycles.

---

## 15. API Contracts & Data Interfaces

DocuMente's MVP is a Streamlit application without a public REST API. Internal "interfaces" exist in three forms:

### 15.1 Streamlit session state contract

| Key | Type | Set by | Read by |
|---|---|---|---|
| `pagina` | `str` (page name) | Any page | `app.py:main()` router |
| `documento_actual_id` | `str` (UUID) | importar, crear_nuevo, home (open recent) | dashboard, entrevista, onboarding, vista_previa, auditoria |
| `entrevista_seccion_id` | `str` | dashboard | entrevista |
| `dialog_export_open` | `bool` | dashboard | dashboard (modal) |
| `mostrar_*` | `bool` | various | components for conditional rendering |

### 15.2 Use case interfaces (Python)

Each use case is callable with explicit inputs and produces an explicit result. Examples:

```python
# Create a fresh document
uc = CrearDocumentoEnBlanco(repo=DocumentoRepository())
doc: Documento = uc.ejecutar(nombre_modelo="ESG Stochastic", model_id="MD-2026-001")

# Import an existing .docx
uc = ImportarDocumento(storage=storage, reader=DocxReader(),
                       repo=DocumentoRepository(), analyzer=GapAnalyzer())
result: ResultadoImportacion = uc.ejecutar(archivo, "model_doc.docx")

# Export to .docx
uc = ExportarDocumento(repo=..., writer=..., extractor=..., translator=...)
result: ResultadoExportacion = uc.ejecutar(documento_id=uuid,
                                           idioma_objetivo="es")
# result.contenido: bytes, result.nombre_archivo: str
```

These are the primary integration points if a future headless API is built (Phase 3).

### 15.3 Persistence row schemas

Already documented in §7.1 (`documentos`, `estados_entrevista` tables).

### 15.4 LLM prompt contracts

System prompts are versioned Jinja2 templates in `src/llm/prompts/`:

| Prompt | Used by | Cached |
|---|---|---|
| `tono.j2` | All tasks | Yes |
| `mrm_standard.j2` | Drafter, GapAnalyzer | Yes |
| `marca_guidelines.j2` | Drafter | Yes |
| `entrevista_seccion.j2` | InterviewEngine | Section-specific portion not cached |
| `drafting_seccion.j2` | Drafter | Same |
| `extraccion_tabla.j2` | TableExtractor | Cached |
| `traduccion_corporate_en.j2` | TraductorDocumento | Cached |
| `extraccion_conocimiento.j2` | KnowledgeExtractor | Cached |

Total fixed-context size at runtime: ~12K tokens. Cache hit rate target: >0.6 after 5 calls in a session.

### 15.5 Future REST API (Phase 3, speculative)

If/when DocuMente needs to be integrated with internal SMNYL document repositories or other systems, a thin FastAPI layer can be added on top of the existing use cases. Proposed shape:

| Endpoint | Method | Body | Response |
|---|---|---|---|
| `/api/v1/documentos` | POST | `{nombre_modelo, model_id}` | `{documento_id, ...}` |
| `/api/v1/documentos/{id}` | GET | — | Full Documento JSON |
| `/api/v1/documentos/{id}/export` | POST | `{idioma}` | Binary `.docx` |
| `/api/v1/documentos/{id}/audit` | GET | — | `list[EventoAuditoria]` |

Use cases stay identical; the API just exposes them over HTTP. No domain or persistence changes required.

---

## Summary

**DocuMente** is a layered, test-driven, migration-ready application. Its architecture emphasizes:

1. **Strict layer separation** — domain logic is pure and infrastructure is swappable.
2. **Auditability** — every change is an immutable event; sign-offs are events, not flags.
3. **Aesthetic compliance** — the `.docx` output is brand-grade by construction (master template + `docxtpl`).
4. **Provider-neutral LLM** — Anthropic today, Bedrock if Compliance requires; ~1–2 days to switch.
5. **Migration-ready by design** — every MVP decision (storage URI, file storage, LLM provider, user identity) is behind an interface evaluated against the AWS migration question.

For **AWS deployment**, the system moves from local single-user to a multi-user, EC2-hosted, RDS-backed, S3-backed setup — preserving every audit and aesthetic guarantee of the laptop version. Estimated 3 weeks of execution from M1 (containerize) to M7 (observability), at USD 125–300/month operational cost during pilot.

---

## Appendix A — Document inventory (related artifacts)

| Document | Purpose | Audience |
|---|---|---|
| `CLAUDE.md` | Project conventions, tech stack policy | Contributors / agents |
| `docs/MRM_REQUIREMENTS.md` | MRM standard reference | All |
| `docs/TEMPLATE_MODEL_DEV.md` | Verbatim NYL template structure | Reader/Drafter authors |
| `docs/TEMPLATE_PLACEHOLDERS_GUIDE.md` | How to edit the master `.docx` | Template owners |
| `docs/BRAND_GUIDELINES.md` | SMNYL palette + typography rules | UI + DocxWriter authors |
| `docs/UX_PRINCIPLES.md` | UX principles non-negotiables | UI authors |
| `docs/MIGRATION_TO_EC2.md` | Migration runbook with §8 step-by-step | Architecture + DevOps |
| `docs/technical_architecture_for_data_architect.md` | This document | Vidal (Data Architect) |

## Appendix B — Contact

**For technical questions:**
- Architecture, schemas, domain logic, prompt design → **Alberto Solano** (albertosm08@gmail.com)
- AWS infrastructure, networking, security → **Vidal** (Data Architect)
- MRM compliance, attestation requirements → **SMNYL Risk Management team**
- Brand & aesthetic compliance → **SMNYL Marketing / Brand team**

---

**Document version:** 1.0
**Last updated:** May 7, 2026
**Next review:** Post-M3 (after EC2 + RDS + S3 are provisioned)
