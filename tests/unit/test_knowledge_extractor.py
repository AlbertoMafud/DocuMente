"""Tests del KnowledgeExtractor con LLM mockeado."""

from __future__ import annotations

from src.core.models import (
    Documento,
    EstadoEntrevista,
    MensajeEntrevista,
    MetadataModelo,
    Seccion,
)
from src.core.usecases.knowledge_extractor import KnowledgeExtractor, _extraer_json
from tests.unit.test_interview_engine import FakeLLM


def _setup() -> tuple[Documento, Seccion, EstadoEntrevista]:
    seccion = Seccion(
        id="4.4.assumptions",
        nombre="Key Assumptions",
        numero="4.4",
        obligatoria=True,
        intencion="x",
    )
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Test"),
        secciones=[seccion],
    )
    estado = EstadoEntrevista(
        documento_id=str(doc.id),
        seccion_id=seccion.id,
        mensajes=[
            MensajeEntrevista(rol="assistant", contenido="¿Plataforma?"),
            MensajeEntrevista(
                rol="user",
                contenido="Corremos el modelo en Prophet, mensualmente.",
            ),
        ],
    )
    return doc, seccion, estado


def test_extraer_json_con_texto_limpio() -> None:
    texto = '{"plataforma": "Prophet", "lenguaje_codigo": ""}'
    result = _extraer_json(texto)
    assert result == {"plataforma": "Prophet", "lenguaje_codigo": ""}


def test_extraer_json_con_fences_markdown() -> None:
    texto = '```json\n{"plataforma": "Prophet"}\n```'
    result = _extraer_json(texto)
    assert result == {"plataforma": "Prophet"}


def test_extraer_json_con_texto_alrededor() -> None:
    texto = 'Aquí va el JSON:\n{"plataforma": "Prophet"}\n\nFin.'
    result = _extraer_json(texto)
    assert result == {"plataforma": "Prophet"}


def test_extraer_json_invalido_devuelve_none() -> None:
    assert _extraer_json("no es json") is None
    assert _extraer_json("{invalid json}") is None


def test_extractor_actualiza_memoria() -> None:
    fake = FakeLLM(
        [
            '{"plataforma": "Prophet", "frecuencia_corridas": "mensual", '
            '"lenguaje_codigo": "", "esg_usado": "", "rutas_principales": [], '
            '"owner_responsable": "", "fae_responsable": "", '
            '"dependencias_upstream": [], "dependencias_downstream": [], '
            '"hechos_libres": []}'
        ]
    )
    extractor = KnowledgeExtractor(fake)
    doc, seccion, estado = _setup()

    cambios = extractor.extraer_y_actualizar(doc, seccion, estado)

    assert cambios is True
    assert doc.memoria_modelo.plataforma == "Prophet"
    assert doc.memoria_modelo.frecuencia_corridas == "mensual"
    assert any(e.tipo == "metadata_actualizada" for e in doc.audit_trail)


def test_extractor_sin_hechos_no_marca_cambios() -> None:
    fake = FakeLLM(
        [
            '{"plataforma": "", "frecuencia_corridas": "", "lenguaje_codigo": "", '
            '"esg_usado": "", "rutas_principales": [], "owner_responsable": "", '
            '"fae_responsable": "", "dependencias_upstream": [], '
            '"dependencias_downstream": [], "hechos_libres": []}'
        ]
    )
    extractor = KnowledgeExtractor(fake)
    doc, seccion, estado = _setup()

    cambios = extractor.extraer_y_actualizar(doc, seccion, estado)

    assert cambios is False
    assert doc.memoria_modelo.esta_vacia is True


def test_extractor_pide_tarea_extraction() -> None:
    """Validamos que el extractor usa Haiku, no Opus/Sonnet."""
    fake = FakeLLM(['{"plataforma": "Prophet"}'])
    extractor = KnowledgeExtractor(fake)
    doc, seccion, estado = _setup()
    extractor.extraer_y_actualizar(doc, seccion, estado)

    tarea, _, _ = fake.llamadas[0]
    assert tarea == "extraction", "KnowledgeExtractor debe usar tarea='extraction' (Haiku)"
