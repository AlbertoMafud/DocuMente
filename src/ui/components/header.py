"""Header con logo SMNYL + navegación + breadcrumbs clickeables.

Los breadcrumbs son ahora clickeables (cada nivel intermedio te lleva a esa
página). El último item es el current y se renderea como texto, no botón.

Auto-inferencia de destinos:
- `"Inicio"` → `home`
- segundo item (si existe doc actual y hay >2 items) → `dashboard`
- el resto: no clickeable (auto-inferencia no asume)

Para sobreescribir el comportamiento, pasa `destinos=[...]` paralelo a
`breadcrumbs`, con `None` para los no-clickeables y el slug de página para
los clickeables.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.ui.theme import SMNYL_COLORS

LOGO_PATH = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "logo-smnyl.jpg"


def _inferir_destinos(breadcrumbs: list[str]) -> list[str | None]:
    """Mapea cada breadcrumb a una página de destino o None (no clickeable).

    Reglas:
    - El último breadcrumb es el current, no clickeable.
    - "Inicio" → "home" (siempre).
    - Si hay >2 items y hay `documento_actual_id` en session, el segundo
      breadcrumb (típicamente nombre del modelo) → "dashboard".
    - Cualquier otro → no clickeable.
    """
    n = len(breadcrumbs)
    destinos: list[str | None] = []
    tiene_doc_actual = bool(st.session_state.get("documento_actual_id"))
    for i, label in enumerate(breadcrumbs):
        if i == n - 1:
            destinos.append(None)  # current
        elif label.strip().lower() in ("inicio", "home"):
            destinos.append("home")
        elif i == 1 and n > 2 and tiene_doc_actual:
            destinos.append("dashboard")
        else:
            destinos.append(None)
    return destinos


def _ratio_para_label(label: str) -> float:
    """Ratio compacto para la columna del breadcrumb según length del texto.

    Mantenemos las columnas muy estrechas; el CSS hace que el botón NO ocupe
    el 100% de su columna (`width: auto`). Combinado con `gap=0` en el
    horizontal block, los items quedan agrupados a la izquierda sin huecos.
    """
    return max(0.6, len(label) * 0.08)


def render(
    breadcrumbs: list[str] | None = None,
    *,
    destinos: list[str | None] | None = None,
) -> None:
    """Renderiza el header de la app.

    Args:
        breadcrumbs: lista de strings para ruta de navegación, ej. ["Inicio", "Importar"].
        destinos: opcional, lista paralela con slug de página o `None` por crumb.
            Si no se pasa, se infiere automáticamente (ver `_inferir_destinos`).
    """
    col_logo, col_breadcrumbs = st.columns([1, 5])
    with col_logo:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=140)
    with col_breadcrumbs:
        if breadcrumbs:
            _render_breadcrumbs(breadcrumbs, destinos)
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


def _render_breadcrumbs(
    breadcrumbs: list[str], destinos: list[str | None] | None
) -> None:
    """Renderiza cada breadcrumb como botón clickeable o texto plano.

    Layout: una fila de columnas que alterna crumb / separador / crumb / …
    El separador es un slash sutil. El padding-top inicial alinea visualmente
    con el centro vertical del logo.
    """
    if destinos is None:
        destinos = _inferir_destinos(breadcrumbs)

    n = len(breadcrumbs)
    # Columnas: [crumb, sep, crumb, sep, …, crumb, padding_derecha]
    # Las columnas son MUY estrechas; el CSS abajo evita que el botón ocupe
    # todo el ancho de su columna (sin esto los breadcrumbs salen separados).
    ratios: list[float] = []
    for i, label in enumerate(breadcrumbs):
        ratios.append(_ratio_para_label(label))
        if i < n - 1:
            ratios.append(0.15)  # separador angosto
    ratios.append(8.0)  # padding derecho grande: empuja todo a la izquierda

    cols = st.columns(ratios, gap="small", vertical_alignment="center")

    muted = SMNYL_COLORS["text_muted"]
    text = SMNYL_COLORS["text"]

    st.markdown(
        f"""
        <style>
        /* Botones de breadcrumb: look de link, no de botón.
           Streamlit los renderiza como block-button con width:100% por default;
           los re-estilizamos para que parezcan texto enlazado inline. */
        div[data-testid="stHorizontalBlock"]
            div[data-testid="stColumn"] button[kind="tertiary"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            width: auto !important;
            min-width: 0 !important;
            color: {muted} !important;
            font-weight: 400 !important;
            font-size: 0.875rem !important;
            text-decoration: none;
            white-space: nowrap;
        }}
        div[data-testid="stHorizontalBlock"]
            div[data-testid="stColumn"] button[kind="tertiary"]:hover {{
            color: {SMNYL_COLORS["primary"]} !important;
            text-decoration: underline;
            background: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    for i, label in enumerate(breadcrumbs):
        idx = i * 2
        with cols[idx]:
            destino = destinos[i] if i < len(destinos) else None
            if destino:
                # Botón clickeable. type="tertiary" en Streamlit 1.36+; si la
                # versión no lo soporta, cae al estilo default (igualmente clickeable).
                try:
                    clicked = st.button(
                        label,
                        key=f"crumb_btn_{i}_{destino}",
                        type="tertiary",
                    )
                except TypeError:
                    clicked = st.button(label, key=f"crumb_btn_{i}_{destino}")
                if clicked:
                    st.session_state["pagina"] = destino
                    st.rerun()
            else:
                # Último item / no clickeable: texto plano. El último va más fuerte.
                color = text if i == n - 1 else muted
                peso = "500" if i == n - 1 else "400"
                st.markdown(
                    f"<span style='color: {color}; font-size: 0.875rem; "
                    f"font-weight: {peso}; white-space: nowrap;'>{label}</span>",
                    unsafe_allow_html=True,
                )
        if i < n - 1:
            with cols[idx + 1]:
                st.markdown(
                    f"<span style='color: {muted}; font-size: 0.875rem; "
                    f"opacity: 0.6;'>/</span>",
                    unsafe_allow_html=True,
                )
