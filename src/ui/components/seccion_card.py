"""SectionCard — visualización de una sección del documento con su completitud."""

from __future__ import annotations

import streamlit as st

from src.core.models import Seccion
from src.ui.theme import SMNYL_COLORS

_COLORS_POR_COMPLETITUD = {
    "vacia": (SMNYL_COLORS["danger"], "Vacía"),
    "parcial": (SMNYL_COLORS["warning"], "Parcial"),
    "completa": (SMNYL_COLORS["success"], "Completa"),
    "omitida": (SMNYL_COLORS["text_muted"], "Omitida"),
}


def render(seccion: Seccion, *, brechas_count: int = 0) -> None:
    """Renderiza una card visual con el estado de la sección."""
    color, label = _COLORS_POR_COMPLETITUD[seccion.completitud]
    obligatoria_marker = (
        f"<span style='color: {SMNYL_COLORS['text_muted']}; font-size: 0.75rem;'>obligatoria</span>"
        if seccion.obligatoria
        else f"<span style='color: {SMNYL_COLORS['text_muted']}; font-size: 0.75rem;'>"
        "opcional</span>"
    )

    chars = len(seccion.contenido or "")
    if seccion.completitud == "omitida":
        chars_str = "—"
    elif chars:
        chars_str = f"{chars:,} caracteres"
    else:
        chars_str = "sin contenido"

    brechas_html = (
        f"<span style='color: {SMNYL_COLORS['danger']}; font-size: 0.75rem;'>"
        f"{brechas_count} brecha(s)</span>"
        if brechas_count and seccion.completitud != "omitida"
        else ""
    )

    motivo_html = ""
    if seccion.completitud == "omitida" and seccion.motivo_omision:
        motivo_html = (
            f"<div style='margin-top: 6px; font-size: 0.75rem;"
            f" color: {SMNYL_COLORS['text_muted']}; font-style: italic;'>"
            f"Motivo: {seccion.motivo_omision}</div>"
        )

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span style="
                    width: 10px; height: 10px; border-radius: 50%;
                    background: {color}; display: inline-block;
                "></span>
                <span style="
                    color: {SMNYL_COLORS["text_muted"]};
                    font-size: 0.875rem;
                    font-weight: 500;
                ">{seccion.numero}</span>
                <span style="font-weight: 600; color: {SMNYL_COLORS["text"]};">
                    {seccion.nombre}
                </span>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;
                margin-top: 8px; padding-top: 8px;
                border-top: 1px solid {SMNYL_COLORS["border"]};">
                <span style="color: {color}; font-size: 0.75rem; font-weight: 600;">{label}</span>
                {obligatoria_marker}
                <span style="color: {SMNYL_COLORS["text_muted"]}; font-size: 0.75rem;">
                    {chars_str}
                </span>
                {brechas_html}
            </div>
            {motivo_html}
            """,
            unsafe_allow_html=True,
        )
