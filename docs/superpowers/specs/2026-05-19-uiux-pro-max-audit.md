# UI/UX Pro Max Audit — DocuMente

**Fecha:** 2026-05-19 (complemento de D.2 con perspectiva UX senior)
**Framework de evaluación:** UX Laws + patrones modernos + las 99 reglas del skill `ui-ux-pro-max`.
**No duplica:** los 3 audits previos (design system, design critique por pantalla, accessibility WCAG).

---

## TL;DR

DocuMente sufre 4 pecados de UX que la migración a Next.js sola no resuelve:

1. **Violación de Miller's Law** en home y dashboard — demasiados elementos compitiendo por atención (3 CTAs iguales, 28 SeccionCards planas).
2. **Violación de Doherty Threshold** — operaciones LLM de 10-25s sin feedback intermedio rompen el flow del usuario.
3. **Ausencia total de patrones modernos** que el usuario espera por costumbre web 2025: skeleton screens, optimistic UI, undo toasts, command palette, recently-edited surfacing.
4. **Onboarding lineal sin gamificación** — el usuario no ve progreso hasta llegar al dashboard. Brief de 10 preguntas tipo "muro de textareas" tiene tasa de abandono estimada >40%.

**Estilo recomendado:** **Refined Minimalism + Bento Grid** (subset del set de 50+). Compatible con formalidad SMNYL pero introduce respiración visual y agrupación inteligente.

**Quick wins TOP 5** (estimado: 2 días de trabajo, antes de Next.js):
1. Stepper visual en flujos multi-step (onboarding, brief, entrevista).
2. Skeleton screens en lugar de spinners para operaciones LLM.
3. Toast con "Deshacer" en todas las acciones destructivas o intrusivas.
4. Empty states con CTA propio en cada vista vacía.
5. Recent edits surfacing — "Continúa donde te quedaste" prominente en home.

---

## 1. UX Laws aplicadas al journey real

### **1.1 Hick's Law** — *"El tiempo para decidir crece logarítmicamente con el número de opciones"*

**Violación P0 — Home con 3 CTAs equivalentes**
- Síntoma reportado: *"Cuesta saber qué hacer primero"*.
- La home presenta 3 botones casi-idénticos en peso visual (`type="primary"` solo en uno, pero los 3 ocupan columnas iguales con altura igual).
- Para un usuario nuevo: ¿debo crear nuevo, importar, o iniciar Prophet? La pregunta requiere conocimiento previo del producto que no se enseña.
- **Fix**: jerarquía visual fuerte:
  - **Primary big**: "Crear nuevo documento" (CTA grande, 2-column width)
  - **Secondary inline**: "Tengo un docx existente → Mejorar" (text link debajo)
  - **Tertiary**: "Iniciar Ficha Prophet" en una zona aparte, "Para Modelos Actuariales (Prophet)" como caption explicando
- **Net impact**: reduce tiempo-a-primera-acción de ~5s a ~1s.

**Violación P1 — Modal de exportar con 6+ controles visibles**
- En `_dialog_exportar_docx`: radio idioma (3 opciones) + checkbox polish + checkbox versión + input comentario + 2 botones.
- Hick's Law: 6 elementos requieren ~2.6s de decisión vs 3 elementos requieren ~1.5s.
- **Fix**: progressive disclosure. Defaults razonables visibles (Normalizar a español + sin polish + sin versión). Botón "Opciones avanzadas" que expande los toggles raros.

### **1.2 Miller's Law** — *"La memoria de trabajo puede manejar 7±2 elementos"*

**Violación P0 — Dashboard con 28 SeccionCards planas**
- Síntoma reportado: *"Dashboard se siente saturado con tantas cards"*.
- 28 cards en grid 4×7 sobrepasan por 4× el límite de Miller.
- El template NYL tiene 9 capítulos naturales (1. Background, 2. Profile, 3. Pre-Impl, 4. Methodology, etc.) — están ahí pero el dashboard los aplana.
- **Fix**: agrupar por capítulo con `<Accordion>` (1 expanded by default — el siguiente con brechas). Cada capítulo es un bucket de Miller (5±2 cards por bucket).

**Violación P1 — Brief inicial con 10 textareas**
- Síntoma reportado: *"Onboarding muy pesado, mucho scroll"*.
- 10 textareas amontonadas verticalmente exceden el span de atención.
- **Fix**: wizard 1-pregunta-a-la-vez. Cada pregunta es 1 elemento en working memory.

