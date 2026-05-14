"""Lector de DOCX secundario — extrae solo texto plano.

A diferencia del `DocxReader` principal de `src/docs/reader.py` que parsea
estructura del template NYL, este reader solo extrae párrafos y celdas de
tablas como texto, sin interpretar headings ni mapear a secciones.

Útil cuando el usuario adjunta un `.docx` como **fuente de contexto**
adicional (instructivos, procedimientos viejos, notas técnicas) en lugar
de como ancla estructural del documento.
"""

from __future__ import annotations

from typing import IO

from docx import Document as DocxDocument


def leer_docx_texto(archivo: IO[bytes]) -> str:
    """Devuelve párrafos + tablas como texto plano, separados por saltos de línea."""
    archivo.seek(0)
    doc = DocxDocument(archivo)

    fragmentos: list[str] = []

    for parrafo in doc.paragraphs:
        texto = parrafo.text.strip()
        if texto:
            fragmentos.append(texto)

    for tabla in doc.tables:
        for fila in tabla.rows:
            celdas = [c.text.strip() for c in fila.cells]
            if any(celdas):
                fragmentos.append(" | ".join(celdas))

    return "\n".join(fragmentos)
