# Design System Audit — DocuMente

**Fecha:** 2026-05-19 (D.2.a del plan de remediación S13→S16)
**Alcance:** `src/ui/theme.py`, `src/ui/components/*.py` (10 componentes), `src/ui/pages/*.py` (12 pantallas), `docs/BRAND_GUIDELINES.md`.
**Objetivo:** identificar qué tokens existen, qué está hardcodeado, qué duplicación hay, y qué subset debe sobrevivir a la migración a Next.js + shadcn/cult-ui.

---

## Summary

| Métrica | Valor |
|---|---|
| Tokens definidos en `theme.py` | 9 colores + 2 fuentes + 6 spacings + 3 radii + 3 shadows = **23 tokens** |
| Colores hex hardcoded FUERA de `theme.py` | **5** (en gap_badge, chat_bubble, vista_previa) |
| `font-size`/`padding`/`margin` literales (no tokens) | **102 ocurrencias** en 20 archivos |
| `var(--*)` usados correctamente | **58 ocurrencias** en 15 archivos |
| Componentes con responsabilidad clara | **8/10** |
| Componentes con duplicación de estilo | **3** (badge logic, card pattern, color-by-state) |
| Cobertura de marca SMNYL | **80%** — tokens core sí están; faltan light variants y tipos de elevación |
| **Score global** | **62/100** |

---

## 1. Token Coverage

### Colores (paleta SMNYL)

| Token | Estado | Hardcoded fuera |
|---|---|---|
| `primary` (`#0079c2`) | ✅ definido | — |
| `primary_dark` (`#0a385e`) | ✅ | — |
| `bg` (`#ffffff`) | ✅ | `chat_bubble.py:13` usa `"#ffffff"` literal (redundante) |
| `bg_soft` (`#f4f5f6`) | ⚠️ | El brand guideline dice "Quartz `#bdc1c2` con 10% opacity", pero el theme usa `#f4f5f6` (un gris cualquiera). **Divergencia.** |
| `text` (`#0a3c53`) | ✅ | — |
| `text_muted` (`#565656`) | ✅ | — |
| `border` (`#bdc1c2`) | ✅ | — |
| `success` (`#4b8b7f`) | ✅ | — |
| `warning` (`#ce7046`) | ✅ | — |
| `danger` (`#754a62`) | ✅ | — |
| `info` (`#2e86af`) | ✅ | — |
| `accent_soft` (`#b2d4e4`) | ✅ | — |
| **`success_soft`** | ❌ falta | — |
| **`warning_soft`** | ❌ falta | `gap_badge.py:12` usa `"#fdf4ee"` literal |
| **`danger_soft`** | ❌ falta | `gap_badge.py:11` usa `"#fdf2f6"` literal |
| **`info_soft`** | ❌ falta | `gap_badge.py:13` usa `"#eef6fb"` literal |
| **`amber_soft`** (warm warn) | ❌ falta | `vista_previa.py:54` usa `"#fdf6e3"` literal; `chat_bubble.py:26` usa `"#fef9e7"` literal |

**Hallazgo principal:** los **soft variants** de cada color semántico (success/warning/danger/info) son hardcodeados en 3 componentes distintos. Faltan en `theme.py`.

### Tipografía

| Token | Estado |
|---|---|
| `--font-display` (Georgia) | ✅ definido en `theme.py:31` |
| `--font-body` (Tahoma) | ✅ definido en `theme.py:31` |
| Escala de tamaños (xs/sm/md/lg/xl/2xl) | ❌ **no existe** |
| Pesos (light/regular/medium/bold) | ❌ **no existe** |
| Line-height tokens | ❌ |
| Letter-spacing tokens | ❌ (se usa literal `0.04em`, `0.05em` en 8+ lugares) |

**Hallazgo:** existen los family tokens pero NO la escala. Los `font-size: 0.875rem` / `0.75rem` / `0.95rem` / `1.25rem` se repiten literales por todas las pantallas. **Tabla de frecuencia:**

| Tamaño | Apariciones | Sugerencia |
|---|---|---|
| `0.7rem` | 4 | → `--text-xs` (11px) |
| `0.75rem` | 22 | → `--text-sm` (12px) |
| `0.875rem` | 28 | → `--text-base` (14px) — el más común |
| `0.95rem` | 3 | → eliminar (usar base) |
| `1rem` | implicit default | → `--text-md` (16px) |
| `1.25rem` | 4 | → `--text-lg` (20px) |
| `1.5rem` | 3 | → `--text-xl` (24px) |
| `1.75rem` | 1 | → `--text-2xl` (28px) |
| `2rem` | 2 | → `--text-3xl` (32px) |
| `2.25rem`+ | 4 | → `--text-display` |

