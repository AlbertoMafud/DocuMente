# Design Critique — DocuMente, 12 pantallas

**Fecha:** 2026-05-19 (D.2.b del plan de remediación S13→S16)
**Stack actual:** Streamlit 1.36+ con CSS inyectado vía `theme.py`.
**Input:** código de `src/ui/{pages,components}/*.py` + feedback de usuarios + brand guidelines SMNYL.
**Output:** input al plan dedicado de migración Next.js + shadcn/cult-ui.

## Por qué se "siente Streamlit default" pese al theme custom

Antes de las pantallas, la causa raíz general (afecta a todas):

1. **Block-level por default.** Streamlit acomoda cada widget como bloque ancho de columna → genera ese look "formulario gubernamental" plano. La marca SMNYL tiene un theme decente pero las primitivas siguen llenando 100% de ancho.
2. **Cero microinteracciones.** No hay hover states diferenciados, ni transitions, ni animations sutiles. La app se siente "estática" — un PDF interactivo, no una webapp moderna.
3. **Densidad inconsistente.** Algunas pantallas tienen demasiado padding vertical (`<div style='height: 1.5rem'>` repetido), otras son densas sin respiro.
4. **Hierarchy plana.** Casi todo es texto medio. Faltan tres cosas: H1/H2 más fuertes con la tipografía Georgia, dividers visuales jerárquicos, y label tipográfico "eyebrow" para metadata.
5. **Tipografía display infrautilizada.** Georgia solo aparece en H1/H2 grandes. En cards y badges se usa Tahoma — pierde personalidad.

Estos 5 problemas son sistémicos. Cualquier fix incremental en Streamlit los aliviana pero no los elimina. Por eso el plan llama a la migración a Next.js + shadcn — donde las primitivas (Button, Card, Badge) ya vienen con microinteracciones y los breakpoints son nativos.

---

## 1. Home (`app.py:_render_home`)

**Lo que hace:** Hero + 3 CTAs en línea + tabs Activos / Archivados / Papelera + lista de docs.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🔴 P0 | **3 CTAs con igual peso visual** ("Crear nuevo", "Mejorar existente", "Iniciar Ficha Prophet"). El usuario no sabe cuál es la acción primaria | Solo "Crear nuevo" es `type="primary"`; los otros son secondary. Pero los 3 ocupan columnas iguales y se ven equivalentes. **Fix:** layout en F-pattern — Crear nuevo grande arriba, los otros 2 más pequeños debajo. O agrupar "Mejorar / Prophet" bajo "Más opciones" |
| 2 | 🔴 P0 | **Tabs Activos/Archivados/Papelera sin pista de cantidad** | Cambiar labels a `Activos (5)`, `Archivados (2)`, `Papelera (1)`. Streamlit `st.tabs` no acepta badges nativos — hay que poner el contador en el label string |
| 3 | 🟡 P1 | Cards de docs recientes tienen 5 columnas con ratios `[3, 2, 1.2]` que se ven desbalanceadas (la columna "Abrir" queda muy ancha relativa al meta) | Ratios `[3.5, 1.5, 1]`. Botón "Abrir" más pequeño, alineado a la derecha |
| 4 | 🟡 P1 | **Acciones secundarias (📦 Archivar / 🗑️ Papelera) en una segunda fila** con `[1, 1, 4]` quedan empujadas a la izquierda dejando un hueco vacío de 4/6 ancho | Esas acciones deberían vivir en un menú "⋯" colapsado, no inline. En Streamlit puro: `st.popover("⋯")` con los 2 botones adentro |
| 5 | 🟢 P2 | El hero copy `"Documenta modelos sin fricción"` es genérico — podría ser más vivido | Más útil: meta-CTA dinámico: si hay 0 docs → "Empieza tu primer documento de modelo"; si ya hay → "Continúa donde te quedaste" con el doc más reciente |

**Lo que funciona:** los 3 botones tienen helpers tooltips informativos; la portada blanca con azul SMNYL respeta marca.

---

