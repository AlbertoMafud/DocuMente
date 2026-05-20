"""DTOs para Brecha."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.core.models import Brecha
from src.core.models.brecha import Severidad, TipoBrecha


class BrechaDTO(BaseModel):
    """Vista de una brecha detectada por el GapAnalyzer."""

    model_config = ConfigDict(from_attributes=True)

    seccion_id: str
    tipo: TipoBrecha
    severidad: Severidad
    mensaje: str
    sugerencia: str = ""

    @classmethod
    def from_domain(cls, b: Brecha) -> BrechaDTO:
        return cls(
            seccion_id=b.seccion_id,
            tipo=b.tipo,
            severidad=b.severidad,
            mensaje=b.mensaje,
            sugerencia=b.sugerencia or "",
        )
