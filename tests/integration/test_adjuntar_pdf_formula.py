"""Tests de integración de AdjuntarPdfApendice y AdjuntarFormulaApendice (C.1)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import fitz  # PyMuPDF
import pytest

from src.core.models import Documento, EstadoEntrevista, MetadataModelo, Seccion
from src.core.usecases import (
    AdjuntarFormulaApendice,
    AdjuntarPdfApendice,
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


def _seed_doc() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Test"),
        secciones=[
            Seccion(
                id="4.2.theory",
                nombre="Theory",
                numero="4.2",
                obligatoria=True,
                intencion="x",
            ),
        ],
    )


def _pdf_de_3_paginas() -> bytes:
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 100), f"Página {i + 1}", fontsize=20)
    return doc.tobytes()


def test_adjuntar_pdf_crea_apendice_tipo_pdf(tmp_path: Path) -> None:
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]

    uc = AdjuntarPdfApendice(storage=storage, doc_repo=doc_repo, estado_repo=estado_repo)
    resultado = uc.ejecutar(
        documento=doc,
        seccion=seccion,
        archivo=BytesIO(_pdf_de_3_paginas()),
        nombre_original="formulas.pdf",
        titulo="Fórmulas Inversiones",
    )

    assert resultado.n_paginas == 3
    assert resultado.apendice.tipo == "pdf"
    assert resultado.apendice.titulo == "Fórmulas Inversiones"
    assert resultado.apendice.archivo_id_storage is not None

    # Persistencia
    recuperado = doc_repo.obtener(doc.id)
    assert recuperado is not None
    assert len(recuperado.apendices) == 1
    assert recuperado.apendices[0].tipo == "pdf"
    eventos = [e for e in recuperado.audit_trail if "PDF agregado" in e.descripcion]
    assert len(eventos) == 1
    assert eventos[0].metadata.get("n_paginas") == "3"


def test_adjuntar_pdf_inyecta_nota_a_estado_si_existe(tmp_path: Path) -> None:
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)
    seccion = doc.secciones[0]
    estado = EstadoEntrevista(documento_id=str(doc.id), seccion_id=seccion.id)
    estado_repo.guardar(estado)

    uc = AdjuntarPdfApendice(storage=storage, doc_repo=doc_repo, estado_repo=estado_repo)
    uc.ejecutar(
        documento=doc,
        seccion=seccion,
        archivo=BytesIO(_pdf_de_3_paginas()),
        nombre_original="formulas.pdf",
        titulo="Apéndice X",
    )

    estado_rec = estado_repo.obtener(str(doc.id), seccion.id)
    assert estado_rec is not None
    notas = [m for m in estado_rec.mensajes if m.rol == "system_note"]
    assert any("PDF" in n.contenido and "Apéndice X" in n.contenido for n in notas)


def test_adjuntar_pdf_corrupto_levanta_value_error(tmp_path: Path) -> None:
    storage = FilesystemStorage(tmp_path)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)

    uc = AdjuntarPdfApendice(storage=storage, doc_repo=doc_repo, estado_repo=estado_repo)
    with pytest.raises(ValueError, match="No se pudo leer el PDF"):
        uc.ejecutar(
            documento=doc,
            seccion=doc.secciones[0],
            archivo=BytesIO(b"no es un PDF"),
            nombre_original="corrupto.pdf",
            titulo="X",
        )


# --- Fórmulas LaTeX ----------------------------------------------------------


def test_adjuntar_formula_crea_apendice_tipo_formula() -> None:
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)

    uc = AdjuntarFormulaApendice(doc_repo=doc_repo, estado_repo=estado_repo)
    resultado = uc.ejecutar(
        documento=doc,
        seccion=doc.secciones[0],
        latex_source=r"\frac{a}{b}",
        titulo="Razón a/b",
    )

    assert resultado.apendice.tipo == "formula"
    assert resultado.apendice.latex_source == r"\frac{a}{b}"
    assert resultado.apendice.titulo == "Razón a/b"

    recuperado = doc_repo.obtener(doc.id)
    assert recuperado is not None
    assert len(recuperado.apendices) == 1
    assert recuperado.apendices[0].tipo == "formula"


def test_adjuntar_formula_latex_invalido_levanta_value_error() -> None:
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)

    uc = AdjuntarFormulaApendice(doc_repo=doc_repo, estado_repo=estado_repo)
    with pytest.raises(ValueError, match="LaTeX no válido"):
        uc.ejecutar(
            documento=doc,
            seccion=doc.secciones[0],
            latex_source=r"\comandoinventado{x}",
            titulo="X",
        )


def test_adjuntar_formula_vacia_levanta_value_error() -> None:
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    doc = _seed_doc()
    doc_repo.guardar(doc)

    uc = AdjuntarFormulaApendice(doc_repo=doc_repo, estado_repo=estado_repo)
    with pytest.raises(ValueError, match="no puede estar vacío"):
        uc.ejecutar(
            documento=doc,
            seccion=doc.secciones[0],
            latex_source="   ",
            titulo="X",
        )


def test_apendice_extendido_acepta_tipos_pdf_y_formula() -> None:
    """Sanity: el modelo Apendice acepta los nuevos literales."""
    from src.core.models import Apendice

    ap_pdf = Apendice(
        seccion_origen_id="x",
        titulo="t",
        tipo="pdf",
        archivo_id_storage="abc",
    )
    assert ap_pdf.tipo == "pdf"

    ap_formula = Apendice(
        seccion_origen_id="x",
        titulo="t",
        tipo="formula",
        latex_source=r"\alpha",
    )
    assert ap_formula.tipo == "formula"
    assert ap_formula.latex_source == r"\alpha"
