"""Modelo de dominio: Version — snapshot inmutable del Documento.

Cada export DOCX puede crear una nueva versión (opt-in vía toggle en la UI).
La versión guarda:
- snapshot_json: el `Documento` Pydantic serializado completo. Permite
  reconstruir el estado exacto que se exportó.
- hash_contenido: SHA-256 del payload. Útil para detectar si dos versiones
  son idénticas (caso: usuario exporta dos veces sin editar nada en medio).
- numero: monotónicamente creciente por documento (v1, v2, v3…).
- comentario: opcional, lo que el usuario escribe al crear la versión.

Las versiones son inmutables — no se editan ni se eliminan. Para "deshacer"
una versión, se restaura el snapshot al estado actual del documento.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Version(BaseModel):
    """Snapshot inmutable de un Documento en un punto del tiempo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    documento_id: UUID
    numero: int = Field(..., ge=1, description="Monotónicamente creciente por documento (1, 2, …)")
    snapshot_json: str = Field(..., description="Payload del Documento serializado.")
    hash_contenido: str = Field(..., description="SHA-256 del snapshot_json (hex).")
    comentario: str = Field(default="", description="Comentario libre opcional del usuario.")
    creado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))


def calcular_hash(snapshot_json: str) -> str:
    """SHA-256 hex del payload, usado como `hash_contenido`."""
    return hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()
