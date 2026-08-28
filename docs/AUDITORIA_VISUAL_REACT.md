# Auditoría visual — Frontend Next.js (React)

**Fecha:** 2026-08-28 · **Tipo:** auditoría estática de código (sin app corriendo, sin screenshots)
**Alcance:** `frontend/src/` completo — 19 rutas, 26 componentes, `tailwind.config.ts`, `globals.css`
**Referencias de método:** las 4 auditorías S13 sobre el frontend Streamlit (`docs/superpowers/specs/2026-05-19-*.md`), `docs/BRAND_GUIDELINES.md`, `docs/UX_PRINCIPLES.md`
**Nota de estilo:** en este documento la aseguradora se refiere como **"la institución"**. Los tokens de código usan el prefijo corporativo abreviado (`smnyl-*`); se citan tal cual por precisión técnica.

---

## Resumen ejecutivo

El frontend Next.js **heredó bien lo esencial**: la migración S14 aplicó las lecciones de las auditorías S13. Los tokens `*_dark` y `*_soft` que resolvieron los 5 críticos de contraste de Streamlit **sí existen y se usan correctamente** (`tailwind.config.ts:69-79`); no hay una sola clase genérica de Tailwind (`blue-500`, `gray-*`, `slate-*`) en todo el código; hay skeletons, toasts con "Deshacer", agrupación por capítulos, ContinueHero, stepper y microinteracciones de 200ms. La base es sólida.

Lo que **sí está roto o falta** se concentra en tres frentes:

1. **Confianza enterprise**: breadcrumb estático que siempre dice "Inicio", tres botones muertos en el topbar, un indicador "API conectada" hardcodeado en verde, y cero navegación en pantallas <1024px.
2. **Detalles de marca sin cerrar**: checkboxes y selects nativos del sistema operativo (el plugin que los tematiza no está instalado), 8 hex hardcodeados, una clase de animación inválida, y la ausencia del logo institucional en toda la app.
3. **Estados de error**: 4 páginas enmascaran errores de API como "no hay datos" y 5 muestran texto crudo sin CTA.

**Conteo: 6 P0 · 12 P1 · 9 P2 = 27 hallazgos.**

---

## 1. Fidelidad de marca

### 1.1 Hex hardcodeados fuera de `tailwind.config.ts`

Grep de `#[0-9a-fA-F]{3,8}` sobre `frontend/src/**/*.tsx` — solo 8 ocurrencias (excelente disciplina general):

| Archivo:línea | Valor | Problema |
|---|---|---|
| `frontend/src/components/dashboard/metrics-row.tsx:69` | `#0079c2` | Duplica `smnyl.primary`; pasa por prop `accent` como string |
| `frontend/src/components/dashboard/metrics-row.tsx:76` | `#754a62` | Duplica `smnyl.danger` |
| `frontend/src/components/dashboard/metrics-row.tsx:82` | `#544235` | Duplica `smnyl.warning-dark` |
| `frontend/src/components/dashboard/metrics-row.tsx:88` | `#0a385e` | Duplica `smnyl.info-dark` |
| `frontend/src/components/dashboard/metrics-row.tsx:94` | `#565656` | Duplica `smnyl.text-muted` |
| `frontend/src/app/documentos/[id]/vista-previa/page.tsx:184` | `#fdf4ee` | Inline style; existe `bg-smnyl-warning-soft` |
| `frontend/src/app/documentos/[id]/vista-previa/page.tsx:185` | `#544235` | Inline style; existe `border-smnyl-warning-dark` |
| `frontend/src/components/home/continue-hero.tsx:31` | `rgba(0,121,194,0.06)` | Primario en rgba dentro de un `bg-[radial-gradient(...)]` arbitrario |

Los valores **coinciden** con los tokens (no hay drift de color), pero bypasean la fuente única: un rebrand no los alcanzaría. Fix: en `metrics-row` pasar clases o leer de un mapa tipado; en `vista-previa` usar las clases utilitarias que ya existen.

*(Exclusión legítima: `frontend/src/app/icon.svg:2` usa `#0079c2` literal — un favicon no puede consumir CSS vars.)*

### 1.2 Clases genéricas de Tailwind

**Cero ocurrencias** de `bg|text|border-{slate,gray,zinc,blue,red,green,...}-N` en todo `frontend/src`. Todos los colores pasan por `smnyl-*` o por los tokens semánticos shadcn (`bg-background`, `text-foreground`). Este es el mejor resultado de toda la auditoría.

Único gris no-token: `bg-white` / `text-white` usados extensamente (aceptable — blanco es color primario de la paleta), y `border-white` en `timeline.tsx:174` (anillo del marcador, correcto).

### 1.3 Tipografías

**Correctamente configuradas y aplicadas.** No quedó la fuente default de shadcn/Next:

- `tailwind.config.ts:85-86` define `font-display: Georgia` y `font-body: Tahoma` (los reemplazos oficialmente autorizados por el manual, p. 75).
- `globals.css:57` aplica `font-body` al `body`; `globals.css:61` aplica `font-display` a todos los headings con `letter-spacing: -0.015em`.
- Los toasts de Sonner reciben `font-body` explícito (`providers.tsx:33`).
- No hay `next/font` ni imports de Inter — consistente con la decisión de fuentes nativas del sistema.

