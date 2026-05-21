"""DTOs para Documento — request/response de los endpoints /documentos."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.api.schemas.seccion import SeccionDTO
from src.core.models import Documento
from src.core.models.documento import (
    EstadoDocumento,
    EstadoVisibilidad,
    MetadataModelo,
    TierRiesgo,
    TipoDocumento,
)


class MetadataModeloDTO(BaseModel):
    """Metadata estructurada del modelo (tabla de atributos, sección 1.1)."""

    model_config = ConfigDict(from_attributes=True)

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
    nomenclatura: str = ""

    @classmethod
    def from_domain(cls, m: MetadataModelo) -> MetadataModeloDTO:
        return cls.model_validate(m, from_attributes=True)


class DocumentoListItem(BaseModel):
    """Vista resumida de un Documento para listas (home, dashboard)."""

    id: UUID
    user_id: str
    tipo: TipoDocumento
    estado: EstadoDocumento
    visibilidad: EstadoVisibilidad
    nombre_modelo: str = Field(..., description="metadata_modelo.nombre_modelo o ''.")
    porcentaje_completitud: float
    porcentaje_resuelto: float
    n_secciones: int
    n_secciones_obligatorias: int
    creado_en: datetime
    actualizado_en: datetime
    archivado: bool
    en_papelera: bool

    @classmethod
    def from_domain(cls, d: Documento) -> DocumentoListItem:
        return cls(
            id=d.id,
            user_id=d.user_id,
            tipo=d.tipo,
            estado=d.estado,
            visibilidad=d.visibilidad,
            nombre_modelo=d.metadata_modelo.nombre_modelo or "",
            porcentaje_completitud=d.porcentaje_completitud,
            porcentaje_resuelto=d.porcentaje_resuelto,
            n_secciones=len(d.secciones),
            n_secciones_obligatorias=len(d.secciones_obligatorias),
            creado_en=d.creado_en,
            actualizado_en=d.actualizado_en,
            archivado=d.archivado,
            en_papelera=d.en_papelera,
        )


class DocumentoDTO(BaseModel):
    """Vista completa de un Documento — incluye secciones."""

    id: UUID
    user_id: str
    tipo: TipoDocumento
    estado: EstadoDocumento
    visibilidad: EstadoVisibilidad
    metadata_modelo: MetadataModeloDTO
    secciones: list[SeccionDTO]
    porcentaje_completitud: float
    porcentaje_resuelto: float
    cobertura_catalogo: float
    creado_en: datetime
    actualizado_en: datetime
    archivo_origen: str | None = None
    archivado: bool
    archivado_en: datetime | None = None
    en_papelera: bool
    n_eventos_audit: int

    @classmethod
    def from_domain(cls, d: Documento) -> DocumentoDTO:
        return cls(
            id=d.id,
            user_id=d.user_id,
            tipo=d.tipo,
            estado=d.estado,
            visibilidad=d.visibilidad,
            metadata_modelo=MetadataModeloDTO.from_domain(d.metadata_modelo),
            secciones=[SeccionDTO.from_domain(s) for s in d.secciones],
            porcentaje_completitud=d.porcentaje_completitud,
            porcentaje_resuelto=d.porcentaje_resuelto,
            cobertura_catalogo=d.cobertura_catalogo,
            creado_en=d.creado_en,
            actualizado_en=d.actualizado_en,
            archivo_origen=d.archivo_origen,
            archivado=d.archivado,
            archivado_en=d.archivado_en,
            en_papelera=d.en_papelera,
            n_eventos_audit=len(d.audit_trail),
        )


class CrearDocumentoRequest(BaseModel):
    """Payload para POST /documentos.

    Crea un documento en blanco con las secciones del template oficial.
    Si `tipo='prophet'`, usa el catálogo Prophet.
    """

    tipo: TipoDocumento = "model_development"
    nombre_modelo: str = Field(
        default="",
        description="Nombre opcional inicial. Editable después en metadata.",
    )
    actor: str = Field(default="default", description="user_id del creador.")


class EditarMetadataRequest(BaseModel):
    """Payload para PATCH /documentos/{id}/metadata.

    Todos los campos son opcionales — solo se actualizan los enviados.
    """

    nombre_modelo: str | None = None
    model_id: str | None = None
    model_class: str | None = None
    profit_center: str | None = None
    fae: str | None = None
    model_owner: str | None = None
    model_developers: list[str] | None = None
    model_users: list[str] | None = None
    current_version: str | None = None
    implementation_platform: str | None = None
    financial_impact: str | None = None
    model_status: str | None = None
    target_production_date: str | None = None
    inherent_risk_tier: TierRiesgo | None = None
    intended_use: str | None = None
    use_restrictions: str | None = None
    nomenclatura: str | None = None