### Spacing

| Token | Valor | Estado |
|---|---|---|
| `xs` | 4px | ✅ definido pero **rara vez usado** |
| `sm` | 8px | ✅ |
| `md` | 16px | ✅ |
| `lg` | 24px | ✅ |
| `xl` | 40px | ✅ |
| `2xl` | 64px | ✅ |

**Hallazgo:** los tokens existen pero la mayoría de los CSS literales usan `8px`, `12px`, `4px`, `16px` directamente en lugar de `var(--space-sm)`, etc. **102 instancias** lo confirman.

### Borders + Shadows + Motion

| Categoría | Estado |
|---|---|
| `--radius-sm/md/lg` | ✅ definidos, pero `999px` (pill), `6px`, `4px`, `8px`, `12px`, `16px` aparecen hardcodeados en 11+ lugares |
| `--shadow-sm/md/lg` | ✅ definidos, **nunca usados** en CSS de componentes — todos los componentes con sombra escriben `box-shadow: 0 1px 2px rgba(...)` literal |
| Motion / transitions | ❌ no existe ningún token (`transition: all 150ms ease` aparece literal en `theme.py:137` pero no se reutiliza) |
| Z-index scale | ❌ no existe |

---

## 2. Component Audit

| Componente | Líneas | Responsabilidad | Reuse | Hardcoded | Score |
|---|---|---|---|---|---|
| `header.py` | 165 | Logo + breadcrumbs clickeable | Alta | Spacing literal, font-size literal | 7/10 |
| `back_button.py` | 45 | Botón "Volver" con auto-key | Alta | — | 9/10 |
| `auth_gate.py` | 138 | Password gate temporal | Media (uso único) | rgba shadow literal | 7/10 |
| `seccion_card.py` | 82 | Card con estado de sección | Alta | `width: 10px`, `border-radius: 50%`, font-sizes literales (5) | 6/10 |
| `gap_badge.py` | 35 | Chip de severidad | Alta | **3 fondos hardcoded** (`#fdf2f6`, `#fdf4ee`, `#eef6fb`) — soft variants faltantes | 5/10 |
| `empty_state.py` | 43 | Estado vacío con CTA opcional | Alta | `border-radius: 12px`, `padding: 4rem 2rem` literal | 7/10 |
| `chat_bubble.py` | 66 | Burbuja conversación 3 roles | Alta | **2 colores hardcoded** (`#ffffff`, `#fef9e7`), rgba shadow literal | 6/10 |
| `timeline.py` | 167 | Audit trail vertical | Alta | `width: 2px`, `width: 14px`, font-sizes literales (5) | 7/10 |
| `loading_state.py` | 27 | Spinner con mensaje contextual | Baja (2 helpers) | — | 9/10 |
| `onboarding_banner.py` | 100 | Resumen post-onboarding | Alta | `font-weight: 600`, font-size literales (4) | 7/10 |

### Duplicación detectada

#### Pattern 1: "color por estado" (3 componentes lo reimplementan)

```python
# seccion_card.py:10-15
_COLORS_POR_COMPLETITUD = {
    "vacia": (SMNYL_COLORS["danger"], "Vacía"),
    "parcial": (SMNYL_COLORS["warning"], "Parcial"),
    ...
}

# gap_badge.py:10-14
_COLORS_POR_SEVERIDAD = {
    "alta": (SMNYL_COLORS["danger"], "#fdf2f6", "Crítica"),
    "media": (SMNYL_COLORS["warning"], "#fdf4ee", "Atención"),
    ...
}

# timeline.py:21-32
_ESTILO_POR_TIPO = {
    "documento_creado": (SMNYL_COLORS["primary"], "Documento creado"),
    "seccion_editada": (SMNYL_COLORS["success"], "Sección editada"),
    ...
}
```

**Recomendación:** abstraer a `state_to_color(estado, *, kind="completitud" | "severidad" | "evento") -> (color, soft, label)`. Lo usan 3 componentes + el dashboard inline (`_ETIQUETA_ESTADO`).

#### Pattern 2: "card con border + padding"

Aparece inline en 4+ pantallas con `st.container(border=True)` + markdown HTML. Cada uno tiene su propio padding/margin literal.

**Recomendación:** componente `<Card padding="md" elevation="sm">` con tokens.

#### Pattern 3: "label uppercase muted"

```css
font-size: 0.7rem;
font-weight: 600;
letter-spacing: 0.04em;
text-transform: uppercase;
color: <muted>;
```

Se repite en chat_bubble (label), timeline (tipo), home (Sistema de documentación), dashboard (varios). Es un mini-token tipográfico que merece su propia clase: **`.eyebrow`** o `--type-eyebrow`.

