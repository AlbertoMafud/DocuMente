# SMNYL Brand Guidelines — Fuente única para DocuMente

> Extracto accionable del manual oficial de marca *Seguros Monterrey New York Life Brand Guidelines 2022* (`SMNYL/Identidad de marca/SMNYL Guideline 2022 (1).pdf`). Esta es la **fuente única** que tanto el `theme.py` de Streamlit como la plantilla `.docx` y todos los componentes de UI consumen. Cualquier divergencia entre código/UI y este archivo debe corregirse aquí primero.

---

## 1. Paleta primaria (azul + blanco)

> *Manual SMNYL §Paleta primaria — pp. 27*

La paleta primaria es **solo dos colores**: azul New York Life y blanco. El azul es el color principal y se reserva preferentemente para el logo y elementos de mayor jerarquía visual, para preservar su impacto.

| Nombre | HEX | RGB | CMYK | Pantone |
|---|---|---|---|---|
| **New York Life Blue** | `#0079c2` | 0/121/194 | 100/44/0/0 | 300 U / 300 C |
| **White** | `#ffffff` | 255/255/255 | 0/0/0/0 | — |

---

## 2. Paleta secundaria (8 familias × 3 intensidades)

> *Manual SMNYL §Paleta secundaria — pp. 28-29*

**Importante:** No existe `Medium Gold` en esta paleta — fue removido por similitud con el New York Life Gold (que está reservado solo para usos especiales con autorización del equipo de branding).

### Light (intensidad clara)

| Nombre | HEX | RGB | Pantone |
|---|---|---|---|
| Light Rose | `#d2a8b5` | 210/168/181 | 685 U / 684 C |
| Light Twilight | `#bdbed2` | 189/190/210 | 7445 U / 7445 C |
| Light Rain | `#b2d4e4` | 178/212/228 | 545 U / 290 C |
| Light Pine | `#bbddd2` | 187/221/210 | 7464 U / 7464 C |
| Light Palm | `#ccd8bf` | 204/216/191 | 4204 U / 4204 C |
| Light Sunset | `#e7a88c` | 231/168/140 | 4031 U / 4033 C |
| Light Gold | `#ddcfb2` | 221/207/178 | 7501 U / 7501 C |
| Quartz (neutro) | `#bdc1c2` | 189/193/194 | CG 4 U / CG 4 C |
| Steel (neutro) | `#0a3c53` | 10/60/83 | 3035 U / 3035 C |

### Medium (intensidad media)

| Nombre | HEX | RGB | Pantone |
|---|---|---|---|
| Medium Rose | `#b56f85` | 181/111/133 | 7432 U / 7431 C |
| Medium Twilight | `#5a5c8e` | 90/92/142 | 7676 U / 667 C |
| Medium Rain | `#2e86af` | 46/134/175 | 2185 U / 2390 C |
| Medium Pine | `#4b8b7f` | 75/139/127 | 7716 U / 7716 C |
| Medium Palm | `#6b9160` | 107/145/96 | 7741 U / 2264 C |
| Medium Sunset | `#ce7046` | 206/112/70 | 2434 U / 2434 C |
| Slate (neutro) | `#92999a` | 146/153/154 | 4278 U / 4278 C |
| *(no hay Medium Gold)* | — | — | — |

### Dark (intensidad oscura)

| Nombre | HEX | RGB | Pantone |
|---|---|---|---|
| Dark Rose | `#754a62` | 117/74/98 | 689 U / 689 C |
| Dark Twilight | `#313372` | 49/51/114 | 2755 U / 5265 C |
| Dark Rain | `#0a385e` | 10/56/94 | 3025 U / 3025 C |
| Dark Pine | `#264640` | 38/70/64 | 7721 U / 7721 C |
| Dark Palm | `#364432` | 54/68/50 | 4217 U / 2266 C |
| Dark Sunset | `#544235` | 84/66/53 | 4695 U / 7518 C |
| Dark Gold | `#816730` | 129/103/48 | 4495 U / 4495 C |
| Iron (neutro) | `#565656` | 86/86/86 | 433 U / 425 C |

