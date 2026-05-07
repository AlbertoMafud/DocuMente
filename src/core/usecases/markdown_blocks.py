"""Separador de bloques markdown — prosa vs tabla nativa.

Cuando un apéndice contiene tablas markdown, queremos renderizarlas como
**tablas nativas de Word** (con bordes, celdas, font size adaptable) — no
como párrafos planos. Este módulo separa el texto en bloques tipados que
el `DocxWriter` puede procesar de forma diferenciada:

- `BloqueProsa` → se procesa con el parser markdown estándar (negritas,
  cursivas, bullets, subtítulos).
- `BloqueTabla` → se inserta como tabla nativa con `subdoc.add_table()`,
  preservando estructura tabular y permitiendo ajuste de tamaño de letra.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEPARATOR = re.compile(r"^\s*\|[\s\-:|]+\|\s*$")


@dataclass(frozen=True)
class BloqueProsa:
    """Bloque de texto narrativo (no tabla)."""

    texto: str


@dataclass(frozen=True)
class BloqueTabla:
    """Bloque de tabla parseado de markdown pipe-separated."""

    headers: list[str]
    rows: list[list[str]]


def separar_bloques(texto: str) -> list[BloqueProsa | BloqueTabla]:
    """Divide el texto en bloques alternados de prosa y tabla.

    Una tabla markdown válida tiene 3+ líneas: header `| a | b |`, separador
    `|---|---|`, y filas de datos. Si falta el separador, la línea con pipes
    se considera prosa.
    """
    if not texto or not texto.strip():
        return []

    lineas = texto.splitlines()
    bloques: list[BloqueProsa | BloqueTabla] = []
    buffer_prosa: list[str] = []
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if (
            _TABLE_LINE.match(linea)
            and i + 1 < len(lineas)
            and _TABLE_SEPARATOR.match(lineas[i + 1])
        ):
            # Volcar prosa acumulada
            if buffer_prosa:
                texto_prosa = "\n".join(buffer_prosa).strip()
                if texto_prosa:
                    bloques.append(BloqueProsa(texto_prosa))
                buffer_prosa = []
            # Parsear tabla
            headers = _parsear_celdas(linea)
            j = i + 2
            rows: list[list[str]] = []
            while j < len(lineas) and _TABLE_LINE.match(lineas[j]):
                rows.append(_parsear_celdas(lineas[j]))
                j += 1
            bloques.append(BloqueTabla(headers=headers, rows=rows))
            i = j
        else:
            buffer_prosa.append(linea)
            i += 1

    if buffer_prosa:
        texto_prosa = "\n".join(buffer_prosa).strip()
        if texto_prosa:
            bloques.append(BloqueProsa(texto_prosa))

    return bloques


def _parsear_celdas(linea: str) -> list[str]:
    """`'| a | b | c |'` → `['a', 'b', 'c']`."""
    interior = linea.strip().strip("|")
    return [c.strip() for c in interior.split("|")]


def font_size_para_tabla(*, n_filas: int, n_columnas: int) -> int:
    """Heurística de tamaño de letra (pt) para tablas según su densidad.

    Objetivo: que tablas grandes quepan en una hoja A4 sin perder legibilidad.
    Mínimo absoluto: 7pt. Las columnas también pesan: una tabla 10×8 escala
    igual que una 30×2.

    Tabla de decisión (aproximada):
    - hasta 15 filas y ≤ 4 columnas → 10pt (tamaño normal).
    - hasta 30 filas o 5-6 columnas → 9pt.
    - hasta 60 filas o 7-8 columnas → 8pt.
    - más allá → 7pt (mínimo).
    """
    densidad = n_filas + n_columnas * 4  # cada columna pesa 4 filas-equivalentes
    if densidad <= 23:
        return 10
    if densidad <= 38:
        return 9
    if densidad <= 60:
        return 8
    return 7
