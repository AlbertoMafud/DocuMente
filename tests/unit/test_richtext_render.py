"""Tests del parser markdown → estructuras de párrafo/run para Subdoc."""

from __future__ import annotations

from src.core.usecases.richtext_render import (
    InlineRun,
    ParrafoSpec,
    parsear_parrafos,
    parsear_runs_inline,
)

# ---- parsear_runs_inline ----


def test_runs_texto_plano() -> None:
    assert parsear_runs_inline("texto normal") == [InlineRun("texto normal")]


def test_runs_texto_con_bold_intermedio() -> None:
    runs = parsear_runs_inline("hola **mundo** adios")
    assert runs == [
        InlineRun("hola "),
        InlineRun("mundo", bold=True),
        InlineRun(" adios"),
    ]


def test_runs_solo_bold() -> None:
    runs = parsear_runs_inline("**todo bold**")
    assert runs == [InlineRun("todo bold", bold=True)]


def test_runs_con_italic() -> None:
    runs = parsear_runs_inline("texto *italica* normal")
    assert runs == [
        InlineRun("texto "),
        InlineRun("italica", italic=True),
        InlineRun(" normal"),
    ]


def test_runs_bold_y_italic_combinados() -> None:
    runs = parsear_runs_inline("**bold** y *italic*")
    assert runs == [
        InlineRun("bold", bold=True),
        InlineRun(" y "),
        InlineRun("italic", italic=True),
    ]


def test_runs_bold_no_se_confunde_con_italic_simple() -> None:
    """`**texto**` debe ser bold, no italic+italic."""
    assert parsear_runs_inline("**bold**") == [InlineRun("bold", bold=True)]


# ---- parsear_parrafos ----


def test_parrafos_uno_simple() -> None:
    pars = parsear_parrafos("Solo un párrafo.")
    assert len(pars) == 1
    assert pars[0].runs == [InlineRun("Solo un párrafo.")]
    assert pars[0].es_subtitulo is False
    assert pars[0].es_bullet is False


def test_parrafos_separados_por_doble_salto() -> None:
    pars = parsear_parrafos("Uno.\n\nDos.\n\nTres.")
    assert len(pars) == 3
    assert pars[0].runs[0].text == "Uno."
    assert pars[1].runs[0].text == "Dos."
    assert pars[2].runs[0].text == "Tres."


def test_parrafo_subtitulo_solo_bold() -> None:
    """Línea que es SOLO `**xxx**` se marca como subtítulo (alineación izq)."""
    pars = parsear_parrafos("**Algoritmo central**\n\nDescripción.")
    assert len(pars) == 2
    assert pars[0].es_subtitulo is True
    assert pars[0].runs == [InlineRun("Algoritmo central", bold=True)]
    assert pars[1].es_subtitulo is False


def test_parrafo_no_es_subtitulo_si_tiene_texto_extra() -> None:
    """`**bold**` con texto adicional NO es subtítulo, solo párrafo con runs."""
    pars = parsear_parrafos("**Punto** seguido de explicación.")
    assert len(pars) == 1
    assert pars[0].es_subtitulo is False


def test_parrafos_lista_bullets() -> None:
    pars = parsear_parrafos("- item uno\n- item dos\n- item tres")
    assert len(pars) == 3
    assert all(p.es_bullet for p in pars)
    assert pars[0].runs == [InlineRun("item uno")]
    assert pars[1].runs == [InlineRun("item dos")]


def test_parrafos_bullet_con_bold_inline() -> None:
    pars = parsear_parrafos("- **clave** del modelo")
    assert len(pars) == 1
    assert pars[0].es_bullet is True
    assert pars[0].runs == [
        InlineRun("clave", bold=True),
        InlineRun(" del modelo"),
    ]


def test_parrafos_input_vacio() -> None:
    assert parsear_parrafos("") == []
    assert parsear_parrafos("   ") == []


def test_parrafos_realista_key_assumptions() -> None:
    """Caso real de Alberto: subtítulos + bullets + prosa mezclados."""
    entrada = (
        "**Supuestos del modelo**\n\n"
        "El modelo incorpora dos categorías de supuestos externos.\n\n"
        "**Supuesto 1: Mix de venta**\n\n"
        "**Descripción**\n\n"
        "El mix de venta representa la distribución proporcional.\n\n"
        "**Estructura**\n\n"
        "El mix está desagregado por dos dimensiones:\n"
        "- Tipo de producto\n"
        "- Canal de distribución"
    )
    pars = parsear_parrafos(entrada)
    # Subtítulos detectados
    subs = [p for p in pars if p.es_subtitulo]
    assert len(subs) >= 3  # Supuestos del modelo, Supuesto 1, Descripción, Estructura
    # Bullets detectados
    bullets = [p for p in pars if p.es_bullet]
    assert len(bullets) == 2
    assert bullets[0].runs[0].text == "Tipo de producto"
    assert bullets[1].runs[0].text == "Canal de distribución"


def test_parrafos_descarta_lineas_solo_whitespace() -> None:
    pars = parsear_parrafos("Uno.\n\n   \n\nDos.")
    assert len(pars) == 2


def test_dataclass_inline_run_default_sin_formato() -> None:
    r = InlineRun("hola")
    assert r.bold is False
    assert r.italic is False


def test_dataclass_parrafo_spec_default() -> None:
    p = ParrafoSpec(runs=[InlineRun("x")])
    assert p.es_subtitulo is False
    assert p.es_bullet is False
