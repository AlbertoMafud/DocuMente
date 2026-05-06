"""GapBadge — chip de severidad de brecha."""

from __future__ import annotations

import streamlit as st

from src.core.models import Severidad
from src.ui.theme import SMNYL_COLORS

_COLORS_POR_SEVERIDAD: dict[Severidad, tuple[str, str, str]] = {
    "alta": (SMNYL_COLORS["danger"], "#fdf2f6", "Crítica"),
    "media": (SMNYL_COLORS["warning"], "#fdf4ee", "Atención"),
    "baja": (SMNYL_COLORS["info"], "#eef6fb", "Sugerencia"),
}


def render(severidad: Severidad, texto: str | None = None) -> None:
    """Renderiza un badge inline de severidad."""
    color, bg, label = _COLORS_POR_SEVERIDAD[severidad]
    contenido = texto or label
    st.markdown(
        f"""<span style="
            display: inline-block;
            background: {bg};
            color: {color};
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid {color};
            letter-spacing: 0.02em;
        ">{contenido}</span>""",
        unsafe_allow_html=True,
    )
