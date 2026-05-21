"""Tests del renderizador LaTeX → PNG (C.1)."""

from __future__ import annotations

import pytest

from src.docs.formulas.latex_to_image import (
    LatexRenderError,
    renderizar_latex_a_png,
)


def test_renderiza_formula_simple_devuelve_png_valido() -> None:
    """Fracción básica → PNG válido."""
    png = renderizar_latex_a_png(r"\frac{a}{b}")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 100  # razonable: no es una imagen 1x1


def test_renderiza_formula_con_simbolos_griegos() -> None:
    png = renderizar_latex_a_png(r"\alpha + \beta = \gamma")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_renderiza_formula_actuarial_realista() -> None:
    """Fórmula del valor presente actuarial."""
    expr = r"\bar{A}_x = \int_0^\infty e^{-\delta t} \, _tp_x \, \mu_{x+t} \, dt"
    png = renderizar_latex_a_png(expr)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_renderiza_acepta_delimitadores_dollar() -> None:
    """Si el usuario pasa `$...$`, también funciona."""
    png = renderizar_latex_a_png(r"$x^2 + y^2 = z^2$")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_source_vacio_levanta_latex_render_error() -> None:
    with pytest.raises(LatexRenderError, match="vac"):
        renderizar_latex_a_png("")
    with pytest.raises(LatexRenderError, match="vac"):
        renderizar_latex_a_png("   ")


def test_latex_invalido_levanta_latex_render_error() -> None:
    """Comando inexistente en MathText → LatexRenderError."""
    with pytest.raises(LatexRenderError):
        renderizar_latex_a_png(r"\comandoinventado{x}")


def test_dpi_mas_alto_aumenta_tamano_png() -> None:
    expr = r"\frac{1}{2}"
    png_low = renderizar_latex_a_png(expr, dpi=72)
    png_high = renderizar_latex_a_png(expr, dpi=300)
    assert len(png_high) > len(png_low)
