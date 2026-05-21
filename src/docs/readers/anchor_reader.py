"""AnchorReader — factory que despacha .docx vs .pdf al reader correspondiente.

`DocxReader` y `PdfAnchorReader` exponen el mismo método `leer(ruta, user_id)`
que devuelve un `Documento` poblado con las secciones detectadas. Esta factory
decide cuál usar según la extensión del archivo.

Uso típico desde `ImportarDocumento`::

    reader = AnchorReader()
    documento = reader.leer(ruta, user_id=user_id)

Si la extensión no está soportada, levanta `ValueError`.
"""

from __future__ import annotations

from pathlib import Path

from src.core.models import Documento
from src.docs.reader import DocxReader
from src.docs.readers.pdf_anchor_reader import PdfAnchorReader


class AnchorReader:
    """Factory que delega según extensión: .docx → DocxReader, .pdf → PdfAnchorReader."""

    def __init__(
        self,
        docx_reader: DocxReader | None = None,
        pdf_reader: PdfAnchorReader | None = None,
    ) -> None:
        self._docx = docx_reader or DocxReader()
        self._pdf = pdf_reader or PdfAnchorReader()

    def leer(self, ruta: Path, user_id: str = "default") -> Documento:
        ext = ruta.suffix.lower()
        if ext == ".docx":
            return self._docx.leer(ruta, user_id=user_id)
        if ext == ".pdf":
            return self._pdf.leer(ruta, user_id=user_id)
        raise ValueError(f"Tipo de archivo ancla no soportado: '{ext}'. Soportados: .docx, .pdf.")
