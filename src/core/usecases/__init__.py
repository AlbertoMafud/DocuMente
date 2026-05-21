"""Use cases — orquestadores de la lógica de aplicación."""

from src.core.usecases.adjuntar_tabla import (
    SECCIONES_DATA_HEAVY,
    AdjuntarFormulaApendice,
    AdjuntarPdfApendice,
    AdjuntarTablaApendice,
    ResultadoAdjuntar,
    ResultadoAdjuntarFormula,
    ResultadoAdjuntarPdf,
    es_seccion_data_heavy,
)
from src.core.usecases.archivar_documento import (
    ArchivarDocumento,
    ResultadoVisibilidad,
    purgar_papelera_expirada,
)
from src.core.usecases.cambiar_estado import (
    CambiarEstadoDocumento,
    RegistrarSignoff,
    TransicionRechazada,
)
from src.core.usecases.crear_documento import CrearDocumentoEnBlanco
from src.core.usecases.crear_version import CrearVersion, ResultadoCrearVersion
from src.core.usecases.detectar_modelos_prophet import (
    DetectarModelosProphet,
    ModeloProphetInfo,
    ResultadoDeteccion,
)
from src.core.usecases.document_polisher import (
    DocumentPolisher,
    ResultadoPolish,
    SugerenciaPolish,
)
from src.core.usecases.docx_writer import DocxWriter
from src.core.usecases.docx_writer_prophet import DocxWriterProphet
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
from src.core.usecases.importar_registro_prophet import (
    ImportarRegistroProphet,
    ResultadoImportacionProphet,
)
from src.core.usecases.interview_engine import InterviewEngine
from src.core.usecases.knowledge_extractor import KnowledgeExtractor
from src.core.usecases.omitir_seccion import MOTIVOS_OMISION, OmitirSeccion
from src.core.usecases.restaurar_version import (
    RestaurarVersion,
    ResultadoRestaurar,
    VersionNoEncontrada,
)
from src.core.usecases.table_extractor import TableExtractor, TableSchema

__all__ = [
    "MOTIVOS_OMISION",
    "SECCIONES_DATA_HEAVY",
    "AdjuntarFormulaApendice",
    "AdjuntarPdfApendice",
    "AdjuntarTablaApendice",
    "ArchivarDocumento",
    "CambiarEstadoDocumento",
    "CrearDocumentoEnBlanco",
    "CrearVersion",
    "DetectarModelosProphet",
    "DocumentPolisher",
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
    "RestaurarVersion",
    "ResultadoAdjuntar",
    "ResultadoAdjuntarFormula",
    "ResultadoAdjuntarPdf",
    "ResultadoCrearVersion",
    "ResultadoDeteccion",
    "ResultadoExportacion",
    "ResultadoImportacion",
    "ResultadoImportacionProphet",
    "ResultadoPolish",
    "ResultadoRestaurar",
    "ResultadoVisibilidad",
    "SugerenciaPolish",
    "TableExtractor",
    "TableSchema",
    "TransicionRechazada",
    "TurnoEntrevista",
    "VersionNoEncontrada",
    "es_seccion_data_heavy",
    "purgar_papelera_expirada",
]
