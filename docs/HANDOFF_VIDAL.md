# Handoff técnico para Vidal — Cambios vs main

> Documento snapshot. Refleja el estado del branch `claude/affectionate-noether-8e038f` (18 commits sobre `main`) al 2026-05-20.
>
> **Propósito:** dar a Vidal toda la información necesaria para validar la nueva arquitectura, planificar el deploy en EC2, y decidir el merge a main.

---

## TL;DR (1 minuto)

1. **DocuMente pasó de Streamlit monolítico a arquitectura de 3 servicios.** El dominio Python (`src/core/`) no cambió; solo se agregaron dos capas nuevas: una **API REST FastAPI** y un **frontend Next.js premium**.
2. **El frontend nuevo tiene paridad funcional total con el Streamlit anterior**, pero look enterprise (sidebar fijo, shadcn/ui, Tailwind, TanStack Query). Streamlit sigue funcionando en paralelo en `:8052` para que nada se rompa durante la transición.
3. **Lo que necesito de Vidal:** validar arquitectura, decidir si EC2 puede correr los 3 servicios o si separamos, y agendar la reunión Cognito (A.1.c).
4. **`main` sigue congelada en `51d845e`** — todo el trabajo vive en el branch. No hay merge hasta que tú apruebes.

---

## 1. Arquitectura antes y después

### Antes (main, commit `51d845e`)

```
┌──────────────────────────────────────────┐
│  Usuario → Streamlit :8052               │
│           ↓                              │
│           src/core/ (Pydantic)           │
│           src/llm/  (Anthropic)          │
│           src/docs/ (docx)               │
│           src/storage/ (SQLite)          │
└──────────────────────────────────────────┘
   1 proceso uvicorn-streamlit
```

### Después (branch `claude/affectionate-noether-8e038f`)

```
┌──────────────────────┐      ┌──────────────────────────────┐
│  Browser (Chrome,    │ ───→ │  Next.js 14 estático :3000   │
│  Edge, Safari)       │      │  Tailwind + shadcn/ui        │
└──────────────────────┘      └──────────────┬───────────────┘
                                              │ fetch JSON
                                              ↓
                              ┌──────────────────────────────┐
                              │  FastAPI :8001               │
                              │  src/api/ (routers, DTOs)    │
                              │  Bearer token auth (gate)    │
                              │  CORS (* en dev)             │
                              └──────────────┬───────────────┘
                                              │ in-process
                                              ↓
                              ┌──────────────────────────────┐
                              │  src/core/ Pydantic          │
                              │  src/llm/   Anthropic        │
                              │  src/docs/  docx             │
                              │  src/storage/ SQLite         │
                              └──────────────────────────────┘
                                              ↑
                              ┌──────────────┴───────────────┐
                              │  Streamlit :8052 (legacy)    │
                              │  Lee mismo dominio en proceso│
                              └──────────────────────────────┘
```

**Lo crítico:** Streamlit y FastAPI consumen el mismo dominio Python y la misma BD SQLite. No hay duplicación de lógica. La transición es "swap del frontend" sin riesgo de datos.

---

## 2. Tres servicios — puertos, puesta en marcha, deps

| Servicio | Puerto dev | Comando | Tech stack |
|---|---|---|---|
| **Streamlit (legacy)** | 8052 | `streamlit run app.py --server.port 8052` | Python 3.11+, Streamlit 1.56 |
| **API REST FastAPI** | 8001 | `uvicorn src.api.main:app --port 8001` | Python 3.11+, FastAPI 0.115, uvicorn |
| **Frontend Next.js** | 3000 | `cd frontend && npm run dev` (dev) / `npm run build && npm start` (prod) | Node.js 20+, Next.js 14, npm |

### Dependencias nuevas