Dos matices:

1. **`Textarea` fuerza `font-mono` por default** (`frontend/src/components/ui/textarea.tsx:15`). Correcto para el editor markdown y LaTeX, pero los campos de prosa de onboarding ("Uso intencionado", "Restricciones" — `onboarding/page.tsx:146-150`) y metadata heredan monospace y rompen la voz tipográfica. Brief y entrevista lo corrigen con `font-body` manual (`brief/page.tsx:101`, `entrevista/[sid]/page.tsx:246`), evidencia de que el default está invertido: mono debería ser opt-in.
2. Tahoma no tiene cursiva real — los `italic` de `timeline.tsx:185`, `versiones/page.tsx:179` y otros se sintetizan por el browser (oblicua falsa). Menor, pero visible en un ojo entrenado.

### 1.4 Logo y favicon

- **El logo institucional no aparece en ninguna parte de la app.** `frontend/src/components/layout/brand-logo.tsx` es un logo custom del producto (cerebro + libro sobre gradiente azul) — bien ejecutado como identidad de producto, pero `BRAND_GUIDELINES.md` §5 pide el logo institucional en el header sobre fondo blanco, ≥2.5cm. Hoy solo el DOCX exportado lleva el logo real. Es una **decisión de marca sin documentar**: o se formaliza que la app usa branding de producto propio (y se anota en BRAND_GUIDELINES), o se incorpora el logo institucional (existe en `assets/`) al sidebar o al footer.
- **Favicon:** `frontend/src/app/icon.svg` replica el mismo logo custom sobre cuadrado `#0079c2` con `rx=6` — consistente con el sidebar. ✓ No hay favicon default de Next.
- El gradiente del contenedor del logo (`brand-logo.tsx:22`, `from-smnyl-primary to-smnyl-primary-dark`) técnicamente contradice el "no gradientes en el logo" del manual — defendible porque es el logo del producto, no el institucional; documentar junto con la decisión anterior.

---

## 2. Contraste WCAG 2.1 AA

Ratios calculados con la fórmula de luminancia relativa sRGB (WCAG). Umbrales: 4.5:1 texto normal, 3:1 texto grande (≥18pt / ≥14pt bold) y componentes UI (1.4.11).

### 2.1 La regresión que NO ocurrió

Las auditorías S13 encontraron que `success` (3.96:1), `warning` (3.48:1) e `info` (4.08:1) **fallan AA como texto** sobre blanco, y la solución fue crear variantes `*_dark`. **El frontend Next las tiene y las usa bien**:

- `tailwind.config.ts:70,73,78` define `success-dark #264640`, `warning-dark #544235`, `info-dark #0a385e` (+ los `*-soft` de fondo).
- Todos los badges usan la variante dark como texto: `badge.tsx:23-29` (atención, sugerencia, review, approved, published).
- Los colores medios quedan relegados a iconos, dots y fills — que solo requieren 3:1 y lo cumplen.

### 2.2 Matriz de contraste calculada (combinaciones reales del código)

