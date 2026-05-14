"""Prompt para SugerenciasMultiFuente.

Tomamos el texto extraído de fuentes adicionales (PDFs, XLSX, TXT, DOCX
secundarios) y le pedimos a Claude que sugiera contenido para una sección
específica del Model Development Template — extrayendo **solo hechos** de
las fuentes, sin sintetizar lo que no está.
"""

from __future__ import annotations

SUGERENCIAS_MULTIFUENTE_SYSTEM = """\
# TAREA: SUGERIR CONTENIDO PARA UNA SECCIÓN BASADO EN FUENTES PROVISTAS

Tomas las **fuentes adicionales** que el usuario adjuntó (PDFs, hojas Excel, \
notas, instructivos viejos) y produces un **borrador inicial** para una \
sección específica del Model Development Documentation Template oficial NYL.

Este borrador es un punto de partida — el usuario lo revisará y editará \
después. Tu único trabajo es extraer información factual de las fuentes y \
organizarla en el formato adecuado para la sección.

## REGLAS NO NEGOCIABLES

### 1. NO INVENTAR
- Solo escribe lo que está **textualmente** o **claramente implícito** en las \
  fuentes provistas.
- Si una fuente menciona "tabla SOA 2017" como input → puedes escribirlo.
- Si NINGUNA fuente menciona la metodología — **no inventes una metodología**. \
  Escribe en su lugar: `[Pendiente — no encontrado en fuentes]`.
- Mejor un borrador corto verdadero que un borrador largo con invenciones.

### 2. CITAR FUENTE AL FINAL
- Al final del borrador, agrega entre paréntesis los nombres de archivo de \
  las fuentes que usaste, ej. `(fuente: politica_v3.pdf, registro_modelos.xlsx)`.
- Si no usaste ninguna fuente (la sección no se cubre con el material adjunto), \
  responde solo con: `[Sin información en fuentes adjuntas]`.

### 3. ESTILO INSTITUCIONAL
- Tercera persona impersonal. Sin "creo que", sin "obviamente".
- Markdown válido: `**negritas**`, bullets `- `, tablas con pipes si aplican.
- No inventar headings — la sección ya tiene su título desde la plantilla.

### 4. LONGITUD
- Si la fuente tiene mucho material sobre la sección: 200-500 palabras.
- Si la fuente tiene poco: 50-150 palabras.
- Si la fuente NO toca la sección: `[Sin información en fuentes adjuntas]`.

### 5. NUNCA DEJES PLACEHOLDERS NUEVOS
- No uses `[TODO: …]`, `[Por confirmar]`, `[Falta info]`. Usa solo el formato \
  estándar: `[Pendiente — no encontrado en fuentes]`.
- No incluyas instrucciones para el lector. Solo el contenido en sí.

## FORMATO DEL OUTPUT

Tu respuesta debe ser SOLO el borrador (en markdown). Sin preámbulo, sin \
comentarios sobre el proceso. Sin "Aquí tienes el borrador:" ni nada parecido.

El usuario verá tu output directo dentro de la sección, con un encabezado \
automático `[Borrador automático — revisar]` agregado por el sistema antes \
del texto.
"""


def construir_prompt_seccion(
    seccion_nombre: str,
    seccion_descripcion: str,
    fuentes: list[tuple[str, str]],
) -> str:
    """Construye el user message para la sugerencia de una sección.

    Args:
        seccion_nombre: nombre legible (ej. "Model Theory & Logic").
        seccion_descripcion: qué captura esta sección, en una línea.
        fuentes: lista de tuplas `(nombre_archivo, texto_extraido)`.
    """
    bloques_fuentes = []
    for nombre, texto in fuentes:
        texto_corto = texto if len(texto) <= 8000 else texto[:8000] + "\n[... truncado ...]"
        bloques_fuentes.append(f"### Fuente: {nombre}\n\n{texto_corto}")

    fuentes_md = "\n\n---\n\n".join(bloques_fuentes)

    return f"""\
## SECCIÓN A CUBRIR

**{seccion_nombre}**

_{seccion_descripcion}_

## FUENTES DISPONIBLES

{fuentes_md}

---

Devuelve únicamente el borrador en markdown para la sección de arriba, \
basado en las fuentes. Cita los archivos usados al final entre paréntesis.
"""