---

## 3. Selección de colores aplicada a DocuMente

Para mantener consistencia y profesionalismo, DocuMente usa este subset acotado (Streamlit + DOCX + componentes):

| Token | Color | HEX | Uso |
|---|---|---|---|
| `--color-primary` | New York Life Blue | `#0079c2` | Botones primarios, links, acentos críticos, logo |
| `--color-primary-dark` | Dark Rain | `#0a385e` | Hovers de primario, headers de tablas |
| `--color-bg` | White | `#ffffff` | Fondo principal de la app |
| `--color-bg-soft` | Quartz | `#bdc1c2` con 10% opacity | Fondos de cards, secciones secundarias |
| `--color-text` | Steel | `#0a3c53` | Texto de cuerpo |
| `--color-text-muted` | Iron | `#565656` | Texto secundario, captions, metadata |
| `--color-border` | Quartz | `#bdc1c2` | Bordes de cards, divisores |
| `--color-success` | Medium Pine | `#4b8b7f` | Estado "completo", confirmaciones |
| `--color-warning` | Medium Sunset | `#ce7046` | Estado "en revisión", alerts no-críticos |
| `--color-danger` | Dark Rose | `#754a62` | Errores, acciones destructivas |
| `--color-info` | Medium Rain | `#2e86af` | Info contextual, tooltips |
| `--color-accent-soft` | Light Rain | `#b2d4e4` | Backgrounds de chat-bubbles, badges suaves |

**Regla:** ningún color fuera de esta tabla se usa en DocuMente sin justificación documentada. Si se necesita un nuevo token, agregarlo aquí primero.

---

## 4. Tipografías

> *Manual SMNYL §Tipografía — pp. 75-79*

### Tipografías oficiales

| Familia | Uso | Estilo |
|---|---|---|
| **Alda Pro Regular** | Títulos y elementos resaltados | Serif corporativa |
| **Effra Pro Regular** | Cuerpo, subtítulos, pies de página | Sans-serif corporativa |

### Reemplazos web cuando Alda/Effra no estén disponibles

> "Cuando haya limitantes en poder conseguir o adaptar estas tipografías, podrán reemplazarse por Georgia y Tahoma respectivamente."  
> — *Manual SMNYL p. 75*

| Cuando falta | Sustituir por | Notas |
|---|---|---|
| Alda Pro | **Georgia Regular** | Solo si es estrictamente necesario |
| Effra Pro | **Tahoma Regular** | Solo si es estrictamente necesario |

### Stack tipográfico de DocuMente (CSS / DOCX)

**Decisión MVP:** usamos los reemplazos oficialmente autorizados por el manual SMNYL — Georgia para display y Tahoma para body. Ambas son fuentes nativas de Windows y Mac, no requieren licencia ni descarga, y respetan literalmente lo que dice el manual de marca SMNYL p. 75.

```css
--font-display: Georgia, "Times New Roman", serif;
--font-body:    Tahoma, "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
```

**Cuando se obtengan las fuentes oficiales Alda Pro / Effra Pro**, reemplazar el primer ítem de cada stack — Georgia/Tahoma quedan como fallback automático.

### Reglas de uso (do's y don'ts oficiales)

✅ **Do:**
- Alda Pro Regular para títulos.
- Effra Pro Regular para textos, subtítulos, pies de página y otros elementos.

❌ **Don't:**
- No usar Alda Pro para bloques de texto (es display).
- No usar Alda Pro Bold para titulares (solo Regular).
- No comprimir letras ni alterar tamaños.
- No agregar sombras ni efectos a la tipografía.
- No poner tipografías sobre fotografías.
- No usar el azul New York Life para titulares (reservado para logo y elementos puntuales).

### Jerarquía tipográfica de referencia

