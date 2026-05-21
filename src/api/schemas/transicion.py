"""DTOs para POST /documentos/{id}/estado (cambio de estado MRM)."""

from __future__ import annotations

from pydantic import BaseModel

from src.core.models.documento import EstadoDocumento


class CambiarEstadoRequest(BaseModel):
    """Payload para transición del documento entre estados MRM.

    Las transiciones válidas se definen en src.core.rules.DocumentStateMachine.
    Si la transición es inválida, devuelve 409 Conflict con las razones.
    """

    destino: EstadoDocumento
    actor: str = "default"