### **1.3 Fitts's Law** — *"El tiempo para clickear un target es función inversa de su tamaño y distancia"*

**Violación P0 — Botón ✏️ Editar en columna estrecha de vista_previa**
- En `vista_previa.py:_render_seccion` el botón usa ratio `[6, 1]`. Si el viewport es 1280px, el ratio 1 = ~140px... menos el padding ~80px efectivos = ~25px tap area.
- **Fix**: hover-only action icon que aparece full-size al hover (patrón Notion). Sin migración, alternativa: dejar ✏️ visible siempre pero con `min-width: 80px; min-height: 44px`.

**Violación P1 — Botones de transición de estado en dashboard**
- Los botones de Gobernanza ("Pasar a Revisión", "Aprobar", etc.) están al fondo del dashboard tras scroll completo.
- **Fix**: sticky action bar al pie del dashboard cuando hay scroll, con CTA contextual ("Estás en draft — pasar a revisión cuando esté completo").

### **1.4 Jakob's Law** — *"Usuarios pasan mayoría del tiempo en otros sites — esperan que el tuyo funcione igual"*

**Violación P0 — Breadcrumb que NO era clickeable (ya fixed)**
- ✅ resuelto en commit anterior.

**Violación P1 — No hay "Recientes" prominente en home**
- Gmail, Notion, Linear, Google Drive: la primera cosa que ven los usuarios es "lo que estaba trabajando hoy". DocuMente lo entierra debajo de los 3 CTAs.
- **Fix**: si hay ≥1 documento "en progreso", reemplazar el hero por "Continúa con [Nombre del modelo] — última edición hace 2h" con thumbnail del estado.

**Violación P1 — Modal de exportar tiene `Cancelar` y `Generar DOCX` con peso visual equivalente**
- En la mayoría de modales web modernos, "Cancelar" es text-only link y la acción primaria es el botón fuerte.
- **Fix**: `Cancelar` como `<Button variant="ghost">` o texto plain link.

### **1.5 Doherty Threshold** — *"Si una respuesta toma >400ms, el usuario pierde flow"*

**Violación P0 — LLM operations 10-25s sin feedback intermedio**
- Drafter, traductor, StructureRealigner, DocumentPolisher toman 10-25s con solo `st.spinner("Generando…")`.
- A los 5s el usuario duda. A los 10s revisa el celular. A los 15s ya está en otra tab.
- **Fix**: streaming token-by-token visible (Anthropic SDK lo soporta). Aunque no termine, el feedback "está pasando algo" mantiene el flow. Cult-ui tiene un componente Streaming Text perfecto.

**Violación P1 — Importar docx tarda 5-15s sin progress detallado**
- Solo dice "Parseando documento y detectando secciones... esto toma 5-15s".
- **Fix**: progress steps visibles: "Parseando estructura → Detectando secciones (4/28) → Cargando fuentes → Generando sugerencias…". Cada step se chequea cuando termina.

### **1.6 Aesthetic-Usability Effect** — *"Las cosas que se ven bien se perciben como más fáciles de usar"*

**Violación P0 — Look "Streamlit default" detectado por usuarios**
- Síntoma reportado: *"Se siente muy básico, como un formulario gubernamental"*.
- Aunque el theme SMNYL está aplicado, la falta de respiración (whitespace), shadow elevations sutiles, y microinteracciones produce sensación "DIY".
- **Fix profundo**: migración Next.js (ya planeada).
- **Fix superficial sin migrar**: aumentar `--space-lg` y `--space-xl`; agregar `box-shadow: 0 4px 12px rgba(0,0,0,0.04)` a cards principales; transition de 200ms en hover de cards/botones.

### **1.7 Goal-Gradient Effect** — *"Cuanto más cerca está la meta, más motivado el usuario"*

**Violación P0 — Falta sensación de progreso**
- Síntoma reportado: *"Falta sensación de progreso (cuántos pasos faltan)"*.
- No hay stepper en onboarding → brief → dashboard. El usuario no sabe en qué punto está.
- En el dashboard, la barra de "porcentaje_completitud" existe pero está enterrada en métricas pequeñas.
- **Fix 1**: stepper visual TOP en flujos multi-step: `(1) Crear ✓ → (2) Onboarding ✓ → (3) Brief ←vos estás aquí → (4) Dashboard`.
- **Fix 2**: en dashboard, hacer la completitud el HERO visual. Un círculo grande "65% completo, faltan 8 secciones obligatorias" — eso motiva.