| Combinación (uso) | Ratio | AA texto | Veredicto |
|---|---|---|---|
| Steel `#0a3c53` / blanco (texto cuerpo) | **11.77:1** | ✓ AAA | ✓ |
| Iron `#565656` / blanco (muted) | **7.34:1** | ✓ AAA | ✓ |
| Blanco / primario `#0079c2` (botón default, `button.tsx:29`) | **4.65:1** | ✓ | ⚠️ pasa por margen estrecho (heredado S13 #6); el hover a `primary-dark` sube a 12.07:1 |
| Primario como texto/link sobre blanco | **4.65:1** | ✓ | ⚠️ mismo margen |
| Blanco / `primary-dark #0a385e` (hover) | **12.07:1** | ✓ AAA | ✓ |
| Danger `#754a62` / blanco | **7.21:1** | ✓ AAA | ✓ |
| Danger / `danger-soft #fdf2f6` (badge crítica, `badge.tsx:22`) | **6.60:1** | ✓ | ✓ |
| `warning-dark` / `warning-soft` (badges atención/review/Beta, `badge.tsx:23,27`, `sidebar.tsx:101`) | **8.77:1** | ✓ AAA | ✓ |
| `info-dark` / `info-soft` (badges sugerencia/approved, `badge.tsx:24,28`) | **11.04:1** | ✓ AAA | ✓ |
| `success-dark` / `success-soft` (badge published, `badge.tsx:29`) | **8.92:1** | ✓ AAA | ✓ |
| Iron / `bg-soft #f4f5f6` (badge draft, chips) | **6.72:1** | ✓ | ✓ |
| Blanco / `success-dark` (stepper completado, `stepper.tsx:33`) | **10.33:1** | ✓ AAA | ✓ |
| Steel / burbuja assistant `accent-soft/50` (~`#d7e8f0` efectivo, `chat-bubble.tsx:28`) | **9.35:1** | ✓ AAA | ✓ |
| `warning-dark` / `warning-soft` (system_note, `chat-bubble.tsx:35`) | **8.77:1** | ✓ | ✓ |
| **Border Quartz `#bdc1c2` / blanco** (inputs `input.tsx:13`, `textarea.tsx:12`, selects) | **1.81:1** | — | ❌ **FALLA 1.4.11** (límite de componente UI requiere 3:1; el border es la única frontera del input sobre página blanca) |
| **Placeholder `text-muted/60`** (~`#9a9a9a`, `input.tsx:14`, `textarea.tsx:14`) | **2.81:1** | ❌ | ⚠️ los placeholders con label visible tienen exención parcial, pero varios placeholders llevan contenido instructivo real (`brief/page.tsx:89-98`) |
| **Marker "◐" `text-smnyl-warning`** (`secciones-accordion.tsx:53` vía `:116`) | **3.48:1** | ❌ | ⚠️ glifo de texto a 16px; mitigado porque "X de Y resueltas" repite la información al lado |
| Iconos `success`/`warning`/`info` medios sobre blanco (3:1 para no-texto) | 3.96 / 3.48 / 4.08 | — | ✓ como iconos |

**Conclusión:** un solo fallo AA duro (border de inputs, 1.4.11), dos advertencias de bajo riesgo, y el margen estrecho del botón primario que ya estaba documentado en S13. Fix del border: oscurecer el token de borde de *formularios* a Slate `#92999a` (3.06:1 — justo pasa) o a un gris ~`#8a9194`; mantener Quartz para divisores decorativos (cards sobre `bg-soft`, separadores), que no requieren 3:1.

---

## 3. Consistencia de sistema

### 3.1 Escala tipográfica

**Existe a nivel macro, se fragmenta a nivel micro:**

- ✓ Macro consistente: títulos de página `text-3xl` + `font-display` en las 13 rutas; jerarquía h1/h2/h3 global en `globals.css:65-67`; `text-sm` como cuerpo default, `text-xs` para metadata.
- ❌ Micro fragmentado: **4 tamaños arbitrarios sub-`xs`** repetidos en 13 sitios: `text-[0.65rem]` (chat-bubble:47, sidebar:55,98, quick-links:47, secciones-accordion:191, entrevista:178), `text-[0.68rem]` (globals.css:74, metrics-row:34), `text-[0.7rem]` (continue-hero:33, sidebar:115, apendices:418, versiones:180), `text-[0.78rem]` (metrics-row:48). Es el patrón "eyebrow" (uppercase + bold + tracking) que la auditoría de design system S13 ya había identificado como token faltante — **heredado sin resolver**. Fix: `fontSize: { "2xs": "0.7rem", "3xs": "0.65rem" }` en el config + una utility `.eyebrow`.
- ⚠️ `tracking` también arbitrario: `tracking-[0.12em]` (continue-hero:33), `tracking-[0.07em]` (metrics-row:34) conviviendo con `tracking-wider` (~12 usos). Tokenizar letterSpacing.

### 3.2 Espaciado

**Grid de 4px respetado.** El muestreo de todas las páginas solo encuentra la escala estándar de Tailwind (`p-4/5/6`, `gap-2/3/4`, `space-y-*`, `mb-1/2/3/4/8`). Sin valores arbitrarios de spacing (`p-[...]`). Ritmo vertical de páginas consistente (`space-y-6` casi universal; home usa `space-y-4`, dashboard `space-y-8` — variación menor y deliberada). ✓

### 3.3 Radios y sombras

- Radios: sistema coherente por capa — inputs/botones `rounded-md` (6px), cards `rounded-lg` (8px = `--radius`), dropzones/heros `rounded-xl` (12px), burbujas de chat `rounded-2xl` (16px), pills `rounded-full`. Coincide con UX_PRINCIPLES §8. Solo falta **documentarlo como escala** (hoy `xl`/`2xl` dependen del default de Tailwind, no del token `--radius`).
- Sombras: **3 tokens propios usados de forma disciplinada** (`shadow-smnyl-sm/md/lg`, `tailwind.config.ts:93-97`); no hay ni un `box-shadow` literal en componentes. ✓ Mejora clara vs Streamlit (donde los tokens existían pero nunca se usaban).
- **Bug de animación:** `frontend/src/components/ui/progress.tsx:21` usa `duration-400`, **clase que no existe en Tailwind 3** (la escala salta de 300 a 500). La clase se descarta silenciosamente y la barra de progreso anima con el default (~150ms) en lugar de los 400ms diseñados. Fix: `duration-500` o definir `transitionDuration: { "400": "400ms" }`.

### 3.4 Componentes shadcn sin theming

Auditados los 13 primitivos de `frontend/src/components/ui/`:

| Componente | Theming | Nota |
|---|---|---|
| button, badge, card, input, textarea, label, tabs, accordion, skeleton, separator, progress, dropdown-menu, stepper | ✓ paleta institucional completa | Ninguno quedó con el look default de shadcn |
| **`<select>` nativo** | ❌ | No hay `select.tsx`; `apendices/page.tsx:304-319` y `metadata/page.tsx:187-207` usan `<select>` HTML con border/focus tematizados pero **appearance, flecha y popup del sistema operativo** — la pieza más "no-enterprise" visible en formularios. `@radix-ui/react-popover` ya está instalado; adoptar el Select de shadcn |
| **`<input type="checkbox">` nativo** | ❌ | `importar/page.tsx:190-194` y `crear/page.tsx:287-292` usan clases de `@tailwindcss/forms` (`text-smnyl-primary focus:ring-smnyl-primary`) **pero el plugin no está instalado** (`package.json:41-53` solo tiene typography + animate) → las clases no hacen nada y el checkbox se pinta con el azul default del OS. Fix mínimo: `accent-smnyl-primary` (utility core de Tailwind, sin plugin); fix completo: Checkbox de shadcn |
| Dialog / Tooltip / Toast / Popover (radix) | — | Instalados en `package.json:17-25` y **sin componente ni uso** (ver §5) |

### 3.5 Duplicación de patrones

- Los mapas estado→estilo (`ESTADO_VARIANT`/`ESTADO_LABEL`) están duplicados en `document-card.tsx:32-48` y `dashboard-hero.tsx:59-76`; `SeccionRow` reimplementa un tercer mapa inline (`secciones-accordion.tsx:172-180`) en vez de usar `<Badge>`. Heredado del "Pattern 1: color por estado" de S13 — extraer a `lib/estado-ui.ts`.
- `DropZone` + `FilePreview` + `DropZoneContent` existen **tres veces**: el componente compartido (`upload/dropzone.tsx`) y copias locales en `importar/page.tsx:230-303` y `prophet/page.tsx:282-365`. El comentario de `dropzone.tsx:4-5` dice que se extrajo para reuso — la extracción quedó a medias.

---

## 4. Estados de interfaz por página

✓ = existe y con calidad · ⚠️ = existe pero incompleto · ✗ = falta o roto · — = no aplica

| Página | Vacío | Loading | Error |
|---|---|---|---|
| `/` Home (`page.tsx`, `document-list.tsx`) | ⚠️ EmptyPane con ilustración pero **sin botón CTA** (`document-list.tsx:133-142`; UX_PRINCIPLES exige CTA) | ✓ skeletons (hero :37, lista :63-68) | ✓ card de error con instrucción (`document-list.tsx:72-84`) |
| `/importar` | — | ⚠️ spinner + toast "~10 min" estático (`importar/page.tsx:57-60`) — **sin progreso SSE** que `/crear` sí tiene; violación Doherty heredada de S13 | ✓ toast |
| `/documentos/crear` | — | ✓ **el mejor de la app**: ProgressPanel SSE con fases, ETA y lista animada de secciones (`crear/page.tsx:325-407`) | ✓ fase error + toast |
| `/prophet` | ⚠️ "No se detectaron modelos" solo texto (`prophet/page.tsx:171-176`) | ✓ toasts loading | ✓ toast |
| `/documentos/[id]` dashboard | — | ✓ skeletons con forma (`[id]/page.tsx:29-41`) | ✓ **patrón de referencia**: card + icono + CTA "Volver a Inicio" (`[id]/page.tsx:43-58`) |
| `/documentos/[id]/entrevista/[sid]` | ✓ EmptyState con preguntas guía + CTA (`entrevista/[sid]/page.tsx:270-317`) | ✓ skeleton + typing indicator (:175-194) | ✗ `<p>` crudo sin CTA (:68-72) |
| `/documentos/[id]/secciones/[sid]` | ✓ placeholder del preview (:132-136) | ✓ skeletons (:40-48) | ⚠️ card sin CTA (:50-58) |
| `/documentos/[id]/vista-previa` | ✓ placeholder por sección con instrucción (:180-193) | ✓ skeleton (:49-51) | ✗ `<p>` crudo (:53-57) |
| `/documentos/[id]/versiones` | ⚠️ empty ilustrado sin CTA (:247-258) | ✓ skeletons (:160-165) | ✗ **error enmascarado como vacío** (:166 — si la query falla, `data` undefined cae al empty "Sin versiones todavía") |
| `/documentos/[id]/versiones/[n]/vista-previa` | — | ✓ skeleton (:28-30) | ✓ card (:32-40) |
| `/documentos/[id]/auditoria` | ✓ empty del timeline (`timeline.tsx:147-155`) | ✓ skeletons (:45-50) | ✗ **error enmascarado**: `auditQuery.data ?? []` (:52) muestra "Aún no hay eventos" ante un fallo de API — mensaje falso en la pantalla de *cumplimiento* |
| `/documentos/[id]/apendices` | ⚠️ empty solo texto (:99-104) | ✓ skeletons (:85-86) | ✗ **enmascarado** (:87-99, mismo patrón) |
| `/documentos/[id]/metadata` | — | ✓ skeleton (:53-55) | ✗ `<p>` crudo (:57-61) |
| `/documentos/[id]/onboarding` | — | ✓ skeleton (:80-82) | ✗ inexistente — sin guard de `!data`, renderiza el form vacío. Además la hidratación está rota: `useState(() => {...})` como pseudo-effect (:45-55) corre **antes** de que llegue la data → los campos existentes nunca se rellenan |
| `/documentos/[id]/brief` | — | ✗ sin guard de loading (usa `docQuery` solo al guardar) | ✓ toast |
| `/ayuda`, `/configuracion` | — | ✓ (config: health check en vivo, `configuracion/page.tsx:52-65`) | ✓ (config muestra "Desconectada") |

**Patrones a estandarizar:** un componente `<ErrorState>` (clonando el del dashboard) y añadir la rama `query.error` en auditoría/versiones/apéndices. Los tres "enmascarados" son el mismo bug de un solo patrón (`data ?? []` / `data && length`).

---

## 5. Patrones premium — presentes y faltantes

**Presentes (verificados en código):**
- Microinteracciones consistentes: `transition-all duration-200 ease-out` en los 13 primitivos; hover lift en botones (`hover:-translate-y-px`, `button.tsx:29`) y cards (`.smnyl-card-hover`, `globals.css:77-80`); `animate-fade-in` (200ms) en secciones de página; accordion animado; dropdown con zoom/slide (`dropdown-menu.tsx:32-35`); ping en el dot de estado (`sidebar.tsx:117`); typing indicator de 3 puntos (`entrevista:181-191`).
- Toasts con acción "Deshacer" en archivar/papelera (`document-card.tsx:95-100,115-121`) — patrón moderno correcto.
- Focus visible de marca en primitivos: `focus-visible:ring-2 ring-ring` en button/input/textarea/tabs/badge (`--ring` = primario, `globals.css:42`). ✓
- Confirmaciones inline con explicación de consecuencias en restaurar versión (`versiones:186-213`) y sign-off (`governance-card.tsx:162-184`). ✓

**Faltantes:**

1. **Dark mode: no existe.** `darkMode: ["class"]` está configurado (`tailwind.config.ts:14`) pero hay **0** clases `dark:` en `frontend/src`, ningún bloque de variables dark en `globals.css` y ningún toggle. No es regresión (Streamlit tampoco lo tenía), pero es una decisión sin tomar: o se declara "solo light" en BRAND_GUIDELINES, o se implementa (la arquitectura HSL-vars de `globals.css:14-45` lo deja a ~1 día de trabajo).
2. **Sin navegación en móvil/tablet:** el sidebar es `hidden lg:flex` (`sidebar.tsx:50`) y **no hay hamburguesa ni alternativa** — debajo de 1024px desaparecen Importar, Crear, Prophet, Configuración y Ayuda; solo se navega por URL directa. El resto del responsive es correcto pero mínimo: 16 usos de breakpoints en 12 archivos, casi todos grids `md:`/`lg:`; la entrevista fija `h-[calc(100vh-8rem)]` (`entrevista:120`) sin ajuste móvil.
3. **Focus visible incompleto fuera de primitivos:** los `<Link>` crudos (items del sidebar `sidebar.tsx:83-91`, quick-links, breadcrumb, título de DocumentCard) y las dropzones `role="button"` (`importar:230-257`, `prophet:297-323`, `dropzone.tsx:78-101`) no definen `focus-visible:` — queda el outline default del browser, no el outline 2px primario que pide UX_PRINCIPLES §Accesibilidad.
4. **aria-labels:** bien en topbar (:44-50) y botones "Quitar archivo"; los icon-only de archivar/papelera usan `title=` sin `aria-label` (`document-card.tsx:89,110`) — funciona como nombre accesible pero es frágil; unificar con `aria-label` + Tooltip real.
5. **`confirm()` nativo del navegador** en descartar entrevista (`entrevista/[sid]/page.tsx:113`) — el único diálogo del sistema en toda la app; rompe la ilusión enterprise y viola el principio de confirmaciones con explicación. `@radix-ui/react-dialog` ya está instalado.
6. **Dependencias premium instaladas y sin usar:** `framer-motion` (0 imports), `@radix-ui/react-dialog`, `-popover`, `-tooltip`, `-toast` (`package.json:17-30`) — o se usan (dialog para confirmaciones, tooltip para icon-buttons) o se eliminan; hoy son peso muerto que sugiere intención inconclusa.
7. **Peak-end sin celebración** (heredado S13): exportar DOCX termina en un toast (`dashboard-hero.tsx:102`); el momento clímax del flujo no se distingue de "metadata guardada".
8. **Señales falsas:** "API conectada" hardcodeado en verde (`sidebar.tsx:111-123`, el propio comentario lo admite) aunque el backend esté caído — y `configuracion` demuestra que el health check real ya existe (`configuracion/page.tsx:18-22`); reutilizarlo. Botones Buscar/Notificaciones/Perfil sin handler (`topbar.tsx:44-52`) — affordances muertas.
9. **Breadcrumb estático:** `layout.tsx:34` monta `<Topbar />` sin props y el default es siempre `[{ label: "Inicio" }]` (`topbar.tsx:23`) — en las 12 rutas interiores el breadcrumb miente. Cada página compensa con su propio botón "Volver" (patrón repetido 11 veces). Sincronizar con `usePathname()` + nombre del documento elimina ambos problemas.
10. **Tabs sin contador** (heredado S13 Home #2): Activos/Archivados/Papelera sin `(n)` (`document-list.tsx:30-42`).

---

## 6. Propuesta `design_tokens.json`

Tokenización completa propuesta como **fuente única stack-agnóstica**. No crear el archivo aún — este bloque es la especificación. Consumo: `tailwind.config.ts` lo importa directo (`import tokens from "./design_tokens.json"`); `globals.css` deriva los HSL de shadcn; `theme.py` (Streamlit legacy) y `docx_writer` leen los mismos valores raw.

```json
{
  "$schema": "design-tokens/v1",
  "meta": {
    "brand": "institucional",
    "nota": "Fuente única de marca. Para rebrand: editar SOLO este archivo + los 4 assets listados en meta.rebrand_files.",
    "rebrand_files": [
      "design_tokens.json",
      "frontend/src/app/icon.svg",
      "frontend/src/components/layout/brand-logo.tsx",
      "src/docs/templates/model_development_smnyl.docx"
    ]
  },
  "color": {
    "primary": {
      "50":  "#f0f8fd",
      "100": "#d9edf9",
      "200": "#b2d4e4",
      "300": "#7cc2e9",
      "400": "#3fa3da",
      "500": "#0079c2",
      "600": "#00689f",
      "700": "#2e86af",
      "800": "#0a385e",
      "900": "#072a45",
      "_notas": "500 = azul corporativo oficial; 200 = Light Rain oficial; 700 = Medium Rain oficial; 800 = Dark Rain oficial. 50/100/300/400/600/900 son interpolaciones para hovers, fondos y estados que hoy se resuelven con /opacity ad-hoc."
    },
    "neutral": {
      "bg": "#ffffff",
      "bg-soft": "#f4f5f6",
      "border": "#bdc1c2",
      "border-input": "#8a9194",
      "slate": "#92999a",
      "text-muted": "#565656",
      "text": "#0a3c53",
      "_notas": "border-input es NUEVO: cumple 3:1 (WCAG 1.4.11) para límites de formularios; border (Quartz) queda solo para divisores decorativos."
    },
    "estado": {
      "success": { "base": "#4b8b7f", "texto_aa": "#264640", "soft": "#e8f0ee" },
      "warning": { "base": "#ce7046", "texto_aa": "#544235", "soft": "#fdf4ee" },
      "danger":  { "base": "#754a62", "texto_aa": "#754a62", "soft": "#fdf2f6" },
      "info":    { "base": "#2e86af", "texto_aa": "#0a385e", "soft": "#eef6fb" },
      "_regla": "base → iconos, dots, borders, fills (≥3:1). texto_aa → cualquier glifo de texto (≥4.5:1, verificado: 8.92 / 8.77 / 6.60 / 11.04 sobre su soft). soft → solo fondos."
    },
    "accent-soft": "#b2d4e4"
  },
  "font": {
    "display": "Georgia, 'Times New Roman', serif",
    "body": "Tahoma, 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
    "mono": "ui-monospace, 'Cascadia Code', Consolas, monospace",
    "_notas": "Al licenciar las tipografías corporativas oficiales, se antepone cada una a su stack; el resto no cambia."
  },
  "fontSize": {
    "3xs": ["0.65rem", { "lineHeight": "1rem" }],
    "2xs": ["0.7rem",  { "lineHeight": "1rem" }],
    "xs":  ["0.75rem", { "lineHeight": "1rem" }],
    "sm":  ["0.875rem", { "lineHeight": "1.25rem" }],
    "base": ["1rem",   { "lineHeight": "1.5rem" }],
    "lg":  ["1.125rem", { "lineHeight": "1.75rem" }],
    "xl":  ["1.25rem", { "lineHeight": "1.75rem" }],
    "2xl": ["1.5rem",  { "lineHeight": "2rem" }],
    "3xl": ["1.875rem", { "lineHeight": "2.25rem" }],
    "4xl": ["2.25rem", { "lineHeight": "2.5rem" }],
    "_notas": "3xs y 2xs son NUEVOS: absorben los text-[0.65rem]/[0.68rem]/[0.7rem]/[0.78rem] arbitrarios (13 sitios)."
  },
  "letterSpacing": {
    "tight": "-0.015em",
    "normal": "0",
    "wide": "0.05em",
    "eyebrow": "0.1em",
    "_notas": "eyebrow absorbe tracking-[0.07em]/[0.12em]/tracking-wider del patrón uppercase-muted."
  },
  "space": { "base": "4px", "escala": [4, 8, 12, 16, 20, 24, 32, 40, 64], "_notas": "Grid de 4px; ya se cumple — solo se formaliza." },
  "radius": {
    "sm": "4px", "md": "6px", "lg": "8px", "xl": "12px", "2xl": "16px", "pill": "9999px",
    "_asignacion": "md=inputs/botones · lg=cards · xl=dropzones/heros · 2xl=burbujas chat · pill=badges"
  },
  "shadow": {
    "sm": "0 1px 2px rgba(10,60,83,0.05), 0 1px 1px rgba(10,60,83,0.03)",
    "md": "0 4px 12px rgba(10,60,83,0.08), 0 2px 4px rgba(10,60,83,0.04)",
    "lg": "0 16px 40px rgba(10,60,83,0.14), 0 4px 8px rgba(10,60,83,0.06)",
    "_notas": "Los valores actuales de tailwind.config.ts:93-97 — ya correctos, solo se centralizan. El rgba está anclado a Steel: en rebrand se regenera del color text."
  },
  "motion": {
    "duration": { "fast": "150ms", "base": "200ms", "slow": "300ms", "progress": "400ms" },
    "ease": { "out-smooth": "cubic-bezier(0.4, 0, 0.2, 1)" },
    "_notas": "duration.progress corrige el duration-400 inválido de progress.tsx:21."
  }
}
```

**Alcance de un rebrand completo** (para otra instancia de la institución o cambio de identidad):

| Qué tocar | Archivo(s) | Esfuerzo |
|---|---|---|
| Paleta + tipografías + sombras | `design_tokens.json` (único punto si §1.1 se corrige antes) | 30 min |
| Consumidores automáticos | `frontend/tailwind.config.ts` (importa el JSON), `frontend/src/app/globals.css` (regenerar HSL shadcn), `src/ui/theme.py` (legacy) | 1 h |
| Logo de producto | `frontend/src/components/layout/brand-logo.tsx` (SVG inline) | según diseño |
| Favicon | `frontend/src/app/icon.svg` (hex literal inevitable) | 15 min |
| Plantilla Word del export | `src/docs/templates/model_development_smnyl.docx` (estilos, logo, header/footer — se edita en Word) | 2-4 h |
| Hex residuales (hasta corregir §1.1) | `metrics-row.tsx:69-94`, `vista-previa/page.tsx:184-185`, `continue-hero.tsx:31` | 30 min |
| Textos con nombre de marca en UI | `layout.tsx:16-18` (metadata/title), `sidebar.tsx:56`, strings "template oficial" en welcome-hero/ayuda | 30 min |

---

## 7. Priorización

### P0 — marca o accesibilidad rotas (≈1 día)

| # | Hallazgo | Archivo:línea | Fix |
|---|---|---|---|
| 1 | Border de inputs 1.81:1 — falla WCAG 1.4.11 | `ui/input.tsx:13`, `ui/textarea.tsx:12`, `apendices:308`, `metadata:189` | Nuevo token `border-input` ≈ `#8a9194` (≥3:1) solo para formularios |
| 2 | Checkboxes sin tematizar (clases de plugin no instalado → azul default del OS) | `importar/page.tsx:190-194`, `crear/page.tsx:287-292`, `package.json` | Quitar clases muertas; `accent-smnyl-primary` (core Tailwind) o Checkbox shadcn |
| 3 | Sin navegación <1024px (sidebar `hidden lg:flex`, sin hamburguesa) | `layout/sidebar.tsx:50`, `layout/topbar.tsx` | Sheet/drawer móvil con la misma nav, trigger en topbar |
| 4 | Breadcrumb estático — todas las rutas dicen "Inicio" | `app/layout.tsx:34`, `layout/topbar.tsx:23` | Derivar de `usePathname()` + nombre de documento (context o query cacheada) |
| 5 | "API conectada" hardcodeado en verde | `layout/sidebar.tsx:111-123` | Reusar el health check de `configuracion/page.tsx:18-22` con `useQuery` |
| 6 | Botones muertos Buscar/Notificaciones/Perfil | `layout/topbar.tsx:43-53` | Ocultar hasta que existan (o cablear búsqueda como command palette) |

### P1 — consistencia de sistema (≈2-3 días)

| # | Hallazgo | Archivo:línea | Fix |
|---|---|---|---|
| 7 | 8 hex/rgba hardcodeados | `metrics-row.tsx:69-94`, `vista-previa:184-185`, `continue-hero.tsx:31` | Clases de token / mapa tipado |
| 8 | `duration-400` inválido — progress anima a 150ms | `ui/progress.tsx:21` | `duration-500` o token `motion.duration.progress` |
| 9 | `<select>` nativos con appearance del OS | `apendices:304-319`, `metadata:187-207` | Select shadcn (popover ya instalado) |
| 10 | `Textarea` default `font-mono` en campos de prosa | `ui/textarea.tsx:15`; víctimas: `onboarding:146-163`, `metadata` | Default `font-body`; mono opt-in en editor/LaTeX |
| 11 | `confirm()` nativo del navegador | `entrevista/[sid]/page.tsx:113` | Dialog shadcn con explicación de consecuencias |
| 12 | Errores de API enmascarados como estado vacío | `auditoria:52`, `versiones:166`, `apendices:87-99` | Rama `query.error` con componente `<ErrorState>` |
| 13 | Errores crudos sin CTA (vs patrón correcto del dashboard `[id]/page.tsx:43-58`) | `entrevista:68-72`, `vista-previa:53-57`, `secciones:50-58`, `metadata:57-61` | Extraer `<ErrorState>` reutilizable |
| 14 | Onboarding: hidratación rota (`useState` como pseudo-effect) + sin guard de error | `onboarding/page.tsx:45-55` | `useEffect` con flag `initialized` (patrón ya usado en `metadata:46-51`) |
| 15 | Importar sin progreso SSE (toast "~10 min" estático) | `importar/page.tsx:57-60` | Reusar ProgressPanel + stream de `crear/page.tsx:325-407` |
| 16 | Escala micro-tipográfica arbitraria (13 sitios) + tracking arbitrario | ver §3.1 | Tokens `2xs`/`3xs` + utility `.eyebrow` |
| 17 | Empty states sin CTA | `document-list.tsx:133-142`, `versiones:247-258`, `apendices:99-104`, `prophet:171-176` | Botón de acción por contexto ("Crear documento", "Crear versión", etc.) |
| 18 | Logo institucional ausente en la app (solo logo custom de producto) | `layout/brand-logo.tsx` | Decisión de marca: documentar branding de producto o añadir logo institucional al shell |

### P2 — polish (backlog)

| # | Hallazgo | Archivo:línea | Fix |
|---|---|---|---|
| 19 | Dark mode inexistente pese a `darkMode:["class"]` | `tailwind.config.ts:14`, `globals.css` | Decidir: declarar "solo light" o implementar vía HSL vars |
| 20 | Deps sin usar: framer-motion, radix dialog/popover/tooltip/toast | `package.json:17-30` | Usar (11 y 24) o desinstalar |
| 21 | Focus-visible ausente en Links y dropzones | `sidebar.tsx:83-91`, `quick-links.tsx:34-43`, `dropzone.tsx:78-101`, `importar:230`, `prophet:297` | `focus-visible:ring-2 ring-smnyl-primary` |
| 22 | Icon-buttons con `title` sin `aria-label` ni tooltip | `document-card.tsx:86-127` | `aria-label` + Tooltip shadcn |
| 23 | Duplicación DropZone/FilePreview ×3 y mapas estado→estilo ×3 | `importar:230-303`, `prophet:282-365`, `secciones-accordion:172-180`, `dashboard-hero:59-76` | Consolidar en `upload/dropzone.tsx` y `lib/estado-ui.ts` |
| 24 | Export sin momento de celebración (peak-end, heredado S13) | `dashboard-hero.tsx:102` | Panel de éxito con confetti sutil primera vez por sesión |
| 25 | Placeholder 2.81:1 con contenido instructivo | `ui/input.tsx:14`, `brief:89-98` | Subir a `text-muted/80`; mover instrucciones largas a helper text |
| 26 | Marker "◐" `text-smnyl-warning` 3.48:1 como glifo | `secciones-accordion.tsx:53,116` | Usar `warning-dark` o icono `CircleDashed` que ya importan |
| 27 | Tabs sin contador; skeletons de altura fija sin forma del layout; botón primario 4.65:1 margen estrecho | `document-list.tsx:30-42`, varios, `button.tsx:29` | Contadores `(n)`; skeletons compuestos; considerar `primary-600` para superficies con texto pequeño |

---

## Lo que NO se puede auditar estáticamente

Requiere sesión visual con la app corriendo (y sería la continuación natural de esta auditoría):

1. **Jerarquía percibida y densidad real** — el dashboard apila hero + quick-links + métricas + gobernanza + brechas + secciones (`[id]/page.tsx:62-74`); si "se siente saturado" (queja original S13) solo se ve renderizado con datos reales de 28 secciones.
2. **Screenshots de las 13 rutas** en 1440/1024/375px — especialmente el colapso <1024px sin sidebar y la entrevista con `h-[calc(100vh-8rem)]` en móvil.
3. **Animaciones en movimiento** — timing real de fade-ins encadenados, el accordion, el typing indicator, y si el `animate-fade-in` repetido por sección produce cascada agradable o parpadeo.
4. **Flujos completos** — crear→onboarding→brief→dashboard con datos reales; latencia percibida del SSE; comportamiento del toast de 10 min en importar.
5. **Render tipográfico real** de Georgia/Tahoma en Windows con antialiasing (`globals.css:52-55`) — el peso visual de Georgia en headings solo se juzga en pantalla.
6. **Estados hover/focus reales** y hit-areas táctiles (los `size="icon"` de 36px vs los 44px de WCAG 2.5.5 — medible solo renderizado).
7. **Contraste sobre gradientes** — ContinueHero y CTACard primary usan gradientes suaves; los ratios aquí calculados usan el fondo dominante.
8. **Verificación del look nativo** de checkboxes/selects en cada OS/browser (hallazgos 2 y 9).

---

*Auditoría generada estáticamente a partir del código en el commit actual de `main`. Los ratios de contraste se calcularon con la fórmula de luminancia relativa sRGB de WCAG 2.1.*
