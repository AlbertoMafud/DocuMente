"""ChatBubble — burbujas de la entrevista (usuario / asistente / system_note)."""

from __future__ import annotations

import streamlit as st

from src.core.models import RolMensaje
from src.ui.theme import SMNYL_COLORS

_ESTILOS: dict[str, dict[str, str]] = {
    "user": {
        "bg": SMNYL_COLORS["primary"],
        "fg": "#ffffff",
        "align": "flex-end",
        "border_radius": "16px 16px 4px 16px",
        "label": "Tú",
    },
    "assistant": {
        "bg": SMNYL_COLORS["accent_soft"],
        "fg": SMNYL_COLORS["text"],
        "align": "flex-start",
        "border_radius": "16px 16px 16px 4px",
        "label": "DocuMente",
    },
    "system_note": {
        "bg": "#fef9e7",
        "fg": SMNYL_COLORS["text_muted"],
        "align": "center",
        "border_radius": "8px",
        "label": "Sistema",
    },
}


def render(rol: RolMensaje, contenido: str) -> None:
    """Renderiza una burbuja de chat con estilo SMNYL."""
    estilo = _ESTILOS.get(rol, _ESTILOS["assistant"])
    bg = estilo["bg"]
    fg = estilo["fg"]
    align = estilo["align"]
    radius = estilo["border_radius"]
    label = estilo["label"]

    label_html = (
        f"<div style='font-size: 0.7rem; font-weight: 600; opacity: 0.85; "
        f"margin-bottom: 4px; letter-spacing: 0.04em; text-transform: uppercase;'>"
        f"{label}</div>"
    )

    bubble_html = (
        f"<div style='background: {bg}; color: {fg}; "
        f"padding: 12px 16px; border-radius: {radius}; "
        f"max-width: 85%; box-shadow: 0 1px 2px rgba(10,60,83,0.08); "
        f"font-size: 0.95rem; line-height: 1.5;'>"
        f"{label_html}"
        f"<div style='white-space: pre-wrap;'>{contenido}</div>"
        f"</div>"
    )

    container = (
        f"<div style='display: flex; justify-content: {align}; "
        f"margin-bottom: 12px;'>{bubble_html}</div>"
    )

    st.markdown(container, unsafe_allow_html=True)
