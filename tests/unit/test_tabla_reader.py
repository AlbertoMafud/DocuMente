"""Tests de tabla_reader.py — lectura de Excel/CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.docs.tabla_reader import (
    leer_excel,
    leer_excel_todas_hojas,
    leer_tabla,
    leer_tabla_todas,
)


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


# --- B.3 Multi-hoja Excel -----------------------------------------------------


@pytest.fixture
def xlsx_3_hojas(tmp_path: Path) -> Path:
    """Excel con 3 hojas con datos + 1 hoja vacía (que debe omitirse)."""
    ruta = tmp_path / "supuestos_modelo.xlsx"
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
        # Hoja sin datos — un solo header sin filas
        pd.DataFrame(columns=["col_a", "col_b"]).to_excel(
            xw, sheet_name="Plantilla_Vacia", index=False
        )
    return ruta


def test_leer_excel_todas_hojas_devuelve_una_tabla_por_hoja_con_datos(
    xlsx_3_hojas: Path,
) -> None:
    tablas = leer_excel_todas_hojas(xlsx_3_hojas)
    nombres = [t.nombre_hoja for t in tablas]
    # 3 hojas con datos; la 4ta (vacía) se omite
    assert len(tablas) == 3
    assert "Mortalidad" in nombres
    assert "Lapses" in nombres
    assert "Inversion" in nombres
    assert "Plantilla_Vacia" not in nombres


def test_leer_excel_todas_hojas_preserva_metadata_de_cada_hoja(
    xlsx_3_hojas: Path,
) -> None:
    tablas = leer_excel_todas_hojas(xlsx_3_hojas)
    por_nombre = {t.nombre_hoja: t for t in tablas}
    assert por_nombre["Mortalidad"].n_filas == 2
    assert "edad" in por_nombre["Mortalidad"].headers
    assert por_nombre["Lapses"].n_filas == 3
    assert "lapse" in por_nombre["Lapses"].headers


def test_leer_tabla_todas_para_csv_devuelve_lista_de_uno(csv_temporal: Path) -> None:
    tablas = leer_tabla_todas(csv_temporal)
    assert len(tablas) == 1
    assert tablas[0].nombre_hoja is None


def test_leer_tabla_todas_para_xlsx_devuelve_todas_las_hojas(
    xlsx_3_hojas: Path,
) -> None:
    tablas = leer_tabla_todas(xlsx_3_hojas)
    assert len(tablas) == 3


def test_leer_excel_con_indice_int_recupera_nombre_real_de_hoja(
    xlsx_3_hojas: Path,
) -> None:
    """`leer_excel(ruta, hoja=1)` debe poner `nombre_hoja='Lapses'`, no 'Hoja2'."""
    tabla = leer_excel(xlsx_3_hojas, hoja=1)
    assert tabla.nombre_hoja == "Lapses"
