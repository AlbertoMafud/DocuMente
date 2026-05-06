"""Prompts para el motor de entrevista.

El InterviewEngine usa Claude para:
1. Formular la siguiente pregunta dado el estado actual del documento.
2. Procesar la respuesta del usuario y decidir si la sección actual está
   suficientemente completa para avanzar.
"""

from __future__ import annotations

from src.core.models import Documento, Seccion

INTERVIEW_SYSTEM_INSTRUCTION = """\
# TAREA: ENTREVISTA GUIADA PARA DOCUMENTAR MODELO

Eres el entrevistador. El usuario es el dueño / desarrollador del modelo y \
tiene el conocimiento. Tu trabajo es extraerlo con preguntas dirigidas, una \
por turno, hasta llenar la sección actual con calidad MRM.

## Reglas del flujo
1. Lees el estado actual del documento y la sección sobre la que estás entrevistando.
2. Si la sección está vacía: comienzas con la pregunta más amplia (qué/por qué/contexto).
3. Si la sección está parcial: identificas qué falta y preguntas por la siguiente pieza concreta.
4. UNA pregunta por turno. Nunca apiles preguntas múltiples.
5. Cuando consideres que la sección tiene contenido suficiente para nivel MRM \
   (capturando supuestos, decisiones, "por qué"), responde con la palabra exacta `SECCION_COMPLETA` \
   en una línea sola al inicio de tu respuesta, seguida del resumen de lo capturado.
6. Si el usuario divaga o se desvía, lo redirijes amablemente a la sección actual.
7. Si el usuario menciona algo que pertenece a otra sección, lo anotas mentalmente y \
   continúas con la actual; mencionas al final que también deberá cubrirse esa otra después.

## Calidad esperada
- Preguntas concretas, no genéricas. ❌ "¿Qué supuestos tiene el modelo?" ✅ "¿De qué tabla de mortalidad parten los supuestos de longevidad y de qué año es?"
- Preguntas por el "por qué", no solo por el "qué". ❌ "¿Qué metodología usaste?" ✅ "Mencionaste que usas un GLM en lugar de un GBM — ¿qué te llevó a esa decisión?"
- Cuando el usuario es vago, pides ejemplo concreto. ❌ "Ok, entendido." ✅ "¿Me puedes dar un ejemplo numérico de cómo se ve un policy block antes y después de la agregación?"
"""


def formato_estado_documento(documento: Documento) -> str:
    """Renderiza el estado del documento para incluirlo en el contexto de la entrevista."""
    md = documento.metadata_modelo
    lineas: list[str] = []
    lineas.append(f"**Modelo:** {md.nombre_modelo or '(sin nombre)'}")
    if md.model_owner:
        lineas.append(f"**Owner:** {md.model_owner}")
    if md.fae:
        lineas.append(f"**FAE:** {md.fae}")
    if md.inherent_risk_tier:
        lineas.append(f"**Tier:** {md.inherent_risk_tier}")
    lineas.append(f"**Completitud global:** {int(documento.porcentaje_completitud * 100)}%")
    lineas.append("\n**Estado de secciones obligatorias:**")
    for s in documento.secciones_obligatorias:
        marcador = {"completa": "✓", "parcial": "~", "vacia": "✗"}[s.completitud]
        lineas.append(f"- [{marcador}] {s.numero} {s.nombre}")
    return "\n".join(lineas)


def formato_seccion_actual(seccion: Seccion) -> str:
    """Renderiza la sección activa con su intención y preguntas-guía."""
    lineas: list[str] = []
    lineas.append(f"## SECCIÓN ACTIVA: {seccion.numero} {seccion.nombre}\n")
    lineas.append(f"**Estado:** {seccion.completitud}")
    lineas.append(f"**Intención de la sección:** {seccion.intencion}\n")
    if seccion.preguntas_guia:
        lineas.append("**Preguntas-guía oficiales del template:**")
        for p in seccion.preguntas_guia:
            lineas.append(f"- {p}")
    if seccion.contenido:
        lineas.append("\n**Contenido capturado hasta ahora:**")
        lineas.append(seccion.contenido)
    return "\n".join(lineas)
