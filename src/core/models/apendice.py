"""Apendice: tablas de datos / diagramas / soportes que viven al final del DOCX.

Para secciones data-heavy (4.4 Assumptions, 5.1 Raw Data, 5.2 Upstream Models),
el flujo correcto MRM es: la sección principal contiene narrativa + resumen,
y los datos detallados (tablas grandes, listados completos de supuestos) viven
en apéndices numerados al final del documento.

DocuMente auto-crea apéndices cuando el usuario sube un Excel/CSV durante la
entrevista de una sección data-heavy.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

TipoApendice = Literal["tabla", "diagrama", "pdf", "formula", "otro"]


class Apendice(BaseModel):
    """Un apéndice del documento, vinculado a una sección de origen."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    seccion_origen_id: str
    """ID de la sección que motivó este apéndice, ej. '4.4.assumptions'."""
    titulo: str
    """Ej. 'Tabla de mortalidad SOA 2017'."""
    tipo: TipoApendice = "tabla"
    contenido_md: str = ""
    """Contenido del apéndice en markdown (para vista previa y DOCX).

    Para `tipo='pdf'`: vacío — el contenido visual son las páginas renderizadas
    cargadas desde `archivo_id_storage` al exportar.
    Para `tipo='formula'`: vacío — el source LaTeX vive en `latex_source`.
    """
    archivo_id_storage: str | None = None
    """ID en Storage del archivo original (.xlsx, .csv, .pdf) si fue cargado."""
    nombre_archivo_original: str = ""
    """Nombre del archivo original cargado por el usuario."""
    latex_source: str = ""
    """Source LaTeX para `tipo='formula'`. Vacío para otros tipos. (C.1)"""
    creado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def referencia_corta(self) -> str:
        """Texto corto para referenciar el apéndice desde la sección principal."""
        return f"ver Apéndice: {self.titulo}"
