"""Use case StructureRealigner — remapea texto bruto del ancla a secciones NYL.

Cuándo se ejecuta:
- Cuando `Documento.cobertura_catalogo` < umbral (default 0.5) tras leer el
  ancla con `DocxReader` o `PdfAnchorReader`. Esto indica que el ancla NO
  sigue la nomenclatura NYL y los heading-matchers fallaron en mapear.
- Solo si hay un `LLMClient` configurado.

Política:
- NO inventa contenido. El prompt obliga a usar fragmentos verbatim del ancla.
- NO sobreescribe secciones que ya tienen contenido (del paso anterior del reader).
- Marca cada sección remapeada con el prefijo `[Re-estructurado desde ancla — revisar]`.
- Devuelve `ResultadoRealign` con conteos + errores para que la UI los muestre.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento
from src.core.template_catalog import TEMPLATE_MODEL_DEVELOPMENT
from src.core.usecases.strings_localizados import Idioma, t
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts.structure_realign import (
    STRUCTURE_REALIGN_SYSTEM,
    construir_prompt_realign,
)

logger = logging.getLogger(__name__)

_UMBRAL_COBERTURA_DEFAULT = 0.5


@dataclass(frozen=True)
class ResultadoRealign:
    """Resultado de la reestructuración.

    Attributes:
        ejecutado: True si se llamó al LLM (cobertura baja y umbral aplicó).
        secciones_remapeadas: cantidad de secciones que recibieron contenido nuevo.
        cobertura_antes: fracción de secciones con contenido antes del realign.
        cobertura_despues: fracción después del realign.
        errores: lista de mensajes legibles si algo falló.
    """

    ejecutado: bool = False
    secciones_remapeadas: int = 0
    cobertura_antes: float = 0.0
    cobertura_despues: float = 0.0
    errores: list[str] = field(default_factory=list)

    @property
    def hubo_errores(self) -> bool:
        return bool(self.errores)


def _construir_catalogo_resumen() -> str:
    """Texto compacto del catálogo para incluir en el prompt LLM."""
    lineas: list[str] = []
    for sec in TEMPLATE_MODEL_DEVELOPMENT:
        intencion = (sec.intencion or "").strip()
        marca_obligatoria = " (mandatory)" if sec.obligatoria else " (optional)"
        if intencion:
            lineas.append(
                f"- `{sec.id}` — {sec.numero} {sec.nombre}{marca_obligatoria}: {intencion}"
            )
        else:
            lineas.append(f"- `{sec.id}` — {sec.numero} {sec.nombre}{marca_obligatoria}")
    return "\n".join(lineas)


def _parsear_json_respuesta(texto: str) -> dict[str, str]:
    """Extrae el dict de la respuesta LLM. Tolerante a fences y prosa accidental."""
    # Quita fences de código por si el modelo las agregó pese a la instrucción
    cleaned = texto.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    # Si hay prosa antes/después del JSON, intentamos extraer el primer objeto
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(0)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    # Normalizar: solo keys str y values str
    resultado: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, str) and v.strip():
            resultado[k] = v
    return resultado


class StructureRealigner:
    """Use case que remapea texto bruto del ancla a secciones del catálogo NYL."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def ejecutar(
        self,
        documento: Documento,
        texto_ancla_crudo: str,
        *,
        idioma: Idioma = "es",
        umbral_cobertura: float = _UMBRAL_COBERTURA_DEFAULT,
        max_texto_chars: int = 60_000,
    ) -> ResultadoRealign:
        """Si la cobertura es baja, llama al LLM y aplica el remapeo.

        Args:
            documento: documento ya parseado por el reader (in-place).
            texto_ancla_crudo: texto plano del ancla (lo que el reader vio).
            idioma: idioma del prefijo `[Re-estructurado desde ancla — revisar]`.
            umbral_cobertura: si `cobertura_catalogo >= umbral`, NO se ejecuta.
                Default 0.5 — el reader ya pobló la mitad del catálogo.
            max_texto_chars: corta el texto si excede este límite (control de costo
                en docs muy largos). Default 60K caracteres ≈ 15K tokens.

        Returns:
            ResultadoRealign con conteos y errores.
        """
        cobertura_antes = documento.cobertura_catalogo
        if cobertura_antes >= umbral_cobertura:
            return ResultadoRealign(
                ejecutado=False,
                cobertura_antes=cobertura_antes,
                cobertura_despues=cobertura_antes,
            )

        texto_efectivo = texto_ancla_crudo.strip()
        if not texto_efectivo:
            return ResultadoRealign(
                ejecutado=False,
                cobertura_antes=cobertura_antes,
                cobertura_despues=cobertura_antes,
            )
        if len(texto_efectivo) > max_texto_chars:
            texto_efectivo = texto_efectivo[:max_texto_chars]

        try:
            mapeo = self._invocar_llm(documento, texto_efectivo)
        except Exception as exc:
            msg = f"Falló reestructuración LLM ({exc.__class__.__name__}): {exc}"
            logger.warning(msg, exc_info=True)
            return ResultadoRealign(
                ejecutado=True,
                cobertura_antes=cobertura_antes,
                cobertura_despues=cobertura_antes,
                errores=[msg],
            )

        prefijo = t("reestructurado_revisar", idioma)
        remapeadas = self._aplicar_mapeo(documento, mapeo, prefijo)

        return ResultadoRealign(
            ejecutado=True,
            secciones_remapeadas=remapeadas,
            cobertura_antes=cobertura_antes,
            cobertura_despues=documento.cobertura_catalogo,
        )

    def _invocar_llm(self, documento: Documento, texto: str) -> dict[str, str]:
        system_blocks: list[TextBlockParam] = [{"type": "text", "text": STRUCTURE_REALIGN_SYSTEM}]
        user_msg = construir_prompt_realign(
            texto_ancla=texto,
            catalogo_resumen=_construir_catalogo_resumen(),
        )
        messages: list[MessageParam] = [{"role": "user", "content": user_msg}]
        respuesta = self.llm.chat(
            tarea="chat",  # Sonnet — calidad para mapping semántico
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
        return _parsear_json_respuesta(respuesta.text)

    def _aplicar_mapeo(
        self,
        documento: Documento,
        mapeo: dict[str, str],
        prefijo: str,
    ) -> int:
        """Inyecta cada fragmento en su sección destino, solo si está vacía."""
        remapeadas = 0
        for seccion_id, contenido in mapeo.items():
            seccion = documento.seccion_por_id(seccion_id)
            if seccion is None:
                continue
            # NO pisar contenido del DocxReader que sí detectó
            if seccion.completitud != "vacia":
                continue
            limpio = contenido.strip()
            if not limpio:
                continue
            seccion.contenido = f"{prefijo}\n\n{limpio}"
            seccion.completitud = "parcial"
            remapeadas += 1
        return remapeadas
