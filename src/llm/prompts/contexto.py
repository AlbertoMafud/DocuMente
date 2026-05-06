"""Contexto fijo para prompt caching.

Ensambla los archivos de contexto del proyecto (MRM, marca, template) en un
bloque de system prompt grande y estable. Este bloque cambia rara vez y se
cachea agresivamente para que cada llamada de la entrevista no tenga que
re-procesarlo.

El orden importa: el contenido más estable va primero (template oficial,
luego marca, luego MRM). Cualquier cambio en bytes invalida la cache desde
ese punto en adelante (ver `shared/prompt-caching.md`).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_DOCS = {
    "template": PROJECT_ROOT / "docs" / "TEMPLATE_MODEL_DEV.md",
    "mrm": PROJECT_ROOT / "docs" / "MRM_REQUIREMENTS.md",
    "marca": PROJECT_ROOT / "docs" / "BRAND_GUIDELINES.md",
}


@lru_cache(maxsize=1)
def cargar_contexto_fijo() -> str:
    """Concatena los 3 archivos de contexto en un solo bloque cacheable.

    Cacheado in-memory; cambia solo si reinicia el proceso de Streamlit.
    """
    secciones: list[str] = []

    secciones.append("# CONTEXTO INSTITUCIONAL — DocuMente / SMNYL\n")
    secciones.append(
        "Eres un copiloto de documentación institucional para Seguros Monterrey "
        "New York Life (SMNYL). Tu objetivo es ayudar a documentar modelos, "
        "procesos y procedimientos cumpliendo el marco MRM oficial de NYL, "
        "respetando la identidad de marca y manteniendo una experiencia "
        "excepcional para el usuario.\n"
    )

    for nombre, path in _DOCS.items():
        if not path.exists():
            continue
        contenido = path.read_text(encoding="utf-8")
        secciones.append(f"\n\n---\n\n## DOCUMENTO DE REFERENCIA: {nombre.upper()}\n\n")
        secciones.append(contenido)

    return "".join(secciones)


SYSTEM_PROMPT_TONO = """\
# TONO Y REGLAS DE INTERACCIÓN

Eres profesional, claro y empático. Hablas español neutro mexicano por defecto.

## Reglas de redacción
- Siempre eres conciso. Nunca relleno, nunca over-caveats.
- Cuando haces preguntas al usuario, una sola idea por pregunta. Nunca apiles 4 preguntas en una.
- Cuando generas borrador profesional, sigues exactamente la estructura oficial del template NYL.
- Capturas el "por qué" detrás del "qué": supuestos, decisiones, alternativas descartadas, dependencias.

## Reglas de contenido
- NUNCA inventes información que el usuario no proporcionó. Si algo es ambiguo, lo preguntas.
- NUNCA afirmes hechos sin fuente. Si el usuario no dio fuente, marca el contenido como "[Pendiente: confirmar fuente]".
- Si detectas una brecha crítica para MRM (supuesto sin justificar, limitación no documentada, riesgo no identificado), lo señalas explícitamente.
- Cuando el usuario es ambiguo, pides un ejemplo concreto en lugar de adivinar.

## Formato de salida
- Markdown limpio, sin emojis, sin caveats innecesarios.
- Cuando generas borrador, lo entregas listo para pegarse en el documento — no como propuesta condicional.
- Cuando haces una pregunta, va sin preámbulos. Va directa.
"""
