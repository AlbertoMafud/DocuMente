"""Modelos de dominio Pydantic."""

from src.core.models.apendice import Apendice, TipoApendice
from src.core.models.auditoria import EventoAuditoria, TipoEvento
from src.core.models.brecha import Brecha, Severidad, TipoBrecha
from src.core.models.documento import (
    Documento,
    EstadoDocumento,
    MetadataModelo,
    TierRiesgo,
    TipoDocumento,
)
from src.core.models.entrevista import EstadoEntrevista, MensajeEntrevista, RolMensaje
from src.core.models.fuente_contexto import FuenteContexto, TipoFuente
from src.core.models.memoria import MemoriaModelo
from src.core.models.metricas import LlamadaLLM, MetricasUso
from src.core.models.seccion import Completitud, Seccion
from src.core.models.template_dinamico import (
    EstadoTemplate,
    HallazgoLint,
    ResultadoLint,
    SeccionCatalogoDinamica,
    TemplateDinamico,
    TipoContenido,
)
from src.core.models.version import Version, calcular_hash

__all__ = [
    "Apendice",
    "Brecha",
    "Completitud",
    "Documento",
    "EstadoDocumento",
    "EstadoEntrevista",
    "EstadoTemplate",
    "EventoAuditoria",
    "FuenteContexto",
    "HallazgoLint",
    "LlamadaLLM",
    "MemoriaModelo",
    "MensajeEntrevista",
    "MetadataModelo",
    "MetricasUso",
    "ResultadoLint",
    "RolMensaje",
    "Seccion",
    "SeccionCatalogoDinamica",
    "Severidad",
    "TemplateDinamico",
    "TierRiesgo",
    "TipoApendice",
    "TipoBrecha",
    "TipoContenido",
    "TipoDocumento",
    "TipoEvento",
    "TipoFuente",
    "Version",
    "calcular_hash",
]
