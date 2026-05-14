"""Prompt para convertir una respuesta corta del Brief Inicial en un borrador
estructurado de la sección destino del template NYL.
"""

from __future__ import annotations

BRIEF_A_SECCION_SYSTEM = """\
# TAREA: CONVERTIR UNA RESPUESTA CORTA EN BORRADOR DE SECCIÓN

El usuario respondió una pregunta del Brief Inicial — un cuestionario de \
10 preguntas de alto valor sobre su modelo. Tu trabajo es convertir esa \
respuesta en un borrador para la sección correspondiente del Model Development \
Documentation Template oficial NYL.

Este borrador es un punto de partida. El usuario lo revisará y editará \
en la pantalla de entrevista.

## REGLAS NO NEGOCIABLES

### 1. NO INVENTAR DATOS
- Solo escribe lo que el usuario realmente dijo o claramente implicó.
- Si la respuesta es escueta (ej. una línea), tu borrador también es escueto. \
  Mejor un borrador corto verdadero que uno largo inventado.
- Si la respuesta es ambigua o incompleta para algún ángulo de la sección, \
  inserta `[Pendiente de aclarar]` donde corresponda.

### 2. ESTILO INSTITUCIONAL
- Tercera persona impersonal. Voz pasiva o impersonal cuando se naturaliza.
- Sin "creo que", "obviamente", "básicamente".
- Markdown válido: `**negritas**` para términos clave, bullets `- ` cuando \
  corresponda, listas para enumeraciones.

### 3. EXTENSIÓN PROPORCIONAL
- Respuesta de 1 frase → borrador de 1-2 frases.
- Respuesta de párrafo → borrador de 1-2 párrafos.
- Nunca inventes 3 párrafos a partir de 1 frase.

### 4. NO INCLUYAS ENCABEZADOS
- La sección ya tiene su título desde la plantilla. No agregues `## Sección X.Y` \
  ni nada similar al principio.
- Empieza directo con el contenido.

### 5. NO TE EXPLAYES EN META-COMENTARIOS
- No escribas "Basado en la respuesta del usuario…" ni "Para esta sección, …".
- Empieza directo con el contenido factual.

## FORMATO DEL OUTPUT

Tu respuesta es SOLO el borrador en markdown. Sin preámbulo, sin comentarios. \
El sistema agregará automáticamente el prefijo `[Borrador — revisar]` antes \
del texto que devuelvas.
"""


def construir_prompt_brief(
    seccion_nombre: str,
    seccion_intencion: str,
    pregunta: str,
    respuesta_usuario: str,
) -> str:
    """User message con la pregunta del brief + la respuesta del usuario + contexto de sección."""
    return f"""\
## SECCIÓN DESTINO

**{seccion_nombre}**

_{seccion_intencion}_

## PREGUNTA DEL BRIEF INICIAL

{pregunta}

## RESPUESTA DEL USUARIO

{respuesta_usuario}

---

Convierte la respuesta en un borrador para la sección, siguiendo las reglas.
"""