## 2. Importar (`importar.py`)

**Lo que hace:** uploader de docx/pdf ancla + uploader fuentes adicionales + botón "Analizar".

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🔴 P0 | **3 secciones consecutivas con `### 1. Documento ancla` + `### 2. Fuentes adicionales`** crean look de "lista numerada plana". No hay diferenciación visual entre la sección obligatoria (ancla) y la opcional (fuentes) | Card de ancla con borde primario; fuentes con borde dashed muted (= "opcional"). Tip badge "Recomendado" junto a fuentes |
| 2 | 🟡 P1 | Cuando subes un archivo, aparece una `st.container(border=True)` con metadata (nombre + size) — pero el archivo aún no está procesado. Confusing: ¿ya cargó o no? | Loading state visible: spinner pequeño tras subir mientras el reader extrae texto. Hoy el spinner solo aparece al clickear "Analizar" |
| 3 | 🟡 P1 | `st.info` azul para "PDF detectado — extracción menos precisa" rompe la tipografía SMNYL (Streamlit usa su font default para alerts) | Reemplazar `st.info()` por div custom con marca SMNYL (`bg=info_soft`, `border-left: 3px solid info`) — patrón ya usado en `onboarding_banner.py` |
| 4 | 🟢 P2 | Botón "Analizar documento" usa `use_container_width=False`, queda chico contra el ancho disponible | Tamaño consistente con CTA del home: `use_container_width=True` en un container con padding o `width="content"` (Streamlit 1.46+) |
| 5 | 🟢 P2 | El empty state inicial cuando no hay archivos es genérico ("Aún no has subido un documento") | Empty state visual con icono más grande + texto guía + tip de qué formatos. Componente `empty_state` ya existe — usarlo aquí |

---

## 3. Crear nuevo (`crear_nuevo.py`)

**Lo que hace:** form con 2 campos obligatorios (nombre, model_id) + uploader fuentes opcional.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🔴 P0 | El warning "asistente IA no disponible" aparece antes del form — interrumpe el flujo. Si el usuario nunca va a usar el asistente, no le importa | Mover ese warning al ÁREA de uploader (es donde aplica) en lugar de top de pantalla. O hacerlo un toast colapsable |
| 2 | 🟡 P1 | Campo "Model ID" requiere conocimiento técnico ("M07.P07.S03.006.D") pero solo hay un caption — no hay validación ni formato sugerido | Placeholder con ejemplo + ayuda contextual al focus. Si el ID no sigue el patrón institucional, mostrar warning suave (no blocker) |
| 3 | 🟡 P1 | "Fuentes adicionales" tiene caption largo (3 líneas) explicando el feature antes del uploader — el usuario lee "much wall of text" | Resumirlo a 1 línea + un expander "¿Cómo funciona?" para detalle. Patrón "progressive disclosure" |
| 4 | 🟢 P2 | El botón "Cancelar" tiene mismo peso visual que "Crear documento" — uno es primary, el otro es secondary, pero las columnas son iguales | "Cancelar" en menor peso visual (text-only link a home) |

---

## 4. Onboarding (`onboarding.py`)

**Lo que hace:** formulario de metadata del modelo después de crear/importar.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🔴 P0 | **Formulario plano** con 8+ campos en columna. Sin agrupación visual. El usuario no sabe qué viene después | Agrupar en 3 secciones colapsables: "Identificación" (nombre, ID, FAE), "Tier MRM" (riesgo, plataforma), "Equipo" (developers, users). Cada una expandida por default, colapsable para revisión |
| 2 | 🟡 P1 | No hay indicador de progreso ("paso 2 de 5" o barra) — el usuario no sabe cuánto falta para llegar al dashboard | Stepper visual arriba: `[Crear ✓] [Onboarding ←] [Brief] [Dashboard]` con el actual destacado |
| 3 | 🟢 P2 | Los campos "Inherent Risk Tier" usan selectbox con valores técnicos (`high`, `medium_minus`) | Tooltips por opción explicando qué significa cada tier en lenguaje plano |

