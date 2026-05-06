"""EmptyState — estado vacío amigable con CTA claro."""

from __future__ import annotations

import streamlit as st

from src.ui.theme import SMNYL_COLORS


def render(
    titulo: str,
    descripcion: str,
    icono: str = "📄",
    cta_label: str | None = None,
) -> bool:
    """Renderiza un empty state. Devuelve True si se hizo clic en el CTA."""
    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 4rem 2rem;
            background: {SMNYL_COLORS["bg_soft"]};
            border: 1px dashed {SMNYL_COLORS["border"]};
            border-radius: 12px;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.6;">{icono}</div>
            <h3 style="
                font-family: var(--font-display);
                color: {SMNYL_COLORS["text"]};
                margin-bottom: 0.5rem;
            ">{titulo}</h3>
            <p style="
                color: {SMNYL_COLORS["text_muted"]};
                max-width: 480px;
                margin: 0 auto 1.5rem auto;
            ">{descripcion}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if cta_label:
        return st.button(cta_label, type="primary")
    return False