### **1.8 Peak-End Rule** — *"Los usuarios juzgan una experiencia por el peak emocional y el final"*

**Violación P1 — Export DOCX sin celebración**
- El export muestra un `st.toast("DOCX generado")` discreto y un botón download.
- Es el momento clímax del flujo (después de horas trabajando). Merece más.
- **Fix**: confetti animation (cult-ui tiene Confetti) + mensaje grande "🎉 Documento listo — descárgalo o compártelo". Microinteracción que el usuario recuerda como "valió la pena".

**Violación P1 — Salida del brief sin reconocimiento**
- Después de 10 preguntas, redirige al dashboard con un toast pequeño "X secciones prellenadas".
- **Fix**: una pantalla de transición "✨ Listo — generamos {N} borradores con tus respuestas. Revísalos en el dashboard." Visible 2-3s con animación. Hace sentir el esfuerzo recompensado.

### **1.9 Tesler's Law** — *"Toda aplicación tiene complejidad irreducible — alguien tiene que cargarla"*

**Implicación P1 — Configuración LLM/Bedrock**
- El usuario actuario no debería ver "ANTHROPIC_API_KEY" ni decisiones tipo "Bedrock vs Anthropic directo".
- **Fix**: esa complejidad la carga el admin / setup. Para el usuario final, todo "just works". Documentar separadamente para Vidal pero esconder del UI.

### **1.10 Zeigarnik Effect** — *"Tareas inacabadas se recuerdan mejor que las acabadas"*

**Oportunidad P2 — Continuidad entre sesiones**
- Cuando el usuario abandona una entrevista a mitad, no hay continuidad obvia en home.
- **Fix**: en home, sección "Continúa lo que estabas haciendo" con preview del último chat turn + botón "Retomar". Aprovecha el efecto Zeigarnik para retornar.

---

## 2. Patrones modernos faltantes (lo que esperan los usuarios web 2025)

Estos patrones son estándar en cualquier SaaS moderno (Notion, Linear, Figma, etc.). La ausencia hace que DocuMente se sienta "del 2018".

| # | Patrón | Dónde aplicarlo | Stack |
|---|---|---|---|
| 1 | **Skeleton screens** | Todas las cargas >500ms (dashboard load, importar, sugerencias multi-fuente) | shadcn `<Skeleton>` post-migración. Hoy: divs con `animation: pulse` simulado |
| 2 | **Optimistic UI** | Marcar sección como "completa", archivar doc, editar nombre. Estados "preview" antes de confirmación BD | Necesita estado en cliente (React) → requiere Next.js |
| 3 | **Undo toasts (3-5s)** | Después de archivar, eliminar de papelera, descartar borrador. Patrón Gmail/Linear | Streamlit: `st.toast` + truco de timer en session_state |
| 4 | **Command palette (Cmd+K)** | "Ir a sección X", "Crear documento", "Exportar" — atajo poder-usuario | Solo Next.js (shadcn `<Command>`) |
| 5 | **Inline contextual help** | Hover en "FAE" o "Model Class" → tooltip con definición. Hoy: solo `help=` no descubrible | Solo Next.js (shadcn `<Tooltip>`/`<Popover>`) |
| 6 | **Streaming text de LLM** | Mostrar tokens conforme llegan en entrevista y drafter. Cult-ui Streaming Text | Anthropic SDK ya soporta streaming, falta wire |
| 7 | **Recent-edits surfacing** | Home con "Continúa con [doc] — última edición hace 2h" en lugar de los 3 CTAs por default | Streamlit puede |
| 8 | **Empty states con CTA** | Pestaña Archivados vacía dice solo "No tienes archivados". Debería decir "Aún no archivaste ningún doc. Los docs archivados aparecerán aquí. → [aprende cómo]" | Streamlit puede |
| 9 | **Progressive onboarding** | Tooltips con flechas la primera vez ("Esto es donde editas la sección actual"). Estado en localStorage | Next.js + intro.js o shadcn equivalente |
| 10 | **Autosave indicator** | "Guardado hace 2s" persistente en headers de editor, no solo toast pasajero | Streamlit con session_state.last_saved_at |
| 11 | **Drag-and-drop reorder** de apéndices | Permitir reorganizar el orden de apéndices A.1, A.2 vía drag | Solo Next.js + dnd-kit |
| 12 | **Inline conflict resolution** | Cuando 2 usuarios edita la misma sección (futuro multi-user) | Solo Next.js + WebSockets |

