"""Readers de fuentes de contexto (PDF, XLSX, TXT, DOCX secundario).

Diferenciados del `DocxReader` principal de `src/docs/reader.py`, que parsea
el .docx "ancla" estructural contra el catálogo de secciones NYL. Estos
readers solo extraen texto plano para alimentar `SugerenciasMultiFuente`.
"""

from __future__ import annotations

from io import BytesIO
from typing import IO

from src.core.models import TipoFuente
from src.docs.readers.docx_reader_simple import leer_docx_texto
from src.docs.readers.pdf_reader import leer_pdf
from src.docs.readers.txt_reader import leer_txt
from src.docs.readers.xlsx_reader import leer_xlsx


def extraer_texto(archivo: IO[bytes] | bytes, nombre_archivo: str) -> tuple[TipoFuente, str]:
    """Detecta el tipo de archivo por extensión y devuelve `(tipo, texto)`.

    Acepta tanto `BytesIO`/`IO[bytes]` (lo que envía Streamlit) como bytes crudos.
    Levanta `ValueError` si la extensión no está soportada.
    """
    nombre_lower = nombre_archivo.lower().strip()
    if isinstance(archivo, bytes):
        buf: IO[bytes] = BytesIO(archivo)
    else:
        buf = archivo

    if nombre_lower.endswith(".pdf"):
        return "pdf", leer_pdf(buf)
    if nombre_lower.endswith((".xlsx", ".xlsm")):
        return "xlsx", leer_xlsx(buf)
    if nombre_lower.endswith(".txt"):
        return "txt", leer_txt(buf)
    if nombre_lower.endswith(".docx"):
        return "docx", leer_docx_texto(buf)
    raise ValueError(
        f"Tipo de archivo no soportado: '{nombre_archivo}'. "
        "Soportados: .pdf, .xlsx, .xlsm, .txt, .docx."
    )


EXTENSIONES_SOPORTADAS: tuple[str, ...] = ("pdf", "xlsx", "xlsm", "txt", "docx")

__all__ = ["EXTENSIONES_SOPORTADAS", "extraer_texto"]
