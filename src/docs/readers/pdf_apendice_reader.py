"""Renderiza un PDF como secuencia de imágenes PNG para embeber en el DOCX.

Diferenciado de `pdf_anchor_reader.py` (que parsea texto plano para mapear
a secciones NYL del ancla estructural) y de `pdf_reader.py` (que solo
extrae texto plano para `FuenteContexto`). Este reader convierte CADA
PÁGINA del PDF a una imagen PNG, lista para embebirla en el apéndice
del DOCX final.

Útil cuando el contenido del PDF tiene fórmulas matemáticas, gráficas,
diagramas o layout complejo que no se puede preservar con texto plano —
caso del área de Inversiones (#9).
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import IO

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# DPI alto para que las fórmulas se vean nítidas en Word a tamaño Letter.
# 200 DPI es un balance entre nitidez (>150) y tamaño de archivo (>250 explota).
_DPI_DEFAULT = 200


def renderizar_pdf_a_paginas_png(
    archivo: IO[bytes] | bytes,
    *,
    dpi: int = _DPI_DEFAULT,
    max_paginas: int | None = None,
) -> list[bytes]:
    """Convierte cada página del PDF a una imagen PNG.

    Args:
        archivo: file-like o bytes crudos del PDF.
        dpi: resolución de render. Default 200 (alto pero razonable).
        max_paginas: límite duro de páginas a renderizar. None = sin límite.
            Útil para evitar que PDFs muy grandes (>30 páginas) inflen el .docx.

    Returns:
        Lista de bytes PNG, una por página, en orden.
    """
    if isinstance(archivo, bytes):
        stream = archivo
    else:
        archivo.seek(0)
        stream = archivo.read()

    # PyMuPDF acepta bytes vía `stream=` + `filetype="pdf"`.
    pdf = fitz.open(stream=stream, filetype="pdf")
    try:
        total = pdf.page_count
        n = min(total, max_paginas) if max_paginas is not None else total

        # `Matrix(zoom, zoom)` controla el DPI. 72 es la base de PDF.
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        paginas_png: list[bytes] = []
        for i in range(n):
            try:
                page = pdf.load_page(i)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                paginas_png.append(pixmap.tobytes("png"))
            except Exception as exc:
                logger.warning(
                    "Falló renderizado de página %d del PDF: %s",
                    i + 1,
                    exc,
                    exc_info=True,
                )
                continue
        return paginas_png
    finally:
        pdf.close()


def contar_paginas_pdf(archivo: IO[bytes] | bytes) -> int:
    """Devuelve la cantidad de páginas del PDF sin renderizar."""
    if isinstance(archivo, bytes):
        stream = archivo
    else:
        archivo.seek(0)
        stream = archivo.read()
    pdf = fitz.open(stream=stream, filetype="pdf")
    try:
        return pdf.page_count
    finally:
        pdf.close()


def renderizar_desde_path(path: str, *, dpi: int = _DPI_DEFAULT) -> list[bytes]:
    """Convenience: lee un PDF desde disco y devuelve PNGs."""
    with open(path, "rb") as f:
        contenido = f.read()
    return renderizar_pdf_a_paginas_png(BytesIO(contenido), dpi=dpi)
