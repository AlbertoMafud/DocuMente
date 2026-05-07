"""Cleanup de markdown narrativo para inserción en plantilla DOCX.

`docxtpl` solo hace string replacement — NO interpreta markdown. Cuando Claude
genera contenido con asteriscos, hashes o tablas pipe-separated, esos tokens
quedan literales en el .docx exportado y se ven feos. Este módulo convierte
el markdown narrativo a texto plano apto para incrustar en placeholders Jinja
sin perder legibilidad.

Política: este cleanup es defensivo y conservador. NO intenta reproducir tablas
nativas de Word (eso requeriría python-docx + manipulación post-render). En
cambio, simplifica la sintaxis para que el contenido se lea naturalmente como
párrafos. Las secciones tabulares oficiales (5.1, 5.2, 5.5, 6.5) ya tienen
extracción estructurada vía TableExtractor.
"""

from __future__ import annotations

import re

# Patrones precompilados
_BOLD_AST = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_AST = re.compile(r"(?<!\*)\*([^*\n]+?)\*(?!\*)")
_HASH_HEADING = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_HORIZONTAL_RULE = re.compile(r"^[\s]*[-*_]{3,}[\s]*$", re.MULTILINE)
_NUMBERED_LIST_ITEM = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_BULLET_VARIANTS = re.compile(r"^\s*[*+]\s+", re.MULTILINE)
_TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
_TABLE_SEPARATOR = re.compile(r"^\s*\|[\s\-:|]+\|\s*$", re.MULTILINE)


def limpiar_markdown(texto: str, *, conservar_enfasis: bool = False) -> str:
    """Convierte markdown narrativo a texto plano apto para Word.

    Reglas aplicadas, en orden:
    1. Tablas markdown → líneas con `<col>: <valor>` para cada celda no-header.
    2. Encabezados con `#` → texto sin los hashes.
    3. Negritas/cursivas con `*` → texto sin los asteriscos (a menos que
       `conservar_enfasis=True`, caso en el cual se preservan para que el
       renderizador Subdoc los convierta a bold/italic reales de Word).
    4. Reglas horizontales `---` → eliminadas.
    5. Listas numeradas y bullets `*`/`+` → normalizadas a `- ` (guion).
    6. Whitespace excesivo colapsado a máximo dos saltos consecutivos.
    """
    if not texto or not texto.strip():
        return ""

    salida = texto

    # 1. Convertir tablas markdown
    salida = _convertir_tablas_markdown(salida)

    # 2. Quitar hashes de encabezados
    salida = _HASH_HEADING.sub("", salida)

    # 3. Negritas y cursivas: solo quitar si NO conservamos énfasis.
    if not conservar_enfasis:
        # Bold debe ir antes que italic (** matchearía como dos *)
        salida = _BOLD_AST.sub(r"\1", salida)
        salida = _ITALIC_AST.sub(r"\1", salida)

    # 4. Reglas horizontales
    salida = _HORIZONTAL_RULE.sub("", salida)

    # 5. Listas numeradas → guion
    salida = _NUMBERED_LIST_ITEM.sub("- ", salida)

    # 6. Bullets * y + → guion (solo si no conservamos énfasis, porque *
    #    a inicio de línea podría ser bullet. Si conservamos énfasis, los
    #    bullets `*` se distinguen por contexto y los normalizamos solo si
    #    están al inicio de línea con espacio garantizado).
    if not conservar_enfasis:
        salida = _BULLET_VARIANTS.sub("- ", salida)
    else:
        # Versión más conservadora: solo `+` y bullets numerados ya manejados.
        salida = re.sub(r"^\s*\+\s+", "- ", salida, flags=re.MULTILINE)

    # 7. Colapsar más de 2 saltos consecutivos
    salida = re.sub(r"\n{3,}", "\n\n", salida)

    return salida.strip()


def _convertir_tablas_markdown(texto: str) -> str:
    """Detecta bloques de tabla markdown y los convierte a líneas legibles.

    Una tabla markdown tiene 3+ líneas con `|` al inicio: header, separador,
    filas. Convertimos cada fila de datos a un párrafo con `Header: Valor`
    por columna.
    """
    lineas = texto.splitlines()
    bloques_resultado: list[str] = []
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        # Detectar inicio de tabla: línea con pipes seguida de un separador
        if (
            _TABLE_LINE.match(linea)
            and i + 1 < len(lineas)
            and _TABLE_SEPARATOR.match(lineas[i + 1])
        ):
            header_celdas = _parsear_celdas(linea)
            j = i + 2
            filas: list[list[str]] = []
            while j < len(lineas) and _TABLE_LINE.match(lineas[j]):
                filas.append(_parsear_celdas(lineas[j]))
                j += 1
            bloques_resultado.append(_renderizar_tabla(header_celdas, filas))
            i = j
        else:
            bloques_resultado.append(linea)
            i += 1
    return "\n".join(bloques_resultado)


def _parsear_celdas(linea: str) -> list[str]:
    """Toma '| a | b | c |' y devuelve ['a', 'b', 'c']."""
    interior = linea.strip().strip("|")
    return [c.strip() for c in interior.split("|")]


def _renderizar_tabla(headers: list[str], filas: list[list[str]]) -> str:
    """Convierte una tabla a párrafos planos.

    Si solo hay 1 fila de datos: 'Header: Valor' por línea.
    Si hay varias: 'Item N:' + lista 'Header: Valor' indentada.
    """
    if not filas:
        return ""
    if len(filas) == 1:
        partes = [f"{h}: {v}" for h, v in zip(headers, filas[0], strict=False) if v.strip()]
        return "\n".join(partes)
    # Múltiples filas: numerar y listar
    bloques: list[str] = []
    for n, fila in enumerate(filas, start=1):
        bloques.append(f"Registro {n}:")
        for h, v in zip(headers, fila, strict=False):
            if v.strip():
                bloques.append(f"  - {h}: {v}")
        bloques.append("")
    return "\n".join(bloques).rstrip()
