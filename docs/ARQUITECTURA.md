# Arquitectura de DocuMente

> Documento técnico atemporal. Refleja la arquitectura del sistema, sus capas, dependencias y decisiones técnicas vigentes.
>
> **Última actualización:** 2026-05-20 (S14 — rewrite a Next.js + FastAPI, paridad con Streamlit).

---

## 1. Visión de 30 segundos

DocuMente es un **sistema agéntico de documentación institucional para SMNYL**. Tiene un dominio Python puro que ejecuta los use cases (importar, entrevista LLM, generar DOCX, gap analysis, etc.) y dos frontends que lo consumen:

- **Streamlit (legacy)** — la primera generación de UI, sigue funcional.
- **Next.js (nuevo)** — UI premium consumida vía API REST FastAPI.

Ambos frontends son funcionalmente equivalentes y leen/escriben la misma base de datos.

---

## 2. Diagrama de capas

```
┌─────────────────────────────────────────────────────────────────┐
│                          PRESENTACIÓN                            │
│  ┌──────────────────────┐         ┌────────────────────────┐    │
│  │  Streamlit (Python)  │         │  Next.js 14 (TS)       │    │
│  │  src/ui/             │         │  frontend/             │    │
│  │  In-process          │         │  Browser / Node.js     │    │
│  └────────────┬─────────┘         └──────────────┬─────────┘    │
└───────────────┼──────────────────────────────────┼──────────────┘
                │ imports directos                  │ HTTP/JSON
                │                                   ↓
                │                  ┌────────────────────────────────┐
                │                  │            API REST            │
                │                  │  src/api/ (FastAPI)            │
                │                  │  routers + DTOs Pydantic       │
                │                  └────────────────┬───────────────┘
                │                                    │
                └──────────────────┬─────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                          APLICACIÓN                              │
│  src/core/usecases/                                              │
│  CrearDocumentoEnBlanco · ImportarDocumento · IniciarEntrevista │
│  ResponderPregunta · ExportarDocumento · GapAnalyzer            │
│  CambiarEstadoDocumento · OmitirSeccion · CrearVersion          │
│  AdjuntarTablaApendice · AdjuntarPdfApendice · ...              │
└────────────────────────────────┬────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                            DOMINIO                               │
│  src/core/models/   (Pydantic — entidades inmutables salvo Doc) │
│  Documento · Seccion · Brecha · EventoAuditoria · Version       │
│  Apendice · MemoriaModelo · EstadoEntrevista · MetricasUso      │
│                                                                  │
│  src/core/rules/                                                 │
│  DocumentStateMachine (transiciones MRM)                        │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                       INFRAESTRUCTURA                            │
│  src/llm/         AnthropicClient (LLMClient Protocol)          │
│  src/docs/        DocxReader · DocxWriter · readers (PDF, XLSX) │
│  src/storage/     DocumentoRepository · EstadoEntrevistaRepo    │
│                   VersionRepository · FilesystemStorage         │
└─────────────────────────────────────────────────────────────────┘
```

### Regla fundamental de las capas

**Dominio nunca importa de Infraestructura ni de Presentación.**

Aplicación importa de Dominio. Infraestructura cumple Protocols definidos en Aplicación o Dominio. Presentación importa de Aplicación.

Si un archivo en `src/core/models/` importa algo de `src/storage/` o `src/ui/`, **es un bug arquitectónico** y debe reportarse.

---

## 3. Tres servicios físicos

| Servicio | Puerto dev | Puerto prod | Stack | Estado | Cuándo se usa |
|---|---|---|---|---|---|
| **Streamlit** | 8052 | 8501 (interno) | Python + Streamlit 1.56 | Legacy, mantenido | Mientras transicionamos a Next.js |
| **API REST** | 8001 | 8001 (interno, detrás de nginx) | Python + FastAPI 0.115 + uvicorn | Activo, contrato estable | Consumido por Next.js (y futuros clientes externos) |
| **Frontend Next.js** | 3000 | 443 (nginx + HTTPS) | Node.js 20+ + Next.js 14 | Activo, recomendado | Todos los usuarios nuevos |

Los 3 servicios:
- Comparten la misma BD SQLite local (en prod: misma instancia PostgreSQL)
- Comparten la misma carpeta `data/` para storage (en prod: mismo bucket S3)
- Tienen ciclo de vida independiente (cada uno se reinicia sin afectar a los otros)

---

## 4. Stack técnico detallado

### Backend (Python)