---

## 3. Naming Consistency

| Issue | Detalle |
|---|---|
| ✅ Snake_case en Python | Consistente en toda la app |
| ✅ Tokens en `SMNYL_COLORS` dict | Acceso uniforme con `SMNYL_COLORS["primary"]` |
| ⚠️ Algunos componentes usan `var(--color-primary)`, otros `SMNYL_COLORS["primary"]` | Decidir uno y deprecar el otro. **Recomendación:** CSS vars en HTML inline, Python dict solo cuando se construye lógica (mapas de estado) |
| ⚠️ Tres convenciones de naming de keys de session_state | `mrm_seccion_id`, `documento_actual_id`, `_documente_gate_unlocked` — namespace inconsistente |
| ✅ Componentes nombrados por feature | back_button, gap_badge, chat_bubble, etc. — claros |

---

## 4. Priority Actions (ordenado por ROI)

### **P0 — quick wins, alto impacto** (2-3 horas)

1. **Agregar soft variants al theme** (`success_soft`, `warning_soft`, `danger_soft`, `info_soft`, `amber_soft`). Reemplaza 5 colores hardcoded en `gap_badge`, `chat_bubble`, `vista_previa`.
2. **Agregar escala tipográfica completa** (xs/sm/base/md/lg/xl/2xl/display + weights). Refactor de los `font-size:` literales más comunes (28 instancias del 0.875rem → `var(--text-base)`).
3. **Agregar `--shadow-sm-rgb` y usar los tokens existentes** en `chat_bubble`, `seccion_card`. Quita 4-5 `box-shadow: 0 1px 2px rgba(10,60,83,...)` literales.

### **P1 — abstracciones que pagan dividendos** (4-6 horas)

4. **Helper `state_to_color(estado, kind)`** en `src/ui/theme.py` para unificar los 3 dicts de estado→color. Reduce duplicación + facilita cambios futuros.
5. **Componente `<Card>` reutilizable** con prop `padding`, `elevation`, `border`. Reemplaza 4 patterns inline. Espejo conceptual de shadcn `<Card>`.
6. **Clase utilitaria `.eyebrow`** en theme.py para el patrón uppercase-muted-bold. 4+ usos.

### **P2 — preparación para migración** (no urgente, 1 día)

7. **Exportar tokens a JSON** (`design_tokens.json`) que ambos stacks (Streamlit hoy, Next.js mañana) consuman. Esto desacopla el "qué es la marca" del "qué stack uso".
8. **Documentar cada componente** con props/states/accessibility en un Storybook simple (o markdown estructurado por ahora — Storybook real viene en Next.js).
9. **Agregar tokens de motion** (`--transition-fast: 150ms`, `--transition-slow: 300ms`, `--ease-default: ease-out`). Hoy hay un literal.

---

## 5. Tokens propuestos para migración portable

El JSON siguiente debe servir tanto para Streamlit (vía `theme.py` que lo lee) como para Next.js (vía Tailwind config + shadcn theme).

```json
{
  "color": {
    "primary": { "value": "#0079c2", "type": "color" },
    "primary-dark": { "value": "#0a385e", "type": "color" },
    "bg": { "value": "#ffffff", "type": "color" },
    "bg-soft": { "value": "#f4f5f6", "type": "color", "notes": "diverge del brand: el manual pide Quartz @ 10%" },
    "text": { "value": "#0a3c53", "type": "color" },
    "text-muted": { "value": "#565656", "type": "color" },
    "border": { "value": "#bdc1c2", "type": "color" },
    "success": { "value": "#4b8b7f", "type": "color" },
    "success-soft": { "value": "#e8f1ee", "type": "color" },
    "warning": { "value": "#ce7046", "type": "color" },
    "warning-soft": { "value": "#fdf4ee", "type": "color" },
    "danger": { "value": "#754a62", "type": "color" },
    "danger-soft": { "value": "#fdf2f6", "type": "color" },
    "info": { "value": "#2e86af", "type": "color" },
    "info-soft": { "value": "#eef6fb", "type": "color" },
    "accent-soft": { "value": "#b2d4e4", "type": "color" }
  },
  "font": {
    "display": { "value": "Georgia, 'Times New Roman', serif" },
    "body": { "value": "Tahoma, 'Segoe UI', -apple-system, sans-serif" }
  },
  "fontSize": {
    "xs": { "value": "0.7rem" },
    "sm": { "value": "0.75rem" },
    "base": { "value": "0.875rem" },
    "md": { "value": "1rem" },
    "lg": { "value": "1.25rem" },
    "xl": { "value": "1.5rem" },
    "2xl": { "value": "2rem" },
    "3xl": { "value": "2.25rem" },
    "display": { "value": "3rem" }
  },
  "fontWeight": {
    "regular": { "value": "400" },
    "medium": { "value": "500" },
    "semibold": { "value": "600" },
    "bold": { "value": "700" }
  },
  "lineHeight": {
    "tight": { "value": "1.2" },
    "snug": { "value": "1.4" },
    "normal": { "value": "1.5" },
    "relaxed": { "value": "1.6" }
  },
  "letterSpacing": {
    "tight": { "value": "-0.01em" },
    "normal": { "value": "0" },
    "wide": { "value": "0.04em" },
    "wider": { "value": "0.05em" }
  },
  "space": {
    "xs": { "value": "4px" },
    "sm": { "value": "8px" },
    "md": { "value": "16px" },
    "lg": { "value": "24px" },
    "xl": { "value": "40px" },
    "2xl": { "value": "64px" }
  },
  "radius": {
    "sm": { "value": "4px" },
    "md": { "value": "8px" },
    "lg": { "value": "12px" },
    "pill": { "value": "999px" }
  },
  "shadow": {
    "sm": { "value": "0 1px 2px rgba(10, 60, 83, 0.06)" },
    "md": { "value": "0 4px 12px rgba(10, 60, 83, 0.08)" },
    "lg": { "value": "0 12px 32px rgba(10, 60, 83, 0.12)" }
  },
  "motion": {
    "duration-fast": { "value": "150ms" },
    "duration-slow": { "value": "300ms" },
    "ease-default": { "value": "ease-out" }
  }
}
```

