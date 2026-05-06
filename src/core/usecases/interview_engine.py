"""InterviewEngine: orquesta el chat usuario ↔ Claude para una sección.

Estado conversacional vive en `EstadoEntrevista` y se persiste por documento+sección.
Por cada turno del usuario, el engine:
1. Construye el prompt del sistema (contexto fijo cacheado + tono + instrucción
   de entrevista + estado del documento + sección activa).
2. Manda los mensajes acumulados a Claude vía `LLMClient`.
3. Detecta si la respuesta empieza con `SECCION_COMPLETA` para cerrar la sección.
4. Devuelve la respuesta para que la UI la muestre.

El prompt se diseña con caching agresivo: el contexto institucional (template +
MRM + marca + tono) son ~10-20K tokens estables que se cachean. Solo la última
parte (estado del documento + mensajes del chat) cambia turno a turno.
"""

from __future__ import annotations

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import (
    Documento,
    EstadoEntrevista,
    EventoAuditoria,
    MensajeEntrevista,
    Seccion,
)
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts import (
    INTERVIEW_SYSTEM_INSTRUCTION,
    SYSTEM_PROMPT_TONO,
    cargar_contexto_fijo,
    formato_estado_documento,
    formato_seccion_actual,
)

_MARCADOR_CIERRE = "SECCION_COMPLETA"


def _construir_system_blocks(documento: Documento, seccion: Seccion) -> list[TextBlockParam]:
    """Construye los bloques de system prompt con caching estratégico.

    Bloque 1 (cacheado, ~12K tokens): contexto institucional fijo.
    Bloque 2 (cacheado, ~1K tokens): tono + instrucción de entrevista.
    Bloque 3 (NO cacheado): memoria del modelo + estado del documento + sección activa.
    """
    contexto_fijo = cargar_contexto_fijo()

    # Bloque dinámico: memoria + estado + sección
    memoria_md = documento.memoria_modelo.renderizar_para_prompt()
    bloque_dinamico = ""
    if memoria_md:
        bloque_dinamico += memoria_md + "\n\n"
    bloque_dinamico += "## ESTADO ACTUAL DEL DOCUMENTO\n\n"
    bloque_dinamico += formato_estado_documento(documento)
    bloque_dinamico += "\n\n" + formato_seccion_actual(seccion)

    return [
        # Bloque 1: contexto institucional fijo — cache_control aquí
        # cachea todo lo anterior (en este caso, solo este bloque).
        {
            "type": "text",
            "text": contexto_fijo,
            "cache_control": {"type": "ephemeral"},
        },
        # Bloque 2: tono + instrucción — también estable durante la sesión,
        # se cachea junto.
        {
            "type": "text",
            "text": SYSTEM_PROMPT_TONO + "\n\n" + INTERVIEW_SYSTEM_INSTRUCTION,
            "cache_control": {"type": "ephemeral"},
        },
        # Bloque 3: memoria + estado + sección — cambia cada turno, NO cache_control.
        {
            "type": "text",
            "text": bloque_dinamico,
        },
    ]


def _mensajes_a_messages_param(
    mensajes: list[MensajeEntrevista],
) -> list[MessageParam]:
    """Convierte historial interno a formato MessageParam de Anthropic."""
    out: list[MessageParam] = []
    for m in mensajes:
        if m.rol == "system_note":
            # system_note va como turno de usuario con prefijo claro
            out.append({"role": "user", "content": f"[Nota del sistema] {m.contenido}"})
        else:
            out.append({"role": m.rol, "content": m.contenido})  # type: ignore[typeddict-item]
    return out


class InterviewEngine:
    """Motor de entrevista guiada por Claude para una sección del documento."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def iniciar(self, documento: Documento, seccion: Seccion) -> tuple[EstadoEntrevista, str]:
        """Arranca una entrevista nueva sobre `seccion` y devuelve la primera pregunta de Claude.

        Returns:
            (estado_inicial, primera_pregunta)
        """
        estado = EstadoEntrevista(
            documento_id=str(documento.id),
            seccion_id=seccion.id,
        )
        # Mensaje inicial inyectado para que Claude tenga algo a qué responder.
        kickoff = (
            f"Comienza la entrevista sobre la sección '{seccion.numero} {seccion.nombre}'. "
            "Empieza con tu primera pregunta."
        )
        estado.agregar("user", kickoff)
        respuesta = self._llamar_llm(documento, seccion, estado)
        estado.agregar("assistant", respuesta)
        return estado, respuesta

    def responder(
        self,
        documento: Documento,
        seccion: Seccion,
        estado: EstadoEntrevista,
        respuesta_usuario: str,
    ) -> tuple[EstadoEntrevista, str, bool]:
        """Procesa una respuesta del usuario y devuelve la siguiente pregunta de Claude.

        Returns:
            (estado_actualizado, respuesta_de_claude, seccion_cerrada)
        """
        if estado.cerrada:
            raise ValueError(f"La entrevista de la sección '{seccion.id}' ya está cerrada.")
        estado.agregar("user", respuesta_usuario)
        respuesta_claude = self._llamar_llm(documento, seccion, estado)

        cerrada = respuesta_claude.lstrip().startswith(_MARCADOR_CIERRE)
        if cerrada:
            estado.cerrada = True
            documento.registrar_evento(
                EventoAuditoria(
                    actor=documento.user_id,
                    tipo="seccion_completada",
                    descripcion=(
                        f"Entrevista de '{seccion.numero} {seccion.nombre}' cerrada "
                        "por Claude (SECCION_COMPLETA)."
                    ),
                    seccion_id=seccion.id,
                )
            )

        estado.agregar("assistant", respuesta_claude)
        return estado, respuesta_claude, cerrada

    def _llamar_llm(
        self,
        documento: Documento,
        seccion: Seccion,
        estado: EstadoEntrevista,
    ) -> str:
        system_blocks = _construir_system_blocks(documento, seccion)
        messages = _mensajes_a_messages_param(estado.mensajes)
        respuesta = self.llm.chat(
            tarea="chat",
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=2048,
        )
        documento.metricas_uso.agregar(
            construir_llamada(
                modelo=respuesta.modelo_usado,
                tarea="chat",
                input_tokens=respuesta.input_tokens,
                output_tokens=respuesta.output_tokens,
                cache_read_tokens=respuesta.cache_read_tokens,
                cache_creation_tokens=respuesta.cache_creation_tokens,
            )
        )
        return respuesta.text
