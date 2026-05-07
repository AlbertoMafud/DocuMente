"""TraductorDocumento — traducción del contenido al inglés corporativo americano.

Cuando el documento se va a presentar a audiencias en inglés (NY DFS, casa
matriz NYL, auditoría externa), el contenido capturado en español debe
traducirse manteniendo:
- Vocabulario técnico-actuarial preciso (BEL, MP, ESG, GAAP, IFRS).
- Tono institucional formal (registro de "documentación regulatoria").
- Formato markdown intacto (negritas, cursivas, tablas, bullets).
- Identifiers, nombres propios y rutas de archivo verbatim.

Política: si `idioma_objetivo == 'es'`, devuelve el documento sin tocarlo
(no llama LLM). Si `'en'`, traduce contenido de secciones con texto, los
campos free-text de metadata (intended_use, use_restrictions), y los
apéndices. NO traduce IDs, nombres, ni audit_trail (es histórico).
"""

from __future__ import annotations

import contextlib
from typing import Final, Literal

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento
from src.llm import LLMClient
from src.llm.pricing import construir_llamada

Idioma = Literal["es", "en"]
IDIOMAS_SOPORTADOS: Final[tuple[Idioma, ...]] = ("es", "en")

_PROMPT_TRADUCCION_EN = """\
You are a professional translator specialized in actuarial and insurance \
documentation for U.S. regulatory frameworks (NY DFS, NAIC, GAAP, IFRS).

Translate the source text to **formal American corporate English** \
appropriate for a Model Development Documentation Template under the \
NYL/SMNYL Model Risk Management framework.

## Hard rules

1. Preserve markdown formatting verbatim: `**bold**`, `*italic*`, bullets `- `, \
   tables with pipes `| col | col |`, line breaks. Do NOT convert markdown to \
   plain text or HTML.
2. Preserve technical actuarial terminology accurately: BEL → BEL (no expansion), \
   MP → MP, ESG → ESG, IFRS 17 → IFRS 17, SAP → SAP, etc. When the Spanish term \
   has a precise English equivalent (e.g., "supuestos" → "assumptions", \
   "calibración" → "calibration", "primas" → "premiums"), use it.
3. Preserve verbatim: model names, model IDs, person names, file paths, table \
   names, and any string in backticks.
4. Use third-person impersonal voice. Avoid contractions (use "do not" instead \
   of "don't"). Match the register of regulatory memos.
5. Output ONLY the translation. No preamble, no commentary, no surrounding \
   quotes.
6. If the source text is empty or only whitespace, output an empty string.
"""


class TraductorDocumento:
    """Traduce el contenido textual de un documento al idioma destino vía LLM."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def traducir(self, documento: Documento, *, idioma_objetivo: Idioma) -> Documento:
        """Devuelve un Documento con el contenido traducido al idioma destino.

        Si `idioma_objetivo == 'es'`, devuelve el mismo documento sin tocar.
        Para `'en'`, traduce: contenido de cada sección con texto, intended_use
        y use_restrictions de metadata, y contenido_md de cada apéndice.
        """
        if idioma_objetivo == "es":
            return documento

        if idioma_objetivo not in IDIOMAS_SOPORTADOS:
            raise ValueError(
                f"Idioma '{idioma_objetivo}' no soportado. Opciones: {IDIOMAS_SOPORTADOS}."
            )

        # Mutamos el mismo documento para no perder identidad ni referencias.
        # El consumidor (ExportarDocumento) que decida si quiere persistir o no.
        meta = documento.metadata_modelo
        if meta.intended_use.strip():
            meta.intended_use = self._traducir_texto(documento, meta.intended_use)
        if meta.use_restrictions.strip():
            meta.use_restrictions = self._traducir_texto(documento, meta.use_restrictions)

        for seccion in documento.secciones:
            if seccion.completitud == "omitida":
                continue
            if seccion.contenido and seccion.contenido.strip():
                seccion.contenido = self._traducir_texto(documento, seccion.contenido)

        for apendice in documento.apendices:
            if apendice.contenido_md.strip():
                apendice.contenido_md = self._traducir_texto(documento, apendice.contenido_md)
            if apendice.titulo.strip():
                # Título corto: traducción inline rápida.
                with contextlib.suppress(Exception):
                    apendice.titulo = self._traducir_texto(documento, apendice.titulo)

        return documento

    def _traducir_texto(self, documento: Documento, texto: str) -> str:
        """Una llamada LLM por bloque de texto. Tolerante a errores."""
        if not texto.strip():
            return texto

        system_blocks: list[TextBlockParam] = [{"type": "text", "text": _PROMPT_TRADUCCION_EN}]
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
