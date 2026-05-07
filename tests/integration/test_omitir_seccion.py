"""Tests del use case OmitirSeccion (integración con repo real)."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models import Documento, Seccion
from src.core.usecases.omitir_seccion import (
    MOTIVOS_OMISION,
    OmitirSeccion,
)
from src.storage.repositories import DocumentoRepository


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


def _doc_con_seccion_vacia() -> Documento:
    return Documento(
        secciones=[
            Seccion(
                id="s.1",
                nombre="Sección de prueba",
                numero="1.1",
                obligatoria=True,
                completitud="vacia",
            )
        ]
    )


def test_omitir_seccion_marca_completitud_y_motivo() -> None:
    """OmitirSeccion cambia completitud a 'omitida' y guarda motivo."""
    repo = DocumentoRepository()
    doc = _doc_con_seccion_vacia()
    repo.guardar(doc)

    uc = OmitirSeccion(repo)
    uc.ejecutar(doc.id, seccion_id="s.1", motivo="No aplica al modelo", actor="default")

    recargado = repo.obtener(doc.id)
    assert recargado is not None
    seccion = recargado.seccion_por_id("s.1")
    assert seccion is not None
    assert seccion.completitud == "omitida"
    assert seccion.motivo_omision == "No aplica al modelo"


def test_omitir_seccion_registra_audit_event() -> None:
    """OmitirSeccion genera evento 'seccion_omitida' con motivo en metadata."""
    repo = DocumentoRepository()
    doc = _doc_con_seccion_vacia()
    repo.guardar(doc)

    uc = OmitirSeccion(repo)
    uc.ejecutar(
        doc.id,
        seccion_id="s.1",
        motivo="Información no disponible",
        actor="default",
    )

    recargado = repo.obtener(doc.id)
    assert recargado is not None
    eventos = [e for e in recargado.audit_trail if e.tipo == "seccion_omitida"]
    assert len(eventos) == 1
    assert eventos[0].seccion_id == "s.1"
    assert eventos[0].metadata.get("motivo") == "Información no disponible"


def test_omitir_seccion_inexistente_levanta_error() -> None:
    repo = DocumentoRepository()
    doc = _doc_con_seccion_vacia()
    repo.guardar(doc)

    uc = OmitirSeccion(repo)
    with pytest.raises(ValueError, match="no existe"):
        uc.ejecutar(
            doc.id,
            seccion_id="seccion_inexistente",
            motivo="No aplica al modelo",
            actor="default",
        )


def test_omitir_documento_inexistente_levanta_error() -> None:
    repo = DocumentoRepository()
    uc = OmitirSeccion(repo)
    with pytest.raises(ValueError, match="no encontrado"):
        uc.ejecutar(
            uuid4(),
            seccion_id="s.1",
            motivo="No aplica al modelo",
            actor="default",
        )


def test_omitir_seccion_motivo_vacio_levanta_error() -> None:
    """El motivo no puede ser vacío — la omisión sin razón rompe auditabilidad."""
    repo = DocumentoRepository()
    doc = _doc_con_seccion_vacia()
    repo.guardar(doc)

    uc = OmitirSeccion(repo)
    with pytest.raises(ValueError, match="motivo"):
        uc.ejecutar(doc.id, seccion_id="s.1", motivo="", actor="default")


def test_motivos_omision_predefinidos_disponibles() -> None:
    """MOTIVOS_OMISION expone la lista de opciones predefinidas para la UI."""
    assert "No aplica al modelo" in MOTIVOS_OMISION
    assert "Información no disponible" in MOTIVOS_OMISION
    assert "Pendiente para versión futura" in MOTIVOS_OMISION
    assert len(MOTIVOS_OMISION) >= 3
