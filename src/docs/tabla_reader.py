"""Lectores de Excel/CSV → tabla markdown + resumen estructurado.

Cuando el usuario sube un .xlsx o .csv durante una entrevista de sección
data-heavy (4.4 Assumptions, 5.1 Raw Data, 5.2 Upstream Models), DocuMente
lo lee, lo convierte a markdown para incrustarlo en un apéndice, y produce
un resumen corto que sí entra al contexto de Claude (no la tabla completa).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class TablaLeida:
    """Resultado de leer una tabla Excel o CSV."""

    nombre_archivo: str
    nombre_hoja: str | None
    """Para Excel; None si es CSV."""
    n_filas: int
    n_columnas: int
    headers: list[str]
    primeras_filas_md: str
    """Primeras 5 filas renderizadas como tabla markdown (sirve de muestra para el prompt)."""
    tabla_completa_md: str
    """Tabla completa en markdown — para incrustar en el apéndice del DOCX."""
    resumen_estadistico: str
    """Resumen corto en texto (count, dtypes, missing) para inyectar al prompt sin volar tokens."""


def _df_a_markdown_safe(df: pd.DataFrame, max_rows: int | None = None) -> str:
    """Convierte un DataFrame a tabla markdown sin requerir `tabulate`."""
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_(tabla vacía)_"
    headers = list(df.columns.astype(str))
    lineas = ["| " + " | ".join(headers) + " |"]
    lineas.append("| " + " | ".join("---" for _ in headers) + " |")
    for _, fila in df.iterrows():
        celdas = ["" if pd.isna(v) else str(v).replace("|", "\\|") for v in fila.tolist()]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def _resumen_de_df(df: pd.DataFrame) -> str:
    """Resumen corto del DataFrame para incluir en el contexto del prompt."""
    n_filas, n_cols = df.shape
    info_columnas: list[str] = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_nulos = int(df[col].isna().sum())
        info_columnas.append(f"  - `{col}` ({dtype}, {n_nulos} nulos)")
    return f"Tabla: {n_filas} filas × {n_cols} columnas\nColumnas:\n" + "\n".join(info_columnas)


def leer_csv(ruta: Path) -> TablaLeida:
    df = pd.read_csv(ruta)
    return TablaLeida(
        nombre_archivo=ruta.name,
        nombre_hoja=None,
        n_filas=len(df),
        n_columnas=len(df.columns),
        headers=[str(c) for c in df.columns],
        primeras_filas_md=_df_a_markdown_safe(df, max_rows=5),
        tabla_completa_md=_df_a_markdown_safe(df),
        resumen_estadistico=_resumen_de_df(df),
    )


def leer_excel(ruta: Path, hoja: str | int = 0) -> TablaLeida:
    df = pd.read_excel(ruta, sheet_name=hoja, engine="openpyxl")
    if isinstance(hoja, str):
        nombre_hoja = hoja
    else:
        # Si pasó int, recuperamos el nombre real desde openpyxl para no
        # mostrar "Hoja1" en el apéndice cuando la hoja se llama "Supuestos".
        try:
            with pd.ExcelFile(ruta, engine="openpyxl") as xf:
                nombres = list(xf.sheet_names)
            nombre_hoja = nombres[hoja] if 0 <= hoja < len(nombres) else f"Hoja{hoja + 1}"
        except Exception:
            nombre_hoja = f"Hoja{hoja + 1}"
    return TablaLeida(
        nombre_archivo=ruta.name,
        nombre_hoja=nombre_hoja,
        n_filas=len(df),
        n_columnas=len(df.columns),
        headers=[str(c) for c in df.columns],
        primeras_filas_md=_df_a_markdown_safe(df, max_rows=5),
        tabla_completa_md=_df_a_markdown_safe(df),
        resumen_estadistico=_resumen_de_df(df),
    )


def leer_excel_todas_hojas(ruta: Path) -> list[TablaLeida]:
    """Lee TODAS las hojas de un Excel, una `TablaLeida` por hoja.

    Hojas completamente vacías (sin filas con datos) se omiten para no
    crear apéndices basura. Devuelve [] si todas las hojas están vacías.
    """
    with pd.ExcelFile(ruta, engine="openpyxl") as xf:
        nombres = list(xf.sheet_names)

    resultados: list[TablaLeida] = []
    for nombre in nombres:
        try:
            df = pd.read_excel(ruta, sheet_name=nombre, engine="openpyxl")
        except Exception:
            # Hoja con error de parseo (ej. solo header sin datos) — saltar
            continue
        if df.empty:
            continue
        resultados.append(
            TablaLeida(
                nombre_archivo=ruta.name,
                nombre_hoja=nombre,
                n_filas=len(df),
                n_columnas=len(df.columns),
                headers=[str(c) for c in df.columns],
                primeras_filas_md=_df_a_markdown_safe(df, max_rows=5),
                tabla_completa_md=_df_a_markdown_safe(df),
                resumen_estadistico=_resumen_de_df(df),
            )
        )
    return resultados


def leer_tabla(ruta: Path) -> TablaLeida:
    """Lee un archivo .xlsx, .xls o .csv (solo primera hoja para Excel).

    Para Excel multi-hoja, prefiere `leer_tabla_todas(ruta)`.
    """
    extension = ruta.suffix.lower()
    if extension in (".xlsx", ".xls"):
        return leer_excel(ruta)
    if extension == ".csv":
        return leer_csv(ruta)
    raise ValueError(f"Formato no soportado: {extension}. Usar .xlsx, .xls o .csv.")


def leer_tabla_todas(ruta: Path) -> list[TablaLeida]:
    """Lee TODAS las hojas (Excel) o la tabla única (CSV) y devuelve lista.

    Caso de uso: el usuario sube un Excel con varias hojas y queremos crear
    un apéndice por hoja (B.3). Para CSV devuelve lista de 1 elemento.
    """
    extension = ruta.suffix.lower()
    if extension in (".xlsx", ".xls"):
        return leer_excel_todas_hojas(ruta)
    if extension == ".csv":
        return [leer_csv(ruta)]
    raise ValueError(f"Formato no soportado: {extension}. Usar .xlsx, .xls o .csv.")
