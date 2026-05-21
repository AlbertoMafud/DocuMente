"""Tests del PdfApendiceReader (C.1)."""

from __future__ import annotations

from io import BytesIO

import fitz  # PyMuPDF
import pytest

from src.docs.readers.pdf_apendice_reader import (
    contar_paginas_pdf,
    renderizar_pdf_a_paginas_png,
)


def _crear_pdf_de_n_paginas(n: int) -> bytes:
    """Construye un PDF con n páginas en memoria. Cada página tiene texto distinto."""
    doc = fitz.open()
    for i in range(n):
        page = doc.new_page(width=612, height=792)  # Letter size
        page.insert_text(
            (72, 100),
            f"Página de prueba {i + 1}",
            fontsize=24,
        )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_renderiza_una_imagen_por_pagina() -> None:
    pdf_bytes = _crear_pdf_de_n_paginas(3)
    paginas = renderizar_pdf_a_paginas_png(pdf_bytes)
    assert len(paginas) == 3
    for png in paginas:
        # Cada imagen es PNG válido (firma `\x89PNG\r\n\x1a\n`)
        assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_max_paginas_limita_render() -> None:
    pdf_bytes = _crear_pdf_de_n_paginas(5)
    paginas = renderizar_pdf_a_paginas_png(pdf_bytes, max_paginas=2)
    assert len(paginas) == 2


def test_renderiza_acepta_bytesio() -> None:
    pdf_bytes = _crear_pdf_de_n_paginas(1)
    buf = BytesIO(pdf_bytes)
    paginas = renderizar_pdf_a_paginas_png(buf)
    assert len(paginas) == 1


def test_contar_paginas_devuelve_n_correcto() -> None:
    pdf_bytes = _crear_pdf_de_n_paginas(7)
    assert contar_paginas_pdf(pdf_bytes) == 7


def test_dpi_mas_alto_genera_imagen_mas_grande() -> None:
    pdf_bytes = _crear_pdf_de_n_paginas(1)
    png_low = renderizar_pdf_a_paginas_png(pdf_bytes, dpi=72)[0]
    png_high = renderizar_pdf_a_paginas_png(pdf_bytes, dpi=300)[0]
    assert len(png_high) > len(png_low)


def test_pdf_corrupto_levanta_excepcion() -> None:
    pdf_basura = b"este no es un PDF v\xc3\xa1lido"
    with pytest.raises(Exception):  # noqa: B017
        renderizar_pdf_a_paginas_png(pdf_basura)
