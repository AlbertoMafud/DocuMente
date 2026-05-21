"""Tests del AnchorReader factory + PdfAnchorReader.

Estrategia: para PDF generamos fixtures en runtime con `pypdf` (escribiendo
texto plano simulando contenido extraído). No hace falta `.pdf` real en disco.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from src.docs.reader import DocxReader
from src.docs.readers.anchor_reader import AnchorReader
from src.docs.readers.pdf_anchor_reader import PdfAnchorReader, _candidata_heading


def _crear_pdf_minimal(_texto: str, tmp_path: Path) -> Path:
    """Crea un PDF vacío (sin texto extraíble) para casos de PDF escaneado/empty.

    Construir un PDF con texto vía pypdf requiere reportlab — no lo agregamos
    como dependencia solo para tests. Para tests con texto real, mockeamos
    `leer_pdf` directamente.
    """
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    pdf_path = tmp_path / "empty.pdf"
    with pdf_path.open("wb") as f:
        writer.write(f)
    return pdf_path


def test_candidata_heading_detecta_numero_4_4() -> None:
    assert _candidata_heading("4.4 Key Assumptions") is True


def test_candidata_heading_detecta_mayusculas_cortas() -> None:
    assert _candidata_heading("KEY ASSUMPTIONS") is True


def test_candidata_heading_detecta_title_case() -> None:
    assert _candidata_heading("Theory And Methodology") is True


def test_candidata_heading_descarta_linea_larga() -> None:
    assert _candidata_heading("Este es un párrafo muy largo " * 10) is False


def test_candidata_heading_descarta_vacio() -> None:
    assert _candidata_heading("") is False
    assert _candidata_heading("   ") is False


def test_anchor_reader_factory_dispatcha_docx_a_docx_reader(tmp_path: Path) -> None:
    """Si la ruta es .docx, debería llamar a DocxReader. Lo verificamos
    creando un DocxReader stub que registra el llamado."""
    llamadas: list[Path] = []

    class StubDocxReader(DocxReader):
        def leer(self, ruta: Path, user_id: str = "default"):  # type: ignore[override]
            llamadas.append(ruta)
            return super().__init__() or None  # no se invoca el real

    # Usar mock más simple: parchar PdfAnchorReader y DocxReader
    fake_path = tmp_path / "doc.docx"
    fake_path.write_bytes(b"placeholder")

    class FakeDocxR:
        def leer(self, ruta: Path, user_id: str = "default"):
            llamadas.append(ruta)
            from src.core.models import Documento, MetadataModelo

            return Documento(metadata_modelo=MetadataModelo(nombre_modelo="X"))

    class FakePdfR:
        def leer(self, ruta: Path, user_id: str = "default"):
            raise AssertionError("PdfAnchorReader no debería ser llamado para .docx")

    reader = AnchorReader(docx_reader=FakeDocxR(), pdf_reader=FakePdfR())  # type: ignore[arg-type]
    doc = reader.leer(fake_path, user_id="alice")
    assert doc.metadata_modelo.nombre_modelo == "X"
    assert llamadas == [fake_path]


def test_anchor_reader_factory_dispatcha_pdf_a_pdf_anchor_reader(tmp_path: Path) -> None:
    llamadas: list[Path] = []
    fake_path = tmp_path / "doc.pdf"
    fake_path.write_bytes(b"placeholder")

    class FakeDocxR:
        def leer(self, ruta: Path, user_id: str = "default"):
            raise AssertionError("DocxReader no debería ser llamado para .pdf")

    class FakePdfR:
        def leer(self, ruta: Path, user_id: str = "default"):
            llamadas.append(ruta)
            from src.core.models import Documento, MetadataModelo

            return Documento(metadata_modelo=MetadataModelo(nombre_modelo="PDF"))

    reader = AnchorReader(docx_reader=FakeDocxR(), pdf_reader=FakePdfR())  # type: ignore[arg-type]
    doc = reader.leer(fake_path)
    assert doc.metadata_modelo.nombre_modelo == "PDF"
    assert llamadas == [fake_path]


def test_anchor_reader_factory_rechaza_extension_desconocida(tmp_path: Path) -> None:
    fake_path = tmp_path / "doc.txt"
    fake_path.write_bytes(b"placeholder")
    reader = AnchorReader()
    with pytest.raises(ValueError, match="no soportado"):
        reader.leer(fake_path)


def test_pdf_anchor_reader_pdf_vacio_devuelve_documento_sin_contenido(tmp_path: Path) -> None:
    """PDF sin texto (escaneado / blank) → documento esqueleto con audit event."""
    pdf_path = _crear_pdf_minimal("", tmp_path)
    reader = PdfAnchorReader()
    doc = reader.leer(pdf_path, user_id="alice")
    assert all(s.completitud == "vacia" for s in doc.secciones)
    eventos = [e for e in doc.audit_trail if e.tipo == "documento_importado"]
    assert len(eventos) == 1
    assert "pdf_sin_texto" in str(eventos[0].metadata.values())


def test_pdf_anchor_reader_texto_amorfo_guarda_como_fuente_contexto(
    tmp_path: Path, monkeypatch
) -> None:
    """Si extraemos texto pero no detectamos ninguna sección NYL, el contenido
    debe quedar en `fuentes_contexto` para que SugerenciasMultiFuente lo use."""
    texto_simulado = (
        "Lorem ipsum dolor sit amet, no hay headings reconocibles aquí.\n"
        "Solo un párrafo libre sin estructura NYL.\n"
    )
    monkeypatch.setattr(
        "src.docs.readers.pdf_anchor_reader.leer_pdf",
        lambda _f: texto_simulado,
    )
    pdf_path = _crear_pdf_minimal("", tmp_path)
    reader = PdfAnchorReader()
    doc = reader.leer(pdf_path)
    assert len(doc.fuentes_contexto) == 1
    assert doc.fuentes_contexto[0].tipo == "pdf"
    assert "Lorem ipsum" in doc.fuentes_contexto[0].texto_extraido


def test_pdf_anchor_reader_detecta_seccion_por_numero(tmp_path: Path, monkeypatch) -> None:
    """Si una línea tiene formato '4.4 Key Assumptions' y mapea al catálogo,
    el contenido subsiguiente debe ir a esa sección."""
    texto_simulado = (
        "4.4 Key Assumptions\n"
        "Estos son los supuestos principales del modelo.\n"
        "Supuesto adicional sobre mortalidad.\n"
    )
    monkeypatch.setattr(
        "src.docs.readers.pdf_anchor_reader.leer_pdf",
        lambda _f: texto_simulado,
    )
    pdf_path = _crear_pdf_minimal("", tmp_path)
    reader = PdfAnchorReader()
    doc = reader.leer(pdf_path)

    s44 = doc.seccion_por_id("4.4.assumptions")
    assert s44 is not None
    assert s44.contenido is not None
    assert "Estos son los supuestos principales" in s44.contenido
    # Audit event reporta secciones detectadas
    eventos = [e for e in doc.audit_trail if e.tipo == "documento_importado"]
    assert "1" in eventos[0].metadata.get("secciones_detectadas", "")


def test_pdf_anchor_reader_ignora_marcadores_de_pagina(tmp_path: Path, monkeypatch) -> None:
    """Las líneas '--- Página N ---' del extractor pypdf no son contenido."""
    texto_simulado = (
        "--- Página 1 ---\n"
        "4.4 Key Assumptions\n"
        "Contenido de la página 1\n"
        "--- Página 2 ---\n"
        "Contenido de la página 2\n"
    )
    monkeypatch.setattr(
        "src.docs.readers.pdf_anchor_reader.leer_pdf",
        lambda _f: texto_simulado,
    )
    pdf_path = _crear_pdf_minimal("", tmp_path)
    doc = PdfAnchorReader().leer(pdf_path)
    s44 = doc.seccion_por_id("4.4.assumptions")
    assert s44 is not None and s44.contenido is not None
    assert "Página 1" not in s44.contenido
    assert "Contenido de la página 1" in s44.contenido
    assert "Contenido de la página 2" in s44.contenido
