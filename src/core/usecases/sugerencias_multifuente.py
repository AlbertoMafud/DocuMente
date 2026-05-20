"""Use case SugerenciasMultiFuente — pre-popula secciones vacías con borradores
generados a partir del texto extraído de fuentes adicionales.

Política:
- Solo opera sobre secciones con `completitud == "vacia"`. No pisa contenido
  existente (parcial, completa, omitida).
- Marca el contenido sugerido con prefijo `[Borrador automático — revisar]`
  y `completitud = "parcial"` para que la UI muestre el badge claramente.
- Cita las fuentes consultadas al final del borrador.
- Tolerante a errores LLM: si una sección falla, sigue con las demás y
  registra el error en el resultado (no se suprime silenciosamente).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento, FuenteContexto
from src.core.usecases.strings_localizados import Idioma, t
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts.sugerencias_multifuente import (
    SUGERENCIAS_MULTIFUENTE_SYSTEM,
    construir_prompt_seccion,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoSugerencias:
    """Resultado de aplicar sugerencias multi-fuente sobre un documento.

    Attributes:
        secciones_pobladas: cantidad de secciones que se llenaron con borrador.
        secciones_intentadas: cantidad de secciones vacías que se intentaron.
        errores: lista de mensajes legibles si alguna sección falló por LLM.
        fuentes_usadas: cantidad de fuentes con texto extraído utilizadas.
    """

    secciones_pobladas: int = 0
    secciones_intentadas: int = 0
    errores: list[str] = field(default_factory=list)
    fuentes_usadas: int = 0

    @property
    def hubo_errores(self) -> bool:
        return bool(self.errores)


class SugerenciasMultiFuente:
    """Use case: extrae sugerencias de fuentes adicionales y pre-popula secciones."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def ejecutar(
        self,
        documento: Documento,
        fuentes: list[FuenteContexto] | None = None,
        *,
        idioma: Idioma = "es",
        max_secciones: int = 28,
    ) -> ResultadoSugerencias:
        """Genera sugerencias para secciones vacías.

        Args:
            documento: documento donde escribir las sugerencias (in-place).
            fuentes: lista de FuenteContexto. Si None, usa `documento.fuentes_contexto`.
            idioma: idioma del prefijo "[Borrador automático — revisar]".
            max_secciones: límite duro de secciones a sugerir (control de costo).

        Returns:
            ResultadoSugerencias con conteos y errores agregados durante la corrida.
        """
        fuentes_efectivas = fuentes if fuentes is not None else documento.fuentes_contexto
        if not fuentes_efectivas:
            return ResultadoSugerencias()

        fuentes_payload: list[tuple[str, str]] = [
            (f.nombre_archivo, f.texto_extraido)
            for f in fuentes_efectivas
            if f.texto_extraido.strip()
        ]
        if not fuentes_payload:
            return ResultadoSugerencias()

        prefijo_borrador = t("borrador_automatico_revisar", idioma)
        pobladas = 0
        intentadas = 0
        errores: list[str] = []

        for seccion in documento.secciones:
            if pobladas >= max_secciones:
                break
            if seccion.completitud != "vacia":
                continue
            intentadas += 1

            try:
                draft = self._sugerir_para_seccion(
                    documento,
                    seccion_nombre=seccion.nombre,
                    seccion_descripcion=seccion.intencion or seccion.nombre,
                    fuentes=fuentes_payload,
                )
            except Exception as exc:
                msg = f"Sección {seccion.id}: falló la sugerencia LLM ({exc.__class__.__name__})"
                logger.warning(msg, exc_info=True)
                errores.append(msg)
                continue

            if draft and "[Sin información en fuentes adjuntas]" not in draft:
                seccion.contenido = f"{prefijo_borrador}\n\n{draft.strip()}"
                seccion.completitud = "parcial"
                pobladas += 1

        return ResultadoSugerencias(
            secciones_pobladas=pobladas,
            secciones_intentadas=intentadas,
            errores=errores,
            fuentes_usadas=len(fuentes_payload),
        )

    def _sugerir_para_seccion(
        self,
        documento: Documento,
        *,
        seccion_nombre: str,
        seccion_descripcion: str,
        fuentes: list[tuple[str, str]],
    ) -> str:
        system_blocks: list[TextBlockParam] = [
            {"type": "text", "text": SUGERENCIAS_MULTIFUENTE_SYSTEM}
        ]
        user_msg = construir_prompt_seccion(
            seccion_nombre=seccion_nombre,
            seccion_descripcion=seccion_descripcion,
            fuentes=fuentes,
        )
        messages: list[MessageParam] = [{"role": "user", "content": user_msg}]

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
        return respuesta.text.strip()
