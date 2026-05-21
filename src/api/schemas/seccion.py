"""DTOs para Seccion."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.core.models import Seccion
from src.core.models.seccion import Completitud


class SeccionDTO(BaseModel):
    """Vista completa de una sección."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    numero: str
    obligatoria: bool
    contenido: str | None = None
    completitud: Completitud = "vacia"
    intencion: str = ""
    preguntas_guia: list[str] = Field(default_factory=list)
    motivo_omision: str | None = None
    tiene_contenido: bool

    @classmethod
    def from_domain(cls, s: Seccion) -> SeccionDTO:
        return cls(
            id=s.id,
            nombre=s.nombre,
            numero=s.numero,
            obligatoria=s.obligatoria,
            contenido=s.contenido,
            completitud=s.completitud,
            intencion=s.intencion,
            preguntas_guia=list(s.preguntas_guia),
            motivo_omision=s.motivo_omision,
            tiene_contenido=s.tiene_contenido,
        )


class EditarSeccionRequest(BaseModel):
    """Payload para PUT /documentos/{id}/secciones/{sid}.

    El contenido es markdown libre (MRM) o JSON estructurado (Prophet).
    La completitud se recalcula automáticamente según la longitud del
    contenido — el caller no necesita enviarla.
    """

    contenido: str = Field(..., description="Contenido nuevo (markdown o JSON).")
    actor: str = "default"


class OmitirSeccionRequest(BaseModel):
    """Payload para POST /documentos/{id}/secciones/{sid}/omitir."""

    motivo: str = Field(
        ...,
        description=(
            "Razón documentada — del catálogo MOTIVOS_OMISION o texto libre. "
            "No puede estar vacío (decisión auditable MRM §3.5)."
        ),
    )
    actor: str = "default"
