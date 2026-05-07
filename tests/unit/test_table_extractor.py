"""Tests de TableExtractor — extracción de tabla estructurada desde texto narrativo."""

from __future__ import annotations

from src.core.models import Documento, Seccion
from src.core.usecases.table_extractor import TableExtractor, TableSchema
from tests.unit.test_interview_engine import FakeLLM

SCHEMA_UPSTREAM = TableSchema(
    nombre="upstream_models",
    campos=["num", "name", "key_contact", "inventory_id"],
    descripcion_para_llm=(
        "Lista de modelos upstream o supuestos determinados por la compañía "
        "que el modelo consume. Cada item: número secuencial, nombre del "
        "modelo/supuesto, contacto clave y model ID en inventario MRM."
    ),
)


def _doc_con_seccion(seccion_id: str, contenido: str) -> Documento:
    return Documento(
        secciones=[
            Seccion(
                id=seccion_id,
                nombre="Test",
                numero="5.2",
                obligatoria=True,
                contenido=contenido,
                completitud="completa",
            )
        ]
    )


def test_extraer_devuelve_lista_de_dicts_con_campos_del_schema() -> None:
    """Happy path: el LLM devuelve JSON válido y se parsea a list[dict]."""
    llm = FakeLLM(
        [
            '[{"num": "1", "name": "Prophet Disponible",'
            ' "key_contact": "Yael Aguilera", "inventory_id": "M07.001"}]'
        ]
    )
    doc = _doc_con_seccion(
        "5.2.upstream",
        "El modelo consume Prophet Disponible (M07.001) cuyo contacto es Yael Aguilera.",
    )

    extractor = TableExtractor(llm)
    resultado = extractor.extraer(doc, "5.2.upstream", SCHEMA_UPSTREAM)

    assert resultado == [
        {
            "num": "1",
            "name": "Prophet Disponible",
            "key_contact": "Yael Aguilera",
            "inventory_id": "M07.001",
        }
    ]


def test_extraer_devuelve_lista_vacia_si_seccion_sin_contenido() -> None:
    """Si la sección está vacía u omitida, no llama al LLM y devuelve []."""
    llm = FakeLLM(["nunca debería llamarse"])
    doc = _doc_con_seccion("5.2.upstream", "")

    extractor = TableExtractor(llm)
    resultado = extractor.extraer(doc, "5.2.upstream", SCHEMA_UPSTREAM)

    assert resultado == []
    assert llm.llamadas == []


def test_extraer_devuelve_lista_vacia_si_llm_devuelve_json_invalido() -> None:
    """Robustez: si el LLM devuelve algo que no parsea como JSON, devuelve [] sin romper."""
    llm = FakeLLM(["No JSON parseable, lorem ipsum dolor sit amet"])
    doc = _doc_con_seccion("5.2.upstream", "Texto con info real.")

    extractor = TableExtractor(llm)
    resultado = extractor.extraer(doc, "5.2.upstream", SCHEMA_UPSTREAM)

    assert resultado == []


def test_extraer_acepta_json_envuelto_en_fences_de_codigo() -> None:
    """El LLM a veces envuelve JSON en ```json ... ```; el extractor debe limpiarlo."""
    llm = FakeLLM(
        ['```json\n[{"num": "1", "name": "X", "key_contact": "Y", "inventory_id": "Z"}]\n```']
    )
    doc = _doc_con_seccion("5.2.upstream", "Texto con info.")

    extractor = TableExtractor(llm)
    resultado = extractor.extraer(doc, "5.2.upstream", SCHEMA_UPSTREAM)

    assert len(resultado) == 1
    assert resultado[0]["name"] == "X"


def test_extraer_normaliza_campos_faltantes_a_string_vacio() -> None:
    """Si el LLM omite un campo del schema, se rellena con '' para que docxtpl no falle."""
    llm = FakeLLM(['[{"num": "1", "name": "Solo nombre"}]'])
    doc = _doc_con_seccion("5.2.upstream", "Texto.")

    extractor = TableExtractor(llm)
    resultado = extractor.extraer(doc, "5.2.upstream", SCHEMA_UPSTREAM)

    assert resultado == [{"num": "1", "name": "Solo nombre", "key_contact": "", "inventory_id": ""}]


def test_extraer_usa_tarea_extraction_para_modelo_haiku() -> None:
    """Verifica que pide tarea='extraction' al LLM (mapea a Haiku, no Opus)."""
    llm = FakeLLM(["[]"])
    doc = _doc_con_seccion("5.2.upstream", "Texto.")

    TableExtractor(llm).extraer(doc, "5.2.upstream", SCHEMA_UPSTREAM)

    assert len(llm.llamadas) == 1
    tarea, _, _ = llm.llamadas[0]
    assert tarea == "extraction"


def test_extraer_registra_llamada_en_metricas_uso() -> None:
    """Cada extracción agrega entrada al audit de costo del documento."""
    llm = FakeLLM(["[]"])
    doc = _doc_con_seccion("5.2.upstream", "Texto.")
    assert len(doc.metricas_uso.llamadas) == 0

    TableExtractor(llm).extraer(doc, "5.2.upstream", SCHEMA_UPSTREAM)

    assert len(doc.metricas_uso.llamadas) == 1
    assert doc.metricas_uso.llamadas[0].tarea == "extraction"
