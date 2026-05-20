"""DTOs para POST /documentos/{id}/exportar."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Idioma = Literal["es", "en", "es_normalize", "en_normalize", "bilingue"]


class ExportarRequest(BaseModel):
    """Opciones del export DOCX.

    Mapea 1:1 al `ExportarDocumento.ejecutar(...)`. Default: bilingue
    (sin cambiar el idioma del contenido) + sin polish + sin versión.
    """

    idioma_objetivo: Idioma = "bilingue"
    polish: bool = Field(
        default=False,
        description="Si True, ejecuta DocumentPolisher antes del export.",
    )
    crear_version: bool = Field(
        default=False,
        description="Si True, crea una versión inmutable (snapshot) al exportar.",
    )
    comentario_version: str = Field(default="", description="Comentario para la versión.")
    actor: str = "default"