**Python (en `pyproject.toml`):**
- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.30.0`
- `python-multipart>=0.0.7` (upload de archivos)

**Node.js (en `frontend/package.json`):**
- `next@14.2.35`, `react@18`, `typescript@5`
- `tailwindcss@3.4`, `@tanstack/react-query@5`
- `@radix-ui/*` (~12 paquetes — primitivos shadcn/ui)
- `lucide-react`, `sonner`, `framer-motion`, `class-variance-authority`, `clsx`, `tailwind-merge`

Sin deps de sistema operativo nuevas (no necesitas instalar nada con `apt-get` o similar).

---

## 3. Variables de entorno

### Existentes (sin cambio)

```bash
ANTHROPIC_API_KEY=...                # La usa FastAPI y Streamlit
DATABASE_URL=sqlite:///data/documente.db
DOCUMENTE_GATE_PASSWORD=...          # Existía para Streamlit; ahora también la lee FastAPI
```

### Nuevas (frontend)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001       # En prod: https://api.documente.smnyl.mx
NEXT_PUBLIC_API_TOKEN=...                       # Opcional; solo si gate password está activo
```

**Hay un `.env.local.example`** en `frontend/` con el formato esperado.

### Auth — qué hace hoy el backend FastAPI

`src/api/auth.py` implementa un **bearer token compartido** que reutiliza `DOCUMENTE_GATE_PASSWORD`:

- Si la env var **no está definida** → API permite acceso anónimo (modo dev local).
- Si **está definida** → exige header `Authorization: Bearer <password>` en cada request.

Esto es **temporal hasta Cognito real (A.1.c)**. Cuando definamos la mecánica Cognito con ALB-header o JWT-middleware, reemplazo `src/api/auth.py` con la verificación correspondiente. El resto de la API no cambia.

---

## 4. Endpoints REST disponibles

**Swagger UI auto-generado:** http://localhost:8001/docs

**46 endpoints en 11 routers:**

| Router | Endpoints clave |
|---|---|
| `/healthz`, `/readyz` | Health checks (sin auth) |
| `/templates` | Catálogo MRM (9 capítulos, 28 secciones) + Prophet |
| `/documentos` | CRUD + filtros (activos/archivados/papelera) |
| `/documentos/{id}/metadata` | PATCH parcial (17 campos MRM) |
| `/documentos/{id}/archivar`, `/desarchivar`, `/papelera`, `/restaurar`, `/permanente` | Visibilidad |
| `/documentos/{id}/estado` | Transiciones MRM (draft→in_review→approved→published→retired) |
| `/documentos/{id}/signoff` | Sign-off reviewer/FAE |
| `/documentos/{id}/secciones[/{sid}]` | Listar / editar / omitir / reactivar |
| `/documentos/{id}/brechas` | GapAnalyzer (síncrono, sin LLM) |
| `/documentos/{id}/auditoria` | Audit trail (paginable) |
| `/documentos/{id}/exportar[/prophet]` | DOCX descarga directa |
| `/documentos/{id}/polish` | DocumentPolisher LLM |
| `/documentos/{id}/entrevista/{sid}/iniciar`, `/responder`, `/estado` | Entrevista LLM |
| `/documentos/{id}/versiones`, `/versiones/{vid}/snapshot` | Snapshots inmutables |
| `/documentos/{id}/apendices`, `/apendices/{aid}` | Listar + borrar |
| `/documentos/{id}/secciones/{sid}/apendices/tabla|pdf|formula` | Uploads |
| `/documentos/importar` | Multipart .docx/.pdf + fuentes adicionales |
| `/prophet/detectar`, `/prophet/importar` | Excel Prophet → modelos detectados → ficha |

**Spec OpenAPI 3.1** disponible en http://localhost:8001/openapi.json — puede usarse para autogenerar clientes en cualquier lenguaje.

---

## 5. CORS — qué necesitas configurar en producción

**Hoy (dev local):** `allow_origins=["*"]` — abierto para que Next.js dev en cualquier puerto funcione.

### Tu contexto de deploy (URL interna EC2, IP 172.x.x.x)

Como la app va a vivir dentro de la VPN corporativa de SMNYL y solo será accesible desde IPs internas (`172.x.x.x`), **el riesgo real de CORS baja mucho** — el internet abierto no puede llegar al endpoint. **Pero no se elimina por completo**: un empleado con malware dentro de la VPN, o una página interna comprometida, sigue siendo vector teórico.

**3 opciones para decidir:**

| Opción | Setup | Riesgo | Recomendado para |
|--------|-------|--------|------------------|
| **A. Dejar `*` durante piloto** | Cero cambios | Bajo (con VPN como perímetro) | Piloto interno temporal — explicitar la decisión y cerrarlo después |
| **B. Cerrar al IP específico** | `CORS_ORIGINS=http://172.x.x.x:3000` | Mínimo | Si el IP de la EC2 es estable. Funciona pero el config queda con un número, feo |
| **C. Hostname interno** | DNS interno o `/etc/hosts` con `documente.smnyl.local` → `172.x.x.x` + `CORS_ORIGINS=https://documente.smnyl.local` | Mínimo | **Recomendado.** Limpio, sobrevive si la EC2 cambia de IP, permite HTTPS con cert interno |

**Mi recomendación:** **Opción C** desde el inicio. Tú decides si el setup del DNS interno + cert es viable rápido; si no, **A** durante piloto y migración a C en sprint 2.

### Implementación cuando decidas

```python
# src/api/main.py:55
import os

CORS_ORIGINS_RAW = os.environ.get("CORS_ORIGINS", "*")
allow_origins = ["*"] if CORS_ORIGINS_RAW == "*" else CORS_ORIGINS_RAW.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Y en `.env` de EC2:

```env
# Piloto:
CORS_ORIGINS=*

# Cuando decidas cerrar:
CORS_ORIGINS=https://documente.smnyl.local
```

---

## 6. Tests + calidad

| Métrica | Valor |
|---|---|
| Tests unitarios Python | 429 ✅ |
| Tests integration API (smoke) | 28 ✅ |
| TypeScript `--noEmit` | 0 errores ✅ |
| ESLint frontend | 0 warnings ✅ |
| Ruff (Python lint+format) | clean ✅ |
| Regresiones vs main | **0** (todo Python existente sigue passing) |

Las 7 pruebas de integration que fallan son por fixtures `SMNYL/Ejemplos actuales/*.docx` que no se copian al worktree (problema de path local, no de código).

---

## 7. Lo que cambia para el deploy

### Antes (Streamlit solo)

```bash
# 1 servicio en EC2
systemd: documente-streamlit.service
  ExecStart=/opt/documente/.venv/bin/streamlit run app.py
  Port=8052
```

### Después (3 servicios)

**Opción A — Todo en un EC2** (recomendado para MVP en producción interna):

```bash
# 3 servicios en el mismo EC2
systemd: documente-api.service          # uvicorn FastAPI :8001
systemd: documente-streamlit.service    # Streamlit :8052 (mantener mientras se transiciona)
nginx:    sirve frontend Next.js build estático en :443 (HTTPS)
          + reverse proxy /api → localhost:8001
```

**Opción B — Frontend separado** (si quieres usar S3+CloudFront o Vercel):

- API + Streamlit en EC2
- Frontend Next.js build estático en S3 (o Vercel) con CloudFront
- CORS apuntando al dominio del frontend

### Build del frontend

```bash
cd frontend
npm install            # una vez por máquina
npm run build          # genera .next/ con build optimizado
npm start              # corre el servidor Next.js en producción
# O para estático puro: npm run build → exportar y servir con nginx
```

### Checklist de deploy para ti

- [ ] Decidir Opción A (todo en EC2) vs Opción B (frontend separado)
- [ ] Instalar Node.js 20+ y npm en EC2 (si Opción A)
- [ ] Configurar `CORS_ORIGINS` en variable de entorno o hardcodear el dominio
- [ ] Generar `DOCUMENTE_GATE_PASSWORD` para producción (no usar el de dev)
- [ ] Configurar `NEXT_PUBLIC_API_URL` apuntando al dominio real
- [ ] Definir cuándo se apaga Streamlit (¿coexistencia permanente? ¿migración suave?)
- [ ] systemd units para `documente-api.service` + frontend
- [ ] HTTPS con cert válido (Let's Encrypt o el cert de SMNYL)
- [ ] Reunión Cognito A.1.c — decidir mecánica (ALB-header / JWT / Hosted UI)

---

## 8. Decisiones pendientes que necesito de ti

### Decisión 1 — Cognito real (A.1.c) [BLOQUEANTE para producción real]

**Tres opciones técnicas:**

| Mecánica | Pros | Contras |
|---|---|---|
| **ALB-header injection** | Cero cambios al backend Python; ALB inyecta `X-Amzn-Oidc-Data` con JWT | Solo funciona dentro de AWS (no local) |
| **JWT middleware en FastAPI** | Funciona en cualquier lugar; control total | Más código, manejo de PKCE en frontend |
| **Hosted UI Cognito** | Flujo estándar OAuth | Redirect dance; requiere callback en frontend |

Quiero validar contigo cuál encaja mejor con la infra de SMNYL.

### Decisión 2 — Coexistencia o sunset de Streamlit

¿Apagamos Streamlit cuando Next.js esté en prod, o lo mantenemos como fallback? Mi recomendación: coexistencia 2-3 semanas para validación, después sunset.

### Decisión 3 — Bedrock vs Anthropic directo

Ya acordamos Bedrock. El swap es trivial — `src/llm/client.py` tiene `LLMClient` como Protocol; agregar `BedrockClient` paralelo a `AnthropicClient` es ~1 día.

### Decisión 4 — Dominio del frontend

¿Subdominio (`documente.smnyl.mx`) o ruta (`smnyl.mx/documente`)? Esto afecta la config de nginx + cookies + CORS.

---

## 9. Riesgos identificados

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Build de Next.js no validado en producción | Medio | Validar `npm run build` antes del deploy real |
| CORS `*` quedó en código por accidente | Alto | Issue creado: cambiar a variable de entorno antes del merge a main |
| Streamlit y FastAPI compiten por la misma SQLite | Bajo | SQLite tolera readers concurrentes; writes son serializados por SQLAlchemy. En multi-user real, migrar a PostgreSQL |
| Auth bearer token compartido es débil | Medio | Mitigación: solo para piloto interno + VPN. Reemplazar por Cognito antes de exposición externa |
| Frontend en Node.js agrega superficie de ataque | Bajo | Build estático servido por nginx no ejecuta JS server-side. Si usamos `npm start` en EC2, considerar `pm2` + logging |

---

## 10. Archivos clave para tu revisión

| Archivo | Por qué leerlo |
|---|---|
| `src/api/main.py` | FastAPI app + middleware + router registration |
| `src/api/auth.py` | Bearer token actual (placeholder Cognito) |
| `src/api/deps.py` | DI providers (repos + llm + settings) |
| `src/api/routers/*.py` | 11 routers — empezar por `documentos.py` y `exportar.py` |
| `frontend/src/lib/api/client.ts` | Cliente fetch tipado |
| `frontend/src/lib/api/types.ts` | DTOs TypeScript espejo de Pydantic |
| `frontend/next.config.mjs` | Config Next.js |
| `tests/integration/test_api_smoke.py` | 28 tests que validan el contrato de la API |
| `docs/ARQUITECTURA.md` | Doc técnico atemporal — la arquitectura como referencia futura |
| `docs/MIGRATION_TO_EC2.md` | Plan de migración actualizado |

---

## 11. Commits del branch

18 commits sobre `main` (`51d845e`). Orden cronológico:

```
c2a3b1a  fix(a11y): 5 fixes WCAG 2.1 AA críticos
0163675  feat(ux): dashboard agrupado por capítulo NYL (QW#4)
c924117  feat(ux): stepper visual multi-step (QW#1)
9c226c2  feat(ux): hero 'Continúa donde te quedaste' (QW#2)
0dc68cc  feat(ux): indicador 'Guardado hace X' (QW#8)
8b8c85a  feat(ux): microinteracciones globales (QW#10)
e25a535  feat(ux): empty states con CTA + celebración (QW#3)
aebfee4  feat(ux): tokens *_soft globales (QW#5)
1bee041  feat(ux): celebración st.balloons al primer export (QW#7)
d3ea1bf  feat(ux): banner Deshacer post archivar/papelera (QW#6)
de14aec  feat(ux): emojis → Material Symbols (QW#9)
c6c1b9b  feat(ux): premium polish T1 (densidad + brechas accordion)
6854547  feat(api): FastAPI REST exponiendo los use cases (F1)
0b4700f  feat(frontend): Next.js 14 skeleton premium (F2)
041e154  feat(frontend): F3 — dashboard, crear, importar, editor, prophet
1cac71a  feat(frontend): F4 — paridad funcional completa con Streamlit
```

Cada commit message tiene contexto extenso. Para diff completo:

```bash
git log main..claude/affectionate-noether-8e038f --stat
```

---

## 12. Cómo verificarlo localmente

```bash
# En la máquina con el repo clonado
git fetch
git checkout claude/affectionate-noether-8e038f

# Backend (terminal 1)
pip install -e ".[dev]"
cp /ruta/al/.env .env       # ANTHROPIC_API_KEY necesaria
uvicorn src.api.main:app --reload --port 8001
# → http://localhost:8001/docs para Swagger

# Frontend (terminal 2)
cd frontend
npm install
npm run dev
# → http://localhost:3000 (o el puerto siguiente libre)

# Streamlit legacy (terminal 3, opcional)
streamlit run app.py --server.port 8052
```

Los 3 servicios coexisten sin conflicto — comparten la misma BD SQLite.

---

## 13. Próximos pasos sugeridos contigo

1. **Reunión 30 min** para que revises esto + agendar Cognito.
2. **PR a main** después de que valides. Yo lo abro cuando me digas.
3. **Plan de deploy concreto** post-validación — yo redacto el systemd + nginx config.
4. **Sunset plan de Streamlit** — definir fecha tentativa.

---

## 14. Áreas exactas que TÚ tocas (Cognito + PostgreSQL + Bedrock)

> Tres swaps que tú vas a ejecutar en EC2. Aquí los paths específicos para que no tengas que buscarlos.

### 14.1 Cognito real — reemplaza el bearer token compartido

**Estado actual:** `src/api/auth.py` tiene un bearer token simple que reutiliza `DOCUMENTE_GATE_PASSWORD`. Es un placeholder.

**Qué tocar:**

| Archivo | Qué hacer |
|---|---|
| **`src/api/auth.py`** | **Único archivo que reescribes.** Sustituye la función `require_auth()` por verificación de JWT (ALB-header) o validación contra Cognito User Pool. El resto de la API consume `CurrentUser = Annotated[str, Depends(require_auth)]` y no se entera del cambio |
| `src/api/main.py` (opcional) | Si usas ALB-header injection, agregar middleware que extraiga `X-Amzn-Oidc-Data` antes del router |
| `frontend/src/lib/api/client.ts` | Si pasas a Hosted UI, ajustar de bearer estático (`API_TOKEN`) a token dinámico desde sesión Cognito |
| `frontend/.env.production` | Quitar `NEXT_PUBLIC_API_TOKEN` (ya no se necesita en build-time si el token viene del flow OAuth) |

**Las 3 opciones técnicas en concreto:**

```python
# Opción A — ALB-header (recomendado si todo está dentro de AWS)
def require_auth(request: Request) -> str:
    oidc_data = request.headers.get("X-Amzn-Oidc-Data")
    if not oidc_data:
        raise HTTPException(401, "ALB JWT missing")
    payload = jwt.decode(oidc_data, public_key, algorithms=["ES256"])
    return payload["cognito:username"]
```

```python
# Opción B — JWT middleware (funciona dentro y fuera de AWS)
def require_auth(creds: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    token = creds.credentials
    payload = jwt.decode(
        token,
        jwks_client.get_signing_key_from_jwt(token).key,
        algorithms=["RS256"],
        audience=os.environ["COGNITO_CLIENT_ID"],
    )
    return payload["cognito:username"]
```

```python
# Opción C — Hosted UI con cookies de sesión (más Next.js-friendly)
# El frontend hace login en Hosted UI → callback → setea httponly cookie
# El backend valida la cookie en cada request
```

**Tests a actualizar:** `tests/integration/test_api_smoke.py` líneas 220-250 (los 3 tests de auth gate). Reemplazar el bearer token mock por un JWT mock válido contra tu Cognito User Pool de test.

**Lo que NO tienes que cambiar:** ningún router, ningún use case, ningún DTO. La auth está aislada en `src/api/auth.py` y `CurrentUser` es la única superficie pública.

---

### 14.2 SQLite → PostgreSQL — migración de persistencia

**Estado actual:** la app lee `DATABASE_URL` de env. En local apunta a `sqlite:///data/documente.db`. SQLAlchemy abstrae el dialecto.

**Qué tocar:**

| Archivo | Qué hacer |
|---|---|
| **`.env` (en EC2)** | **Único cambio en código.** `DATABASE_URL=postgresql://documente:<pass>@<rds-endpoint>:5432/documente` |
| `pyproject.toml` | Agregar `psycopg2-binary>=2.9` o `psycopg[binary]>=3.1` como dep (driver PostgreSQL) |
| `src/storage/db.py` | **No tocar** — SQLAlchemy elige el dialecto desde la URI automáticamente |
| `src/storage/repositories.py` | **No tocar** — usa SQLAlchemy ORM puro, agnóstico al dialecto |

**Script de inicialización en EC2 (crear tablas la primera vez):**

```python
# scripts/init_schema_postgres.py (crear este archivo)
from src.storage.db import engine, Base
Base.metadata.create_all(engine)
print(f"Schema creado en {engine.url}")
```

Correr una vez post-deploy: `python -m scripts.init_schema_postgres`

**Migración de datos (si hay datos seed en SQLite que mover):**

```bash
# Exportar de SQLite local
sqlite3 data/documente.db .dump > dump.sql

# Limpieza SQLite-specific antes de importar a PG
sed -i 's/AUTOINCREMENT/SERIAL/g; s/PRAGMA.*$//' dump.sql

# Importar a PostgreSQL
psql $DATABASE_URL < dump.sql
```

Para el MVP probablemente no hay datos seed que migrar — RDS arranca vacía y los usuarios crean docs nuevos.

**Tests a actualizar:** `tests/integration/conftest.py` (si existe) — usar `testcontainers` para levantar Postgres efímero en CI, o seguir usando SQLite en CI (los repos son agnósticos).

---

### 14.3 Anthropic directo → Bedrock — swap del LLM provider

**Estado actual:** `src/llm/client.py` define `LLMClient` como Protocol; `AnthropicClient` lo implementa con el SDK de Anthropic directo.

**Qué tocar:**

| Archivo | Qué hacer |
|---|---|
| **`src/llm/client.py`** | Agregar nueva clase `BedrockClient` que cumpla el mismo Protocol `LLMClient`. Mantener `AnthropicClient` por compatibilidad (toggle por env var) |
| `pyproject.toml` | Agregar `boto3>=1.34` como dep (no instalar `anthropic-sdk` adicional, Bedrock se usa vía boto3) |
| **`src/api/deps.py`** | Cambiar el provider `get_llm_client()` para que devuelva `BedrockClient()` o `AnthropicClient()` según `LLM_PROVIDER` env var |
| `.env` | Nueva var `LLM_PROVIDER=bedrock` (default `anthropic`); `AWS_REGION=us-east-1` |
| `src/llm/prompts/` | **No tocar** — los prompts son agnósticos del provider |
| `src/core/usecases/` | **No tocar** — los use cases reciben un `LLMClient` por inyección |

**Implementación del `BedrockClient`:**

```python
# src/llm/client.py (agregar al final)
class BedrockClient:
    """Cumple LLMClient pero usa AWS Bedrock en lugar de Anthropic SDK directo."""

    def __init__(self, region: str = "us-east-1") -> None:
        import boto3
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def chat(self, messages: list[dict], tarea: Tarea, **kwargs) -> LLMResponse:
        modelo = self.modelo_para(tarea)  # mismo mapping tiered: Sonnet/Opus/Haiku
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            # ... resto de params equivalentes
        }
        resp = self._client.invoke_model(
            modelId=f"anthropic.{modelo}-v1:0",
            body=json.dumps(body),
        )
        return self._parse_bedrock_response(resp)

    def modelo_para(self, tarea: Tarea) -> str:
        # Mismo mapping que AnthropicClient pero con IDs Bedrock
        return BEDROCK_MODEL_IDS[tarea]
```

**Lo crítico:** mismo Protocol, misma firma de `chat()`, mismo formato de `LLMResponse`. Los use cases (`InterviewEngine`, `Drafter`, `KnowledgeExtractor`, `TraductorDocumento`, `DocumentPolisher`) **no se enteran del cambio**.

**Costo del swap:** ~1 día de Vidal incluyendo configurar IAM role + invocación de modelos en Bedrock + ajustar pricing (Bedrock tiene tarifas distintas a Anthropic directo — actualizar `src/llm/pricing.py`).

**Tests a actualizar:** `tests/unit/test_anthropic_client.py` (si existe) — agregar `tests/unit/test_bedrock_client.py` con mocks de boto3.

---

### 14.4 Resumen de superficie tocada por Vidal

| Migración | Archivos modificados | Archivos NUEVOS | Costo |
|---|---|---|---|
| Cognito real | `src/api/auth.py`, `frontend/src/lib/api/client.ts`, `.env.production` | — | 2-3 días |
| SQLite → PostgreSQL | `.env`, `pyproject.toml` | `scripts/init_schema_postgres.py` | 1 día |
| Anthropic → Bedrock | `src/llm/client.py`, `src/api/deps.py`, `.env`, `pyproject.toml` | (interno: `BedrockClient` en mismo archivo) | 1-2 días |

**Total estimado:** 5-6 días para las 3 migraciones cerradas.

---

Cualquier duda escríbeme. Documentos relacionados:
- `docs/ARQUITECTURA.md` — referencia técnica atemporal
- `docs/MIGRATION_TO_EC2.md` — plan de migración detallado
- `docs/ARCHIVOS_AUDITORIA.md` — qué archivos sobran post-merge