**Path de aplicación:**
- **Streamlit (hoy):** `theme.py` consume el JSON y emite CSS variables. Los componentes Python construyen f-strings con `var(--color-primary)` etc.
- **Next.js (futuro):** `tailwind.config.ts` consume el mismo JSON con `style-dictionary` o `@tokens-studio/sd-transforms`. shadcn `components.json` lee los CSS vars.
- **DOCX (siempre):** el theme.py expone también los valores raw para que `docx_writer.py` los use al escribir runs (que no soportan CSS vars).

---

## 6. Component completeness — gap a shadcn/cult-ui

shadcn provee ~50 componentes battle-tested. Hoy DocuMente tiene **10 wrappers Streamlit**. Para una migración limpia, mapeo conceptual:

| DocuMente actual | Equivalente shadcn/cult-ui | Notas migración |
|---|---|---|
| `back_button` | `<Button variant="ghost">` + icon | Trivial |
| `header` (breadcrumbs) | `<Breadcrumb>` + `<BreadcrumbLink>` | shadcn lo tiene listo |
| `auth_gate` | `<Card>` + `<Input type="password">` | Temporal — desaparece con Cognito |
| `seccion_card` | `<Card>` + `<Badge>` | Composición directa |
| `gap_badge` | `<Badge variant="destructive">` etc. | shadcn ya tiene 4 variants |
| `empty_state` | `<Card>` + `<Button>` con composition | Patrón estándar |
| `chat_bubble` | shadcn no lo tiene → **cult-ui** "Conversation" o custom | Mantener custom |
| `timeline` | shadcn no lo tiene → **cult-ui** "Timeline" o custom | Considerar `magic-ui` Timeline |
| `loading_state` | `<Skeleton>` + `<Spinner>` | shadcn ya |
| `onboarding_banner` | `<Alert>` con variant `success` | shadcn ya |

**Componentes nuevos que shadcn aporta y faltan en DocuMente:**

- `<Toast>` (notificaciones efímeras) — hoy se usa `st.toast` ad-hoc.
- `<Dialog>` con estados controlados — hoy `st.dialog` está OK pero no permite UX avanzada.
- `<Tabs>` (cult-ui tiene una versión animada) — sería ideal para el home post-A.5.
- `<DataTable>` con sort/filter/paginación — el dashboard de docs lo amerita.
- `<Command>` (palette) — para "ir a sección X" sin scroll.
- `<Tooltip>`, `<Popover>`, `<Sheet>` — patrones que hoy se hackean con expanders.

---

## 7. Action plan (siguientes pasos D.2)

Esta auditoría es D.2.a + D.2.d parcial (tokens). Falta:

- **D.2.b** — `design:design-critique` por pantalla (visual issues, hierarchy, contrast).
- **D.2.c** — `design:accessibility-review` (WCAG 2.1 AA, keyboard nav, screen reader).
- **D.2.e** — **plan dedicado de migración Next.js + shadcn/cult-ui** consumiendo este audit + los 2 anteriores.

Si el budget permite, los 2 pendientes (`design-critique` por pantalla + accessibility-review) son de ~1 día. Plan de migración Next.js requiere otro día post-audits.
