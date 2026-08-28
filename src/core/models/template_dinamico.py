"""Modelos de dominio del Template Studio (templates dinámicos).

Un template dinámico es un catálogo de secciones AI-ready creado en el
Template Studio y persistido como DATOS (payload JSON en BD), no como
código. Razón crítica: un template nuevo no debe exigir migración de
código a la instancia corporativa. Ver docs/TEMPLATE_STUDIO_SPEC.md §6
y las reglas de conversión en docs/TEMPLATE_AIREADY_RULES.md.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.core.models.auditoria import EventoAuditoria

TipoContenido = Literal["texto", "tabla", "campos"]
EstadoTemplate = Literal["borrador", "propuesto", "publicado", "retirado"]
SeveridadLint = Literal["error", "advertencia"]


class HallazgoLint(BaseModel):
    """Un hallazgo del lint de AI-readiness (checks L1-L9)."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    codigo: str = Field(..., description="Código del check, ej. 'L4'.")
    severidad: SeveridadLint
    seccion_id: str | None = Field(
        default=None,
        description="Sección afectada; None si el hallazgo es del template completo.",
    )
    mensaje: str = Field(..., description="Explicación legible para el curador.")


class ResultadoLint(BaseModel):
    """Resultado de una corrida del lint (capa determinística y/o dry-run)."""

    hallazgos: list[HallazgoLint] = Field(default_factory=list)
    incluyo_dry_run: bool = False
    ejecutado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def errores(self) -> list[HallazgoLint]:
        return [h for h in self.hallazgos if h.severidad == "error"]

    @property
    def advertencias(self) -> list[HallazgoLint]:
        return [h for h in self.hallazgos if h.severidad == "advertencia"]

    @property
    def aprobado(self) -> bool:
        """True si no hay errores bloqueantes (advertencias no bloquean)."""
        return not self.errores


class SeccionCatalogoDinamica(BaseModel):
    """Una sección AI-ready de un template dinámico.

    Superset deliberado de `SeccionCatalogo` (MRM) y `SeccionCatalogoProphet`:
    cualquier template existente es expresable en este formato, lo que permite
    al registro (`template_registry`) envolver los catálogos congelados sin
    tocarlos.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Slug estable; NUNCA cambia una vez asignado (R1).")
    numero: str = Field(
        ..., description="Número jerárquico, ej. '4' o '4.1'. Reordenar cambia esto, no el id."
    )
    nombre: str
    obligatoria: bool = True
    intencion: str = Field(
        default="",
        description="Qué conocimiento captura la sección — no qué formato tiene (R2).",
    )
    tipo_contenido: TipoContenido = "texto"
    schema_tabla: list[str] = Field(
        default_factory=list,
        description="Columnas de la tabla; obligatorio si tipo_contenido == 'tabla' (R6).",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Títulos alternativos en documentos reales, para importación (R4).",
    )
    preguntas_guia: list[str] = Field(
        default_factory=list,
        description="Preguntas de entrevistador experto del dominio (R3).",
    )


class TemplateDinamico(BaseModel):
    """Template creado en el Template Studio (entidad raíz de su propio ciclo)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    slug: str = Field(
        ...,
        description="Identificador del tipo de documento, ej. 'procedimiento_operativo'. Es el valor que viaja en Documento.tipo.",
    )
    nombre: str = Field(..., description="Nombre humano, ej. 'Ficha de Procedimiento Operativo'.")
    descripcion: str = ""
    area_duena: str = ""
    version: int = 1
    estado: EstadoTemplate = "borrador"
    secciones: list[SeccionCatalogoDinamica] = Field(default_factory=list)
    creado_por: str = "default"
    archivo_origen: str | None = Field(
        default=None,
        description="Nombre del .docx del que se extrajo la estructura, si aplica.",
    )
    resultado_lint: ResultadoLint | None = None
    audit_trail: list[EventoAuditoria] = Field(default_factory=list)
    creado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actualizado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def seccion_por_id(self, seccion_id: str) -> SeccionCatalogoDinamica | None:
        return next((s for s in self.secciones if s.id == seccion_id), None)

    def registrar_evento(self, evento: EventoAuditoria) -> None:
        """Agrega un evento al audit_trail y actualiza `actualizado_en`."""
        self.audit_trail.append(evento)
        self.actualizado_en = datetime.now(UTC)