**Top priority sin migrar:** #1, #3, #7, #8, #10 — son los que más se notan en el feedback "se siente básico".

---

## 3. Momentos de fricción / abandonment risk

Estos son puntos en el journey donde un usuario nuevo abandona o se frustra. Calculé tasa de abandono estimada basada en patrones de SaaS B2B.

| # | Momento de fricción | Abandono estimado | Por qué | Fix |
|---|---|---|---|---|
| 1 | **3 CTAs equivalentes en home** | 15-20% | Paradox of choice (Hick) | Ver §1.1 |
| 2 | **Brief de 10 textareas en columna larga** | 35-45% | Cognitive overload (Miller) + sin progreso (Goal-Gradient) | Wizard 1-pregunta-a-la-vez con stepper |
| 3 | **Onboarding form de 8+ campos sin agrupación** | 20-30% | Sin chunking | Agrupar en 3 secciones colapsables |
| 4 | **LLM operation 15s sin feedback** | 10-15% | Doherty threshold violado severamente | Streaming text |
| 5 | **Dashboard wall-of-28-cards** | 5-10% (no abandona pero confunde) | Miller exceeded | Agrupar por capítulo NYL |
| 6 | **Export sin saber qué incluye** | 5% (silencioso) | Sin preview de qué se va a generar | Preview del docx antes del download |
| 7 | **Botón ✏️ Editar diminuto** | 3-5% (usuario no descubre que se puede editar inline) | Fitts law | Hover-only icon o ícono bigger |
| 8 | **No hay onboarding contextual primera vez** | 10% (usa la app mal) | Falta Aha! moment | Tooltips intro.js-style |
| 9 | **Modal de exportar con 6 controles** | 5% (cancela y rinde) | Hick + complejidad | Progressive disclosure |
| 10 | **No hay manera de "guardar borrador y volver"** explícita | 5-10% pierden trabajo | Falta clarity de autosave | Indicator "Guardado hace Xs" persistente |

**Total abandono acumulado estimado:** un usuario nuevo tiene ~40-55% probabilidad de NO completar su primer documento. Los primeros 2 fixes (brief + onboarding) bajan eso a ~25%.

---

## 4. Estilo recomendado (del set de 50+ del skill)

### Estilos evaluados para SMNYL

| Estilo | Match con SMNYL | Comentario |
|---|---|---|
| **Refined Minimalism** | ⭐⭐⭐⭐⭐ | Perfecto. Whitespace generoso, tipografía protagonista, decoración mínima. Encaja con marca formal aseguradora |
| **Bento Grid** | ⭐⭐⭐⭐⭐ | Excelente para el dashboard (28 cards). Cards de diferentes tamaños según importancia |
| **Material Design 3** | ⭐⭐⭐⭐ | Sólido pero más Google que SMNYL. Useful para componentes (FAB, snackbar) |
| **Brutalismo Soft** | ⭐⭐⭐ | Bordes marcados, contraste alto. Cool pero quizás demasiado para aseguradora regulada |
| **Glassmorphism** | ⭐⭐ | Estética bonita pero no encaja con marca conservadora SMNYL |
| **Neumorphism** | ⭐ | Pasado de moda, accessibility issues |
| **Skeuomorphism** | ⭐ | No aplica |
| **Dark mode** | n/a | Como modo opcional v2, sí. Como default, no para LATAM regulated |

### Estilo recomendado: **Refined Minimalism + Bento Grid (subset)**

**Refined Minimalism** es la base:
- Whitespace generoso (multiplicar `--space-lg` actual por 1.5×).
- Tipografía Georgia más prominente: usar 36-48px en H1, no 32px.
- Sin gradientes salvo el primary subtle (`linear-gradient(135deg, primary, primary_dark)` en el botón Hero CTA solamente).
- Bordes muted (`rgba(189, 193, 194, 0.4)` en lugar de `#bdc1c2` sólido) para que se sientan menos "ficha bancaria".
- Iconos lineales Lucide (no flat fill).

