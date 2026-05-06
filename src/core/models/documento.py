"""Modelo de dominio: Documento.

Representa un documento de modelo en construcción. Es la entidad raíz del
dominio. Conoce su tipo, sus secciones, su estado en el ciclo de vida y su
audit trail completo.

Diseñado para que la migración a multi-usuario sea trivial: el campo `user_id`
ya existe desde MVP (siempre "default" hasta que se introduzca auth).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.core.models.apendice import Apendice
from src.core.models.auditoria import EventoAuditoria
from src.core.models.memoria import MemoriaModelo
from src.core.models.metricas import MetricasUso
from src.core.models.seccion import Seccion

TipoDocumento = Literal["model_development"]
EstadoDocumento = Literal["draft", "in_review", "approved", "published", "retired"]
TierRiesgo = Literal[
    "low",
    "medium_minus",
    "medium",
    "high",
    "very_high",
    "very_high_plus",
    "critical",
]


class MetadataModelo(BaseModel):
    """Metadata estructurada del modelo (tabla de atributos, sección 1.1)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_modelo: str = ""
    model_id: str = ""
    model_class: str = ""
    profit_center: str = ""
    fae: str = ""
    model_owner: str = ""
    model_developers: list[str] = Field(default_factory=list)
    model_users: list[str] = Field(default_factory=list)
    current_version: str = ""
    implementation_platform: str = ""
    financial_impact: str = ""
    model_status: str = ""
    target_production_date: str = ""
    inherent_risk_tier: TierRiesgo | None = None
    intended_use: str = ""
    use_restrictions: str = ""
    nomenclatura: str = Field(
        default="",
        description="Nomenclatura institucional, ej. 'M07.P07.S03.006.D'.",
    )


class Documento(BaseModel):
    """Documento de modelo institucional (entidad raíz del dominio)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(
        default="default",
        description="ID del usuario dueño. En MVP siempre 'default'; ya listo para multi-user.",
    )
    tipo: TipoDocumento = "model_development"
    estado: EstadoDocumento = "draft"
    metadata_modelo: MetadataModelo = Field(default_factory=MetadataModelo)
    secciones: list[Seccion] = Field(default_factory=list)
    audit_trail: list[EventoAuditoria] = Field(default_factory=list)
    creado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actualizado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))
    archivo_origen: str | None = Field(
        default=None,
        description="Path del .docx original importado, si aplica.",
    )
    # Campos agregados en Fase 2.5 — todos opcionales con defaults para
    # compatibilidad backwards con documentos persistidos previos.
    memoria_modelo: MemoriaModelo = Field(default_factory=MemoriaModelo)
    apendices: list[Apendice] = Field(default_factory=list)
    metricas_uso: MetricasUso = Field(default_factory=MetricasUso)

    def seccion_por_id(self, seccion_id: str) -> Seccion | None:
        """Devuelve la sección por su ID o None."""
        return next((s for s in self.secciones if s.id == seccion_id), None)

    @property
    def secciones_obligatorias(self) -> list[Seccion]:
        return [s for s in self.secciones if s.obligatoria]

    @property
    def porcentaje_completitud(self) -> float:
        """Porcentaje de secciones obligatorias en estado 'completa' (0.0 a 1.0)."""
        oblig = self.secciones_obligatorias
        if not oblig:
            return 0.0
        completas = sum(1 for s in oblig if s.completitud == "completa")
        return completas / len(oblig)

    def registrar_evento(self, evento: EventoAuditoria) -> None:
        """Agrega un evento al audit_trail y actualiza `actualizado_en`."""
        self.audit_trail.append(evento)
        self.actualizado_en = datetime.now(UTC)
