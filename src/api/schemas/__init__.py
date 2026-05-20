"""DTOs de la API REST.

Separados del dominio (Pydantic models en src/core/models/) para que la
representación HTTP/JSON pueda evolucionar sin tocar el dominio. Los DTOs
incluyen métodos `from_domain(...)` para serializar entidades del dominio.
"""

from src.api.schemas.auditoria import EventoDTO
from src.api.schemas.brecha import BrechaDTO
from src.api.schemas.common import OkResponse, PaginatedResponse
from src.api.schemas.documento import (
    CrearDocumentoRequest,
    DocumentoDTO,
    DocumentoListItem,
    EditarMetadataRequest,
    MetadataModeloDTO,
)
from src.api.schemas.entrevista import (
    IniciarEntrevistaResponse,
    ResponderPreguntaRequest,
    TurnoEntrevistaDTO,
)
from src.api.schemas.exportar import ExportarRequest
from src.api.schemas.seccion import (
    EditarSeccionRequest,
    OmitirSeccionRequest,
    SeccionDTO,
)
from src.api.schemas.signoff import RegistrarSignoffRequest
from src.api.schemas.transicion import CambiarEstadoRequest
from src.api.schemas.version import CrearVersionRequest, VersionDTO

__all__ = [
    "BrechaDTO",
    "CambiarEstadoRequest",
    "CrearDocumentoRequest",
    "CrearVersionRequest",
    "DocumentoDTO",
    "DocumentoListItem",
    "EditarMetadataRequest",
    "EditarSeccionRequest",
    "EventoDTO",
    "ExportarRequest",
    "IniciarEntrevistaResponse",
    "MetadataModeloDTO",
    "OkResponse",
    "OmitirSeccionRequest",
    "PaginatedResponse",
    "RegistrarSignoffRequest",
    "ResponderPreguntaRequest",
    "SeccionDTO",
    "TurnoEntrevistaDTO",
    "VersionDTO",
]
