"""Tests de GapAnalyzer."""

from __future__ import annotations

from src.core.models import Documento, MetadataModelo, Seccion
from src.core.usecases.gap_analyzer import GapAnalyzer


def _doc_con_secciones(*secciones: Seccion) -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(
            nombre_modelo="Test",
            model_owner="Owner",
            fae="FAE",
            intended_use="test use",
        ),
        secciones=list(secciones),
    )


def test_gap_analyzer_detecta_obligatoria_vacia_como_alta() -> None:
    doc = _doc_con_secciones(
        Seccion(id="x.1", nombre="X", numero="1", obligatoria=True, completitud="vacia"),
    )
    brechas = GapAnalyzer().analizar(doc)
    assert any(b.severidad == "alta" and b.seccion_id == "x.1" for b in brechas)


def test_gap_analyzer_detecta_parcial_como_media() -> None:
    doc = _doc_con_secciones(
        Seccion(
            id="x.1",
            nombre="X",
            numero="1",
            obligatoria=True,
            completitud="parcial",
            contenido="muy poco",
        ),
    )
    brechas = GapAnalyzer().analizar(doc)
    assert any(b.severidad == "media" and b.seccion_id == "x.1" for b in brechas)


def test_gap_analyzer_no_genera_brecha_para_completas() -> None:
    doc = _doc_con_secciones(
        Seccion(
            id="x.1",
            nombre="X",
            numero="1",
            obligatoria=True,
            completitud="completa",
            contenido="contenido suficiente " * 30,
        ),
    )
    brechas = GapAnalyzer().analizar(doc)
    assert not any(b.seccion_id == "x.1" for b in brechas)


def test_gap_analyzer_opcional_vacia_como_baja() -> None:
    doc = _doc_con_secciones(
        Seccion(id="x.1", nombre="X", numero="1", obligatoria=False, completitud="vacia"),
    )
    brechas = GapAnalyzer().analizar(doc)
    assert any(b.severidad == "baja" and b.seccion_id == "x.1" for b in brechas)


def test_gap_analyzer_metadata_faltante_es_alta() -> None:
    doc = Documento(secciones=[])  # sin metadata
    brechas = GapAnalyzer().analizar(doc)
    assert any(b.tipo == "metadata_faltante" and b.severidad == "alta" for b in brechas)


def test_gap_analyzer_orden_severidad_descendente() -> None:
    """Las brechas se devuelven con altas primero, luego medias, luego bajas."""
    doc = _doc_con_secciones(
        Seccion(id="a", nombre="A", numero="1", obligatoria=False, completitud="vacia"),
        Seccion(id="b", nombre="B", numero="2", obligatoria=True, completitud="vacia"),
        Seccion(
            id="c",
            nombre="C",
            numero="3",
            obligatoria=True,
            completitud="parcial",
            contenido="x",
        ),
    )
    # Falta metadata también → alta
    brechas = GapAnalyzer().analizar(doc)
    severidades = [b.severidad for b in brechas]
    # Validar que altas vienen antes que medias y bajas
    posiciones = {"alta": 0, "media": 1, "baja": 2}
    indices = [posiciones[s] for s in severidades]
    assert indices == sorted(indices)
