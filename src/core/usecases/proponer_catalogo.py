"""Use case: ProponerCatalogo (Template Studio, paso 3).

Toma la estructura extraída del .docx y pide al LLM el catálogo AI-ready
completo (tarea 'drafting' — la calidad de intenciones y preguntas guía es
el corazón del producto; no se escatima aquí). El output es SOLO una
propuesta: la curación humana del paso 4 es obligatoria.

Tolerante a JSON malformado: si el LLM devuelve algo inparseable, se
reporta en advertencias y se devuelve propuesta vacía — nunca se truena.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.core.models.template_dinamico import SeccionCatalogoDinamica
from src.core.usecases.extraer_estructura_template import EstructuraExtraida
from src.llm import LLMClient
from src.llm.prompts.proponer_catalogo import (
    PROPONER_CATALOGO_SYSTEM,
    construir_prompt_propuesta,
)

logger = logging.getLogger(__name__)

_MAX_TOKENS_PROPUESTA = 8000


@dataclass
class ResultadoPropuesta:
    secciones: list[SeccionCatalogoDinamica] = field(default_factory=list)
    notas_llm: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


def _estructura_a_texto(estructura: EstructuraExtraida) -> str:
    lineas: list[str] = []
    if estructura.preambulo:
        lineas.append(f"[Preámbulo]\n{estructura.preambulo}\n")
    for s in estructura.secciones:
        encabezado = f"{s.numero} {s.titulo}".strip()
        lineas.append(f"## {encabezado} (nivel {s.nivel})")
        if s.texto:
            lineas.append(s.texto)
    if estructura.n_tablas_total:
        lineas.append(f"[El documento contiene {estructura.n_tablas_total} tabla(s).]")
    return "\n".join(lineas)


def _extraer_json(texto: str) -> dict[str, Any]:
    """Parsea el JSON de la respuesta, tolerando fences y texto alrededor."""
    limpio = texto.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", limpio, re.DOTALL)
    if fence:
        limpio = fence.group(1).strip()
    if not limpio.startswith("{"):
        inicio = limpio.find("{")
        fin = limpio.rfind("}")
        if inicio == -1 or fin <= inicio:
            raise ValueError("La respuesta no contiene un objeto JSON.")
        limpio = limpio[inicio : fin + 1]
    resultado = json.loads(limpio)
    if not isinstance(resultado, dict):
        raise ValueError("El JSON raíz no es un objeto.")
    return resultado


class ProponerCatalogo:
    """Propone el catálogo AI-ready de un template con el LLM."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def ejecutar(
        self,
        *,
        nombre_template: str,
        descripcion: str,
        estructura: EstructuraExtraida,
    ) -> ResultadoPropuesta:
        prompt = construir_prompt_propuesta(
            nombre_template=nombre_template,
            descripcion=descripcion,
            estructura_texto=_estructura_a_texto(estructura),
        )
        respuesta = self._llm.chat(
            tarea="drafting",
            system_blocks=[
                {
                    "type": "text",
                    "text": PROPONER_CATALOGO_SYSTEM,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=_MAX_TOKENS_PROPUESTA,
        )

        resultado = ResultadoPropuesta()
        try:
            data = _extraer_json(respuesta.text)
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("Propuesta LLM inparseable: %s", exc)
            resultado.advertencias.append(
                "La propuesta del asistente no se pudo interpretar — reintenta o "
                "construye el catálogo manualmente desde la estructura extraída."
            )
            return resultado

        crudas = data.get("secciones", [])
        for i, cruda in enumerate(crudas):
            if not isinstance(cruda, dict):
                continue
            try:
                resultado.secciones.append(SeccionCatalogoDinamica.model_validate(cruda))
            except Exception as exc:  # Pydantic ValidationError y similares
                logger.warning("Sección propuesta %d inválida: %s", i, exc)
                nombre = cruda.get("nombre", f"#{i + 1}")
                resultado.advertencias.append(
                    f"La sección propuesta '{nombre}' venía malformada y se descartó."
                )

        notas = data.get("notas", [])
        if isinstance(notas, list):
            resultado.notas_llm = [str(n) for n in notas]

        if not resultado.secciones:
            resultado.advertencias.append("El asistente no propuso ninguna sección válida.")
        return resultado
