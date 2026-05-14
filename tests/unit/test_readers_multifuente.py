"""Tests de los readers de fuentes adicionales (PDF, XLSX, TXT, DOCX simple)."""

from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook

from src.docs.readers import EXTENSIONES_SOPORTADAS, extraer_texto
from src.docs.readers.txt_reader import leer_txt
from src.docs.readers.xlsx_reader import leer_xlsx


def test_leer_txt_utf8() -> None:
    archivo = BytesIO("Texto con acentos áéíóú y eñe".encode())
    assert leer_txt(archivo) == "Texto con acentos áéíóú y eñe"


def test_leer_txt_latin1_fallback() -> None:
    archivo = BytesIO("Texto con eñe".encode("latin-1"))
    assert "eñe" in leer_txt(archivo)


def test_leer_xlsx_serializa_hojas() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.append(["Producto", "Factor"])
    ws.append(["A", 0.5])
    ws.append(["B", 0.3])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    texto = leer_xlsx(buf)
    assert "Hoja: Datos" in texto
    assert "Producto" in texto
    assert "Factor" in texto
    assert "A" in texto
    assert "0.5" in texto


def test_extraer_texto_por_extension_txt() -> None:
    tipo, texto = extraer_texto(BytesIO(b"hola mundo"), "notas.txt")
    assert tipo == "txt"
    assert "hola mundo" in texto


def test_extraer_texto_por_extension_xlsx() -> None:
    wb = Workbook()
    wb.active.append(["A", "B"])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    tipo, _ = extraer_texto(buf, "datos.xlsx")
    assert tipo == "xlsx"


def test_extraer_texto_extension_no_soportada_levanta_value_error() -> None:
    with pytest.raises(ValueError, match="no soportado"):
        extraer_texto(BytesIO(b"datos"), "archivo.xyz")


def test_extraer_texto_acepta_bytes_crudos() -> None:
    tipo, texto = extraer_texto(b"contenido", "notas.txt")
    assert tipo == "txt"
    assert "contenido" in texto


def test_extensiones_soportadas_incluye_todas() -> None:
    assert "pdf" in EXTENSIONES_SOPORTADAS
    assert "xlsx" in EXTENSIONES_SOPORTADAS
    assert "txt" in EXTENSIONES_SOPORTADAS
    assert "docx" in EXTENSIONES_SOPORTADAS
