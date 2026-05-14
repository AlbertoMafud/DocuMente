"""Botón "Volver" reusable para mantener navegación consistente entre pantallas.

Patrón observado en la app: `st.button("...") → st.session_state["pagina"] = destino → st.rerun()`.
Este componente encapsula ese patrón para evitar duplicación y dejar un look-and-feel uniforme
en todas las pantallas (importar, onboarding, dashboard, auditoría, entrevista, vista previa).
"""

from __future__ import annotations

import streamlit as st


def render(
    destino: str = "home",
    *,
    etiqueta: str = "← Volver",
    key: str | None = None,
    use_container_width: bool = False,
) -> bool:
    """Renderiza un botón de navegación hacia `destino`.

    Devuelve `True` si el usuario hizo click (útil para que el caller
    encadene comportamiento adicional antes del rerun, si lo necesita).

    Args:
        destino: nombre de página en `session_state["pagina"]` (ej. "home",
            "dashboard", "importar"). Default: "home".
        etiqueta: texto del botón. Default: "← Volver".
        key: clave única de Streamlit. Si no se pasa, se genera a partir de
            `destino` y `etiqueta`.
        use_container_width: pasa el flag al `st.button` subyacente.
    """
    if key is None:
        key = f"back_btn_{destino}_{etiqueta}".replace(" ", "_")

    clicked = st.button(
        etiqueta,
        key=key,
        use_container_width=use_container_width,
    )
    if clicked:
        st.session_state["pagina"] = destino
        st.rerun()
    return clicked
