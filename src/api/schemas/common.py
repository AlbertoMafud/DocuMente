"""DTOs comunes: respuestas paginadas, OK genérico, error."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class OkResponse(BaseModel):
    """Respuesta genérica de éxito sin payload."""

    ok: bool = True
    mensaje: str = ""


class PaginatedResponse(BaseModel, Generic[T]):
    """Wrapper para listas paginadas — preparado para cursor pagination futura."""

    items: list[T]
    total: int = Field(..., description="Número total de items (sin pagination).")


class ErrorDetail(BaseModel):
    detail: str
    type: str = "error"