---

## 5. Brief inicial (`brief_inicial.py`)

**Lo que hace:** 10 textareas con preguntas guiadas.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🔴 P0 | **10 textareas amontonadas vertical** → scroll infinito. El usuario se cansa antes de la pregunta 4 | Wizard de 1-pregunta-a-la-vez con barra de progreso (`5/10`). Botones "Anterior" / "Siguiente" / "Saltar". Permite revisar respuestas previas con un collapsible |
| 2 | 🟡 P1 | El tip "respuestas de 1-3 frases son suficientes" aparece arriba — los usuarios lo olvidan al llegar a la pregunta 5 | Repetir el tip de forma sutil al lado de cada textarea, o como placeholder dinámico |
| 3 | 🟡 P1 | Botón "Saltar" tiene mismo peso visual que "Generar borradores y continuar" | Saltar debería ser link `text-only`, no botón |
| 4 | 🟢 P2 | Si el LLM falla, aparecen 2 botones grandes "Reintentar" y "Continuar sin borradores" — pero el contexto del error es texto plano | Inline alert con icono + mensaje + acciones secundarias visualmente menores |

---

## 6. Dashboard (`dashboard.py`)

**La pantalla más densa de la app.** Lo que muestra: título + breadcrumb + métricas (4 métricas) + grid de SeccionCards (28 cards) + card Gobernanza (export + revisión coherencia + versión) + historial de versiones + lista de brechas.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🔴 P0 | **Información dump.** Las 28 SeccionCards + card Gobernanza + brechas + historial = >10 secciones verticales sin priorización clara | Layout 2-column: izquierda = SeccionCards (lo que el usuario hace), derecha = sidebar "Estado del documento" (completitud, brechas, gobernanza). Como un IDE moderno |
| 2 | 🔴 P0 | **Grid de 28 SeccionCards en 4 columnas** se ve como wall-of-cards. No hay agrupación por capítulo NYL (1. Background, 2. Model Profile, 3. Pre-Implementation, etc.) | Agrupar las cards por capítulo del template NYL con headers H3. Cada capítulo es una sección colapsable. Reduce visualmente de 28 cards planas a 9 grupos |
| 3 | 🟡 P1 | Card Gobernanza ocupa ancho full y mete 3 botones (Exportar / Auditoría / Editar metadata) + sub-features (sign-off, versionado) — se vuelve mini-pantalla | Convertir Gobernanza en un panel lateral fijo (sticky) con tabs internas: "Exportar", "Estado", "Versiones", "Auditoría" |
| 4 | 🟡 P1 | El "Historial de versiones" como expander dentro del flujo principal compite con la lista de brechas — ambos en mismo nivel jerárquico | Versiones va al sidebar de gobernanza. Brechas como banner SOBRE las SeccionCards (priorizan el trabajo) |
| 5 | 🟢 P2 | Métricas top usan `st.metric` default Streamlit (look spreadsheet) | Custom metric cards con marca SMNYL: número grande Georgia, label uppercase muted, delta opcional |

---

## 7. Entrevista (`entrevista.py`)

**Lo que hace:** split chat ↔ preview de la sección + expander apéndices abajo.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🔴 P0 | El expander "📎 Adjuntar apéndice" está colapsado pero tiene 3 sub-secciones adentro (tabla / PDF / fórmula LaTeX) con scroll interno | Reemplazar expander con 3 mini-tabs: `Tabla` / `PDF` / `Fórmula`. Cada uno limpio. UX más rápida — el usuario ve los 3 modos sin abrir nada |
| 2 | 🔴 P0 | El **layout split 1.4 : 1** entre chat y preview es subóptimo. El preview queda demasiado angosto para texto markdown formateado | Ratios `1 : 1` o permitir resize draggable. Streamlit no soporta drag-resize nativo — alternativa: toggle "Maximizar preview" |
| 3 | 🟡 P1 | Cuando una sección se cierra con borrador, aparece un `st.success` grande seguido del historial completo del chat. El usuario tiene que scrollear mucho para ver el borrador | Auto-collapse el chat history cuando hay borrador final; mostrar solo "Ver conversación completa (12 turnos)" como expander |
| 4 | 🟡 P1 | El uploader de fórmula LaTeX usa `st.latex()` para preview KaTeX, pero el preview aparece dentro del MISMO expander que el input → el usuario no ve el output sin scroll | Split lado a lado: textarea LaTeX a la izquierda, preview a la derecha. Como hicieron con el editor MRM (B.4) |
| 5 | 🟢 P2 | El chat usa `chat_bubble` con tres roles (user/assistant/system_note). Los system_notes tienen color amarillo crudo `#fef9e7` que no respeta marca | Soft variant del color `warning` (`#fdf4ee`) o `info_soft` (`#eef6fb`). Ver D.2.a tokens propuestos |

