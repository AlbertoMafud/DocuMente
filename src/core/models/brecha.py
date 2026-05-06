"""Modelo de dominio: Brecha.

Una brecha (gap) es una diferencia detectada entre lo que el documento contiene
hoy y lo que el template oficial NYL exige. El GapAnalyzer produce una lista
de brechas por documento; la UI las muestra como cards verde/amarillo/rojo.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severidad = Literal["alta", "media", "baja"]
TipoBrecha = Literal[
    "seccion_faltante",
    "seccion_vacia",
    "seccion_incompleta",
    "metadata_faltante",
    "supuesto_no_documentado",
    "limitacion_no_documentada",
]


class Brecha(BaseModel):
    """Una brecha detectada por el GapAnalyzer."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    seccion_id: str = Field(
        ...,
        description="ID de la sección afectada, ej. '4.4.assumptions'.",
    )
    tipo: TipoBrecha = Field(...)
    severidad: Severidad = Field(...)
    mensaje: str = Field(
        ...,
        description="Mensaje en lenguaje natural para mostrar al usuario.",
    )
    sugerencia: str = Field(
        default="",
        description="Acción sugerida para cerrar la brecha.",
    )
