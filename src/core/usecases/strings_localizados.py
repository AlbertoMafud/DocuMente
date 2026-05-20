"""Catálogo de cadenas localizadas (ES/EN) que aparecen en el DOCX exportado.

El traductor LLM cubre el contenido capturado por el usuario, pero hay cadenas
generadas en runtime por el writer (marcadores de sección omitida, etiquetas
de apéndices, motivos predefinidos de omisión) que nunca pasan por el LLM y
quedaban hardcodeadas en español, contaminando los exports en inglés.

Este módulo centraliza esas cadenas para que tanto el writer como el traductor
las resuelvan vía `t(key, idioma)`. Para los motivos predefinidos de omisión,
el traductor hace swap directo sin llamada LLM (más rápido y consistente).
"""

from __future__ import annotations

from typing import Final, Literal

Idioma = Literal["es", "en"]

STRINGS_UI: Final[dict[str, dict[Idioma, str]]] = {
    # Marcadores del writer cuando una sección no tiene contenido renderizable.
    "seccion_omitida_prefijo": {
        "es": "Sección omitida — ",
        "en": "Section omitted — ",
    },
    "seccion_sin_motivo": {
        "es": "Sin motivo registrado",
        "en": "No reason recorded",
    },
    "seccion_no_catalogo": {
        "es": "[Sección no presente en el catálogo]",
        "en": "[Section not present in the catalog]",
    },
    "pendiente_sin_contenido": {
        "es": "[Pendiente — sin contenido capturado]",
        "en": "[Pending — no content captured]",
    },
    # Borrador automático (multi-fuente / brief inicial — puntos 1 y 5).
    "borrador_revisar": {
        "es": "[Borrador — revisar]",
        "en": "[Draft — review]",
    },
    "borrador_automatico_revisar": {
        "es": "[Borrador automático — revisar]",
        "en": "[Automatic draft — review]",
    },
    # Reestructurado por StructureRealigner (B.1) — contenido del ancla
    # mapeado a una sección NYL distinta a la nomenclatura original.
    "reestructurado_revisar": {
        "es": "[Re-estructurado desde ancla — revisar]",
        "en": "[Re-structured from anchor — review]",
    },
    # Motivos predefinidos de omisión (en `OmitirSeccion.MOTIVOS_OMISION`).
    "motivo_no_aplica": {
        "es": "No aplica al modelo",
        "en": "Not applicable to the model",
    },
    "motivo_info_no_disponible": {
        "es": "Información no disponible",
        "en": "Information not available",
    },
    "motivo_pendiente_version_futura": {
        "es": "Pendiente para versión futura",
        "en": "Pending for a future version",
    },
    "motivo_otro": {
        "es": "Otro (especificar)",
        "en": "Other (please specify)",
    },
    # Etiquetas de apéndices (consumidas por el writer; el rework completo
    # vive en el punto 4 del plan, pero las claves ya están listas).
    "apendice_singular": {"es": "Apéndice", "en": "Appendix"},
    "apendices_plural": {"es": "Apéndices", "en": "Appendix"},
    "ver_apendice": {"es": "ver Apéndice", "en": "see Appendix"},
    # Citas de fuente (multi-fuente — punto 1).
    "fuente_label": {"es": "fuente", "en": "source"},
}


def t(key: str, idioma: Idioma) -> str:
    """Devuelve la traducción de `key` para `idioma`.

    Si la clave no existe, devuelve la clave entre paréntesis angulares
    (`<missing:key>`) para que sea visible en QA en lugar de fallar silencioso.
    """
    entrada = STRINGS_UI.get(key)
    if entrada is None:
        return f"<missing:{key}>"
    return entrada[idioma]


# Lista pública de los 4 motivos predefinidos en su idioma fuente (español),
# útil para que el traductor identifique cuándo hacer swap directo vs LLM.
MOTIVOS_PREDEFINIDOS_ES: Final[tuple[str, ...]] = (
    STRINGS_UI["motivo_no_aplica"]["es"],
    STRINGS_UI["motivo_info_no_disponible"]["es"],
    STRINGS_UI["motivo_pendiente_version_futura"]["es"],
    STRINGS_UI["motivo_otro"]["es"],
)


def traducir_motivo_predefinido(motivo_es: str, idioma: Idioma) -> str | None:
    """Si `motivo_es` es uno de los 4 motivos predefinidos en español, devuelve
    su versión en `idioma`. Si no coincide, devuelve None (caller debe usar LLM).
    """
    if idioma == "es":
        return motivo_es
    mapeo = {
        STRINGS_UI["motivo_no_aplica"]["es"]: STRINGS_UI["motivo_no_aplica"][idioma],
        STRINGS_UI["motivo_info_no_disponible"]["es"]: STRINGS_UI["motivo_info_no_disponible"][
            idioma
        ],
        STRINGS_UI["motivo_pendiente_version_futura"]["es"]: STRINGS_UI[
            "motivo_pendiente_version_futura"
        ][idioma],
        STRINGS_UI["motivo_otro"]["es"]: STRINGS_UI["motivo_otro"][idioma],
    }
    return mapeo.get(motivo_es)
