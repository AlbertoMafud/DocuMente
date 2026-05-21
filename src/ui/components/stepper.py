"""Stepper visual horizontal con marca SMNYL.

Componente reusable para flujos multi-step (onboarding, brief inicial,
entrevista). Reemplaza la sensación "no veo progreso" detectada en el
audit UX (Goal-Gradient effect, §1.7).

Estados por paso:
- Completado: círculo success_dark con check.
- Actual: círculo primary con número.
- Pendiente: círculo border con número muted.
"""

from __future__ import annotations

import streamlit as st

from src.ui.theme import SMNYL_COLORS


def render(
    pasos: list[str],
    actual_idx: int,
    *,
    completados: int | None = None,
) -> None:
    """Renderiza un stepper horizontal con N pasos.

    Args:
        pasos: lista de labels (ej. ["Crear", "Onboarding", "Brief", "Dashboard"]).
        actual_idx: índice 0-based del paso actual.
        completados: cuántos pasos están completados; default = `actual_idx`
            (todos los pasos anteriores se consideran completados).
    """
    if not pasos:
        return

    n = len(pasos)
    actual_idx = max(0, min(actual_idx, n - 1))
    if completados is None:
        completados = actual_idx
    completados = max(0, min(completados, n))

    st.markdown(_css(), unsafe_allow_html=True)
    st.markdown(_html(pasos, actual_idx, completados), unsafe_allow_html=True)


def _html(pasos: list[str], actual_idx: int, completados: int) -> str:
    n = len(pasos)
    parts: list[str] = ["<div class='dm-stepper'>"]
    for i, label in enumerate(pasos):
        if i < completados:
            estado = "completed"
            marker = "✓"
        elif i == actual_idx:
            estado = "actual"
            marker = str(i + 1)
        else:
            estado = "pending"
            marker = str(i + 1)
        parts.append(
            f"<div class='dm-step'>"
            f"<div class='dm-step-circle dm-step-{estado}' aria-current="
            f"{'true' if estado == 'actual' else 'false'}>{marker}</div>"
            f"<div class='dm-step-label dm-step-label-{estado}'>{label}</div>"
            f"</div>"
        )
        if i < n - 1:
            line_estado = "completed" if i < completados else "pending"
            parts.append(f"<div class='dm-step-line dm-step-line-{line_estado}'></div>")
    parts.append("</div>")
    return "".join(parts)


def _css() -> str:
    c = SMNYL_COLORS
    return f"""<style>
    .dm-stepper {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 16px 0 32px;
        padding: 4px 0;
    }}
    .dm-step {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
    }}
    .dm-step-circle {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: var(--font-body);
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 200ms ease-out;
    }}
    .dm-step-completed {{
        background: {c["success_dark"]};
        color: white;
    }}
    .dm-step-actual {{
        background: {c["primary"]};
        color: white;
        box-shadow: 0 0 0 4px {c["accent_soft"]};
    }}
    .dm-step-pending {{
        background: {c["bg"]};
        color: {c["text_muted"]};
        border: 1.5px solid {c["border"]};
    }}
    .dm-step-label {{
        font-size: 0.75rem;
        font-weight: 500;
        text-align: center;
        max-width: 110px;
        line-height: 1.2;
        font-family: var(--font-body);
    }}
    .dm-step-label-completed {{
        color: {c["success_dark"]};
    }}
    .dm-step-label-actual {{
        color: {c["primary_dark"]};
        font-weight: 600;
    }}
    .dm-step-label-pending {{
        color: {c["text_muted"]};
    }}
    .dm-step-line {{
        height: 2px;
        flex-grow: 1;
        margin-top: -22px;
        transition: background 200ms ease-out;
    }}
    .dm-step-line-completed {{
        background: {c["success_dark"]};
    }}
    .dm-step-line-pending {{
        background: {c["border"]};
    }}
    </style>"""
