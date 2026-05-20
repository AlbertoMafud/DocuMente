# Accessibility Audit — DocuMente

**Estándar:** WCAG 2.1 Nivel AA · **Fecha:** 2026-05-19 (D.2.c del plan de remediación)
**Alcance:** tokens de color del theme, primitivas Streamlit usadas, HTML inyectado vía `unsafe_allow_html`, formularios y navegación.

## Summary

| Severidad | Count | Categoría |
|---|---|---|
| 🔴 Critical (bloquea WCAG AA) | **5** | Contraste — 3 colores fallan AA normal text |
| 🟡 Major | **6** | Touch targets, ARIA missing, labels collapsed |
| 🟢 Minor | **4** | Focus indicators, semantics |

**Veredicto:** la app **NO cumple WCAG 2.1 AA** hoy. Los hallazgos críticos son TODOS de contraste de color — algunos colores semánticos (success, warning, info) están bajo el threshold AA cuando se usan como texto sobre fondo blanco. Fixes son sencillos (cambiar token de texto o usar variantes oscuras existentes en el manual SMNYL).

---

## 1. Color Contrast Check (WCAG 1.4.3, 1.4.11)

Calculé los ratios usando la fórmula WCAG sRGB luminance. Marca AA = 4.5:1 normal text, 3:1 large text (≥18pt o ≥14pt bold) y UI components.

| Combinación | Foreground | Background | Ratio | AA Normal (4.5:1) | AA Large (3:1) | AAA (7:1) |
|---|---|---|---|---|---|---|
| Body text | `text` #0a3c53 | white | **11.77:1** | ✅ | ✅ | ✅ |
| Muted text | `text_muted` #565656 | white | **7.34:1** | ✅ | ✅ | ✅ AAA |
| Primary as text | `primary` #0079c2 | white | **4.65:1** | ✅ (barely) | ✅ | ❌ |
| **Success as text** | `success` #4b8b7f | white | **3.96:1** | ❌ **FAIL** | ✅ | ❌ |
| **Warning as text** | `warning` #ce7046 | white | **3.48:1** | ❌ **FAIL** | ✅ | ❌ |
| **Info as text** | `info` #2e86af | white | **4.08:1** | ❌ **FAIL** | ✅ | ❌ |
| Danger as text | `danger` #754a62 | white | **7.21:1** | ✅ | ✅ | ✅ AAA |
| White on primary (botones) | white | `primary` #0079c2 | **4.65:1** | ✅ (barely) | ✅ | ❌ |
| White on primary-dark (hover) | white | `primary_dark` #0a385e | **12.49:1** | ✅ | ✅ | ✅ |
| Text in cards | `text` | `bg_soft` #f4f5f6 | **10.76:1** | ✅ | ✅ | ✅ |
| Muted in cards | `text_muted` | `bg_soft` | **4.97:1** | ✅ | ✅ | ❌ |
| Chat bubble assistant | `text` | `accent_soft` #b2d4e4 | **7.53:1** | ✅ | ✅ | ✅ |
| Gap badge "alta" | `danger` | `#fdf2f6` (soft) | **6.66:1** | ✅ | ✅ | ❌ |
| **Gap badge "media"** | `warning` | `#fdf4ee` (soft) | **3.18:1** | ❌ **FAIL** | ✅ | ❌ |
| **Gap badge "baja"** | `info` | `#eef6fb` (soft) | **3.77:1** | ❌ **FAIL** | ✅ | ❌ |

### Hallazgos críticos de contraste

| # | Issue | WCAG | Severidad | Fix |
|---|---|---|---|---|
| 1 | **`success` #4b8b7f como texto sobre fondo blanco** falla AA normal text (3.96 vs 4.5 requerido). Usado en `seccion_card.py:71` (label "Completa"), `timeline.py:24` (eventos seccion_editada), múltiples tooltips | 1.4.3 | 🔴 | Reemplazar el verde Pine cuando se use como texto por **Dark Pine `#264640`** (manual SMNYL, paleta dark). Mantener `success` solo para iconos, dots, backgrounds y borders (esos solo requieren 3:1 que sí cumplen) |
| 2 | **`warning` #ce7046 como texto sobre fondo blanco** falla AA normal (3.48 vs 4.5). Usado en `seccion_card.py:71`, badges, `vista_previa.py:42` (border-left de placeholder), múltiples lugares | 1.4.3 | 🔴 | Reemplazar por **Dark Sunset `#544235`** (paleta dark del manual) o calcular un Sunset medio-oscuro custom. Mantener Sunset original solo para fondos/iconos |
| 3 | **`info` #2e86af como texto sobre fondo blanco** falla AA normal (4.08 vs 4.5). Usado en `gap_badge.py` (severidad "baja"), `timeline.py:29` (exportado), `dashboard.py` (estado approved) | 1.4.3 | 🔴 | Reemplazar por **Dark Rain `#0a385e`** (es justo el `primary_dark` que ya tenemos en theme). Para text-on-bg pasa AAA |
| 4 | **Gap badge "media" — warning sobre warning_soft** apenas 3.18:1 | 1.4.3 | 🔴 | Cambiar el `color` a Dark Sunset; el background soft puede quedar igual |
| 5 | **Gap badge "baja" — info sobre info_soft** apenas 3.77:1 | 1.4.3 | 🔴 | Cambiar el `color` a Dark Rain |
| 6 | `primary` #0079c2 sobre white: 4.65:1 — **pasa AA por margen estrecho** pero un usuario con baja visión leve podría tener dificultad | 1.4.3 | 🟡 | Para texto crítico (CTAs principales, links de navegación), preferir `primary_dark` (12.49:1). Mantener `primary` solo para backgrounds de botones y iconos grandes |

