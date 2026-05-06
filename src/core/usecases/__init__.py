"""Use cases — orquestadores de la lógica de aplicación."""

from src.core.usecases.adjuntar_tabla import (
    SECCIONES_DATA_HEAVY,
    AdjuntarTablaApendice,
    ResultadoAdjuntar,
    es_seccion_data_heavy,
)
from src.core.usecases.drafter import Drafter
from src.core.usecases.entrevista_uc import (
    IniciarEntrevista,
    ResponderPregunta,
    TurnoEntrevista,
)
from src.core.usecases.gap_analyzer import GapAnalyzer
from src.core.usecases.importar_documento import (
    ImportarDocumento,
    ResultadoImportacion,
)
from src.core.usecases.interview_engine import InterviewEngine
from src.core.usecases.knowledge_extractor import KnowledgeExtractor

__all__ = [
    "SECCIONES_DATA_HEAVY",
    "AdjuntarTablaApendice",
    "Drafter",
    "GapAnalyzer",
    "ImportarDocumento",
    "IniciarEntrevista",
    "InterviewEngine",
    "KnowledgeExtractor",
    "ResponderPregunta",
    "ResultadoAdjuntar",
    "ResultadoImportacion",
    "TurnoEntrevista",
    "es_seccion_data_heavy",
]