---

## 8. Vista previa (`vista_previa.py`)

**Lo que hace:** documento renderizado completo + panel lateral con metadata.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🟡 P1 | El botón "✏️ Editar" recién agregado (B.4) está en una columna estrecha `[6, 1]` → queda flotando arriba a la derecha del título. Cuando el título es largo, se desbalancea | Hover-only icon button al lado del título. Por default invisible, aparece en hover de la sección. Patrón "Notion" |
| 2 | 🟡 P1 | El placeholder de sección vacía (`#fdf6e3` amber suave + texto italic) es informativo pero todas se ven iguales — no hay sensación de prioridad | Diferenciar entre "obligatoria-vacía" (border-left rojo, urgente) vs "opcional-vacía" (muted, baja prioridad) |
| 3 | 🟢 P2 | El panel lateral con metadata, costo y métricas es un st.container que ocupa altura indefinida → cuando el documento principal es largo, el panel queda en la parte de arriba lejos del scroll | Sticky sidebar (CSS `position: sticky`). Streamlit no lo hace nativo pero se puede vía CSS custom |
| 4 | 🟢 P2 | Apéndices al final usan `Apéndice A, B, C` en lugar de `A.1, A.2, A.3` del DOCX final | Consistencia: usar el mismo formato A.N que el writer |

---

## 9. Auditoría (`auditoria.py`) + Timeline component

**Lo que hace:** lista cronológica de eventos del audit_trail.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🟡 P1 | El timeline tiene línea vertical + marcadores circulares con bordes — buen patrón, pero todos los items son del mismo color/peso | Agrupar visualmente por día (header sticky por fecha: "Hoy", "Ayer", "Hace 3 días") |
| 2 | 🟡 P1 | Cada item de timeline muestra `tipo · fecha` arriba y `descripcion` debajo — pero el `tipo` es uppercase fuerte y la descripción muted. La jerarquía está invertida (el TIPO no debería robar atención) | El protagonista es la descripción. Tipo va como pequeño icon + label muted al lado |
| 3 | 🟢 P2 | No hay filtro por rango de fechas (solo por tipo) | Picker de rango: "Últimos 7 días" / "Últimos 30" / "Custom" |
| 4 | 🟢 P2 | No hay forma de exportar el audit_trail (CSV/JSON) — para regulatory queries puede ser útil | Botón "Exportar audit trail (CSV)" arriba a la derecha |

---

## 10. Editor sección MRM (`editar_seccion_mrm.py`)

**Lo que hace:** textarea + preview live lado a lado (B.4).

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🟡 P1 | El textarea `height=520` es fijo — si la sección es larga, el preview también tiene que scrollear pero el textarea no | Sincronizar scroll entre textarea y preview (avanzado) o ambos autoexpansibles |
| 2 | 🟡 P1 | El help text `"Markdown soportado: **negritas**, *cursivas*..."` está en el `help=` del st.text_area — el usuario lo descubre solo si pasa el mouse | Toolbar pequeña arriba del textarea con botones: **B** (bold), *I* (italic), `🔗` (link), ▦ (tabla). Inserta sintaxis markdown en el cursor |
| 3 | 🟢 P2 | Botón "Cancelar" tiene mismo peso que "Guardar cambios" | Cancelar como text-link |
| 4 | 🟢 P2 | Si el usuario edita y navega fuera sin guardar, pierde el trabajo silenciosamente | Detectar cambios pendientes + confirm dialog antes de navegar away |