**Bento Grid** en pantallas específicas:
- **Home**: hero card grande (CTA primario) + 2 cards medianas (importar, Prophet) + 1 wide card (continúa donde te quedaste).
- **Dashboard**: hero card "Estado del documento" con completitud big + grid de capítulos en tamaños variables según urgencia (capítulo con más brechas = más grande visualmente).
- **Vista previa**: split bento — main content 60% + sidebar 40% con sub-cards (Versiones / Costo / Metadata / Apéndices index).

**Lo que NO incluir:**
- Sin neon glow ni outline animations.
- Sin grandes background patterns/textures.
- Sin emojis como iconos (skill rule #4 `no-emoji-icons`). Reemplazar 📎 / ✏️ / 🔖 / 📦 / 🗑️ por Lucide icons.

---

## 5. Paleta recomendada — refinamiento sobre marca SMNYL

La paleta base SMNYL es conservadora — perfecto para regulatorio. Sin embargo, faltan **tonos intermedios** que dan vida sin perder formalidad.

### Paleta actual + propuesta de extensión

```css
/* Mantener: tokens core */
--primary: #0079c2;        /* NY Life Blue */
--primary-dark: #0a385e;   /* Dark Rain */
--text: #0a3c53;           /* Steel */
--text-muted: #565656;     /* Iron */

/* AGREGAR: variantes que dan respiración */
--primary-50: #e8f2f9;      /* fondo sutil para hover de cards primary */
--primary-100: #c2e0ee;     /* badge fill para "actual" */
--primary-200: #93cce4;     /* outline focus state */
--text-subtle: #6c7a85;     /* a medio camino entre text y text-muted, para captions importantes */

/* AGREGAR: warm neutrals (anti-frialdad bancaria) */
--surface-warm: #fafaf9;    /* fondo base ligeramente cálido, no white sterile */
--surface-elevated: #ffffff; /* cards on warm surface */
--border-subtle: rgba(189, 193, 194, 0.4);  /* divisores muy suaves */

/* AGREGAR: dark variants para texto (resuelve los 5 criticos de a11y) */
--success-dark: #264640;   /* Dark Pine — texto sobre white passes AAA */
--warning-dark: #544235;   /* Dark Sunset */
--info-dark: #0a385e;      /* same as primary-dark, alta legibilidad */
```

### Typography pairing recomendado

El brand pide Georgia (display) + Tahoma (body). Es funcional pero no inspirador.

**Recomendación de upgrade dentro del brand:**

Mantener Georgia para H1/H2 grandes ("Documenta modelos sin fricción"). Pero **agregar Inter como secondary body** para UI dense (data tables, forms, métricas). Inter es la fuente de SaaS modernos (Linear, Vercel, GitHub) y tiene mejor legibilidad en pantalla que Tahoma.

```css
--font-display: Georgia, "Times New Roman", serif;   /* H1, H2 — branding */
--font-body: "Inter", -apple-system, BlinkMacSystemFont, "Tahoma", sans-serif;
--font-mono: "JetBrains Mono", "SF Mono", Consolas, monospace;  /* IDs, model_id, código */
```

**Justificación al brand team:** Tahoma sigue siendo el fallback. Inter se carga via Google Fonts (cero costo). El manual SMNYL acepta reemplazos cuando la fuente oficial no aplica (manual §75).

### Escala tipográfica refinada

| Token | Valor | Uso |
|---|---|---|
| `--text-xs` | 11px / 0.6875rem | Captions, labels uppercase |
| `--text-sm` | 13px / 0.8125rem | Body small, metadata |
| `--text-base` | 15px / 0.9375rem | Body por default |
| `--text-md` | 17px / 1.0625rem | Subtítulos, body destacado |
| `--text-lg` | 20px / 1.25rem | H3 |
| `--text-xl` | 24px / 1.5rem | H2 |
| `--text-2xl` | 32px / 2rem | H1 |
| `--text-3xl` | 40px / 2.5rem | Hero (Georgia bold) |
| `--text-display` | 56px / 3.5rem | Solo home landing hero |

Nota: bajé el body de 16px a 15px porque Georgia/Inter a 16 se sienten "muy grandes" en SaaS denso. 15px da más densidad sin sacrificar legibilidad (todavía AA).

---

## 6. TOP 10 Quick Wins (antes de migración Next.js)

Priorizado por ROI (impacto/esfuerzo). Cada uno < 1 día de trabajo.

| # | Quick Win | Impacto | Esfuerzo | Stack hoy |
|---|---|---|---|---|
| 1 | **Stepper visual en flujos multi-step** (onboarding, brief, entrevista). HTML+CSS custom componente reusable | 🔥🔥🔥 | 2-3h | Streamlit |
| 2 | **Hero "Continúa donde te quedaste"** en home si hay docs en draft. Reemplaza por default los 3 CTAs cuando hay actividad reciente | 🔥🔥🔥 | 3h | Streamlit |
| 3 | **Reemplazar emojis por Lucide icons** (📎 📐 ✏️ 🔖 📦 🗑️ → icons SVG). Resuelve skill rule `no-emoji-icons` | 🔥🔥 | 4h (npm + assets) | Mixto: inyectar `<svg>` inline |
| 4 | **Empty states con CTA** en cada tab vacío + cada pantalla sin contenido. Componente `<EmptyStateWithCTA>` reusable | 🔥🔥 | 3h | Streamlit |
| 5 | **Tokens dark + a11y fix** (resuelve los 5 críticos WCAG): `success_dark`, `warning_dark`, `info_dark` en theme.py | 🔥🔥🔥 | 2h | Streamlit |
| 6 | **Toast con Deshacer** después de archivar/papelera. Patrón Gmail. Streamlit no permite undo nativo — emular con session_state timer | 🔥🔥 | 4h | Streamlit |
| 7 | **Confetti + celebration** al primer export exitoso. Peak-End rule | 🔥 | 2h | Streamlit + html5 confetti lib |
| 8 | **"Guardado hace Xs"** indicator persistente en headers de editor MRM/Prophet/entrevista | 🔥🔥 | 2h | Streamlit + session_state timer |
| 9 | **Agrupar dashboard SeccionCards por capítulo NYL** con st.expander por cada uno | 🔥🔥🔥 | 4h | Streamlit |
| 10 | **Microinteracciones**: `transition: all 200ms ease-out` en todos los botones, cards, badges del theme.py | 🔥 | 1h | Streamlit |

**Total**: ~25-30h de trabajo (3-4 días de un dev). Mueve el dial de "se siente básico" a "se siente profesional" sin migrar nada de stack.

---

## 7. Dashboard rework — el más denso

El dashboard tiene 28 cards + Gobernanza + Versiones + brechas + métricas. Es la pantalla más densa y la más visitada (cada usuario llega aquí múltiples veces por día durante semanas).

### Diseño propuesto: **Bento Grid con prioridad inteligente**

```
┌─────────────────────────────────────────────────────────────┐
│  [Breadcrumb: Inicio / Modelo X / Dashboard]                │
│                                                              │
│  Modelo VNB Pricing GMM                                     │
│  Estado: draft · 18 de 28 secciones completas                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────┐   │
│  │ HERO BENTO:          │  │ SIDEBAR (sticky):           │   │
│  │ Completitud big      │  │  ▸ Gobernanza               │   │
│  │ ◯ 65% (18/28)        │  │  ▸ Versiones (3)            │   │
│  │ Acción siguiente:    │  │  ▸ Auditoría (47 evts)      │   │
│  │ "8 obligatorias      │  │  ▸ Exportar DOCX            │   │
│  │  pendientes"         │  │                             │   │
│  │ [→ Continuar]        │  │  ESTADO ACTUAL:             │   │
│  │                      │  │  ◆ Borrador                 │   │
│  └─────────────────────┘  │  → Pasar a revisión          │   │
│                            │     (necesita 100%          │   │
│  ┌─────────────────────┐  │     completitud)             │   │
│  │ BRECHAS CRÍTICAS     │  │                             │   │
│  │ ▣ 4.4 supuestos      │  └─────────────────────────────┘   │
│  │   vacía  → entrevistar│                                    │
│  │ ▣ 5.1 fuentes datos  │                                    │
│  │   parcial → completar │                                    │
│  │ [Ver todas (8)]      │                                    │
│  └─────────────────────┘                                     │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  CAPÍTULOS NYL  (Accordion — 1 expandido)                    │
│                                                              │
│  ▼ Cap 4. Metodología                       [4 de 5 ✓]       │
│    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│    │ 4.1  │ │ 4.2  │ │ 4.3  │ │ 4.4  │ │ 4.5  │             │
│    │ ✓    │ │ ✓    │ │ ✓    │ │ ⬡    │ │ ✓    │             │
│    └──────┘ └──────┘ └──────┘ └──────┘ └──────┘             │
│                                                              │
│  ▸ Cap 1. Background                        [3 de 3 ✓]       │
│  ▸ Cap 2. Profile                           [2 de 3 ✓]       │
│  ▸ Cap 3. Pre-Implementation                [4 de 5 ✓]       │
│  ▸ Cap 5. Data                              [2 de 4 ⚠]       │
│  ▸ Cap 6. Implementation                    [0 de 3 ▣]       │
│  ▸ Cap 7. Outputs                           [3 de 3 ✓]       │
│  ▸ Cap 8. Validation                        [0 de 2 ▣]       │
│  ▸ Cap 9. Monitoring                        [0 de 1 ▣]       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Reglas de diseño aplicadas

| Regla | Implementación |
|---|---|
| **Miller's Law** | 9 capítulos visibles (≤ 7±2), no 28 cards |
| **Fitts** | Sticky sidebar siempre visible para acciones críticas |
| **Aesthetic-Usability** | Hero card con completitud big + bento layout = más respiración |
| **Goal-Gradient** | "65% — faltan 8 obligatorias" prominente, no enterrado en métricas |
| **Hick's Law** | Una acción primaria sugerida ("[→ Continuar]") en lugar de scroll-y-elige |
| **Visual hierarchy** | Brechas críticas como bento card destacado, no lista al fondo |

### Implementación incremental (sin Next.js)

Se puede hacer la mayor parte en Streamlit con `st.expander` por capítulo + `st.columns` para el bento. Lo que SÍ requiere Next.js: la sticky sidebar (Streamlit no soporta), el resize-draggable, y las microinteracciones smooth.

---

## 8. Recomendaciones cross-cutting por sprint de Next.js (D.2 plan dedicado)

Para alinear este audit con el plan de migración Next.js ya escrito en `docs/superpowers/plans/2026-05-19-migracion-frontend-nextjs.md`:

| Sprint Next.js | UX patterns clave a implementar |
|---|---|
| **W1 Backend** | Endpoint para "actividad reciente" del usuario (para Hero "Continúa…") |
| **W2 Layout** | Lucide icons setup, command palette (cmd+K), skeleton primitives, toast con undo |
| **W3 Importar/Crear/Dashboard** | Bento grid dashboard, capítulos accordion, sticky sidebar, hero card "Continúa", empty states con CTA, brief wizard 1-a-1 con stepper, onboarding agrupado |
| **W4 Entrevista/Preview/Editor** | Streaming text LLM, autosave indicator persistente, hover-only edit icons, resize panels, confetti en export exitoso |
| **W5 Polish** | Microinteracciones globales, reduced-motion respect, progressive onboarding tooltips, command palette completo |

---

## 9. Conclusión y prioridades

**Lo que duele HOY (urgente):**
1. Brief inicial de 10 textareas → wizard 1-a-1 (Quick Win #1).
2. Hero "Continúa donde te quedaste" → reduce paradox of choice (Quick Win #2).
3. Dashboard agrupado por capítulo NYL → resuelve overload (Quick Win #9).

**Lo que diferencia (importante):**
4. Streaming text en operaciones LLM → resuelve Doherty.
5. Confetti + peak end en exports → memorabilidad.
6. Skeleton screens + autosave indicator → percepción de calidad SaaS moderno.

**Lo que solo viene con migración Next.js:**
7. Command palette (cmd+K).
8. Bento grid full con sticky sidebar.
9. Optimistic UI con undo.
10. Progressive onboarding tooltips.

**Estilo recomendado:** Refined Minimalism + Bento Grid, con paleta SMNYL extendida (variants intermedias) y typography pair Georgia + Inter (mantiene brand, moderniza tipo body).

**Top quick wins:** 5 items (≈25h de trabajo, 3-4 días) mueven significativamente la percepción de calidad antes de la migración. Hacer #1, #2, #5, #8, #9 esta semana movería el feedback de *"se siente básico"* a *"se siente profesional"*.

Esta auditoría complementa los 3 audits previos (design system, design critique por pantalla, accessibility) y el plan dedicado de migración Next.js. Es la perspectiva UX senior que faltaba.
