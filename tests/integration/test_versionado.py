"""Tests integration del versionado de documentos (C.2)."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models import Documento, MetadataModelo, Seccion
from src.core.models.version import calcular_hash
from src.core.usecases.crear_version import CrearVersion
from src.core.usecases.exportar_documento import (
    _incrustar_metadata_version,
    leer_metadata_version,
)
from src.storage.repositories import DocumentoRepository, VersionRepository


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


def _doc_simple() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Test", model_id="T-1"),
        secciones=[
            Seccion(
                id="1.1",
                nombre="A",
                numero="1.1",
                obligatoria=True,
                contenido="contenido inicial",
                completitud="completa",
            ),
        ],
    )


def test_crear_version_genera_v1_en_primera_corrida() -> None:
    doc_repo = DocumentoRepository()
    version_repo = VersionRepository()
    doc = _doc_simple()
    doc_repo.guardar(doc)

    uc = CrearVersion(doc_repo=doc_repo, version_repo=version_repo)
    resultado = uc.ejecutar(doc, comentario="primera versión")

    assert resultado.es_duplicado is False
    assert resultado.version.numero == 1
    assert resultado.version.comentario == "primera versión"
    # El hash excluye audit_trail / timestamps. Recalculamos de la misma forma.
    hash_esperado = calcular_hash(
        doc.model_dump_json(
            exclude={"audit_trail", "actualizado_en", "metricas_uso"},  # type: ignore[arg-type]
        )
    )
    assert resultado.version.hash_contenido == hash_esperado


def test_crear_version_incrementa_numero_en_corridas_consecutivas() -> None:
    doc_repo = DocumentoRepository()
    version_repo = VersionRepository()
    doc = _doc_simple()
    doc_repo.guardar(doc)

    uc = CrearVersion(doc_repo=doc_repo, version_repo=version_repo)
    uc.ejecutar(doc, comentario="v1")
    # Modificar el documento entre versiones para que el hash cambie
    seccion = doc.secciones[0]
    seccion.contenido = "contenido editado"
    doc_repo.guardar(doc)
    resultado_v2 = uc.ejecutar(doc, comentario="v2")

    assert resultado_v2.es_duplicado is False
    assert resultado_v2.version.numero == 2


def test_crear_version_es_idempotente_si_hash_no_cambio() -> None:
    """Si el documento NO cambió desde la última versión, no se duplica."""
    doc_repo = DocumentoRepository()
    version_repo = VersionRepository()
    doc = _doc_simple()
    doc_repo.guardar(doc)

    uc = CrearVersion(doc_repo=doc_repo, version_repo=version_repo)
    r1 = uc.ejecutar(doc, comentario="v1")
    r2 = uc.ejecutar(doc, comentario="reintento")

    assert r1.es_duplicado is False
    assert r2.es_duplicado is True
    assert r2.version.numero == r1.version.numero  # mismo número, no se duplicó
    # Solo hay 1 versión en la BD
    assert len(version_repo.listar_por_documento(doc.id)) == 1


def test_listar_por_documento_devuelve_en_orden_ascendente() -> None:
    doc_repo = DocumentoRepository()
    version_repo = VersionRepository()
    doc = _doc_simple()
    doc_repo.guardar(doc)
    uc = CrearVersion(doc_repo=doc_repo, version_repo=version_repo)

    for i in range(3):
        doc.secciones[0].contenido = f"edición {i}"
        doc_repo.guardar(doc)
        uc.ejecutar(doc, comentario=f"v{i + 1}")

    versiones = version_repo.listar_por_documento(doc.id)
    assert [v.numero for v in versiones] == [1, 2, 3]


def test_audit_trail_registra_evento_version_creada() -> None:
    doc_repo = DocumentoRepository()
    version_repo = VersionRepository()
    doc = _doc_simple()
    doc_repo.guardar(doc)

    CrearVersion(doc_repo=doc_repo, version_repo=version_repo).ejecutar(doc, comentario="x")

    recuperado = doc_repo.obtener(doc.id)
    assert recuperado is not None
    eventos = [e for e in recuperado.audit_trail if e.tipo == "version_creada"]
    assert len(eventos) == 1
    assert eventos[0].metadata.get("version_numero") == "1"


# --- Metadata en core_properties --------------------------------------------


def _docx_minimal_bytes() -> bytes:
    """Genera un .docx vacío en memoria para tests de metadata."""
    from io import BytesIO

    from docx import Document as DocxDocument

    d = DocxDocument()
    d.add_paragraph("contenido placeholder")
    buf = BytesIO()
    d.save(buf)
    return buf.getvalue()


def test_incrustar_y_leer_metadata_version_roundtrip() -> None:
    blob_inicial = _docx_minimal_bytes()
    from uuid import uuid4

    doc_id = uuid4()
    blob_actualizado = _incrustar_metadata_version(
        blob_inicial,
        documento_id=doc_id,
        version_numero=3,
        hash_contenido="abcd1234ef56",
    )
    meta = leer_metadata_version(blob_actualizado)
    assert meta["documento_id"] == str(doc_id)
    assert meta["version"] == "3"
    assert meta["hash"] == "abcd1234ef56"


def test_leer_metadata_devuelve_dict_vacio_si_no_es_documente() -> None:
    blob = _docx_minimal_bytes()
    meta = leer_metadata_version(blob)
    assert meta == {}


def test_incrustar_metadata_sin_version_es_aceptable() -> None:
    """Si no se crea versión, podemos incrustar solo `documento_id`."""
    from uuid import uuid4

    blob = _incrustar_metadata_version(
        _docx_minimal_bytes(),
        documento_id=uuid4(),
        version_numero=None,
        hash_contenido=None,
    )
    meta = leer_metadata_version(blob)
    assert "documento_id" in meta
    assert "version" not in meta
    assert "hash" not in meta
