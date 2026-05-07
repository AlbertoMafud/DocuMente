"""Tests del separador de bloques markdown (prosa vs tabla)."""

from __future__ import annotations

from src.core.usecases.markdown_blocks import (
    BloqueProsa,
    BloqueTabla,
    font_size_para_tabla,
    separar_bloques,
)


def test_solo_prosa() -> None:
    bloques = separar_bloques("Solo texto.\n\nOtro párrafo.")
    assert len(bloques) == 1
    assert isinstance(bloques[0], BloqueProsa)


def test_solo_tabla() -> None:
    entrada = "| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    bloques = separar_bloques(entrada)
    assert len(bloques) == 1
    assert isinstance(bloques[0], BloqueTabla)
    assert bloques[0].headers == ["a", "b"]
    assert bloques[0].rows == [["1", "2"], ["3", "4"]]


def test_prosa_seguida_de_tabla_seguida_de_prosa() -> None:
    entrada = "Texto antes.\n\n| col1 | col2 |\n|---|---|\n| 1 | 2 |\n\nTexto después."
    bloques = separar_bloques(entrada)
    assert len(bloques) == 3
    assert isinstance(bloques[0], BloqueProsa)
    assert "Texto antes" in bloques[0].texto
    assert isinstance(bloques[1], BloqueTabla)
    assert isinstance(bloques[2], BloqueProsa)
    assert "Texto después" in bloques[2].texto


def test_dos_tablas_seguidas() -> None:
    entrada = "| a | b |\n|---|---|\n| 1 | 2 |\n\n| x | y |\n|---|---|\n| 3 | 4 |"
    bloques = separar_bloques(entrada)
    assert len(bloques) == 2
    assert all(isinstance(b, BloqueTabla) for b in bloques)


def test_tabla_descarta_filas_con_pipes_pero_sin_separador() -> None:
    """Para que una tabla cuente, debe tener línea de separador `|---|---|`."""
    entrada = "| no es tabla porque falta separador |"
    bloques = separar_bloques(entrada)
    assert len(bloques) == 1
    assert isinstance(bloques[0], BloqueProsa)


def test_caso_realista_apendice_excel() -> None:
    """Caso real: contenido_md de un apéndice creado por upload de Excel."""
    entrada = (
        "**Archivo origen:** `factores.xlsx` · Hoja: `Hoja1`\n\n"
        "**Dimensiones:** 38 filas × 2 columnas\n\n"
        "| Producto | Factor |\n"
        "|---|---|\n"
        "| 1.0 | 0.158 |\n"
        "| 2.0 | 0.383 |\n"
        "| 3.0 | 0.450 |"
    )
    bloques = separar_bloques(entrada)
    # Debe haber prosa (metadatos) + tabla (datos)
    tablas = [b for b in bloques if isinstance(b, BloqueTabla)]
    prosas = [b for b in bloques if isinstance(b, BloqueProsa)]
    assert len(tablas) == 1
    assert tablas[0].headers == ["Producto", "Factor"]
    assert len(tablas[0].rows) == 3
    assert tablas[0].rows[0] == ["1.0", "0.158"]
    assert len(prosas) >= 1


def test_input_vacio() -> None:
    assert separar_bloques("") == []


# Heurística de font size


def test_font_size_tabla_pequena() -> None:
    """Tablas con pocas filas usan tamaño normal."""
    assert font_size_para_tabla(n_filas=5, n_columnas=2) == 10
    assert font_size_para_tabla(n_filas=15, n_columnas=2) == 10


def test_font_size_tabla_mediana() -> None:
    """Tablas medianas reducen un poco."""
    assert font_size_para_tabla(n_filas=20, n_columnas=2) == 9
    assert font_size_para_tabla(n_filas=30, n_columnas=2) == 9


def test_font_size_tabla_grande() -> None:
    """Tablas grandes reducen más."""
    assert font_size_para_tabla(n_filas=50, n_columnas=2) == 8


def test_font_size_tabla_muy_grande() -> None:
    """Tablas muy grandes llegan al mínimo legible."""
    assert font_size_para_tabla(n_filas=100, n_columnas=2) == 7


def test_font_size_muchas_columnas_reduce_mas() -> None:
    """Si hay muchas columnas, también reduce."""
    assert font_size_para_tabla(n_filas=10, n_columnas=8) == 8