---

## 11. Editor Prophet (`editar_seccion_prophet.py`)

**Lo que hace:** 3 tipos de editor según `cat.tipo_contenido` (tabla / texto / campos).

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🟡 P1 | El `st.data_editor` para tipo tabla muestra todas las columnas con width igual — datos numéricos se ven igual de anchos que strings largos | Column config con widths inferidos por tipo (numérico estrecho, string ancho) |
| 2 | 🟢 P2 | El editor de "campos" es un form vertical de text_inputs — para 8+ campos se vuelve largo | 2 columnas adaptativas + agrupar campos relacionados (nombre+id juntos, fecha+versión juntos) |

---

## 12. Auth gate (`auth_gate.py`)

**Lo que hace:** password temporal antes de cualquier ruta.

| # | Prio | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | 🟢 P2 | El form está centrado pero hay mucho whitespace arriba (margin `4rem`). En pantallas chicas se ve desperdiciado | Margin auto, no fijo. Centrado vertical (`min-height: 80vh; display: flex`) |
| 2 | 🟢 P2 | El password incorrecto muestra un `st.error` Streamlit default debajo del form, rompiendo la marca SMNYL | Inline alert custom dentro del card |

---

## Cross-cutting recommendations (afectan todo)

### Quick wins en Streamlit (1-2 días, sin migrar)

1. **Add soft variants** al theme (D.2.a tabla §5) y refactorizar `gap_badge`, `chat_bubble`, `vista_previa` para consumirlos. Quita 5 hardcoded.
2. **Custom alert component** que reemplace `st.info/warning/error/success` por divs con marca SMNYL. Hoy 30+ usos crudos rompen tipografía.
3. **Componente `<Eyebrow>`** para el patrón uppercase-muted-bold que se repite en 4 lugares.
4. **CSS de transitions** en `theme.py`: `transition: all var(--duration-fast) var(--ease-default)` a botones, cards, badges. Da microinteracciones sin nuevas dependencias.
5. **Sticky sidebars** vía CSS custom en pages que tienen panel lateral (dashboard, vista_previa). Reduce scrolling.

### Lo que solo se arregla con migración

1. **Tabs con badges de cantidad** (`Activos (5)`) — Streamlit no lo soporta nativo; shadcn sí.
2. **DataTable con sort/filter/paginación** para listado de docs — Streamlit `dataframe` es read-only.
3. **Resize-draggable split** entre chat y preview — Streamlit no permite.
4. **Hover-only action icons** en cards (patrón Notion) — Streamlit los rendereá siempre visibles.
5. **Wizard 1-pregunta-a-la-vez** con animaciones de transición — Streamlit las puede hacer feas con rerun, shadcn Framer Motion las hace bien.

---

## Priority matrix global

| Categoría | Quick wins en Streamlit (1-2 días) | Solo con migración Next.js |
|---|---|---|
| **Visual** (theme, marca) | ✅ Soft variants, eyebrow, transitions | Animaciones complejas, gradientes shadcn |
| **Layout** | Sticky sidebars vía CSS | Drag-resize, masonry grids |
| **Interactividad** | st.popover, st.tabs con counts en string | Hover states, micro-animations |
| **Información** | Agrupar SeccionCards por capítulo NYL | DataTable con sort/filter, search palette |
| **Flujos** | Wizard pseudo (rerun por step) | Wizard real con motion |

**Recomendación general:** los **20+ P0/P1 items** identificados aquí se dividen en `~12 que se pueden fixear sin migrar` (Streamlit quick wins) + `~8+ que justifican la migración a Next.js + shadcn`. Esa lista de los 8+ es el "ROI mínimo" para invocar el plan dedicado de migración.
