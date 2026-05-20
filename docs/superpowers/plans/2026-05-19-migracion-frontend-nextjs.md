# Plan de migración frontend — Streamlit → Next.js + shadcn/cult-ui

**Tipo de plan:** plan dedicado (D.2.e del plan de remediación S13→S16).
**Pre-requisitos:** este plan consume los 3 audits previos:
- [docs/superpowers/specs/2026-05-19-design-system-audit.md](../specs/2026-05-19-design-system-audit.md)
- [docs/superpowers/specs/2026-05-19-design-critique-por-pantalla.md](../specs/2026-05-19-design-critique-por-pantalla.md)
- [docs/superpowers/specs/2026-05-19-accessibility-audit.md](../specs/2026-05-19-accessibility-audit.md)

---

## Context

DocuMente está construida en **Streamlit con CSS inyectado**. Los 3 audits (design system, design critique, accessibility) confirman lo que ya intuíamos por feedback de usuarios:

1. **Look "Streamlit default" pese al theme custom** — las primitivas Streamlit son block-level por default y se ven como formulario gubernamental incluso con marca SMNYL aplicada.
2. **5 hallazgos críticos de WCAG AA** que requieren rework (3 de contraste de color son fáciles, los demás del touch-target / labels requieren más trabajo).
3. **20+ findings de design crítica** donde ~8 son imposibles de arreglar en Streamlit (tabs con badges de cantidad, hover-only icons, data tables interactivas, wizards con animaciones).
4. **102 ocurrencias de valores tipográficos hardcodeados** en lugar de tokens, y 5 colores fuera del theme.

**Decisión:** migrar a **Next.js 15 (App Router) + Tailwind CSS + shadcn/ui + cult-ui** porque:
- shadcn da componentes accesibles WCAG AA out-of-the-box (basados en Radix Primitives).
- cult-ui aporta los componentes "premium" que shadcn no tiene (animated timeline, chat, kbd palette).
- Tailwind permite consumir el `design_tokens.json` exportado del audit del design system.
- Next.js sirve la SPA con SSR/SSG opcional, perfecta para Cognito + ALB en EC2.

**Resultado esperado:** una webapp que se sienta "Linear / Vercel / Notion" — moderna, accesible, con microinteracciones y respiración visual. **Misma lógica de negocio** (use cases de `src/core/*` quedan intactos). Solo cambia la capa de presentación.

---

## Arquitectura objetivo

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend: Next.js 15 App Router                             │
│  - React Server Components (default)                         │
│  - Client Components donde haya interactividad real          │
│  - shadcn/ui + cult-ui + tailwind                            │
│  - Tokens desde design_tokens.json                           │
│  - Cognito JWT via @aws-amplify/auth (cliente) / middleware  │
└─────────────────────┬────────────────────────────────────────┘
                      │ REST (fetch / SWR)
                      │ JSON con types compartidos vía Pydantic→OpenAPI→TS
                      ▼
