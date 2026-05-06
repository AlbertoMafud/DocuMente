# UX Principles — DocuMente

> Este archivo es la **fuente única** de los principios de experiencia y la biblioteca de componentes de DocuMente. La premisa es no-negociable: **la app no puede sentirse como prototipo Streamlit**. Debe verse y operarse como producto enterprise (referencias visuales: Notion, Linear, Stripe Dashboard).

---

## Los 8 principios no-negociables

### 1. Cero callejones sin salida
En cualquier pantalla el usuario sabe (a) **dónde está**, (b) **qué viene siguiendo**, (c) **cómo retroceder**. Cada vista incluye breadcrumbs visibles + un botón "Volver" siempre accesible. Si una acción no se puede completar, ofrecer al menos un siguiente paso constructivo.

### 2. Auto-guardado constante
Nada se pierde. Cada respuesta de la entrevista persiste a SQLite al instante. Cerrar la app a la mitad de una entrevista y reabrir → todo está exactamente donde quedó. Nunca se muestra "se perdió tu trabajo".

### 3. Feedback inmediato a cada acción
- Acciones < 200ms: respuesta visual inmediata (button press, transición).
- Acciones de 200ms–2s: skeleton o pulse en la zona afectada.
- Acciones > 2s: spinner con **mensaje contextual específico** ("Analizando tu documento — esto toma 10-15s", no "Loading…").
- Acciones > 10s: barra de progreso con etapas ("1/3: Parseando .docx").

### 4. Progreso siempre visible
- Barra de progreso global (X de N secciones completas) en el header sticky.
- Indicador de completitud por sección (verde / amarillo / rojo) siempre a la vista.
- Estado del documento (Draft / In Review / Approved / Published) como badge prominente.

### 5. Lenguaje humano, no de sistema
- ✅ "Sigamos con la sección de Supuestos" / "El modelo no se pudo guardar — reintenta en 30s"
- ❌ "POST /sections/4/initialize failed" / "Error 500: Internal server error"

Errores se traducen a acciones, no a stack traces. Si la causa raíz es técnica, mostrar mensaje humano + opción "Ver detalles técnicos" colapsable para troubleshooting.

### 6. Decisiones reversibles
- Cualquier cambio textual se puede deshacer (Ctrl+Z + historial visible).
- Acciones de transición de estado piden confirmación con explicación clara: "Cambiar a 'In Review' bloquea ediciones hasta que el Reviewer apruebe. ¿Continuar?"
- Acciones destructivas (borrar documento, retirar modelo) requieren typing del nombre para confirmar.

### 7. Onboarding de 60 segundos
La primera vez que un usuario abre DocuMente:
- Tour de **máximo 4 pasos** (no tutorial largo).
- Se puede saltar siempre con "Empezar a usar".
- No se vuelve a mostrar a menos que el usuario lo pida desde Ayuda.

### 8. Estética enterprise, no corporativa-aburrida
Aplicamos la marca SMNYL al 100% (`docs/BRAND_GUIDELINES.md`), pero con:
- Espaciado moderno generoso (8/16/24/40 px scale)
- Microinteracciones sutiles (hovers de 150ms, fades de 200ms)
- Jerarquía tipográfica clara (display vs body bien diferenciados)
- Sombras suaves (no flat ni bordes duros)
- Border radius consistente (`8px` para cards, `4px` para inputs, `12px` para modals)

---

## Stack para potenciar Streamlit

Streamlit por defecto se siente prototipo. Lo potenciamos así:

| Recurso | Para qué |
|---|---|
| `streamlit-extras` | Componentes pulidos: `tags`, `metric_cards`, `colored_header`, `vertical_space`, `toggle_switch` |
| `streamlit-shadcn-ui` (opcional) | Cards, dialogs, tabs estilo shadcn — nivel Stripe Dashboard |
| **CSS custom** vía `st.markdown(unsafe_allow_html=True)` | Override de estilos default: paleta SMNYL en botones/sliders/inputs, sombras, radios suaves, ocultar el menú default de Streamlit |
| `streamlit-lottie` | Animaciones Lottie para loading states, celebraciones (export exitoso) |
| Custom React component (Fase 5+ si necesario) | Si la entrevista necesita UI conversacional rica que Streamlit no da bien |