| Capa | Tecnología | Versión mínima | Por qué |
|---|---|---|---|
| Runtime | Python | 3.11+ (probado 3.11–3.14) | Type hints maduros, mejor performance, pattern matching |
| Validación | Pydantic v2 | 2.7 | Schemas tipados con validación + serialización JSON nativa |
| Settings | pydantic-settings | 2.3 | Carga tipada de `.env` |
| Web (legacy) | Streamlit | 1.36 | UI rápida en Python, ya funcional |
| Web (REST) | FastAPI | 0.110 | OpenAPI auto, type-safe, sync+async |
| ASGI server | uvicorn[standard] | 0.30 | Performance + auto-reload en dev |
| Multipart | python-multipart | 0.0.7 | Upload de archivos en FastAPI |
| ORM | SQLAlchemy | 2.0 | Industry standard; ya con type hints v2 |
| DB local | SQLite | builtin | Cero deps, perfecto para dev/MVP |
| LLM | Anthropic SDK | 0.50+ | Soporte `thinking` y prompt caching |
| DOCX | python-docx + docxtpl | 1.1 / 0.18 | Template-driven; calidad estética garantizada por construcción |
| PDF | pypdf + PyMuPDF | 4.3 / 1.23 | Lectura PDF + render página-as-imagen sin deps SO |
| Excel | openpyxl | 3.1 | Lectura nativa de .xlsx |
| LaTeX | matplotlib | 3.7 | Render de fórmulas LaTeX a PNG |
| Logging | structlog | 24.2 | Logs estructurados, compatibles con CloudWatch |
| Tests | pytest + httpx | 8.2 / 0.27 | Estándar industria + TestClient para FastAPI |
| Lint/format | ruff | 0.5 | Reemplaza black + isort + flake8 |
| Type check | mypy --strict | 1.10 | Detecta bugs antes de runtime |

### Frontend (Next.js)

| Capa | Tecnología | Versión | Por qué |
|---|---|---|---|
| Runtime | Node.js | 20+ | LTS, requerido por Next.js 14 |
| Framework | Next.js | 14.2 (App Router) | RSC + routing + DX premium |
| Lenguaje | TypeScript | 5+ | Strict mode, catch bugs en compile |
| Estilos | Tailwind CSS | 3.4 | Utility-first, tokens SMNYL inyectados |
| UI primitives | shadcn/ui | (copy-paste) | No es lib instalada — componentes vivos en `src/components/ui/` |
| Headless components | Radix UI | varios | Base de shadcn — accesibilidad correcta de fábrica |
| Server state | TanStack Query | 5 | Cache + invalidations + optimistic updates |
| Iconos | Lucide React | latest | Consistencia cross-platform vs emoji |
| Toasts | Sonner | latest | Toasts con acción "Deshacer" (Gmail-pattern) |
| Animaciones | Framer Motion | latest | Disponible; uso futuro en transiciones de página |
| Form composition | (sin lib) | — | React Hook Form se evaluará si los forms crecen |

---

## 5. Flujo de datos típico — ejemplo end-to-end

**Escenario:** usuario crea un documento desde el frontend Next.js.

```
1. Browser
   ↓ user click "Crear nuevo" en home
2. Next.js Component (crear/page.tsx)
   ↓ form.submit() → useCrearDocumento.mutate(...)
3. TanStack Query hook (lib/api/hooks.ts)
   ↓ llama a documentosApi.crear(payload)
4. API client (lib/api/client.ts)
   ↓ POST /documentos con bearer token + JSON
5. FastAPI router (src/api/routers/documentos.py)
   ↓ recibe + valida CrearDocumentoRequest (Pydantic)
   ↓ inyecta DocRepoDep
6. Use case (src/core/usecases/crear_documento.py)
   ↓ CrearDocumentoEnBlanco.ejecutar(nombre, model_id, user_id)
   ↓ construye Documento Pydantic
   ↓ registra EventoAuditoria
   ↓ repo.guardar(doc)
7. Repository (src/storage/repositories.py)
   ↓ SQLAlchemy → SQLite (persiste)
8. Vuelve por el camino inverso:
   Use case → Router → JSON response → Frontend
9. TanStack Query
   ↓ invalida queryKey ["documentos"]
   ↓ refresca lista de docs en home
10. Toast "X creado" + redirect a /documentos/{id}
```

**Lo crítico:** el use case no sabe que se llamó desde una API REST. Funcionaría idéntico si lo llamara Streamlit, un script CLI o un worker batch.

---

## 6. Decisiones técnicas vivas

### Por qué FastAPI y no Flask/Django

- **OpenAPI auto-generado** elimina el costo de mantener docs API manualmente
- **Type hints + Pydantic** se traducen directo a contratos REST tipados
- **Compatibilidad sync/async** sin reescribir código
- **TestClient de httpx integrado** — smoke tests rápidos sin levantar servidor real

### Por qué Next.js 14 (App Router) y no Pages Router o Vite

