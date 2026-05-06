"""Tests de integración: flujo completo de importar un .docx real.

Usa los ejemplos reales de SMNYL en `SMNYL/Ejemplos actuales/` como fixtures.
Estos archivos están en el repo y NO se modifican.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from src.core.usecases import GapAnalyzer, ImportarDocumento
from src.docs.reader import DocxReader
from src.storage.repositories import DocumentoRepository
from src.storage.storage import FilesystemStorage

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EJEMPLOS_DIR = PROJECT_ROOT / "SMNYL" / "Ejemplos actuales"

EJEMPLO_VNB = EJEMPLOS_DIR / "M07.P07.S04.019.B Value of New Business.docx"
EJEMPLO_NIL = EJEMPLOS_DIR / "M07.P07.S03.006.D Modelos NIL (EV_VNB)_V3.0.docx"


@pytest.fixture
def storage(tmp_path: Path) -> FilesystemStorage:
    return FilesystemStorage(tmp_path)


@pytest.fixture
def use_case(storage: FilesystemStorage) -> ImportarDocumento:
    return ImportarDocumento(
        storage=storage,
        reader=DocxReader(),
        repo=DocumentoRepository(),
        analyzer=GapAnalyzer(),
    )


def test_importar_vnb_no_falla(use_case: ImportarDocumento) -> None:
    """El ejemplo VNB se importa sin errores."""
    assert EJEMPLO_VNB.exists(), f"Fixture no encontrada: {EJEMPLO_VNB}"
    with EJEMPLO_VNB.open("rb") as f:
        resultado = use_case.ejecutar(BytesIO(f.read()), EJEMPLO_VNB.name)
    assert resultado.documento is not None
    assert resultado.file_id.startswith("uploads/")


def test_importar_nil_no_falla(use_case: ImportarDocumento) -> None:
    """El ejemplo NIL se importa sin errores."""
    assert EJEMPLO_NIL.exists(), f"Fixture no encontrada: {EJEMPLO_NIL}"
    with EJEMPLO_NIL.open("rb") as f:
        resultado = use_case.ejecutar(BytesIO(f.read()), EJEMPLO_NIL.name)
    assert resultado.documento is not None


def test_documento_importado_tiene_todas_las_secciones_del_catalogo(
    use_case: ImportarDocumento,
) -> None:
    with EJEMPLO_VNB.open("rb") as f:
        resultado = use_case.ejecutar(BytesIO(f.read()), EJEMPLO_VNB.name)
    # Debe haber tantas secciones como en el catálogo (28+)
    assert len(resultado.documento.secciones) >= 28


def test_documento_importado_tiene_audit_trail_no_vacio(
    use_case: ImportarDocumento,
) -> None:
    with EJEMPLO_VNB.open("rb") as f:
        resultado = use_case.ejecutar(BytesIO(f.read()), EJEMPLO_VNB.name)
    assert len(resultado.documento.audit_trail) >= 1
    primer_evento = resultado.documento.audit_trail[0]
    assert primer_evento.tipo == "documento_importado"


def test_gap_analyzer_produce_brechas_para_documento_real(
    use_case: ImportarDocumento,
) -> None:
    """Los ejemplos SMNYL son procedimientos parciales, deben tener brechas críticas."""
    with EJEMPLO_VNB.open("rb") as f:
        resultado = use_case.ejecutar(BytesIO(f.read()), EJEMPLO_VNB.name)
    assert len(resultado.brechas) > 0
    # Al menos 1 brecha de alta severidad (es esperable: estos no son docs MRM completos)
    altas = [b for b in resultado.brechas if b.severidad == "alta"]
    assert len(altas) > 0


def test_documento_persiste_y_se_recupera(
    use_case: ImportarDocumento,
) -> None:
    with EJEMPLO_VNB.open("rb") as f:
        resultado = use_case.ejecutar(BytesIO(f.read()), EJEMPLO_VNB.name)
    repo = DocumentoRepository()
    recuperado = repo.obtener(resultado.documento.id)
    assert recuperado is not None
    assert recuperado.id == resultado.documento.id
    assert len(recuperado.secciones) == len(resultado.documento.secciones)
    repo.borrar(resultado.documento.id)


def test_reader_detecta_al_menos_3_secciones_en_vnb(
    use_case: ImportarDocumento,
) -> None:
    """Sanity check: el reader debe detectar al menos 3 secciones en VNB
    (Objetivo→Problem Statement, Alcance→Model Scope, Frecuencia→Monitoring)."""
    with EJEMPLO_VNB.open("rb") as f:
        resultado = use_case.ejecutar(BytesIO(f.read()), EJEMPLO_VNB.name)
    detectadas = [s for s in resultado.documento.secciones if s.tiene_contenido]
    assert len(detectadas) >= 3, (
        f"Reader detectó solo {len(detectadas)} secciones; se esperaban >= 3. "
        "Posible regresión en aliases del catálogo."
    )
