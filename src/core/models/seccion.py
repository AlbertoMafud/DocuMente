"""Modelo de dominio: Seccion.

Una sección del documento de modelo. Su estructura, ID y obligatoriedad
se derivan del catálogo definido en `src.core.template_catalog` (que a
su vez refleja `docs/TEMPLATE_MODEL_DEV.md`).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Completitud = Literal["vacia", "parcial", "completa", "omitida"]


class Seccion(BaseModel):
    """Una sección del documento de modelo (ej. '4.4 Key Assumptions')."""

    model_config = ConfigDict(frozen=False, str_strip_whitespace=True)

    id: str = Field(
        ...,
        description="ID estable de la sección, ej. '4.4.assumptions'.",
    )
    nombre: str = Field(
        ...,
        description="Nombre oficial de la sección, ej. 'Key Assumptions'.",
    )
    numero: str = Field(
        ...,
        description="Número jerárquico, ej. '4.4'.",
    )
    obligatoria: bool = Field(
        ...,
        description="Si la sección es obligatoria según el template oficial NYL.",
    )
    contenido: str | None = Field(
        default=None,
        description="Contenido textual de la sección. None = nunca se ha tocado.",
    )
    completitud: Completitud = Field(
        default="vacia",
        description="Estado de completitud, derivado de heurísticas en GapAnalyzer.",
    )
    intencion: str = Field(
        default="",
        description="Qué información debe capturar esta sección (extraído de TEMPLATE_MODEL_DEV.md).",
    )
    preguntas_guia: list[str] = Field(
        default_factory=list,
        description="Preguntas que el InterviewEngine usará para llenar esta sección.",
    )
    motivo_omision: str | None = Field(
        default=None,
        description="Si la sección se marcó como omitida, justificación capturada del usuario.",
    )

    @property
    def tiene_contenido(self) -> bool:
        """True si la sección tiene contenido no vacío."""
        return bool(self.contenido and self.contenido.strip())
