"""Modelo de dominio: FuenteContexto.

Representa un archivo adicional (PDF, XLSX, TXT, DOCX secundario) que el usuario
adjunta al importar/crear un documento, distinto del docx "ancla" estructural.

Su texto extraído alimenta `SugerenciasMultiFuente`, que pre-popula las
secciones vacías del template con borradores marcados como
`[Borrador automático — revisar]`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

TipoFuente = Literal["pdf", "xlsx", "txt", "docx"]


class FuenteContexto(BaseModel):
    """Archivo adicional cuyo texto sirve como contexto para sugerencias."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    nombre_archivo: str
    tipo: TipoFuente
    texto_extraido: str = Field(
        description="Texto plano extraído del archivo, listo para pasarle a Claude."
    )
    creado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))
