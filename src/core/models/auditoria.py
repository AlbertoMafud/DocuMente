"""Modelo de dominio: EventoAuditoria.

Cada cambio en un Documento se registra como un EventoAuditoria inmutable.
Esto materializa el requisito de trazabilidad del MRM Standard §3.5
(documentación debe registrar quién hizo qué cuándo).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TipoEvento = Literal[
    "documento_creado",
    "documento_importado",
    "seccion_editada",
    "seccion_completada",
    "seccion_omitida",
    "transicion_estado",
    "metadata_actualizada",
    "exportado",
    "signoff_reviewer",
    "signoff_fae",
]


class EventoAuditoria(BaseModel):
    """Evento inmutable registrado en el audit_trail de un Documento."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: str = Field(
        ...,
        description="user_id del actor (en MVP siempre 'default').",
    )
    tipo: TipoEvento = Field(...)
    descripcion: str = Field(
        ...,
        description="Descripción humana del evento, ej. 'Editó sección 4.4 Key Assumptions'.",
    )
    seccion_id: str | None = Field(
        default=None,
        description="ID de la sección afectada, si aplica.",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Metadata adicional del evento (estado origen, estado destino, etc.).",
    )