**Nota sobre el manual SMNYL:** la paleta oficial sí tiene los "dark" variants que necesitamos (Dark Pine, Dark Sunset, Dark Rain). El problema es que `theme.py` no los expuso. Hay que agregarlos como tokens `success_dark`, `warning_dark`, `info_dark` (que también resuelve el item 7 de la D.2.a auditoría de design system).

---

## 2. Touch Targets (WCAG 2.5.5)

WCAG AA 2.5.5 pide mínimo 44×44 CSS pixels para targets táctiles. Streamlit default:

| Elemento | Tamaño efectivo | Pass 44×44? |
|---|---|---|
| `st.button` default | ~38px alto (padding 0.6rem + line-height) × ancho variable | ❌ alto, ✅ ancho típico |
| `st.button` con icon-only (ej. ✏️) en columna estrecha | ~38px × ~38px | ❌ |
| Breadcrumb buttons (tertiary, recién agregados) | ~24px alto sin padding aplicado por CSS custom | ❌ ❌ |
| File uploader drop zone | ~80px alto | ✅ |
| Checkbox `st.checkbox` | ~20px caja | ❌ (caja chica, pero hit area incluye label) |
| Tabs `st.tabs` headers | ~36px alto | ❌ (apenas debajo) |
| Sidebar collapse button | ~40px | ❌ marginal |

| # | Issue | WCAG | Severidad | Fix |
|---|---|---|---|---|
| 7 | **st.button alto ~38px** está debajo de los 44px requeridos | 2.5.5 | 🟡 Major | CSS custom en `theme.py`: aumentar `padding-block` de `.stButton button` a `0.75rem` para llegar a ~44px. Aplicar globalmente |
| 8 | **Icon-only buttons (`✏️ Editar` en vista_previa)** en columnas estrechas pueden caer por debajo de 44×44 | 2.5.5 | 🟡 Major | Asegurar `min-width: 44px; min-height: 44px` en CSS. O reemplazar emojis por iconos con label oculto (ARIA) |
| 9 | **Breadcrumb buttons (tertiary)** que acabo de implementar son muy pequeños (~24px alto sin padding) | 2.5.5 | 🟡 Major | Aumentar padding del tertiary button en CSS, o cambiar la estrategia: navegación de breadcrumb con `<a>` tags estilizados que tengan al menos 44px de target area |

---

## 3. Keyboard Navigation (WCAG 2.1.1, 2.4.3, 2.4.7)

| # | Issue | WCAG | Severidad | Fix |
|---|---|---|---|---|
| 10 | **Custom HTML divs con `unsafe_allow_html=True` no son focusables** — chat bubbles, timeline items, gap badges, breadcrumb separator. Por suerte ninguno tiene acción (son visual-only) — solo necesitan ARIA si conllevan información significativa | 2.1.1 | 🟢 Minor | Son decorativos. Solo agregar `role="presentation"` o `aria-hidden="true"` para que SR los skipee |
| 11 | **Section cards (`seccion_card.py`)** son visuales — pero conceptualmente representan ítems navegables. Hoy NO son clickeables. Para entrar a una sección hay que ir a entrevista o editor MRM por separado | 2.1.1 | 🟢 Minor | Considerar hacer toda la card clickeable como entry point a la entrevista. Hoy se debe ir a una pantalla aparte |
| 12 | **Focus indicator del default Streamlit button** está OK (outline azul Chrome/FF) pero no es marca SMNYL | 2.4.7 | 🟢 Minor | CSS custom: `.stButton button:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }` |

---

## 4. Form Labels (WCAG 3.3.2, 4.1.2)

| # | Issue | WCAG | Severidad | Fix |
|---|---|---|---|---|
| 13 | **`label_visibility="collapsed"` en varios inputs**: auth_gate password, file uploaders en importar, chat input en entrevista, brief_inicial textareas con la primera columna oculta | 3.3.2 | 🟡 Major | Cambiar a `label_visibility="visible"` siempre; si el label estorba visualmente, ocultarlo solo con CSS (`.visually-hidden { position: absolute; clip: rect(0 0 0 0); }`) que SÍ lo mantiene accesible para SR |
| 14 | **El uploader principal (importar.py:67)** dice `"Arrastra el archivo .docx o .pdf principal aquí"` como label, pero `label_visibility="visible"` está OK. **El segundo uploader (fuentes)** sí tiene `label_visibility="collapsed"` — pierde contexto | 3.3.2 | 🟡 Major | Mismo fix: `visible` siempre |
| 15 | **Captions de Streamlit (`st.caption`)** se renderean como `<p>` con menor tamaño. NO están asociados semánticamente con el input de arriba — un SR no los lee como ayuda del input | 3.3.2 | 🟡 Major | Para captions críticos (ej. "Ambos campos son obligatorios"), usar `st.markdown` con `<small id="help-X">...` + el input con `aria-describedby="help-X"`. Streamlit no facilita esto, requiere `unsafe_allow_html` |