- **Server Components por default** — reduce JS al cliente, mejor performance
- **App Router es el camino oficial de Next.js** (Pages está en mantenimiento)
- **Vite/SPA pura** no nos da SEO o SSR cuando los necesitemos (ej. reportes públicos)
- **API Routes opcionales** — si más adelante queremos endpoints solo del frontend, ya están

### Por qué shadcn/ui (copy-paste) y no MUI/Chakra/Ant

- **No es una dependencia npm** — son componentes que viven en tu repo. Cero version-lock, cero estilos atrapados en CSS-in-JS de la librería.
- **Tailwind + Radix por debajo** — accesibilidad correcta sin sacrificar control de estilos.
- **MUI/Chakra** tienen mucho peso (~300KB JS) y opinions visuales que pelearíamos contra los tokens SMNYL.
- **Trade-off:** los componentes son tuyos, los mantienes tú. Para un proyecto pequeño-mediano es ideal.

### Por qué TanStack Query y no Redux/Zustand

- **Server state ≠ client state**. La mayoría del estado de DocuMente es eco de la API.
- **TanStack Query** se especializa en server state con cache + invalidations + optimistic updates listos.
- **Zustand** lo usaríamos solo si tuviéramos estado UI complejo (form wizards, drag-drop, etc.) — hoy no.

### Por qué SQLite local en MVP y PostgreSQL en EC2

- **SQLite** = cero dependencias en local. Perfecto para desarrollo, demos y MVP single-user.
- **PostgreSQL** = robustez para multi-user + RDS managed en AWS. Migración es swap de URI en `DATABASE_URL` (SQLAlchemy hace el resto).
- **Si en algún momento necesitamos vector search** (RAG futuro), PostgreSQL + pgvector es trivial.

### Por qué `LLMClient` Protocol y no Anthropic SDK directo

- **Decisión política:** TI/Riesgos de SMNYL acordó usar Bedrock para no sacar datos de la nube de AWS corporativa.
- **Decisión técnica:** `src/llm/client.py` define un `LLMClient` Protocol. Hoy lo cumple `AnthropicClient`; mañana lo cumplirá `BedrockClient`.
- **Costo del swap:** ~1 día. Los use cases nunca se enteran.

### Por qué tokens SMNYL en `tailwind.config.ts` Y en CSS variables

- **Tailwind utilities** (`bg-smnyl-primary`) son cómodos para escribir UI rápido.
- **CSS variables HSL** (`hsl(var(--primary))`) son requeridas por shadcn/ui.
- **Trade-off:** duplicación controlada de los hex en 2 archivos (`tailwind.config.ts` + `globals.css`). La fuente canónica sigue siendo `docs/BRAND_GUIDELINES.md`.

---

## 7. Auth y seguridad — estado actual

**Hoy:** Bearer token compartido (`DOCUMENTE_GATE_PASSWORD`) reutilizado por:

| Servicio | Cómo |
|---|---|
| Streamlit | Componente `auth_gate.proteger_app()` exige el password en la primera carga |
| FastAPI | `src/api/auth.py` exige `Authorization: Bearer <password>` cuando la env var está definida; permite acceso anónimo cuando no |
| Next.js | Manda el token vía `NEXT_PUBLIC_API_TOKEN` (público en el bundle JS — **OK solo para piloto interno + VPN**) |

**Mañana (post-Cognito A.1.c):**
- Reemplazar `src/api/auth.py` con verificación de JWT (ALB-injected o middleware propio).
- Frontend hace login con Cognito Hosted UI → recibe JWT → lo pasa al API.
- Eliminar `DOCUMENTE_GATE_PASSWORD` como mecanismo de auth (puede quedar como kill-switch admin).

---

## 8. Persistencia — modelo de datos

### Tablas SQLite/PostgreSQL actuales

| Tabla | Modelo Pydantic | Propósito |
|---|---|---|
| `documentos` | `Documento` (root) | Entidad raíz; serializada en JSON dentro de columna `payload`. Incluye secciones, audit_trail, metadata, apéndices |
| `estados_entrevista` | `EstadoEntrevista` | Estado conversacional del chat LLM por (documento_id, seccion_id) |
| `versions` | `Version` | Snapshots inmutables del documento serializado |

**Patrón clave:** `Documento` se persiste como JSON dentro de SQLite/PostgreSQL — no se normaliza en tablas relacionales. Esto:
- Reduce drásticamente el código de mapeo
- Permite evolucionar el schema sin migrations
- Es trade-off aceptable porque no hacemos queries cross-doc (cada query es por `documento_id`)
- Si queremos analytics cross-doc en el futuro, escribimos vistas o materializamos en otra tabla

### Storage de archivos

- `FilesystemStorage` (MVP) escribe a `data/uploads/`, `data/exports/`, `data/backups/`
- `Storage` es un Protocol con métodos `guardar_upload`, `ruta_local`, `borrar`
- Migración a S3 = swap del adaptador

---

