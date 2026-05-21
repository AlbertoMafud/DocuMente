"""TraductorDocumento — gestiona el idioma del documento al exportar.

Cinco modos disponibles:

- `"es"` (legacy): no toca el documento — equivale a "bilingüe" para back-compat.
- `"en"` (legacy): traduce todo el contenido al inglés, sin importar el idioma
  original — preserva el comportamiento histórico anterior a A.3.
- `"es_normalize"`: detecta el idioma de cada sección. Las que NO estén en
  español, se traducen a español. Las que ya estén en español, se preservan.
- `"en_normalize"`: simétrico al anterior, hacia inglés.
- `"bilingue"`: no toca el documento — útil cuando el usuario quiere preservar
  contenido mixto intencionalmente.

Política compartida:
- Vocabulario técnico-actuarial preciso (BEL, MP, ESG, GAAP, IFRS) se preserva.
- Identifiers, nombres propios y rutas de archivo verbatim.
- Audit trail e IDs no se traducen.
- Las llamadas LLM se contabilizan en `documento.metricas_uso`.
- Errores LLM se loggean y se siguen procesando el resto de secciones.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Final, Literal

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento
from src.core.usecases.strings_localizados import (
    MOTIVOS_PREDEFINIDOS_ES,
    traducir_motivo_predefinido,
)
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts.traduccion import (
    PROMPT_DETECTAR_IDIOMA,
    PROMPT_TRADUCCION_EN,
    PROMPT_TRADUCCION_ES,
)

# Modos del exportador: legacy ("es", "en") + nuevos.
Idioma = Literal["es", "en", "es_normalize", "en_normalize", "bilingue"]
IDIOMAS_SOPORTADOS: Final[tuple[Idioma, ...]] = (
    "es",
    "en",
    "es_normalize",
    "en_normalize",
    "bilingue",
)

# Idiomas “físicos” usados para detección y dirección de traducción.
IdiomaBase = Literal["es", "en"]

logger = logging.getLogger(__name__)


def _idioma_base_target(modo: Idioma) -> IdiomaBase | None:
    """Devuelve el idioma base hacia el que se está convirtiendo.

    `None` significa que el modo NO traduce (es/bilingue legacy/nuevo).
    """
    if modo in ("es", "bilingue"):
        return None
    if modo == "en":
        return "en"
    if modo == "es_normalize":
        return "es"
    if modo == "en_normalize":
        return "en"
    return None


class TraductorDocumento:
    """Traduce o normaliza el contenido del documento al idioma destino."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def traducir(self, documento: Documento, *, idioma_objetivo: Idioma) -> Documento:
        """Mutación efímera del documento en el idioma objetivo.

        El comportamiento depende del modo elegido (ver docstring del módulo).
        """
        if idioma_objetivo not in IDIOMAS_SOPORTADOS:
            raise ValueError(
                f"Idioma '{idioma_objetivo}' no soportado. Opciones: {IDIOMAS_SOPORTADOS}."
            )

        # Modos que no tocan el documento.
        if idioma_objetivo in ("es", "bilingue"):
            return documento

        idioma_base = _idioma_base_target(idioma_objetivo)
        if idioma_base is None:
            return documento

        normalizar = idioma_objetivo in ("es_normalize", "en_normalize")

        # Metadata free-text
        meta = documento.metadata_modelo
        if meta.intended_use.strip():
            meta.intended_use = self._convertir_si_necesario(
                documento, meta.intended_use, idioma_base, normalizar
            )
        if meta.use_restrictions.strip():
            meta.use_restrictions = self._convertir_si_necesario(
                documento, meta.use_restrictions, idioma_base, normalizar
            )

        # Secciones
        for seccion in documento.secciones:
            if seccion.completitud == "omitida":
                if seccion.motivo_omision:
                    seccion.motivo_omision = self._traducir_motivo(
                        documento, seccion.motivo_omision, idioma_base
                    )
                continue
            if seccion.contenido and seccion.contenido.strip():
                seccion.contenido = self._convertir_si_necesario(
                    documento, seccion.contenido, idioma_base, normalizar
                )

        # Apéndices
        for apendice in documento.apendices:
            if apendice.contenido_md.strip():
                apendice.contenido_md = self._convertir_si_necesario(
                    documento, apendice.contenido_md, idioma_base, normalizar
                )
            if apendice.titulo.strip():
                with contextlib.suppress(Exception):
                    apendice.titulo = self._convertir_si_necesario(
                        documento, apendice.titulo, idioma_base, normalizar
                    )

        return documento

    def _convertir_si_necesario(
        self,
        documento: Documento,
        texto: str,
        idioma_base: IdiomaBase,
        normalizar: bool,
    ) -> str:
        """Decide si traducir o preservar.

        - Si `normalizar` es True: detecta idioma del texto. Si ya está en
          `idioma_base`, lo devuelve sin tocar. Si no, lo traduce.
        - Si `normalizar` es False (modo "en" legacy): traduce siempre.
        """
        if not texto.strip():
            return texto

        if not normalizar:
            return self._traducir_texto(documento, texto, idioma_base)

        detectado = self._detectar_idioma(documento, texto)
        if detectado == idioma_base:
            return texto  # ya está en el idioma destino, preservar
        # detectado es "en", "es" o "mixed" — en los tres casos traducimos.
        return self._traducir_texto(documento, texto, idioma_base)

    def _detectar_idioma(self, documento: Documento, texto: str) -> str:
        """Llama a Haiku para detectar el idioma. Devuelve 'es', 'en' o 'mixed'.

        Tolerante: si falla, devuelve 'mixed' (forzando traducción para no
        ocultar contenido al usuario).
        """
        try:
            system_blocks: list[TextBlockParam] = [{"type": "text", "text": PROMPT_DETECTAR_IDIOMA}]
            # Limitamos a primeros 1500 chars: muestra representativa suficiente
            # para detectar idioma sin gastar tokens innecesarios.
            muestra = texto[:1500]
            messages: list[MessageParam] = [{"role": "user", "content": muestra}]
            respuesta = self.llm.chat(
                tarea="extraction",  # tarea barata: Haiku
                system_blocks=system_blocks,
                messages=messages,
                max_tokens=8,
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
            valor = respuesta.text.strip().lower()
            if valor in ("es", "en", "mixed"):
                return valor
            # respuesta inesperada → tratar como mixed (más seguro)
            logger.warning("Detector de idioma devolvió token inesperado: %r", valor)
            return "mixed"
        except Exception as exc:
            logger.warning(
                "Detección de idioma falló (%s) — asumiendo 'mixed' para forzar traducción.",
                exc.__class__.__name__,
                exc_info=True,
            )
            return "mixed"

    def _traducir_motivo(
        self, documento: Documento, motivo: str, idioma_objetivo: IdiomaBase
    ) -> str:
        """Traduce el motivo de omisión.

        Si el motivo es uno de los 4 predefinidos en `MOTIVOS_PREDEFINIDOS_ES`,
        usa el swap directo de `strings_localizados` (sin LLM).
        """
        directo = traducir_motivo_predefinido(motivo, idioma_objetivo)
        if directo is not None and directo != motivo:
            return directo

        for predefinido in MOTIVOS_PREDEFINIDOS_ES:
            prefijo = f"{predefinido} — "
            if motivo.startswith(prefijo):
                comentario = motivo[len(prefijo) :]
                comentario_traducido = self._traducir_texto(documento, comentario, idioma_objetivo)
                pred_traducido = traducir_motivo_predefinido(predefinido, idioma_objetivo)
                return f"{pred_traducido} — {comentario_traducido}"

        return self._traducir_texto(documento, motivo, idioma_objetivo)

    def _traducir_texto(self, documento: Documento, texto: str, idioma_objetivo: IdiomaBase) -> str:
        """Una llamada LLM por bloque. Idioma destino elige el prompt."""
        if not texto.strip():
            return texto

        prompt = PROMPT_TRADUCCION_EN if idioma_objetivo == "en" else PROMPT_TRADUCCION_ES
        system_blocks: list[TextBlockParam] = [{"type": "text", "text": prompt}]
        messages: list[MessageParam] = [{"role": "user", "content": texto}]
        respuesta = self.llm.chat(
            tarea="chat",
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=4096,
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
