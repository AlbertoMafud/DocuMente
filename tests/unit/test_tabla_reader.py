"""Tests de tabla_reader.py — lectura de Excel/CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.docs.tabla_reader import leer_tabla


@pytest.fixture
def csv_temporal(tmp_path: Path) -> Path:
    df = pd.DataFrame(
        {
            "edad": [30, 35, 40, 45, 50],
            "qx": [0.001, 0.0015, 0.002, 0.003, 0.004],
            "tipo": ["male", "male", "female", "female", "male"],
        }
    )
    ruta = tmp_path / "mortalidad.csv"
    df.to_csv(ruta, index=False)
    return ruta


@pytest.fixture
def xlsx_temporal(tmp_path: Path) -> Path:
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    ruta = tmp_path / "datos.xlsx"
    df.to_excel(ruta, index=False, engine="openpyxl")
    return ruta


def test_leer_csv_devuelve_metadata_correcta(csv_temporal: Path) -> None:
    tabla = leer_tabla(csv_temporal)
    assert tabla.n_filas == 5
    assert tabla.n_columnas == 3
    assert "edad" in tabla.headers
    assert "qx" in tabla.headers


def test_leer_csv_genera_markdown_valido(csv_temporal: Path) -> None:
    tabla = leer_tabla(csv_temporal)
    md = tabla.tabla_completa_md
    assert "edad" in md
    assert "| --- |" in md  # separador de tabla markdown
    # 5 filas + header + separador = 7 líneas como mínimo
    assert md.count("\n") >= 6


def test_leer_csv_primeras_filas_limita_a_5(csv_temporal: Path) -> None:
    tabla = leer_tabla(csv_temporal)
    primeras = tabla.primeras_filas_md
    # header + separador + máximo 5 filas
    assert primeras.count("\n") <= 6


def test_leer_csv_resumen_estadistico_no_vacio(csv_temporal: Path) -> None:
    tabla = leer_tabla(csv_temporal)
    assert "5 filas" in tabla.resumen_estadistico
    assert "3 columnas" in tabla.resumen_estadistico
    assert "edad" in tabla.resumen_estadistico


def test_leer_xlsx_devuelve_metadata_correcta(xlsx_temporal: Path) -> None:
    tabla = leer_tabla(xlsx_temporal)
    assert tabla.n_filas == 3
    assert tabla.n_columnas == 2
    assert tabla.nombre_hoja is not None  # Excel siempre tiene nombre de hoja


def test_leer_formato_no_soportado_levanta_error(tmp_path: Path) -> None:
    ruta = tmp_path / "archivo.txt"
    ruta.write_text("foo")
    with pytest.raises(ValueError, match="no soportado"):
        leer_tabla(ruta)
