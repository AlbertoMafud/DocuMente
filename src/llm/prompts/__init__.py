"""Prompts del sistema para Claude."""

from src.llm.prompts.contexto import SYSTEM_PROMPT_TONO, cargar_contexto_fijo
from src.llm.prompts.drafting import DRAFTING_SYSTEM_INSTRUCTION
from src.llm.prompts.extraction import EXTRACTION_SYSTEM_INSTRUCTION
from src.llm.prompts.interview import (
    INTERVIEW_SYSTEM_INSTRUCTION,
    formato_estado_documento,
    formato_seccion_actual,
)

__all__ = [
    "DRAFTING_SYSTEM_INSTRUCTION",
    "EXTRACTION_SYSTEM_INSTRUCTION",
    "INTERVIEW_SYSTEM_INSTRUCTION",
    "SYSTEM_PROMPT_TONO",
    "cargar_contexto_fijo",
    "formato_estado_documento",
    "formato_seccion_actual",
]
