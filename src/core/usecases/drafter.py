"""Drafter: convierte el material capturado en una entrevista en borrador profesional.

Una vez que `InterviewEngine` cierra una sección (devuelve `cerrada=True`),
el `Drafter` toma todo el historial conversacional de esa sección y lo
sintetiza en un borrador markdown listo para pegar en el `.docx` final.

Si Claude considera que el material no alcanza para redactar (caso edge), devuelve
una marca `[BORRADOR INSUFICIENTE: ...]` que el caller puede detectar y reabrir
la entrevista.
"""

from __future__ import annotations

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import EstadoEntrevista, EventoAuditoria, Seccion
from src.core.models.documento import Documento
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts import (
    DRAFTING_SYSTEM_INSTRUCTION,
    SYSTEM_PROMPT_TONO,
    cargar_contexto_fijo,
    formato_seccion_actual,
)

_MARCADOR_INSUFICIENTE = "[BORRADOR INSUFICIENTE"


def _historial_a_texto(estado: EstadoEntrevista) -> str:
    """Renderiza el historial conversacional para incluirlo en el prompt del Drafter."""
    lineas: list[str] = []
    for m in estado.mensajes:
        prefijo = {"user": "USUARIO", "assistant": "CLAUDE", "system_note": "NOTA"}[m.rol]
        lineas.append(f"### {prefijo}\n{m.contenido}\n")
    return "\n".join(lineas)


def _construir_system_blocks(seccion: Seccion) -> list[TextBlockParam]:
    return [
        # Bloque cacheable
        {
            "type": "text",
            "text": cargar_contexto_fijo(),
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": SYSTEM_PROMPT_TONO + "\n\n" + DRAFTING_SYSTEM_INSTRUCTION,
            "cache_control": {"type": "ephemeral"},
        },
        # Bloque variable: la sección que se está redactando
        {
            "type": "text",
            "text": ("## SECCIÓN A REDACTAR\n\n" + formato_seccion_actual(seccion)),
        },
    ]


class Drafter:
    """Genera borrador profesional a partir del historial de la entrevista."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def redactar(
        self,
        documento: Documento,
        seccion: Seccion,
        estado: EstadoEntrevista,
    ) -> tuple[str, bool]:
        """Genera el borrador. Devuelve (contenido_markdown, fue_suficiente)."""
        if not estado.mensajes:
            return ("", False)

        system_blocks = _construir_system_blocks(seccion)
        instruction = (
            "A continuación está el historial completo de la entrevista para esta sección. "
            "Redacta el borrador profesional siguiendo todas las reglas del system prompt.\n\n"
            + _historial_a_texto(estado)
        )
        messages: list[MessageParam] = [{"role": "user", "content": instruction}]

        respuesta = self.llm.chat(
            tarea="drafting",
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=4096,
        )
        documento.metricas_uso.agregar(
            construir_llamada(
                modelo=respuesta.modelo_usado,
                tarea="drafting",
                input_tokens=respuesta.input_tokens,
                output_tokens=respuesta.output_tokens,
                cache_read_tokens=respuesta.cache_read_tokens,
                cache_creation_tokens=respuesta.cache_creation_tokens,
            )
        )

        texto = respuesta.text.strip()
        suficiente = not texto.lstrip().startswith(_MARCADOR_INSUFICIENTE)

        if suficiente:
            seccion.contenido = texto
            seccion.completitud = "completa"  # type: ignore[assignment]
            documento.registrar_evento(
                EventoAuditoria(
                    actor=documento.user_id,
                    tipo="seccion_editada",
                    descripcion=(
                        f"Borrador generado para '{seccion.numero} {seccion.nombre}' "
                        f"({len(texto)} caracteres)."
                    ),
                    seccion_id=seccion.id,
                )
            )

        return (texto, suficiente)
