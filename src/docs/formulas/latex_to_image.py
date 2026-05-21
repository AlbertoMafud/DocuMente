"""Renderiza una fórmula LaTeX a imagen PNG vía matplotlib MathText.

MathText es el subset de LaTeX nativo de matplotlib — no requiere
instalación externa de TeX/LaTeX en el sistema. Cubre el 95% de los
casos actuariales: fracciones, integrales, sumatorias, productorias,
matrices, símbolos griegos, índices/exponentes, paréntesis grandes.

Casos NO cubiertos por MathText (raros en docs actuariales):
- `\\begin{align}`, `\\begin{equation*}` (entornos avanzados).
- Comandos personalizados con `\\newcommand`.
- Paquetes externos como `physics`, `siunitx`.

Si el LaTeX recibido falla, `renderizar_latex_a_png` levanta
`LatexRenderError` con la causa — el caller decide qué hacer
(reportar al usuario o caer a un placeholder).
"""

from __future__ import annotations

import io

import matplotlib

# Backend no-interactivo (importante para entornos sin display como EC2).
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class LatexRenderError(ValueError):
    """LaTeX inválido o no soportado por MathText."""


_DPI_DEFAULT = 250
_FONTSIZE_DEFAULT = 16


def renderizar_latex_a_png(
    latex_source: str,
    *,
    dpi: int = _DPI_DEFAULT,
    fontsize: int = _FONTSIZE_DEFAULT,
    color: str = "#0a3c53",  # SMNYL Steel
) -> bytes:
    """Renderiza la fórmula a PNG con fondo transparente.

    Args:
        latex_source: source LaTeX SIN los delimitadores `$...$` o `\\[...\\]`.
            Ejemplo: `r"\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}"`.
        dpi: resolución del PNG (default 250 = nítido en Word a 100% zoom).
        fontsize: tamaño de fuente (default 16 = legible inline).
        color: color del texto en hex (default Steel SMNYL).

    Returns:
        bytes del PNG.

    Raises:
        LatexRenderError: si la sintaxis LaTeX no es interpretable por MathText.
    """
    if not latex_source.strip():
        raise LatexRenderError("El source LaTeX está vacío.")

    # Forzar delimitadores `$...$` para que matplotlib lo trate como math.
    expr = latex_source.strip()
    if not (expr.startswith("$") and expr.endswith("$")):
        expr = f"${expr}$"

    fig = plt.figure(figsize=(0.01, 0.01))  # tamaño inicial mínimo; se ajusta
    fig.patch.set_alpha(0)  # transparente
    try:
        try:
            text = fig.text(
                0,
                0,
                expr,
                fontsize=fontsize,
                color=color,
                horizontalalignment="left",
                verticalalignment="bottom",
            )
            # Ajustar tamaño de figura al tamaño real del texto.
            fig.canvas.draw()
            bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
            # Convertir bbox de pixels a inches dividiendo por DPI inicial (100).
            ancho_in = bbox.width / 100 + 0.1
            alto_in = bbox.height / 100 + 0.1
            fig.set_size_inches(ancho_in, alto_in)

            buf = io.BytesIO()
            fig.savefig(
                buf,
                format="png",
                dpi=dpi,
                bbox_inches="tight",
                pad_inches=0.05,
                transparent=True,
            )
            buf.seek(0)
            return buf.read()
        except (ValueError, RuntimeError) as exc:
            raise LatexRenderError(
                f"No se pudo renderizar la fórmula LaTeX: {exc}. "
                "Verifica la sintaxis (MathText subset)."
            ) from exc
    finally:
        plt.close(fig)
