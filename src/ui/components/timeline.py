"""Timeline — línea de tiempo vertical del audit_trail con marca SMNYL.

Muestra eventos del audit trail de un Documento en orden cronológico
inverso (más reciente primero). Cada evento se renderiza como una tarjeta
con marcador visual coloreado por tipo de evento, timestamp, actor,
descripción y badge de sección si aplica.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final

import streamlit as st

from src.core.models import EventoAuditoria
from src.core.models.auditoria import TipoEvento
from src.ui.theme import SMNYL_COLORS

# Mapeo tipo → (color marcador, color texto del label, etiqueta humana)
# El marker es UI component (3:1 OK); el label es texto y necesita AA (4.5:1).
_ESTILO_POR_TIPO: Final[dict[TipoEvento, tuple[str, str, str]]] = {
    "documento_creado": (SMNYL_COLORS["primary"], SMNYL_COLORS["primary"], "Documento creado"),
    "documento_importado": (
        SMNYL_COLORS["primary"],
        SMNYL_COLORS["primary"],
        "Documento importado",
    ),
    "seccion_editada": (SMNYL_COLORS["success"], SMNYL_COLORS["success_dark"], "Sección editada"),
    "seccion_completada": (
        SMNYL_COLORS["success"],
        SMNYL_COLORS["success_dark"],
        "Sección completada",
    ),
    "seccion_omitida": (
        SMNYL_COLORS["text_muted"],
        SMNYL_COLORS["text_muted"],
        "Sección omitida",
    ),
    "transicion_estado": (
        SMNYL_COLORS["primary_dark"],
        SMNYL_COLORS["primary_dark"],
        "Cambio de estado",
    ),
    "metadata_actualizada": (
        SMNYL_COLORS["text_muted"],
        SMNYL_COLORS["text_muted"],
        "Metadata actualizada",
    ),
    "exportado": (SMNYL_COLORS["info"], SMNYL_COLORS["info_dark"], "Exportado"),
    "signoff_reviewer": (
        SMNYL_COLORS["warning"],
        SMNYL_COLORS["warning_dark"],
        "Sign-off Reviewer",
    ),
    "signoff_fae": (SMNYL_COLORS["warning"], SMNYL_COLORS["warning_dark"], "Sign-off FAE"),
}


def _formato_timestamp(ts: datetime) -> tuple[str, str]:
    """Devuelve (fecha_legible, hora) en hora local del usuario."""
    local = ts.astimezone()
    fecha = local.strftime("%d %b %Y").lower()
    hora = local.strftime("%H:%M")
    return fecha, hora


def render(eventos: list[EventoAuditoria]) -> None:
    """Renderiza una lista de EventoAuditoria como timeline vertical."""
    if not eventos:
        muted = SMNYL_COLORS["text_muted"]
        st.markdown(
            f"<div style='padding: 2rem; text-align: center; color: {muted}; font-style: italic;'>Aún no hay eventos registrados.</div>",
            unsafe_allow_html=True,
        )
        return

    # Más reciente primero
    ordenados = sorted(eventos, key=lambda e: e.timestamp, reverse=True)

    # CSS único para la lista
    st.markdown(_css_timeline(), unsafe_allow_html=True)

    items_html = "".join(_render_item(e) for e in ordenados)
    st.markdown(
        f"<div class='dm-timeline'>{items_html}</div>",
        unsafe_allow_html=True,
    )


def _render_item(evento: EventoAuditoria) -> str:
    """Devuelve el HTML del item en una sola línea para evitar que markdown lo trate como code block."""
    color_marker, color_label, etiqueta = _ESTILO_POR_TIPO.get(
        evento.tipo,
        (SMNYL_COLORS["text_muted"], SMNYL_COLORS["text_muted"], evento.tipo),
    )
    fecha, hora = _formato_timestamp(evento.timestamp)
    seccion_badge = (
        f"<span class='dm-tl-seccion'>{evento.seccion_id}</span>" if evento.seccion_id else ""
    )
    descripcion = (evento.descripcion or "").replace("<", "&lt;").replace(">", "&gt;")
    actor = (evento.actor or "").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"<div class='dm-tl-item'>"
        f"<div class='dm-tl-marker' style='background:{color_marker};' aria-hidden='true'></div>"
        f"<div class='dm-tl-content'>"
        f"<div class='dm-tl-header'>"
        f"<span class='dm-tl-tipo' style='color:{color_label};'>{etiqueta}</span>"
        f"{seccion_badge}"
        f"<span class='dm-tl-time'>{fecha} · {hora}</span>"
        f"</div>"
        f"<div class='dm-tl-desc'>{descripcion}</div>"
        f"<div class='dm-tl-actor'>por {actor}</div>"
        f"</div>"
        f"</div>"
    )


def _css_timeline() -> str:
    c = SMNYL_COLORS
    return f"""<style>
    .dm-timeline {{
        position: relative;
        padding-left: 24px;
        margin-top: 8px;
    }}
    .dm-timeline::before {{
        content: '';
        position: absolute;
        left: 7px;
        top: 8px;
        bottom: 8px;
        width: 2px;
        background: {c["border"]};
    }}
    .dm-tl-item {{
        position: relative;
        padding-bottom: 18px;
    }}
    .dm-tl-marker {{
        position: absolute;
        left: -23px;
        top: 6px;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: 2px solid {c["bg"]};
        box-shadow: 0 0 0 2px {c["border"]};
    }}
    .dm-tl-content {{
        padding: 8px 14px 10px;
        background: {c["bg_soft"]};
        border-radius: 8px;
        border: 1px solid {c["border"]};
    }}
    .dm-tl-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 4px;
    }}
    .dm-tl-tipo {{
        font-weight: 600;
        font-size: 0.825rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .dm-tl-seccion {{
        font-size: 0.7rem;
        color: {c["text_muted"]};
        background: {c["bg"]};
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid {c["border"]};
        font-family: monospace;
    }}
    .dm-tl-time {{
        margin-left: auto;
        font-size: 0.75rem;
        color: {c["text_muted"]};
    }}
    .dm-tl-desc {{
        color: {c["text"]};
        font-size: 0.92rem;
        line-height: 1.5;
    }}
    .dm-tl-actor {{
        margin-top: 4px;
        font-size: 0.7rem;
        color: {c["text_muted"]};
        font-style: italic;
    }}
    </style>"""
