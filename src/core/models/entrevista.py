"""Modelos de dominio relacionados con la entrevista.

`MensajeEntrevista` es un turno individual del chat (usuario o asistente).
`EstadoEntrevista` es el estado conversacional persistido por sección.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RolMensaje = Literal["user", "assistant", "system_note"]


class MensajeEntrevista(BaseModel):
    """Un turno del chat de entrevista."""

    model_config = ConfigDict(str_strip_whitespace=True)

    rol: RolMensaje
    contenido: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EstadoEntrevista(BaseModel):
    """Estado conversacional para una sección específica del documento."""

    model_config = ConfigDict(str_strip_whitespace=True)

    documento_id: str
    seccion_id: str
    mensajes: list[MensajeEntrevista] = Field(default_factory=list)
    cerrada: bool = Field(
        default=False,
        description="True si Claude marcó la sección como SECCION_COMPLETA.",
    )
    actualizada_en: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def agregar(self, rol: RolMensaje, contenido: str) -> None:
        self.mensajes.append(MensajeEntrevista(rol=rol, contenido=contenido))
        self.actualizada_en = datetime.now(UTC)
