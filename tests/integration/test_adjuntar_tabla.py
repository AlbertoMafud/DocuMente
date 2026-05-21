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


# --- B.3 Multi-hoja Excel + apéndices en todas las secciones ---------------


@pytest.fixture
def xlsx_3_hojas(tmp_path: Path) -> bytes:
    """Excel con 3 hojas con datos."""
    ruta = tmp_path / "supuestos.xlsx"
    with pd.ExcelWriter(ruta, engine="openpyxl") as xw:
        pd.DataFrame({"edad": [30, 40], "qx": [0.001, 0.002]}).to_excel(
            xw, sheet_name="Mortalidad", index=False
        )
        pd.DataFrame({"año": [1, 2, 3], "lapse": [0.08, 0.06, 0.05]}).to_excel(
            xw, sheet_name="Lapses", index=False
        )
        pd.DataFrame({"escenario": ["base"], "tasa": [0.075]}).to_excel(
            xw, sheet_name="Inversion", index=False
        )
    return ruta.read_bytes()


def test_ejecutar_multihoja_crea_un_apendice_por_hoja(tmp_path: Path, xlsx_3_hojas: bytes) -> None:
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]

    uc = AdjuntarTablaApendice(storage=storage, doc_repo=doc_repo, estado_repo=estado_repo)
    resultados = uc.ejecutar_multihoja(
        documento=doc,
        seccion=seccion,
        archivo=BytesIO(xlsx_3_hojas),
        nombre_original="supuestos.xlsx",
        titulo_base="Supuestos del modelo",
    )

    assert len(resultados) == 3
    titulos = sorted(r.apendice.titulo for r in resultados)
    assert titulos == [
        "Supuestos del modelo — Inversion",
        "Supuestos del modelo — Lapses",
        "Supuestos del modelo — Mortalidad",
    ]
    assert len(doc.apendices) == 3
    # Todos vinculados a la misma sección y al mismo archivo origen
    for ap in doc.apendices:
        assert ap.seccion_origen_id == seccion.id
        assert ap.nombre_archivo_original == "supuestos.xlsx"


def test_ejecutar_multihoja_csv_crea_un_solo_apendice_sin_sufijo(
    tmp_path: Path, csv_excel_data: bytes
) -> None:
    """Para CSV solo hay una 'hoja' → no se agrega sufijo al título."""
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]

    uc = AdjuntarTablaApendice(storage=storage, doc_repo=doc_repo, estado_repo=estado_repo)
    resultados = uc.ejecutar_multihoja(
        documento=doc,
        seccion=seccion,
        archivo=BytesIO(csv_excel_data),
        nombre_original="datos.csv",
        titulo_base="Tabla mortalidad",
    )

    assert len(resultados) == 1
    assert resultados[0].apendice.titulo == "Tabla mortalidad"


def test_ejecutar_multihoja_inyecta_nota_consolidada_a_estado(
    tmp_path: Path, xlsx_3_hojas: bytes
) -> None:
    """Cuando hay >1 hoja, la nota al LLM resume todos los apéndices."""
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]

    estado = EstadoEntrevista(documento_id=str(doc.id), seccion_id=seccion.id)
    estado_repo.guardar(estado)

    uc = AdjuntarTablaApendice(storage=storage, doc_repo=doc_repo, estado_repo=estado_repo)
    uc.ejecutar_multihoja(
        documento=doc,
        seccion=seccion,
        archivo=BytesIO(xlsx_3_hojas),
        nombre_original="supuestos.xlsx",
        titulo_base="Supuestos",
    )

    estado_recuperado = estado_repo.obtener(str(doc.id), seccion.id)
    assert estado_recuperado is not None
    notas = [m for m in estado_recuperado.mensajes if m.rol == "system_note"]
    assert len(notas) == 1
    nota = notas[0].contenido
    assert "3 hojas" in nota
    assert "Mortalidad" in nota
    assert "Lapses" in nota
    assert "Inversion" in nota


def test_ejecutar_multihoja_excel_sin_hojas_validas_falla_con_value_error(
    tmp_path: Path,
) -> None:
    """Excel sin filas de datos → ValueError (no crea apéndices basura)."""
    # Crear un xlsx con una sola hoja vacía
    ruta = tmp_path / "vacio.xlsx"
    pd.DataFrame(columns=["a", "b"]).to_excel(ruta, index=False, engine="openpyxl")
    xlsx_bytes = ruta.read_bytes()

    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]

    uc = AdjuntarTablaApendice(storage=storage, doc_repo=doc_repo, estado_repo=estado_repo)
    with pytest.raises(ValueError, match="hojas con datos"):
        uc.ejecutar_multihoja(
            documento=doc,
            seccion=seccion,
            archivo=BytesIO(xlsx_bytes),
            nombre_original="vacio.xlsx",
            titulo_base="X",
        )