┌──────────────────────────────────────────────────────────────┐
│  Backend: FastAPI (Python)                                   │
│  - Routers que envuelven los use cases existentes            │
│  - SQLAlchemy + SQLite local (igual que hoy)                 │
│  - Anthropic / Bedrock client (sin cambios)                  │
│  - Auth: JWT validation contra Cognito User Pool             │
│  - OpenAPI auto-generado → cliente TS auto-generado          │
└──────────────────────────────────────────────────────────────┘
```

**Lo que NO cambia:**
- `src/core/*` (modelos Pydantic, use cases). Cero línea modificada.
- `src/llm/*` (cliente Anthropic/Bedrock).
- `src/storage/*` (SQLAlchemy, repositorios).
- `src/docs/*` (readers, writer DOCX).
- BD SQLite/PostgreSQL.

**Lo que cambia:**
- `src/ui/*` → DEPRECADO (queda en historia git pero ya no se ejecuta).
- `app.py` → REEMPLAZADO por `api/main.py` (FastAPI) + `web/` (Next.js).
- Auth: Cognito real (A.1.c se resuelve definitivamente aquí).

---

## Stack y dependencias

### Backend (FastAPI)

```toml
# pyproject.toml (sección nueva)
[project.optional-dependencies]
api = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "python-jose[cryptography]>=3.3",  # JWT Cognito
    "python-multipart>=0.0.9",         # uploads
]
```

### Frontend (Next.js)

```json
{
  "dependencies": {
    "next": "15.0.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "tailwindcss": "^4.0.0",
    "@radix-ui/react-*": "^1.1.0",  // viene con shadcn
    "lucide-react": "^0.460.0",      // iconos
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0",
    "react-hook-form": "^7.53.0",
    "zod": "^3.23.0",                // validación tipos
    "@tanstack/react-query": "^5.59.0",  // server state
    "framer-motion": "^11.11.0",     // animaciones (cult-ui depende)
    "@aws-amplify/auth": "^6.0.0",   // Cognito
    "openapi-typescript": "^7.4.0"   // genera tipos del backend
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/node": "^22.0.0",
    "typescript": "^5.6.0",
    "eslint-config-next": "15.0.0"
  }
}
```

### Componentes shadcn a instalar (vía CLI)

```bash
npx shadcn@latest add button card badge input textarea
npx shadcn@latest add tabs dialog sheet popover tooltip
npx shadcn@latest add alert toast skeleton progress
npx shadcn@latest add breadcrumb navigation-menu dropdown-menu
npx shadcn@latest add table form select checkbox radio-group
npx shadcn@latest add command           # palette de búsqueda
npx shadcn@latest add scroll-area separator
```

### Componentes cult-ui custom (copy-paste, no son paquete)

- Animated Tabs
- Conversation (chat bubbles con animaciones)
- Timeline (con motion)
- Family Button (multi-action)
- Glow Card

---

## Diseño de la estructura del repo

```
DocuMente/
├── pyproject.toml          # mantenemos
├── src/                    # Backend Python (sin cambios en src/core, src/llm, src/storage, src/docs)
│   ├── core/               # ← intacto
│   ├── llm/                # ← intacto
│   ├── storage/            # ← intacto
│   ├── docs/               # ← intacto
│   └── ui/                 # ← DEPRECADO (mantener en git mientras coexiste)
├── api/                    # NUEVO: FastAPI wrapping de use cases
│   ├── main.py
│   ├── routers/
│   │   ├── documentos.py
│   │   ├── secciones.py
│   │   ├── apendices.py
│   │   ├── entrevista.py
│   │   ├── export.py
│   │   ├── versiones.py
│   │   └── auth.py
│   ├── middleware/
│   │   └── cognito_jwt.py
│   ├── schemas/            # Pydantic → request/response models
│   └── dependencies.py     # injection (repo, llm, storage)
├── web/                    # NUEVO: Next.js frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx        # home
│   │   ├── importar/page.tsx
│   │   ├── crear/page.tsx
│   │   ├── docs/[id]/
│   │   │   ├── page.tsx           # dashboard
│   │   │   ├── entrevista/[seccionId]/page.tsx
│   │   │   ├── editar/[seccionId]/page.tsx
│   │   │   ├── preview/page.tsx
│   │   │   ├── auditoria/page.tsx
│   │   │   └── versiones/page.tsx
│   │   └── (auth)/
│   │       └── callback/page.tsx   # Cognito callback
│   ├── components/
│   │   ├── ui/             # shadcn auto-generated
│   │   ├── custom/         # cult-ui ports + custom SMNYL
│   │   └── features/       # composiciones de feature (SeccionCard, GapBadge, etc.)
│   ├── lib/
│   │   ├── api-client.ts   # cliente generado de OpenAPI
│   │   ├── tokens.ts       # importa design_tokens.json
│   │   └── auth.ts         # Cognito helpers
│   ├── hooks/
│   ├── tokens/
│   │   └── design_tokens.json   # ← fuente única
│   ├── public/
│   │   └── logo-smnyl.svg
│   ├── tailwind.config.ts
│   ├── components.json     # shadcn config
│   └── package.json
└── docs/                   # sin cambios
```

---

## Fases del plan (5 sprints, ~5 semanas)

### Sprint W1 — Backend API + tokens (5 días)

**Goal:** levantar FastAPI que sirve los use cases existentes vía REST. Generar OpenAPI. Export tokens.

- [ ] **Task 1: Setup FastAPI** (`api/main.py`, `api/dependencies.py`)
  - Lift use cases existentes a routers REST.
  - Endpoints: GET/POST `/documentos`, GET `/documentos/{id}`, POST `/documentos/{id}/exportar`, etc.
  - Auth middleware con `python-jose` validando JWT de Cognito (header `Authorization: Bearer ...`).
  - Tests: `tests/api/test_*.py` con FastAPI TestClient.

- [ ] **Task 2: OpenAPI schema** + cliente TS auto-generado
  - FastAPI lo expone en `/openapi.json` por default.
  - `openapi-typescript /openapi.json -o web/lib/api-types.ts` genera tipos.
  - Cliente fetch wrapper con `auth header` automático.

- [ ] **Task 3: Tokens JSON exportable** (`web/tokens/design_tokens.json`)
  - Mover los tokens de `theme.py` a JSON canónico (forma del audit D.2.a §5).
  - Generar `theme.py` desde el JSON (Streamlit lo seguirá usando durante coexistencia).
  - Generar `tailwind.config.ts` desde el mismo JSON.

- [ ] **Task 4: Storybook-lite** — markdown del catálogo de componentes
  - Documentar 10 componentes existentes con su API actual + mapeo a shadcn/cult-ui equivalente.
  - Output: `docs/superpowers/specs/component-mapping.md`.

### Sprint W2 — Next.js scaffolding + auth (5 días)

**Goal:** Next.js inicializado, Cognito real funcionando, layout base con tokens SMNYL aplicados, home renderea.

- [ ] **Task 5: Next.js project init**
  - `npx create-next-app@latest web --typescript --tailwind --app --src-dir`
  - Configurar Tailwind con tokens del JSON.
  - shadcn init: `npx shadcn@latest init` con base color "neutral" + radius.
  - Custom CSS vars en `globals.css` que importa tokens SMNYL.

- [ ] **Task 6: Cognito integration** (resuelve A.1.c definitivamente)
  - `@aws-amplify/auth` para flujo client-side, o middleware Next.js para validación SSR.
  - `app/(auth)/callback/page.tsx` para Cognito callback.
  - `lib/auth.ts` helpers: `useUser()`, `getServerSession()`.
  - Páginas protegidas via `middleware.ts`.
  - Cognito User Pool + App Client (Vidal provisiona en AWS, frontend solo consume).

- [ ] **Task 7: Layout base** (`web/app/layout.tsx`)
  - Header SMNYL con logo + breadcrumbs (shadcn `<Breadcrumb>` — clickeable nativo).
  - Footer minimal.
  - Theme provider (light por ahora, dark opcional post-MVP).
  - Toaster (shadcn).

- [ ] **Task 8: Home page** (mapea hallazgos D.2.b §1)
  - 1 CTA primario "Crear nuevo documento" grande.
  - 2 CTAs secundarios "Mejorar existente" y "Iniciar Ficha Prophet" más pequeños debajo.
  - Tabs Activos/Archivados/Papelera con badge de cantidad (shadcn `<Tabs>` + `<Badge>`).
  - DataTable con sort/filter para lista de documentos (shadcn `<DataTable>` con TanStack Table).

### Sprint W3 — Páginas core (importar, crear, dashboard) (5 días)

**Goal:** las 3 pantallas de entrada al flujo principal, terminadas y conectadas al backend.

- [ ] **Task 9: Página importar** (mapea D.2.b §2)
  - Drop zone con shadcn + `react-dropzone`.
  - Ancla docx/pdf + uploader fuentes adicionales en cards diferenciadas.
  - PDF detection → custom Alert con marca SMNYL.
  - Progress bar durante el procesamiento.

- [ ] **Task 10: Página crear_nuevo** (mapea D.2.b §3)
  - Form con `react-hook-form` + `zod` validation.
  - Warning de LLM no disponible en área del uploader, no top.
  - Help expandible para Model ID.

- [ ] **Task 11: Página dashboard** (mapea D.2.b §6 — la más densa)
  - Layout 2-column: main (SeccionCards agrupados por capítulo NYL en `<Accordion>`) + sticky sidebar (gobernanza, métricas, versiones).
  - SeccionCards usan `<Card>` + `<Badge>` (color del status).
  - Brechas como banner arriba (Alert) con prioridad.
  - Card de Gobernanza con tabs internas: Exportar / Estado / Versiones / Auditoría.
  - Métricas con custom MetricCard SMNYL (no shadcn default).

- [ ] **Task 12: Page onboarding + brief wizard** (mapea D.2.b §4, §5)
  - Onboarding: 3 secciones colapsables (`<Accordion>`).
  - Brief: wizard 1-pregunta-a-la-vez con framer-motion transitions, progress bar arriba.
  - Stepper visual `Crear → Onboarding → Brief → Dashboard`.

### Sprint W4 — Entrevista, vista previa, editores (5 días)

**Goal:** las pantallas de trabajo de contenido.

- [ ] **Task 13: Entrevista con resize draggable** (mapea D.2.b §7)
  - shadcn `<Resizable>` panels (chat ↔ preview).
  - Chat con cult-ui Conversation o custom con framer-motion.
  - Tabs internas en drop zone apéndices: Tabla / PDF / Fórmula.
  - Auto-collapse de historial si hay borrador final.

- [ ] **Task 14: Vista previa con editor inline** (mapea D.2.b §8)
  - Document render con `react-markdown` + custom styles SMNYL.
  - Hover-only "✏️ Editar" icon button por sección (Notion-like).
  - Sticky sidebar con metadata + costo + apéndices index.

- [ ] **Task 15: Editor MRM full-featured** (mapea D.2.b §10)
  - Textarea (`<Textarea>` shadcn) + preview live lado a lado.
  - Toolbar de markdown: bold, italic, link, table.
  - Detect unsaved changes + confirm dialog si navegar away.
  - shadcn `<Toast>` para feedback.

- [ ] **Task 16: Auditoría timeline** (mapea D.2.b §9)
  - cult-ui Timeline o custom con framer-motion.
  - Agrupado por día con sticky headers.
  - Filtro por tipo + rango de fechas.
  - Botón "Exportar audit (CSV)".

### Sprint W5 — Polish + QA + paridad (5 días)

**Goal:** todos los flujos funcionales, accesibilidad WCAG AA, performance, deploy ready.

- [ ] **Task 17: Accessibility pass** (resuelve los 5 críticos + 7 majors del audit D.2.c)
  - Tokens `_dark` ya integrados en design_tokens.json.
  - Touch targets ≥44px (shadcn lo hace por default, validar).
  - Form labels visibles o `sr-only`.
  - ARIA labels en status dots y custom indicators.
  - Focus indicators con marca SMNYL.
  - Test con axe-core o Lighthouse a11y.

- [ ] **Task 18: Microinteracciones**
  - Page transitions con framer-motion AnimatePresence.
  - Hover states en todos los CTA / cards.
  - Loading skeletons mientras carga data.
  - Toast feedback en mutations.
  - Empty states con icono + tip + CTA.

- [ ] **Task 19: Páginas Prophet** (Editor Prophet, crear_prophet)
  - Editor con 3 tipos (tabla / texto / campos) usando shadcn `<DataTable>` editable + `<Form>`.
  - Crear Prophet con xlsx uploader + preview de modelos detectados.

- [ ] **Task 20: Paridad funcional + tests E2E**
  - Playwright tests de los 5 flujos clave: import, crear, entrevista, export, archivar.
  - Cobertura: home → import → dashboard → entrevista de 4.4 → export DOCX bilingüe → verificar metadata + versión.
  - Cypress/Playwright reporter en CI.

- [ ] **Task 21: Deploy en EC2**
  - Dockerfile multi-stage: build Next.js + bundle FastAPI.
  - Nginx reverse proxy: `/api/*` → FastAPI puerto 8000, `/*` → Next.js puerto 3000.
  - Coexistir con Streamlit en otro path/subdomain durante 1-2 semanas de transición.
  - Cutover: deprecar Streamlit cuando paridad >= 100%.

---

## Componentes a desarrollar (mapeo audit → implementación)

| DocuMente actual | Mapeo audit D.2.a §6 | Trabajo en W3-W4 |
|---|---|---|
| `back_button.py` | shadcn `<Button variant="ghost">` | Reemplazo directo W2 |
| `header.py` (breadcrumbs) | shadcn `<Breadcrumb>` clickeable | W2 (Task 7) |
| `auth_gate.py` | shadcn `<Card>` + Cognito | W2 (Task 6) — desaparece con Cognito real |
| `seccion_card.py` | shadcn `<Card>` + `<Badge>` + aria-labels | W3 (Task 11) |
| `gap_badge.py` | shadcn `<Badge>` con variants | W3 (Task 11) |
| `empty_state.py` | composición shadcn `<Card>` + `<Button>` | W3 utility |
| `chat_bubble.py` | cult-ui Conversation o custom | W4 (Task 13) |
| `timeline.py` | cult-ui Timeline o custom | W4 (Task 16) |
| `loading_state.py` | shadcn `<Skeleton>` + spinner | W2 utility |
| `onboarding_banner.py` | shadcn `<Alert>` variants | W3 utility |

**Componentes nuevos que shadcn aporta y faltan:**
| Componente nuevo | Donde se usa | Sprint |
|---|---|---|
| `<DataTable>` con sort/filter | Home (lista de docs) | W2 |
| `<Resizable>` panels | Entrevista (split chat/preview) | W4 |
| `<Command>` palette | Atajo "ir a sección" | W3 |
| `<Accordion>` | Dashboard (capítulos NYL), Onboarding (3 secciones) | W3 |
| `<Toast>` | Feedback de mutations | W2 |
| `<Tooltip>`, `<Popover>` | Helpers contextuales | W2 |

---

## Verificación end-to-end (al cerrar W5)

1. **Login Cognito** funciona en EC2 → redirige a callback → muestra home.
2. **Home** muestra 3 CTAs con peso visual correcto + tabs con badges de cantidad.
3. **Crear nuevo doc** con fuentes adicionales → onboarding → brief wizard → dashboard.
4. **Dashboard** con 28 SeccionCards agrupadas por capítulo NYL en accordion + sidebar sticky.
5. **Entrevista** con resize draggable, chat con animaciones, apéndices con 3 tabs.
6. **Editor MRM** inline desde preview con toolbar markdown.
7. **Export DOCX** con polish + versionado funciona; el DOCX final visualmente idéntico al de Streamlit.
8. **Auditoría timeline** filtable + exportable a CSV.
9. **Tabs Archivados/Papelera** con DataTable funcional.
10. **Mobile (375px)** — todas las pantallas usables (Streamlit nunca lo fue).
11. **Lighthouse a11y score ≥95** en las 5 pantallas core.
12. **Tiempo de carga** (LCP) ≤ 2s en EC2.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| FastAPI wrapping de use cases revela acoplamientos de UI a state global Streamlit | Media | Auditar `st.session_state` references — todas deben pasar al cliente |
| Reescribir los export DOCX desde frontend = imposible | Baja | Export sigue en backend Python; frontend solo dispara y descarga blob |
| Cognito + ALB integration tiene curva | Media | Vidal lo provisiona, frontend solo consume tokens — el JWT validator es 50 líneas |
| Performance de Next.js en EC2 t3.medium | Baja | Next.js SSG/ISR para páginas estáticas. Server components reducen JS bundle |
| Paridad funcional incompleta al cerrar W5 | Media | Mantener Streamlit corriendo en paralelo en otro path durante 2 semanas |
| Tests E2E flaky | Media | Playwright con retry + screenshots on failure |

---

## Cronograma realista

| Sprint | Días | Hitos visibles |
|---|---|---|
| W1 | 5 | FastAPI sirve `/documentos`. design_tokens.json existe. Cliente TS generado |
| W2 | 5 | Next.js + Cognito real. Home renderea con tokens SMNYL. Login funciona |
| W3 | 5 | Importar + Crear + Dashboard listos en stack nuevo |
| W4 | 5 | Entrevista + Vista previa + Editores listos |
| W5 | 5 | A11y AA, microinteracciones, deploy en EC2, paridad |

**Total: ~5 semanas dedicadas full-time.**

Si el desarrollo es part-time (mezclado con otros proyectos), multiplicar por 1.5-2 → **8-10 semanas calendario realistas**.

---

## Decisiones que hay que tomar antes de empezar W1

| Decisión | Opciones | Recomendación |
|---|---|---|
| Mantener Streamlit durante migración | (a) cutover dura, (b) coexistir 2-4 semanas | (b) coexistir — riesgo más bajo |
| Hosting del frontend | (a) mismo EC2 que backend, (b) Vercel, (c) S3+CloudFront | (a) mismo EC2 — Vidal ya está armado, evita complejidad multi-host |
| Cognito flow | (a) JWT directo en frontend (Amplify), (b) Cognito-Hosted-UI con session cookie | (a) JWT — alineado con la rama "Cognito-Hosted-UI fronteo" del plan A.1 |
| Storybook real vs markdown | (a) Storybook real ~3 días setup, (b) markdown estructurado | (b) markdown — Storybook es lujo, no necesario para MVP |
| Tests E2E | (a) Playwright, (b) Cypress | (a) Playwright — mejor DX en 2026, soporte oficial Microsoft |
| BD durante migración | (a) misma SQLite, (b) migrar a Postgres ya | (a) SQLite — postgres se hace después, son 2 cambios de URI |

---

## Lo que NO incluye este plan

- **Tokens nuevos en el manual SMNYL.** El audit identificó que faltan `success_dark`, `warning_dark`, `info_dark`. Es trivial agregarlos al `design_tokens.json` — pero la decisión de marca formal queda con quien hace branding interno.
- **Storybook completo** con todas las variantes documentadas. Es lujo. Markdown alcanza para MVP.
- **Mobile-first design**. Nuestro usuario es desktop. La app debe funcionar a 375px (responsivo básico) pero el flujo principal sigue siendo desktop 1280+.
- **Dark mode**. shadcn lo facilita pero pospone hasta v2.

---

## Próximos pasos para activar este plan

1. **Aprobar el plan** (revisión con stakeholders).
2. **Resolver A.1.c** con Vidal (definir mecánica Cognito real) — es input crítico para W2.
3. **Crear branch `feat/migracion-nextjs`** desde `feat/remediacion-s13-s16` (o desde main si ya se mergeó).
4. **Empezar W1.** Setup FastAPI + tokens JSON en paralelo a que Vidal arma Cognito.

Cuando este plan se ejecuta, abre su propio ciclo de subagent-driven development con la skill `superpowers:subagent-driven-development`. Cada Task es de granularidad fina (~1 día) y verificable.
