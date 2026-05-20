"""DTOs para Version (snapshots inmutables)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.core.models.version import Version


class VersionDTO(BaseModel):
    """Vista de un snapshot inmutable del documento.

    No incluye `snapshot_json` para mantener la lista liviana — el
    contenido se descarga vía endpoint separado.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    documento_id: UUID
    numero: int
    comentario: str
    creado_en: datetime
    hash_contenido: str

    @classmethod
    def from_domain(cls, v: Version) -> VersionDTO:
        return cls(
            id=v.id,
            documento_id=v.documento_id,
            numero=v.numero,
            comentario=v.comentario,
            creado_en=v.creado_en,
            hash_contenido=v.hash_contenido,
        )


class CrearVersionRequest(BaseModel):
    """Payload para POST /documentos/{id}/versiones."""

    comentario: str = ""
    actor: str = "default"
