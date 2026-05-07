"""Conversión markdown → estructuras de párrafo/run para `docxtpl.Subdoc`.

`docxtpl` solo hace string replacement plano cuando el placeholder se rellena
con un `str`. Para que las negritas, cursivas y subtítulos del contenido
narrativo (que Claude redacta con sintaxis markdown) se rendericen como
formato real de Word — no como asteriscos literales —, hay que convertir el
texto a un `Subdoc` cuyos párrafos y runs tengan los flags `bold`, `italic`,
y la alineación apropiada.

Este módulo implementa el parser puro (sin dependencias de docxtpl). El
módulo `docx_writer.py` lo consume para construir el Subdoc final.

Reglas:
- `**texto**` → run con bold.
- `*texto*` → run con italic (solo si NO es parte de `**`).
- Línea que es **solo** `**texto**` → párrafo de subtítulo (alineación
  izquierda; sirve para evitar el efecto raro de justify-spread con frases
  cortas tipo "Algoritmo central").
- Línea que empieza con `- ` → bullet (genera párrafo con flag `es_bullet`).
- Doble salto `\\n\\n` separa párrafos. Líneas en blanco se descartan.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Patrones para inline runs.
# Bold se busca primero (greedy `**...**`). Italic se busca después con
# lookarounds que excluyen los `*` ya consumidos por bold.
_BOLD_INLINE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_INLINE = re.compile(r"(?<!\*)\*([^*\n]+?)\*(?!\*)")
_LINE_SOLO_BOLD = re.compile(r"^\*\*(.+?)\*\*\s*$")
_LINE_BULLET = re.compile(r"^\s*-\s+(.*)$")


@dataclass(frozen=True)
class InlineRun:
    """Un fragmento de texto con su formato individual."""

    text: str
    bold: bool = False
    italic: bool = False


@dataclass
class ParrafoSpec:
    """Un párrafo del Subdoc final con sus runs y propiedades de alineación."""

    runs: list[InlineRun] = field(default_factory=list)
    es_subtitulo: bool = False
    """Si True, alinear a la izquierda (no justified). Útil para frases cortas en bold."""
    es_bullet: bool = False
    """Si True, renderizar con marca de bullet/lista."""


def parsear_runs_inline(linea: str) -> list[InlineRun]:
    """Parsea una línea a runs con formato inline (bold + italic).

    El algoritmo: encuentra todas las regiones bold primero, después italic
    en los huecos restantes; el resto es texto plano. Preserva el orden
    secuencial.
    """
    if not linea:
        return []

    # Estrategia: marcar regiones con formato y reconstruir secuencialmente.
    spans: list[tuple[int, int, str, dict[str, bool]]] = []
    for m in _BOLD_INLINE.finditer(linea):
        spans.append((m.start(), m.end(), m.group(1), {"bold": True}))
    # Para italic, ignoramos los rangos ya cubiertos por bold.
    bold_ranges = [(s, e) for s, e, _, _ in spans]
    for m in _ITALIC_INLINE.finditer(linea):
        if any(bs <= m.start() and m.end() <= be for bs, be in bold_ranges):
            continue
        spans.append((m.start(), m.end(), m.group(1), {"italic": True}))

    spans.sort(key=lambda x: x[0])

    runs: list[InlineRun] = []
    cursor = 0
    for inicio, fin, contenido, fmt in spans:
        if inicio > cursor:
            runs.append(InlineRun(linea[cursor:inicio]))
        runs.append(
            InlineRun(
                contenido,
                bold=fmt.get("bold", False),
                italic=fmt.get("italic", False),
            )
        )
        cursor = fin
    if cursor < len(linea):
        runs.append(InlineRun(linea[cursor:]))

    return runs or [InlineRun(linea)]


def parsear_parrafos(texto: str) -> list[ParrafoSpec]:
    """Divide el texto en párrafos con sus propiedades.

    Reglas:
    - Doble salto separa bloques.
    - Dentro de un bloque, líneas-bullet (`- `) son párrafo propio.
    - Líneas-prosa contiguas dentro de un bloque se unen en un párrafo único.
    - Bloque de una sola línea que es `**texto**` → párrafo de subtítulo
      (alineación izquierda, evita el efecto raro de justified con frase corta).
    """
    if not texto or not texto.strip():
        return []

    bloques = re.split(r"\n\s*\n", texto.strip())
    parrafos: list[ParrafoSpec] = []
    for bloque in bloques:
        bloque = bloque.strip("\n")
        if not bloque.strip():
            continue
        lineas = [linea for linea in bloque.split("\n") if linea.strip()]

        # Caso especial: bloque de una sola línea con solo **xxx** → subtítulo
        if len(lineas) == 1:
            m = _LINE_SOLO_BOLD.match(lineas[0].strip())
            if m is not None:
                parrafos.append(
                    ParrafoSpec(
                        runs=[InlineRun(m.group(1).strip(), bold=True)],
                        es_subtitulo=True,
                    )
                )
                continue

        # Recorrer las líneas, agrupando prosa contigua y emitiendo bullets sueltos.
        prosa_buffer: list[str] = []
        for linea in lineas:
            m_bullet = _LINE_BULLET.match(linea)
            if m_bullet is not None:
                if prosa_buffer:
                    parrafos.append(ParrafoSpec(runs=parsear_runs_inline(" ".join(prosa_buffer))))
                    prosa_buffer = []
                parrafos.append(
                    ParrafoSpec(
                        runs=parsear_runs_inline(m_bullet.group(1)),
                        es_bullet=True,
                    )
                )
            else:
                prosa_buffer.append(linea.strip())
        if prosa_buffer:
            parrafos.append(ParrafoSpec(runs=parsear_runs_inline(" ".join(prosa_buffer))))

    return parrafos
