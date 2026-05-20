"""DTOs para entrevista (iniciar y responder preguntas)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.core.models.entrevista import MensajeEntrevista

RolMensaje = Literal["user", "assistant", "system_note"]


class MensajeDTO(BaseModel):
    """Un mensaje del chat de entrevista."""

    rol: RolMensaje
    contenido: str

    @classmethod
    def from_domain(cls, m: MensajeEntrevista) -> MensajeDTO:
        return cls(rol=m.rol, contenido=m.contenido)


class TurnoEntrevistaDTO(BaseModel):
    """Un turno de entrevista: pregunta del asistente + estado actual."""

    respuesta_asistente: str = Field(..., description="Pregunta o cierre del asistente.")
    seccion_cerrada: bool = Field(
        ...,
        description="True si la sección quedó cerrada (con borrador suficiente) este turno.",
    )
    borrador: str | None = Field(
        default=None,
        description="Si la sección cerró, borrador final que se guardó.",
    )
    n_mensajes: int = Field(..., description="Total acumulado de mensajes en la sesión.")


class IniciarEntrevistaResponse(BaseModel):
    """Respuesta del POST /entrevista/iniciar."""

    turno: TurnoEntrevistaDTO
    seccion_id: str
    mensajes: list[MensajeDTO] = Field(
        default_factory=list,
        description="Historial completo (puede traer mensajes previos si la entrevista se reanudó).",
    )


class ResponderPreguntaRequest(BaseModel):
    """Payload del POST /entrevista/responder."""

    respuesta: str = Field(..., description="Texto libre del usuario.")
    actor: str = "default"
