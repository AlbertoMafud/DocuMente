"""DTOs para eventos de auditoría."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.core.models import EventoAuditoria
from src.core.models.auditoria import TipoEvento


class EventoDTO(BaseModel):
    """Vista de un evento del audit_trail."""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    actor: str
    tipo: TipoEvento
    descripcion: str
    seccion_id: str | None = None
    metadata: dict[str, str] = {}

    @classmethod
    def from_domain(cls, e: EventoAuditoria) -> EventoDTO:
        return cls(
            timestamp=e.timestamp,
            actor=e.actor,
            tipo=e.tipo,
            descripcion=e.descripcion,
            seccion_id=e.seccion_id,
            metadata=dict(e.metadata),
        )
