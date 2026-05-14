"""Use case SugerenciasMultiFuente — pre-popula secciones vacías con borradores
generados a partir del texto extraído de fuentes adicionales.

Política:
- Solo opera sobre secciones con `completitud == "vacia"`. No pisa contenido
  existente (parcial, completa, omitida).
- Marca el contenido sugerido con prefijo `[Borrador automático — revisar]`
  y `completitud = "parcial"` para que la UI muestre el badge claramente.
- Cita las fuentes consultadas al final del borrador.
- Tolerante a errores LLM: si una sección falla, sigue con las demás.
"""

from __future__ import annotations

import contextlib

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento, FuenteContexto
from src.core.usecases.strings_localizados import Idioma, t
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts.sugerencias_multifuente import (
    SUGERENCIAS_MULTIFUENTE_SYSTEM,
    construir_prompt_seccion,
)


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
    ) -> int:
        """Genera sugerencias para secciones vacías y devuelve cuántas se llenaron.

        Args:
            documento: documento donde escribir las sugerencias (in-place).
            fuentes: lista de FuenteContexto. Si None, usa `documento.fuentes_contexto`.
            idioma: idioma del prefijo "[Borrador automático — revisar]".
            max_secciones: límite duro de secciones a sugerir (control de costo).
        """
        fuentes_efectivas = fuentes if fuentes is not None else documento.fuentes_contexto
        if not fuentes_efectivas:
            return 0

        fuentes_payload: list[tuple[str, str]] = [
            (f.nombre_archivo, f.texto_extraido)
            for f in fuentes_efectivas
            if f.texto_extraido.strip()
        ]
        if not fuentes_payload:
            return 0

        prefijo_borrador = t("borrador_automatico_revisar", idioma)
        rellenadas = 0

        for seccion in documento.secciones:
            if rellenadas >= max_secciones:
                break
            if seccion.completitud != "vacia":
                continue

            with contextlib.suppress(Exception):
                draft = self._sugerir_para_seccion(
                    documento,
                    seccion_nombre=seccion.nombre,
                    seccion_descripcion=seccion.intencion or seccion.nombre,
                    fuentes=fuentes_payload,
                )
                if draft and "[Sin información en fuentes adjuntas]" not in draft:
                    seccion.contenido = f"{prefijo_borrador}\n\n{draft.strip()}"
                    seccion.completitud = "parcial"
                    rellenadas += 1

        return rellenadas

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