### Reglas de uso del CSS custom
- Todo el CSS vive centralizado en `src/ui/theme.py` (función `apply_smnyl_theme()`).
- Variables CSS (`--color-primary`, `--space-md`, etc.) provienen de `BRAND_GUIDELINES.md` §8.
- No CSS inline disperso por la app — siempre via clases en `theme.py`.

---

## Biblioteca de componentes propios

Cada componente vive en `src/ui/components/`, con tests visuales en `tests/visual/` (Fase 4-5).

| Componente | Ubicación | Responsabilidad |
|---|---|---|
| `Header` | `header.py` | Logo SMNYL + navegación principal + breadcrumbs + estado del documento activo |
| `SectionCard` | `seccion_card.py` | Visualización de una sección del documento: estado, completitud, CTA primario |
| `GapBadge` | `gap_badge.py` | Chip "Falta supuesto" / "Sección vacía" / "Listo" / "Atención" |
| `ChatBubble` | `chat_bubble.py` | Burbujas de la entrevista (variantes: usuario / Claude / sistema) |
| `ProgressTimeline` | `progress_timeline.py` | Línea de tiempo Draft → In Review → Approved → Published |
| `AuditEntry` | `audit_entry.py` | Entrada del audit trail: icono, actor, timestamp, descripción |
| `EmptyState` | `empty_state.py` | Estado vacío amigable con CTA claro (no "No data" gris) |
| `ConfirmDialog` | `confirm_dialog.py` | Diálogo de confirmación con explicación de consecuencias |
| `Toast` | `toast.py` | Notificaciones no-intrusivas para acciones exitosas |
| `LoadingState` | `loading_state.py` | Variantes: spinner, skeleton, progress bar — siempre con mensaje contextual |
| `MetadataPanel` | `metadata_panel.py` | Panel lateral con metadata del modelo (nombre, ID, owner, tier) |
| `FileDropZone` | `file_drop_zone.py` | Zona para arrastrar `.docx` con animación al hover |

---

## User journey mapeado (golden path)

### Pantalla 1 — Home

**Layout:**
- Header: logo SMNYL (esquina sup. izq.) + tagline minimalista
- Hero: "Documenta modelos sin fricción" en Alda Pro 48pt, color Steel
- Dos CTAs primarios grandes:
  - **"Crear nuevo documento"** (botón primary, Blue `#0079c2`)
  - **"Mejorar documento existente"** (botón secondary outline)
- Sidebar derecho: lista de documentos recientes con badge de estado

**Estados:**
- Primera vez: tour de onboarding (4 pasos máximo)
- Recurrente: vista limpia con recientes

### Pantalla 2 — Importar (si elige "mejorar existente")

**Layout:**
- Breadcrumb: Home > Importar
- Drop zone grande centrada con animación al arrastrar (border dashed → solid + color shift)
- Lista de tipos aceptados: `.docx`
- Una vez subido: preview del archivo con metadata (nombre, tamaño, modificado)
- CTA: "Analizar documento" (con loading explicativo cuando se hace clic)

### Pantalla 3 — Dashboard de brechas

**Layout:**
- Breadcrumb: Home > [Nombre del modelo] > Brechas
- Resumen visual al top: 6 cards de sección, cada una verde/amarillo/rojo
- Para cada sección: brechas detectadas listadas con explicación natural
- CTA primario: "Empezar entrevista para llenar brechas"
- CTA secundario: "Editar manualmente"
- Panel lateral: metadata del modelo

### Pantalla 4 — Entrevista

**Layout:**
- Header sticky: sección actual ("4.4 Key Assumptions"), progreso global (3 de 6), botón "Pausar y volver"
- Split layout:
  - Izquierda (60%): chat con Claude (`ChatBubble` componentes)
  - Derecha (40%): preview de la sección que se está llenando, actualizada en tiempo real
- Auto-guardado visible: indicador discreto "Guardado hace 5s"
- Al completar sección: animación sutil + toast "Sección completa"

**Microinteracciones:**
- Burbujas aparecen con fade + slide (200ms)
- Typing indicator de Claude (3 puntos animados) durante generación
- El preview de la sección se highlights brevemente al actualizar

### Pantalla 5 — Revisión final

**Layout:**
- Vista previa del documento completo con formato similar al DOCX final
- Lista de chequeo lateral: completitud MRM ✓, marca aplicada ✓, audit trail ✓
- CTAs: "Exportar DOCX" / "Exportar PDF" / "Cambiar a En Revisión"

