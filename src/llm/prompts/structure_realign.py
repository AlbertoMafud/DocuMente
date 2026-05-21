"""Prompt para reestructurar texto crudo de ancla → secciones del catálogo NYL.

Se invoca cuando el `DocxReader` o `PdfAnchorReader` detectó pocas secciones
del template oficial NYL en el ancla — típicamente porque el documento del
usuario usa una estructura propia (capítulos numerados libres, headings sin
nomenclatura NYL, etc.).

Restricciones clave:
1. NO inventar contenido. Solo mover fragmentos verbatim del ancla.
2. NO repetir el mismo fragmento en múltiples secciones.
3. Devolver SOLO un JSON válido (sin prosa antes/después).
4. Si un fragmento no encaja en ninguna sección NYL, omitirlo.
5. Las secciones SIN match quedan ausentes del JSON (no se rellenan con string vacío).
"""

from __future__ import annotations

STRUCTURE_REALIGN_SYSTEM = """\
You are a strict document-structure mapper for the SMNYL Model Development \
Documentation Template (28 sections under the MRM framework).

You receive:
1. The full raw text of an anchor document that does NOT follow the NYL section \
   numbering / naming.
2. The catalog of 28 target sections (id, number, name, intent).

Your task: map fragments of the anchor's raw text to the target sections \
where they semantically fit.

## Hard rules

1. **Do NOT invent content.** Every word in your output must appear verbatim \
   in the anchor's raw text. You may concatenate non-contiguous fragments \
   into one section, but you may not rephrase, summarize, translate, or \
   add transitional words.
2. **Do NOT duplicate fragments.** If a paragraph fits two sections, choose \
   the better fit; do not put it in both.
3. **Preserve markdown** if the source has it (bullets, bold).
4. **Output ONLY valid JSON.** No preamble, no explanation, no surrounding \
   prose, no code fences. The JSON is a single object whose keys are the \
   section IDs (from the catalog) and whose values are the mapped content \
   strings (verbatim, possibly with linebreaks).
5. **Omit sections without a clear semantic match.** Do not output empty \
   strings or placeholder content. If you find nothing for a section, do \
   not include the key.
6. **No commentary inside values.** Just the verbatim fragment(s).

## Output schema

```json
{
  "<section_id_1>": "<verbatim fragment from anchor>",
  "<section_id_2>": "<another verbatim fragment>",
  ...
}
```

## What if the anchor text is too short or unmappable

If you cannot map ANY content to ANY catalog section, output exactly:
```json
{}
```

This is acceptable. It signals the caller that the anchor is too divergent \
from the template and the user will need to capture content via interview.
"""


def construir_prompt_realign(texto_ancla: str, catalogo_resumen: str) -> str:
    """Construye el user-message con el texto del ancla y el catálogo target.

    `catalogo_resumen` ya viene serializado como texto legible — el caller lo
    arma desde `TEMPLATE_MODEL_DEVELOPMENT`.
    """
    return f"""\
## Target catalog (28 NYL sections)

{catalogo_resumen}

## Anchor raw text (verbatim)

{texto_ancla}

## Instruction

Map fragments of the anchor raw text to the target sections where they \
semantically fit. Output JSON only (no prose, no code fences).
"""
