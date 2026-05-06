"""KnowledgeExtractor: extrae hechos transversales del modelo con Haiku.

Después de cerrar una sección, este use case toma el transcript de la
entrevista, llama a Haiku 4.5 con un prompt específico de extracción JSON,
y mergea los hechos extraídos con `MemoriaModelo` del documento.

El uso de Haiku (no Opus) es deliberado: la tarea es extracción estructurada
simple, no razonamiento complejo. Costo ~50× menor que Opus.
"""

from __future__ import annotations

import json
import re

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import (
    Documento,
    EstadoEntrevista,
    EventoAuditoria,
    Seccion,
)
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts import EXTRACTION_SYSTEM_INSTRUCTION


def _historial_a_texto(estado: EstadoEntrevista) -> str:
    lineas: list[str] = []
    for m in estado.mensajes:
        prefijo = {"user": "USUARIO", "assistant": "CLAUDE", "system_note": "NOTA"}[m.rol]
        lineas.append(f"### {prefijo}\n{m.contenido}\n")
    return "\n".join(lineas)


def _extraer_json(texto: str) -> dict[str, object] | None:
    """Extrae el primer objeto JSON balanceado del texto.

    Robusto contra Haiku devolviendo el JSON con/sin fences markdown,
    o con texto explicativo alrededor.
    """
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if fence_match:
        candidato = fence_match.group(1)
    else:
        # Busca el primer { y el último } del texto
        start = texto.find("{")
        end = texto.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidato = texto[start : end + 1]

    try:
        result = json.loads(candidato)
    except json.JSONDecodeError:
        return None
    return result if isinstance(result, dict) else None


class KnowledgeExtractor:
    """Extrae hechos transversales del modelo a partir de un transcript."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def extraer_y_actualizar(
        self,
        documento: Documento,
        seccion: Seccion,
        estado: EstadoEntrevista,
    ) -> bool:
        """Extrae hechos del transcript y mergea con `documento.memoria_modelo`.

        Returns:
            True si se actualizaron hechos, False si no había nada nuevo.
        """
        if not estado.mensajes:
            return False

        memoria_actual = documento.memoria_modelo.renderizar_para_prompt() or "(vacía)"

        system_blocks: list[TextBlockParam] = [
            {
                "type": "text",
                "text": EXTRACTION_SYSTEM_INSTRUCTION,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": (
                    "## MEMORIA YA CONOCIDA DEL MODELO (no la repitas en tu output)\n\n"
                    + memoria_actual
                ),
            },
        ]

        instruction = (
            f"Sección entrevistada: {seccion.numero} {seccion.nombre}\n\n"
            "## TRANSCRIPT DE LA ENTREVISTA\n\n"
            + _historial_a_texto(estado)
            + "\n\nExtrae los hechos transversales NUEVOS en JSON con la forma especificada."
        )
        messages: list[MessageParam] = [{"role": "user", "content": instruction}]

        respuesta = self.llm.chat(
            tarea="extraction",
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=1024,
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

        hechos = _extraer_json(respuesta.text)
        if hechos is None:
            return False

        cambios = documento.memoria_modelo.actualizar_desde_dict(
            hechos, fuente=f"extraccion:{seccion.id}"
        )
        if cambios:
            documento.registrar_evento(
                EventoAuditoria(
                    actor=documento.user_id,
                    tipo="metadata_actualizada",
                    descripcion=(
                        f"Memoria del modelo enriquecida tras cerrar "
                        f"'{seccion.numero} {seccion.nombre}'."
                    ),
                    seccion_id=seccion.id,
                )
            )
        return cambios
