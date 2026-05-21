"""Banner que resume el resultado del onboarding (fuentes + brief inicial).

Se muestra una sola vez en el dashboard tras crear/importar un documento.
La info viene del `st.session_state["onboarding_resultado"]` que dejaron
`crear_nuevo.py`, `importar.py` y `brief_inicial.py`.

Se "consume" en el primer render (pop del session_state) para que no
aparezca cada vez que el usuario vuelve al dashboard.

Diseño:
- Si hubo prellenado → banner verde con icono y conteo.
- Si hubo advertencias o errores → mezcla verde+amarillo con detalle.
- Si LLM no estuvo disponible → banner naranja avisando que el flujo
  manual sigue disponible.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.theme import SMNYL_COLORS

_SESSION_KEY = "onboarding_resultado"


def _consumir_resultado() -> dict[str, Any] | None:
    """Pop the resultado del session_state — devuelve None si no hay."""
    return st.session_state.pop(_SESSION_KEY, None)


def _texto_resumen(data: dict[str, Any]) -> str:
    secciones_pre = int(data.get("secciones_prellenadas", 0) or 0)
    fuentes = int(data.get("fuentes_extraidas", 0) or 0)
    brief_aplicadas = int(data.get("secciones_brief_aplicadas", 0) or 0)
    total = secciones_pre + brief_aplicadas
    partes: list[str] = []
    if total > 0:
        partes.append(f"{total} sección(es) pre-poblada(s)")
    if fuentes > 0:
        partes.append(f"{fuentes} fuente(s) cargada(s) como contexto")
    if brief_aplicadas > 0 and secciones_pre > 0:
        partes.append(f"({secciones_pre} de fuentes + {brief_aplicadas} del brief)")
    return " · ".join(partes) if partes else "No se prellenó ninguna sección"


def render() -> None:
    """Renderiza el banner si hay resultado pendiente; si no, no hace nada."""
    data = _consumir_resultado()
    if data is None:
        return

    llm_disponible = bool(data.get("llm_disponible", True))
    advertencias: list[str] = list(data.get("advertencias", []) or [])
    brief_errores: list[str] = list(data.get("brief_errores", []) or [])
    descartadas: list[str] = list(data.get("fuentes_descartadas", []) or [])

    color_borde = SMNYL_COLORS["success"]
    icono = "✅"
    if not llm_disponible:
        color_borde = SMNYL_COLORS["warning"]
        icono = "⚠️"
    elif advertencias or brief_errores or descartadas:
        color_borde = SMNYL_COLORS["info"]
        icono = "ℹ️"

    resumen = _texto_resumen(data)

    st.markdown(
        f"""
        <div style="
            background-color: {SMNYL_COLORS["bg_soft"]};
            border-left: 4px solid {color_borde};
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 1.5rem;
            color: {SMNYL_COLORS["text"]};
            font-family: var(--font-body);
        ">
            <div style="font-weight: 600; margin-bottom: 4px;">
                {icono} Onboarding aplicado
            </div>
            <div style="font-size: 0.9rem; color: {SMNYL_COLORS["text_muted"]};">
                {resumen}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if advertencias or brief_errores or descartadas:
        with st.expander("Ver detalle de advertencias", expanded=False):
            for adv in advertencias:
                st.markdown(f"- {adv}")
            for err in brief_errores:
                st.markdown(f"- {err}")
            if descartadas:
                st.markdown(f"- Fuentes descartadas (sin texto útil): {', '.join(descartadas)}")
