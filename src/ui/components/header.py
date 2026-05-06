"""Header con logo SMNYL + navegación + breadcrumbs."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.ui.theme import SMNYL_COLORS

LOGO_PATH = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "logo-smnyl.jpg"


def render(breadcrumbs: list[str] | None = None) -> None:
    """Renderiza el header de la app.

    Args:
        breadcrumbs: lista de strings para ruta de navegación, ej. ["Home", "Importar"].
    """
    col_logo, col_breadcrumbs = st.columns([1, 5])
    with col_logo:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=140)
    with col_breadcrumbs:
        if breadcrumbs:
            crumb_html = (
                f"<span style='color: {SMNYL_COLORS['text_muted']}; "
                "font-size: 0.875rem;'> / </span>"
            ).join(
                f"<span style='color: {SMNYL_COLORS['text_muted']}; font-size: 0.875rem;'>{c}</span>"
                if i < len(breadcrumbs) - 1
                else f"<span style='color: {SMNYL_COLORS['text']}; "
                "font-size: 0.875rem; font-weight: 500;'>"
                f"{c}</span>"
                for i, c in enumerate(breadcrumbs)
            )
            st.markdown(
                f"<div style='padding-top: 1.25rem;'>{crumb_html}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="padding-top: 1.25rem;">
                    <span style="
                        color: {SMNYL_COLORS["text_muted"]};
                        font-size: 0.875rem;
                        letter-spacing: 0.05em;
                        text-transform: uppercase;
                    ">Sistema de documentación institucional</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        f"<hr style='margin: 0.75rem 0 2rem 0; border: none; "
        f"border-top: 1px solid {SMNYL_COLORS['border']};'/>",
        unsafe_allow_html=True,
    )
