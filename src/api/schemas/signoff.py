"""DTOs para POST /documentos/{id}/signoff."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RolSignoff = Literal["reviewer", "fae"]


class RegistrarSignoffRequest(BaseModel):
    """Payload para registrar firma de Reviewer o FAE.

    El actor (user_id) firma como `rol`. El use case verifica independencia
    respecto a Owner y Developer del modelo (MRM §3.5).
    """

    rol: RolSignoff
    actor: str = Field(default="default", description="user_id del firmante.")
