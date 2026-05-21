"""Renderizado de fórmulas matemáticas (LaTeX → imagen) para embeber en DOCX."""

from src.docs.formulas.latex_to_image import (
    LatexRenderError,
    renderizar_latex_a_png,
)

__all__ = ["LatexRenderError", "renderizar_latex_a_png"]