## 9. Tests

### Backend

| Suite | Cantidad | Tiempo | Comando |
|---|---|---|---|
| Unit (`tests/unit/`) | 429 | ~20s | `pytest tests/unit/` |
| Integration smoke API | 28 | ~7s | `pytest tests/integration/test_api_smoke.py` |
| Integration completo | varía | ~30s | `pytest tests/integration/` (algunos fixtures requieren `SMNYL/`) |

**Total:** 457 tests verdes (al cierre de S14).

### Frontend

- TypeScript `--noEmit` clean
- ESLint clean
- **Pendiente:** E2E con Playwright o Cypress (cero hoy)
- **Pendiente:** Unit tests de componentes con Vitest (cero hoy)

---

## 10. Comandos esenciales

```bash
# === Backend ===
pip install -e ".[dev]"                                          # Setup deps Python
streamlit run app.py --server.port 8052                          # Streamlit legacy
uvicorn src.api.main:app --reload --port 8001                    # FastAPI dev
pytest tests/unit/                                               # Tests rápidos
pytest                                                            # Suite completa
ruff check src/ tests/ && ruff format src/ tests/ --check        # Lint Python
mypy src/                                                         # Type check Python

# === Frontend ===
cd frontend
npm install                                                       # Setup deps Node
npm run dev                                                       # Next.js dev :3000
npm run build && npm start                                        # Producción
./node_modules/.bin/tsc --noEmit                                  # Type check TS
npm run lint                                                      # ESLint
```

---

## 11. Estructura de carpetas (canon S14)

```
DocuMente/
├── app.py                              ← Streamlit entry point
├── pyproject.toml                      ← deps Python + ruff/mypy/pytest config
├── .env                                ← local (gitignored)
├── status.md                           ← se lee al iniciar sesión
│
├── src/
│   ├── core/                           ← DOMINIO + APLICACIÓN (puro Python)
│   │   ├── models/                     Pydantic: Documento, Seccion, …
│   │   ├── usecases/                   Use cases (CrearDocumento, etc.)
│   │   └── rules/                      DocumentStateMachine
│   │
│   ├── api/                            ← API REST (S14)
│   │   ├── main.py                     FastAPI app
│   │   ├── deps.py                     DI providers
│   │   ├── auth.py                     Bearer token (placeholder Cognito)
│   │   ├── errors.py                   Excepciones → HTTPException
│   │   ├── routers/                    11 routers
│   │   └── schemas/                    DTOs Pydantic (separados del dominio)
│   │
│   ├── ui/                             ← Streamlit legacy
│   │   ├── pages/                      13 pantallas
│   │   ├── components/                 stepper, header, gap_badge, …
│   │   └── theme.py                    Tokens SMNYL + CSS injection
│   │
│   ├── llm/                            AnthropicClient + prompts
│   ├── docs/                           DocxReader, DocxWriter, templates
│   └── storage/                        Repositorios + Storage
│
├── frontend/                           ← Next.js 14 (S14)
│   ├── src/
│   │   ├── app/                        17 rutas App Router
│   │   ├── components/
│   │   │   ├── ui/                     shadcn primitives
│   │   │   ├── layout/                 sidebar + topbar
│   │   │   ├── home/                   continue-hero, document-card, …
│   │   │   ├── dashboard/              metrics-row, brechas-accordion, …
│   │   │   ├── auditoria/              timeline
│   │   │   └── entrevista/             chat-bubble
│   │   └── lib/
│   │       ├── utils.ts                cn() + tiempoRelativo()
│   │       └── api/                    types.ts + client.ts + hooks.ts
│   ├── tailwind.config.ts              Tokens SMNYL + shadcn HSL vars
│   ├── components.json                 shadcn config
│   └── package.json
│
├── docs/                               Esta carpeta (este archivo + otros)
├── tests/                              Unit + integration
├── data/                               BD + uploads + exports (gitignored)
├── SMNYL/                              Material fuente (gitignored)
└── assets/                             Logos (gitignored excepto whitelist)
```

---

## 12. Lecturas relacionadas

- `docs/GUIA_DOCUMENTE.md` — guía conceptual + walkthrough técnico simplificado, en español sencillo
- `docs/HANDOFF_VIDAL.md` — snapshot main → branch para Vidal
- `docs/MIGRATION_TO_EC2.md` — plan detallado de despliegue
- `docs/ARCHIVOS_AUDITORIA.md` — inventario de archivos del repo
- `docs/BRAND_GUIDELINES.md` — fuente canónica de la paleta SMNYL
- `docs/MRM_REQUIREMENTS.md` — requisitos Model Risk Management
- `docs/TEMPLATE_MODEL_DEV.md` — estructura del template oficial NYL
- `docs/UX_PRINCIPLES.md` — principios de UI/UX del proyecto
