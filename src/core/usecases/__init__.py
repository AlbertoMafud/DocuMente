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

__all__ = [
    "MOTIVOS_OMISION",
    "SECCIONES_DATA_HEAVY",
    "AdjuntarTablaApendice",
    "CambiarEstadoDocumento",
    "CrearDocumentoEnBlanco",
    "DocxWriter",
    "Drafter",
    "ExportarDocumento",
    "GapAnalyzer",
    "ImportarDocumento",
    "IniciarEntrevista",
    "InterviewEngine",
    "KnowledgeExtractor",
    "OmitirSeccion",
    "RegistrarSignoff",
    "ResponderPregunta",
    "ResultadoAdjuntar",
    "ResultadoExportacion",
    "ResultadoImportacion",
    "TableExtractor",
    "TableSchema",
    "TransicionRechazada",
    "TurnoEntrevista",
    "es_seccion_data_heavy",
]
