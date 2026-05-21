"""Use case DocumentPolisher — revisión de coherencia narrativa del documento.

Toma el documento completo (todas las secciones con contenido) y le pide a
Claude que detecte inconsistencias, contradicciones, problemas de redacción
y referencias rotas — entre secciones distintas, no dentro de una sola.

Política:
- NO modifica el documento. Solo devuelve `list[SugerenciaPolish]` para que
  el caller (la UI de export) decida cuáles aplicar.
- Se invoca opt-in desde el modal de exportar; cuesta ~$0.02-0.05 USD por
  documento de tamaño medio.
- Tolerante a fallas: si el LLM crashea o devuelve JSON inválido, retorna
  `ResultadoPolish` con `errores` poblado.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Literal

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts.document_polish import (
    DOCUMENT_POLISH_SYSTEM,
    construir_prompt_polish,
)

logger = logging.getLogger(__name__)

TipoHallazgo = Literal["inconsistencia", "contradiccion", "redaccion", "referencia_rota"]
SeveridadHallazgo = Literal["alta", "media", "baja"]


@dataclass(frozen=True)
class SugerenciaPolish:
    """Una observación del Polisher sobre un problema cross-seccional."""

    seccion_id: str
    """Sección donde el hallazgo es más relevante (foco principal)."""
    tipo: TipoHallazgo
    severidad: SeveridadHallazgo
    descripcion: str
    secciones_afectadas: list[str] = field(default_factory=list)
    """Todas las secciones donde aparece el problema (≥1)."""
    texto_sugerido: str | None = None
    """Edit mínimo propuesto, opcional."""


@dataclass(frozen=True)
class ResultadoPolish:
    """Resultado de la revisión completa."""

    ejecutado: bool = False
    sugerencias: list[SugerenciaPolish] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)

    @property
    def hubo_errores(self) -> bool:
        return bool(self.errores)

    @property
    def n_alta(self) -> int:
        return sum(1 for s in self.sugerencias if s.severidad == "alta")

    @property
    def n_media(self) -> int:
        return sum(1 for s in self.sugerencias if s.severidad == "media")

    @property
    def n_baja(self) -> int:
        return sum(1 for s in self.sugerencias if s.severidad == "baja")


def _serializar_documento(documento: Documento, max_chars_por_seccion: int = 4000) -> str:
    """Construye el texto del documento que se manda al LLM.

    Secciones vacías se incluyen como marcador (útiles para detectar
    referencias rotas). Cada sección con contenido se trunca a
    `max_chars_por_seccion` para controlar costo en docs muy grandes.
    """
    lineas: list[str] = []
    for seccion in documento.secciones:
        cabecera = f"### `{seccion.id}` — {seccion.numero} {seccion.nombre}"
        if seccion.completitud == "omitida":
            motivo = seccion.motivo_omision or "sin motivo"
            lineas.append(f"{cabecera}\n[OMITTED — {motivo}]\n")
            continue
        contenido = (seccion.contenido or "").strip()
        if not contenido:
            lineas.append(f"{cabecera}\n[EMPTY]\n")
            continue
        if len(contenido) > max_chars_por_seccion:
            contenido = contenido[:max_chars_por_seccion] + "\n[…truncated for length…]"
        lineas.append(f"{cabecera}\n{contenido}\n")
    return "\n".join(lineas)


def _parsear_array_respuesta(texto: str) -> list[dict[str, object]]:
    """Extrae el array JSON de la respuesta. Tolerante a fences y prosa."""
    cleaned = texto.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    m = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(0)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _hallazgo_valido(d: dict[str, object]) -> SugerenciaPolish | None:
    """Convierte un dict crudo del LLM a `SugerenciaPolish`. None si malformado."""
    tipos_validos = ("inconsistencia", "contradiccion", "redaccion", "referencia_rota")
    severidades_validas = ("alta", "media", "baja")
    seccion_id = d.get("seccion_id")
    tipo = d.get("tipo")
    severidad = d.get("severidad")
    descripcion = d.get("descripcion")
    if not isinstance(seccion_id, str) or not seccion_id:
        return None
    if tipo not in tipos_validos or severidad not in severidades_validas:
        return None
    if not isinstance(descripcion, str) or not descripcion.strip():
        return None
    secciones_afectadas_raw = d.get("secciones_afectadas", [seccion_id])
    if isinstance(secciones_afectadas_raw, list):
        secciones_afectadas = [s for s in secciones_afectadas_raw if isinstance(s, str)]
    else:
        secciones_afectadas = [seccion_id]
    if not secciones_afectadas:
        secciones_afectadas = [seccion_id]
    texto_sugerido_raw = d.get("texto_sugerido")
    texto_sugerido: str | None = None
    if isinstance(texto_sugerido_raw, str) and texto_sugerido_raw.strip():
        texto_sugerido = texto_sugerido_raw.strip()
    return SugerenciaPolish(
        seccion_id=seccion_id,
        tipo=tipo,  # type: ignore[arg-type]
        severidad=severidad,  # type: ignore[arg-type]
        descripcion=descripcion.strip(),
        secciones_afectadas=secciones_afectadas,
        texto_sugerido=texto_sugerido,
    )


class DocumentPolisher:
    """Use case: revisa coherencia narrativa cross-seccional del documento."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def revisar(self, documento: Documento) -> ResultadoPolish:
        """Devuelve `ResultadoPolish` con la lista de sugerencias o errores."""
        resumen = _serializar_documento(documento)
        if not resumen.strip():
            return ResultadoPolish(ejecutado=False)

        try:
            crudos = self._invocar_llm(documento, resumen)
        except Exception as exc:
            msg = f"DocumentPolisher falló ({exc.__class__.__name__}): {exc}"
            logger.warning(msg, exc_info=True)
            return ResultadoPolish(ejecutado=True, errores=[msg])

        sugerencias: list[SugerenciaPolish] = []
        for item in crudos:
            sug = _hallazgo_valido(item)
            if sug is not None:
                sugerencias.append(sug)

        # Ordenar: alta primero, después media, después baja
        prioridad = {"alta": 0, "media": 1, "baja": 2}
        sugerencias.sort(key=lambda s: (prioridad[s.severidad], s.seccion_id))

        return ResultadoPolish(ejecutado=True, sugerencias=sugerencias)

    def _invocar_llm(self, documento: Documento, resumen: str) -> list[dict[str, object]]:
        system_blocks: list[TextBlockParam] = [{"type": "text", "text": DOCUMENT_POLISH_SYSTEM}]
        user_msg = construir_prompt_polish(documento_resumen=resumen)
        messages: list[MessageParam] = [{"role": "user", "content": user_msg}]
        respuesta = self.llm.chat(
            tarea="chat",  # Sonnet — calidad de análisis semántico
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=8192,
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
        return _parsear_array_respuesta(respuesta.text)
