"""Tests integration del use case ExportarDocumento."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import docx
import pytest

from src.core.models import Documento, MetadataModelo, Seccion
from src.core.usecases.exportar_documento import (
    ExportarDocumento,
    ResultadoExportacion,
)
from src.storage.repositories import DocumentoRepository

TEMPLATE_PATH = Path("src/docs/templates/model_development_smnyl_final.docx")


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


def _doc_seed() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(
            nombre_modelo="Modelo Test",
            model_id="M01.001",
            model_owner="Alberto",
            fae="Yael",
        ),
        secciones=[
            Seccion(
                id="2.1.model_uses",
                nombre="Model Uses",
                numero="2.1",
                obligatoria=True,
                contenido="Usado para test.",
                completitud="completa",
            ),
        ],
    )


def test_exportar_genera_blob_y_audit_event(tmp_path: Path) -> None:
    """ExportarDocumento devuelve bytes del .docx y registra evento 'exportado'."""
    repo = DocumentoRepository()
    doc = _doc_seed()
    repo.guardar(doc)

    uc = ExportarDocumento(repo, template_path=TEMPLATE_PATH)
    resultado: ResultadoExportacion = uc.ejecutar(doc.id, actor="default")

    # Bytes válidos
    assert isinstance(resultado.contenido, bytes)
    assert len(resultado.contenido) > 5000
    docx.Document(BytesIO(resultado.contenido))  # parseable

    # Nombre de archivo sugerido es razonable
    assert resultado.nombre_archivo.endswith(".docx")
    assert "Modelo" in resultado.nombre_archivo or "doc" in resultado.nombre_archivo.lower()

    # Audit event registrado
    recargado = repo.obtener(doc.id)
    assert recargado is not None
    eventos = [e for e in recargado.audit_trail if e.tipo == "exportado"]
    assert len(eventos) == 1
    assert eventos[0].actor == "default"


def test_exportar_documento_inexistente_levanta_error() -> None:
    repo = DocumentoRepository()
    uc = ExportarDocumento(repo, template_path=TEMPLATE_PATH)

    with pytest.raises(ValueError, match="no encontrado"):
        uc.ejecutar(uuid4(), actor="default")


def test_exportar_template_inexistente_levanta_error() -> None:
    repo = DocumentoRepository()
    doc = _doc_seed()
    repo.guardar(doc)

    uc = ExportarDocumento(repo, template_path=Path("ruta/que/no/existe.docx"))
    with pytest.raises(FileNotFoundError):
        uc.ejecutar(doc.id, actor="default")