| Elemento | Familia | Tamaño aprox. | Color |
|---|---|---|---|
| Hero title (página 1) | Alda Pro Regular | 48–72pt + 2pt leading | Steel `#0a3c53` |
| Heading 1 | Alda Pro Regular | 28-32pt | Steel `#0a3c53` |
| Heading 2 | Alda Pro Regular | 20-24pt | Steel `#0a3c53` |
| Heading 3 | Effra Pro Regular | 16-18pt | Steel `#0a3c53` |
| Body | Effra Pro Regular | 11-12pt | Steel `#0a3c53` |
| Caption / metadata | Effra Pro Regular | 9-10pt | Iron `#565656` |

---

## 5. Logo SMNYL — reglas de uso

> *Manual SMNYL §Logo — pp. 18-31*

### Composición y formato
- El logo debe estar en forma de caja con esquinas redondeadas. **Las esquinas cuadradas son incorrectas.**
- El logotipo debe tener altura igual al ancho de "NEW YORK LIFE".
- Posición preferida en documentos: barra inferior izquierda.
- Formatos: archivos RGB para digital, archivos CMYK o Pantone para impreso.

### Tamaño mínimo
- **2.5 cm de largo** mínimo. El logo nunca debe disminuirse a un tamaño menor.

### Espacio de protección (margen de seguridad)
- Mantener un espacio alrededor del logo igual a la altura y ancho de "NEW YORK LIFE".

### Fondos permitidos
- ✅ Fondo blanco (preferible)
- ✅ Fondos claros con suficiente contraste
- ⚠️ Fondo azul corporativo: solo en patrocinios y solo si no hay alternativa
- ❌ No colocar el logo blanco sobre fondo de color claro
- ❌ No colocar el logo sobre fondos cargados o con patrones
- ❌ No colocar el logo sobre fotografías sin recuadro de soporte

### Don'ts
- No cambiar el color de ninguna parte del logo
- No alterar proporciones (alto ≠ ancho de "NEW YORK LIFE" es incorrecto)
- No esviar/skew el logotipo
- No agregar sombras, efectos o gradientes
- No poner el logo en color sobre fondo de color (excepto fondo azul en patrocinios)

### Aplicación en DocuMente

| Pieza | Tratamiento |
|---|---|
| Header de la app | Logo color sobre fondo blanco, tamaño 2.5cm, alineado a la izquierda |
| Loading screen / splash | Logo color centrado sobre fondo blanco |
| DOCX exportado (header) | Logo color en esquina superior izquierda, ≥2.5cm, fondo blanco |
| DOCX exportado (footer) | Variante simplificada o referencia textual "Seguros Monterrey New York Life" |

---

## 6. Lineamientos digitales clave

### Contraste y accesibilidad
- Cumplir mínimo **WCAG AA**. Las combinaciones recomendadas en el manual están marcadas con AA / AAA en la matriz de contraste oficial (manual p. 46).
- Texto principal: Steel `#0a3c53` sobre White → AAA.
- Texto en color: validar contra la matriz oficial antes de usar.

### Espaciado
- Margen mínimo: 3 picas (≈ 0.5 inch / 12.7 mm) en piezas impresas. En web/Streamlit traducir a un sistema de spacing consistente:
  - `--space-xs: 4px`
  - `--space-sm: 8px`
  - `--space-md: 16px`
  - `--space-lg: 24px`
  - `--space-xl: 40px`
  - `--space-2xl: 64px`

### Iconografía
- Línea abierta, trazo redondeado, basada en rejilla.
- Mínimo 50×50 px.
- Estilos neutros: sin humor, sin 3D, sin sombras, sin efectos.
- Color sólido o 100% Steel.

### Patrones (para fondos y elementos decorativos)
8 patrones autorizados con nombres temáticos: Legacy, Soporte, Fuerza, Continuidad, Comunidad, Momentum, Estabilidad, Crecimiento.

