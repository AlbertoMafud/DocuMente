"""TableExtractor — convierte texto narrativo en tabla estructurada vía Haiku.

Las tablas de upstream models, raw data sources, input changes y process
changes del template NYL esperan estructura tabular. Pero el contenido que
captura el InterviewEngine es prosa narrativa. Este use case cierra el gap:
cuando se exporta el DOCX, llama a Haiku con un prompt específico de extracción
JSON y devuelve `list[dict]` listo para que `docxtpl` lo itere en un loop de
fila de tabla.

Política de robustez: si el LLM devuelve algo que no parsea, el extractor
devuelve lista vacía. Mejor exportar una tabla vacía que romper el flujo.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento
from src.llm import LLMClient
from src.llm.pricing import construir_llamada


@dataclass(frozen=True)
class TableSchema:
    """Define qué campos extraer y cómo describir la tarea al LLM."""

    nombre: str
    """Nombre lógico de la tabla, ej. 'upstream_models'."""

    campos: list[str]
    """Lista de claves esperadas en cada dict del resultado."""

    descripcion_para_llm: str
    """Texto que describe qué información se busca; va al system prompt del LLM."""


class TableExtractor:
    """Extrae estructura tabular desde el contenido textual de una sección."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def extraer(
        self,
        documento: Documento,
        seccion_id: str,
        schema: TableSchema,
    ) -> list[dict[str, str]]:
        """Devuelve `list[dict]` con la estructura solicitada.

        Devuelve `[]` si:
        - La sección no existe.
        - La sección no tiene contenido textual.
        - El LLM devuelve JSON inválido o malformado.
        """
        seccion = documento.seccion_por_id(seccion_id)
        if seccion is None or not seccion.tiene_contenido:
            return []

        system = (
            "Eres un asistente experto en documentación de modelos actuariales bajo "
            "el marco MRM. Tu tarea es extraer información estructurada en JSON desde "
            "texto narrativo. Devuelve EXCLUSIVAMENTE un array JSON válido. "
            "No incluyas explicaciones, comentarios ni texto adicional. Si el texto "
            "no contiene información extraíble, devuelve `[]`.\n\n"
            f"## TAREA: {schema.nombre}\n\n{schema.descripcion_para_llm}\n\n"
            f"## SCHEMA\n\nCada item del array debe ser un objeto con estas claves "
            f"(todas string, vacío '' si no hay información): "
            f"{', '.join(schema.campos)}."
        )
        system_blocks: list[TextBlockParam] = [{"type": "text", "text": system}]
        instruction = (
            f"Texto a procesar (sección '{seccion.numero} {seccion.nombre}'):\n\n"
            f"{seccion.contenido}\n\n"
            "Devuelve el array JSON con la estructura solicitada."
        )
        messages: list[MessageParam] = [{"role": "user", "content": instruction}]

        respuesta = self.llm.chat(
            tarea="extraction",
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=2048,
        )

        documento.metricas_uso.agregar(
            construir_llamada(
                modelo=respuesta.modelo_usado,
                tarea="extraction",
                input_tokens=respuesta.input_tokens,
                output_tokens=respuesta.output_tokens,
                cache_read_tokens=respuesta.cache_read_tokens,
                cache_creation_tokens=respuesta.cache_creation_tokens,
            )
        )

        return _parsear_y_normalizar(respuesta.text, schema.campos)


def _parsear_y_normalizar(texto: str, campos: list[str]) -> list[dict[str, str]]:
    """Parsea el JSON del LLM, lo normaliza al schema, devuelve [] ante error."""
    raw = _quitar_fences_codigo(texto.strip())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []

    normalizados: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        normalizado = {campo: str(item.get(campo, "") or "") for campo in campos}
        normalizados.append(normalizado)
    return normalizados


_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


def _quitar_fences_codigo(texto: str) -> str:
    """Quita ```json ... ``` o ``` ... ``` si el LLM envolvió el JSON."""
    match = _FENCE_PATTERN.match(texto)
    return match.group(1).strip() if match else texto