### Pantalla 6 — Export con celebración

**Layout:**
- Loading con mensaje "Generando con marca SMNYL..." (spinner + sub-pasos)
- Confeti sutil (lottie) al completar — solo la primera vez por sesión
- Botón de descarga prominente
- CTAs secundarios: "Crear otro documento" / "Volver a biblioteca"

---

## Microinteracciones de referencia

| Acción | Comportamiento |
|---|---|
| Hover sobre botón primario | Background shift 150ms + cursor pointer |
| Click sobre botón primario | Scale 0.98 + ripple 250ms |
| Submit de formulario | Botón se transforma en spinner con texto "Guardando…" |
| Card de sección al hover | Subtle elevation (sombra md → lg) en 200ms |
| Toggle de estado | Fade + slide 250ms |
| Drop file en drop zone | Border dashed → solid + background tint Light Rain |
| Aparición de sección | Fade + slide-from-bottom 300ms staggered |
| Toast de éxito | Slide desde bottom-right, auto-dismiss 4s |
| Error inline | Shake horizontal 300ms + cambio a danger color |

---

## Criterios de aceptación UX (medibles)

Estos checks se ejecutan antes de marcar el MVP como completo (Fase 5).

- [ ] Tiempo desde abrir app hasta primera acción útil: **≤ 3 segundos**
- [ ] Tiempo desde subir documento existente hasta ver dashboard de brechas: **≤ 30 segundos**
- [ ] Cero pantallas con texto técnico crudo (URLs de API, stack traces, IDs UUID visibles al usuario)
- [ ] Todas las acciones destructivas piden confirmación con explicación
- [ ] La app es navegable 100% sin tocar el menú default de Streamlit (lo ocultamos)
- [ ] Test informal: un colega no técnico completa golden path sin ayuda
- [ ] Score visual: capturas de las 6 pantallas pasan revisión "¿se ve enterprise?" contra Notion / Linear / Stripe
- [ ] Auto-guardado verificable: cerrar app durante entrevista y reabrir → estado preservado
- [ ] Toda acción larga muestra loading con mensaje contextual específico
- [ ] Header sticky muestra siempre: documento, sección, progreso global

---

## Anti-patrones (lo que NO hacemos)

- ❌ Mostrar el menú "hamburguesa" default de Streamlit (top-right)
- ❌ Mostrar el footer "Made with Streamlit"
- ❌ Mostrar URLs de API o IDs internos en la UI visible
- ❌ Stack traces visibles al usuario (siempre traducir a mensaje humano)
- ❌ Spinners genéricos "Loading…" sin mensaje contextual
- ❌ Texto en Times New Roman default — siempre Effra/Inter
- ❌ Botones con border-radius cero (look corporativo aburrido) — siempre `4px+`
- ❌ Paleta gris-corporativa default — siempre tokens SMNYL
- ❌ Vacíos sin EmptyState ("No data available" gris) — siempre con ilustración + CTA
- ❌ Confirmaciones genéricas "Are you sure?" — siempre con explicación de consecuencias

---

## Accesibilidad (mínimo WCAG AA)

- Contraste de texto ≥ 4.5:1 (consultar matriz oficial en `BRAND_GUIDELINES.md` §6)
- Focus visible en todos los elementos interactivos (outline de 2px Blue `#0079c2`)
- Todos los inputs tienen labels visibles (no solo placeholder)
- Keyboard navigation funcional (Tab order lógico)
- Screen-reader friendly: alt text en logos, ARIA labels en componentes custom
- No depender solo de color para transmitir información (ej. estado verde/rojo + icono + texto)

---

## Testing visual

En Fase 4-5 implementamos:

- **Snapshot tests**: capturar screenshots de las 6 pantallas en estados clave; comparar contra baseline.
- **Component stories**: cada componente en `src/ui/components/` tiene un archivo `*_story.py` que lo renderiza en variantes para revisión visual rápida.
- **Manual review checklist**: lista de 20 items contra `BRAND_GUIDELINES.md` §9 + este archivo.

---

## Recursos de referencia

- Notion — calidad de texto y jerarquía
- Linear — velocidad percibida y microinteracciones
- Stripe Dashboard — densidad de información sin saturación
- Vercel Dashboard — uso del color con restricción
- Tailwind UI / shadcn — patrones de componentes
