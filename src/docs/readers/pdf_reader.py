"""Lector de PDF — extrae texto plano de todas las páginas vía `pypdf`."""

from __future__ import annotations

from typing import IO

from pypdf import PdfReader


def leer_pdf(archivo: IO[bytes]) -> str:
    """Devuelve el texto plano concatenado de todas las páginas del PDF.

    Tolerante a PDFs escaneados (devuelve string vacío si no hay capa de texto).
    No hace OCR. Si el PDF tiene contraseña, levanta excepción de pypdf.
    """
    archivo.seek(0)
    reader = PdfReader(archivo)
    fragmentos: list[str] = []
    for i, pagina in enumerate(reader.pages, start=1):
        try:
            texto = pagina.extract_text() or ""
        except Exception:
            texto = ""
        if texto.strip():
            fragmentos.append(f"--- Página {i} ---\n{texto.strip()}")
    return "\n\n".join(fragmentos)