---

## 5. ARIA / Semantics / Robust (WCAG 4.1.2)

| # | Issue | WCAG | Severidad | Fix |
|---|---|---|---|---|
| 16 | **Status dot en SectionCard** (`seccion_card.py:55-58`) es un círculo coloreado puro sin texto adyacente que SR pueda leer. El color comunica el estado — un SR no lo capta | 1.4.1, 4.1.2 | 🟡 Major | Agregar `aria-label="{label}"` al span del dot, o un `<span class="visually-hidden">{label}</span>` antes |
| 17 | **Timeline marker** (`timeline.py:113-121`) — mismo problema: color del marcador indica tipo de evento, sin texto SR | 1.4.1, 4.1.2 | 🟢 Minor | `role="presentation"` ya que el tipo se lee en el header del item. OK como está, pero validar |
| 18 | **Gap badges** indican severidad con color + label texto — el label sí está en el DOM, está OK | 4.1.2 | ✅ | OK |
| 19 | **Páginas con `unsafe_allow_html`** no definen `<main>`, `<nav>`, `<aside>`. SR no tiene landmarks | 1.3.1 | 🟢 Minor | Streamlit no facilita esto. En la migración a Next.js, usar `<main>`, `<nav>`, `<aside>` semánticos |
| 20 | **Imagen del logo SMNYL** (`header.py`) usa `st.image()` que renderea `<img>` sin alt | 1.1.1 | 🟢 Minor | Streamlit `st.image` no permite alt fácil. Workaround: HTML inline con `<img src="..." alt="Seguros Monterrey New York Life">` |

---

## Priority Fixes

### 🔴 Critical (resolver antes de demo formal — bloquea WCAG AA)

1. **Agregar tokens `success_dark`, `warning_dark`, `info_dark`** a `theme.py` (Dark Pine #264640, Dark Sunset #544235, Dark Rain #0a385e). Aplicarlos como TEXTO en `seccion_card`, `gap_badge`, `timeline`, etc. Mantener los originales solo para fondos/iconos/borders.
2. **Fix gap_badge "media" y "baja"**: cambiar el `color` a las variantes dark.
3. **Audit cuando se aplique el theme**: cualquier nuevo uso de `success/warning/info` como `color:` en CSS debe automáticamente usar el `_dark` token.

**Esfuerzo:** 1-2 horas. Es 100% un cambio en tokens + 5-6 reemplazos en componentes.

### 🟡 Major (resolver pre-piloto formal)

4. **CSS de touch targets**: subir el padding-block del `.stButton button` a 0.75rem (~44px). En `theme.py` línea 132.
5. **Visually-hidden labels** en lugar de `label_visibility="collapsed"`. Crear utility class `.visually-hidden` en `theme.py` + helper Python que wrappea `st.text_input` con label visible-pero-oculto-CSS.
6. **ARIA labels en status dots** de SectionCard.
7. **Focus indicator SMNYL** vía `:focus-visible` outline.

**Esfuerzo:** 4-6 horas.

### 🟢 Minor (con la migración a Next.js)

8. **Landmarks semánticos** (`<main>`, `<nav>`, `<aside>`) en Next.js layout.
9. **Alt text del logo**.
10. **Mover focus indicators a tokens de marca**.

---

## Lo que mejora "gratis" con la migración a Next.js + shadcn

shadcn-ui sigue **Radix Primitives** que tiene WCAG AA de fábrica:
- Focus management automático con focus-trap en modals.
- `aria-*` atributos automáticos según role.
- Keyboard nav (arrow keys en menus, escape en dialogs) gratis.
- Componentes con touch targets ya pensados ≥44px.
- Semantic HTML (`<main>`, `<nav>`, `<button>` real en vez de `<div onclick>`).

**Net beneficio accesibilidad** post-migración: los 4 hallazgos Minor + 3 de los Major se resuelven automáticamente. Solo quedan los de contraste (5 críticos) que SON decisión de marca y hay que arreglarlos en CUALQUIER stack.

---

## Recomendación

**Antes de demo formal con MA/Vidal:**
- Fixar los 5 criticos (1-2h) — son no-negociables para AA.
- Fixar los 7 majors (4-6h) — mejora UX para usuarios reales con baja visión / motor limitations / SR users.

**Defer a migración Next.js:**
- Los 4 minors + landmarks semánticos completos. shadcn los resuelve.

Esta evaluación se alimenta del plan dedicado de migración Next.js que viene a continuación.
