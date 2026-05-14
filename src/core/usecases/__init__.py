"""Use cases — orquestadores de la lógica de aplicación."""

from src.core.usecases.adjuntar_tabla import (
    SECCIONES_DATA_HEAVY,
    AdjuntarTablaApendice,
    ResultadoAdjuntar,
    es_seccion_data_heavy,
)
from src.core.usecases.cambiar_estado import (
    CambiarEstadoDocumento,
    RegistrarSignoff,
    TransicionRechazada,
)
from src.core.usecases.crear_documento import CrearDocumentoEnBlanco
from src.core.usecases.docx_writer import DocxWriter
from src.core.usecases.drafter import Drafter
from src.core.usecases.entrevista_uc import (
    IniciarEntrevista,
    ResponderPregunta,
    TurnoEntrevista,
)
from src.core.usecases.exportar_documento import (
    ExportarDocumento,
    ResultadoExportacion,
)
from src.core.usecases.gap_analyzer import GapAnalyzer
from src.core.usecases.importar_documento import (
    ImportarDocumento,
    ResultadoImportacion,
)
from src.core.usecases.interview_engine import InterviewEngine
from src.core.usecases.knowledge_extractor import KnowledgeExtractor
from src.core.usecases.omitir_seccion import MOTIVOS_OMISION, OmitirSeccion
from src.core.usecases.table_extractor import TableExtractor, TableSchema
from src.core.usecases.detectar_modelos_prophet import (
    DetectarModelosProphet,
    ModeloProphetInfo,
    ResultadoDeteccion,
)
from src.core.usecases.importar_registro_prophet import (
    ImportarRegistroProphet,
    ResultadoImportacionProphet,
)
from src.core.usecases.docx_writer_prophet import DocxWriterProphet

__all__ = [
    "MOTIVOS_OMISION",
    "SECCIONES_DATA_HEAVY",
    "AdjuntarTablaApendice",
    "CambiarEstadoDocumento",
    "CrearDocumentoEnBlanco",
    "DetectarModelosProphet",
    "DocxWriter",
    "DocxWriterProphet",
    "Drafter",
    "ExportarDocumento",
    "GapAnalyzer",
    "ImportarDocumento",
    "ImportarRegistroProphet",
    "IniciarEntrevista",
    "InterviewEngine",
    "KnowledgeExtractor",
    "ModeloProphetInfo",
    "OmitirSeccion",
    "RegistrarSignoff",
    "ResponderPregunta",
    "ResultadoAdjuntar",
    "ResultadoDeteccion",
    "ResultadoExportacion",
    "ResultadoImportacion",
    "ResultadoImportacionProphet",
    "TableExtractor",
    "TableSchema",
    "TransicionRechazada",
    "TurnoEntrevista",
    "es_seccion_data_heavy",
]