- Solo se aplican en **Light Rain**, **Light Gold** o **Slate** (única variación permitida).
- Dos tamaños: pequeño (toques sutiles) y grande (fondos).
- ❌ No aplicar en gráficos ni ilustraciones.
- ❌ No colocar imágenes, tipografía o gráficos sobre patrones.
- ❌ No usar patrones de colores que no estén autorizados.

### Fotografía
- Luz natural, sombras marcadas, autenticidad.
- Categorías: Personas (familia), Detalles/Lugares, Asesores (4 escenarios: "Nos involucramos", "Escuchamos", "Orientados a acciones", "Ofrecemos apoyo").
- ❌ Evitar: ángulos inusuales, fotos genéricas de stock, desenfoque extremo, colores saturados, blanco/negro con efectos.

> **Para DocuMente MVP:** la fotografía no es un elemento central. Mantener la app minimalista con tipografía + paleta + logo. Si se incorporan imágenes en v2, seguir estas reglas.

---

## 7. Pilares de marca (tono y voz)

> *Manual SMNYL §Pilares — pp. 1-2*

Los tres pilares son **Humanidad, Humildad, Integridad**. En DocuMente esto se traduce a:

- **Humanidad**: lenguaje cálido, empático, en español natural. Nunca robótico.
- **Humildad**: la app no presume — guía. Sugiere sin imponer. Reconoce que el usuario es el experto del modelo.
- **Integridad**: trazabilidad total. Nunca afirmar como verdad lo que el usuario no proveyó. Marcar siempre como "Borrador asistido" cuando hay generación de Claude.

---

## 8. Tokens listos para `src/ui/theme.py`

Estos son los valores definitivos a usar en código. Si el manual cambia, actualizar primero aquí, después regenerar `theme.py`.

```python
# src/ui/theme.py — tokens
SMNYL_COLORS = {
    "primary":         "#0079c2",  # New York Life Blue
    "primary_dark":    "#0a385e",  # Dark Rain
    "bg":              "#ffffff",
    "bg_soft":         "#f4f5f6",  # Quartz @ ~10% mezclado
    "text":            "#0a3c53",  # Steel
    "text_muted":      "#565656",  # Iron
    "border":          "#bdc1c2",  # Quartz
    "success":         "#4b8b7f",  # Medium Pine
    "warning":         "#ce7046",  # Medium Sunset
    "danger":          "#754a62",  # Dark Rose
    "info":            "#2e86af",  # Medium Rain
    "accent_soft":     "#b2d4e4",  # Light Rain
}

SMNYL_FONTS = {
    "display": 'Georgia, "Times New Roman", serif',
    "body":    'Tahoma, "Segoe UI", sans-serif',
}

SMNYL_SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "40px",
    "2xl": "64px",
}

SMNYL_RADIUS = {
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
}

SMNYL_SHADOW = {
    "sm": "0 1px 2px rgba(10, 60, 83, 0.06)",
    "md": "0 4px 12px rgba(10, 60, 83, 0.08)",
    "lg": "0 12px 32px rgba(10, 60, 83, 0.12)",
}
```

---

## 9. Verificación rápida ("¿esto pasa marca?")

Antes de aprobar cualquier pieza visual de DocuMente (UI o DOCX), validar:

- [ ] ¿Los colores están en la lista de tokens (sección 3) o en la paleta oficial (secciones 1-2)?
- [ ] ¿Las tipografías son Alda/Effra o sus fallbacks autorizados (sección 4)?
- [ ] ¿El logo respeta tamaño mínimo (2.5cm), espacio de seguridad y fondo permitido (sección 5)?
- [ ] ¿El contraste de texto pasa AA mínimo (sección 6)?
- [ ] ¿Hay elementos prohibidos (sombras en logo, Alda en bloque de texto, patrones sobre fotos)?

Si todas las casillas pasan → **OK marca**. Si alguna falla → corregir antes de mostrar.
