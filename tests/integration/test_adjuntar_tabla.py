"""Tests de integración del use case AdjuntarTablaApendice."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest

from src.core.models import Documento, EstadoEntrevista, MetadataModelo, Seccion
from src.core.usecases import (
    SECCIONES_DATA_HEAVY,
    AdjuntarTablaApendice,
    es_seccion_data_heavy,
)
from src.storage.repositories import (
    DocumentoRepository,
    EstadoEntrevistaRepository,
)
from src.storage.storage import FilesystemStorage


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


@pytest.fixture
def csv_excel_data(tmp_path: Path) -> bytes:
    df = pd.DataFrame({"edad": [30, 35, 40], "qx": [0.001, 0.002, 0.003]})
    ruta = tmp_path / "tabla.csv"
    df.to_csv(ruta, index=False)
    return ruta.read_bytes()


def _seed_doc() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Test"),
        secciones=[
            Seccion(
                id="4.4.assumptions",
                nombre="Key Assumptions",
                numero="4.4",
                obligatoria=True,
                intencion="x",
            ),
        ],
    )


def test_seccion_4_4_es_data_heavy() -> None:
    assert es_seccion_data_heavy("4.4.assumptions") is True
    assert es_seccion_data_heavy("1.3.problem_statement") is False


def test_secciones_data_heavy_incluye_supuestos_y_data() -> None:
    assert "4.4.assumptions" in SECCIONES_DATA_HEAVY
    assert "5.1.raw_data" in SECCIONES_DATA_HEAVY
    assert "5.2.upstream" in SECCIONES_DATA_HEAVY


def test_adjuntar_csv_crea_apendice_y_persiste(tmp_path: Path, csv_excel_data: bytes) -> None:
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    uc = AdjuntarTablaApendice(storage, doc_repo, estado_repo)

    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]

    resultado = uc.ejecutar(
        documento=doc,
        seccion=seccion,
        archivo=BytesIO(csv_excel_data),
        nombre_original="mortalidad.csv",
        titulo="Tabla de mortalidad SOA 2017",
    )

    assert resultado.apendice.titulo == "Tabla de mortalidad SOA 2017"
    assert resultado.apendice.tipo == "tabla"
    assert resultado.tabla.n_filas == 3
    assert resultado.tabla.n_columnas == 2

    # Persistencia: doc tiene el apéndice
    doc_recuperado = doc_repo.obtener(doc.id)
    assert doc_recuperado is not None
    assert len(doc_recuperado.apendices) == 1
    assert doc_recuperado.apendices[0].titulo == "Tabla de mortalidad SOA 2017"

    # Audit trail registró el evento
    assert any("Apéndice agregado" in e.descripcion for e in doc_recuperado.audit_trail)


def test_adjuntar_inyecta_system_note_si_hay_entrevista_activa(
    tmp_path: Path, csv_excel_data: bytes
) -> None:
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    uc = AdjuntarTablaApendice(storage, doc_repo, estado_repo)

    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]

    estado = EstadoEntrevista(documento_id=str(doc.id), seccion_id=seccion.id)
    estado_repo.guardar(estado)

    uc.ejecutar(
        documento=doc,
        seccion=seccion,
        archivo=BytesIO(csv_excel_data),
        nombre_original="mortalidad.csv",
        titulo="Tabla mortalidad",
    )

    estado_recuperado = estado_repo.obtener(str(doc.id), seccion.id)
    assert estado_recuperado is not None
    notas = [m for m in estado_recuperado.mensajes if m.rol == "system_note"]
    assert len(notas) == 1
    assert "Tabla mortalidad" in notas[0].contenido
    assert "Apéndice" in notas[0].contenido
