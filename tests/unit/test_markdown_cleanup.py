"""Tests del cleanup de markdown para inserción en plantilla DOCX."""

from __future__ import annotations

from src.core.usecases.markdown_cleanup import limpiar_markdown


def test_quita_asteriscos_de_negritas() -> None:
    assert limpiar_markdown("**Overrun de gasto** es importante") == (
        "Overrun de gasto es importante"
    )


def test_quita_asteriscos_de_cursiva_simple() -> None:
    assert limpiar_markdown("Esto es *importante* y único") == ("Esto es importante y único")


def test_quita_hashes_de_subtitulos() -> None:
    entrada = "## Supuestos del modelo\n\nContenido del párrafo."
    salida = limpiar_markdown(entrada)
    assert "##" not in salida
    assert "Supuestos del modelo" in salida
    assert "Contenido del párrafo" in salida


def test_quita_hashes_de_sub_sub_titulos() -> None:
    entrada = "### Supuesto 1: Mix de venta\nDescripción."
    salida = limpiar_markdown(entrada)
    assert "###" not in salida
    assert "Supuesto 1: Mix de venta" in salida


def test_elimina_separadores_horizontales() -> None:
    entrada = "Párrafo uno.\n\n---\n\nPárrafo dos."
    salida = limpiar_markdown(entrada)
    assert "---" not in salida
    assert "Párrafo uno" in salida
    assert "Párrafo dos" in salida


def test_normaliza_listas_a_guion_simple() -> None:
    entrada = "- Item uno\n* Item dos\n+ Item tres"
    salida = limpiar_markdown(entrada)
    assert "- Item uno" in salida
    assert "- Item dos" in salida
    assert "- Item tres" in salida
    assert "*" not in salida


def test_convierte_tabla_markdown_simple_a_lineas() -> None:
    """Tabla pipe-separated se convierte a líneas legibles, no se queda con '|...|'."""
    entrada = (
        "| # | Documento | Ubicación |\n"
        "|---|---|---|\n"
        "| 1 | Estudio Gastos | /Sofia/Estudio.xlsx |\n"
        "| 2 | Memo de precios | /Sofia/memo.docx |"
    )
    salida = limpiar_markdown(entrada)
    assert "|---|" not in salida
    # No debe quedar la sintaxis de pipes literales
    assert "| 1 |" not in salida
    # Pero sí debe preservar los datos
    assert "Estudio Gastos" in salida
    assert "Memo de precios" in salida


def test_preserva_texto_sin_markdown() -> None:
    entrada = "Este es un párrafo normal sin formato."
    assert limpiar_markdown(entrada) == entrada


def test_preserva_saltos_de_linea_entre_parrafos() -> None:
    entrada = "Párrafo uno.\n\nPárrafo dos.\n\nPárrafo tres."
    salida = limpiar_markdown(entrada)
    # Bloques separados deben quedar separados (al menos 1 línea en blanco)
    assert "Párrafo uno." in salida
    assert "Párrafo dos." in salida
    assert "Párrafo tres." in salida


def test_input_vacio() -> None:
    assert limpiar_markdown("") == ""


def test_input_none_safe() -> None:
    """No debe romper si el contenido viene como cadena vacía después de strip."""
    assert limpiar_markdown("   ") == ""


def test_combinacion_realista() -> None:
    """Caso real que reportó Alberto: Key Assumptions con todo el zoo markdown."""
    entrada = (
        "## Supuestos del modelo\n\n"
        "El modelo incorpora dos categorías de supuestos externos.\n\n"
        "---\n\n"
        "### Supuesto 1: Mix de venta\n\n"
        "**Descripción**\n"
        "El mix de venta representa la distribución proporcional.\n\n"
        "**Fuente y responsable**\n"
        "El supuesto es provisto por el área de Plan de Negocios."
    )
    salida = limpiar_markdown(entrada)
    assert "##" not in salida
    assert "**" not in salida
    assert "---" not in salida
    assert "Supuestos del modelo" in salida
    assert "Supuesto 1: Mix de venta" in salida
    assert "Descripción" in salida
    assert "Fuente y responsable" in salida
