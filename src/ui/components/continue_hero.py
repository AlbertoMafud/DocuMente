"""Hero "Continúa donde te quedaste" para la home.

Cuando hay al menos un documento activo en draft o in_review, mostrar este
hero prominente en lugar de los 3 CTAs equivalentes. Resuelve el Hick's
Law de la home (audit §1.4 — paradox of choice) y aprovecha el efecto
Zeigarnik (tareas inacabadas se recuerdan mejor).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import streamlit as st

from src.ui.theme import SMNYL_COLORS


def formato_relativo(ts: datetime) -> str:
    """Devuelve una descripción de tiempo en español: 'hace 3 horas', 'hace 2 días'.

    Acepta datetimes naive y aware; los naive se asumen UTC.
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    delta = datetime.now(UTC) - ts
    segundos = int(delta.total_seconds())

    if segundos < 60:
        return "hace unos segundos"
    if segundos < 3600:
        m = segundos // 60
        return f"hace {m} minuto{'s' if m != 1 else ''}"
    if segundos < 86400:
        h = segundos // 3600
        return f"hace {h} hora{'s' if h != 1 else ''}"
    if segundos < 86400 * 30:
        d = segundos // 86400
        return f"hace {d} día{'s' if d != 1 else ''}"
    meses = segundos // (86400 * 30)
    return f"hace {meses} mes{'es' if meses != 1 else ''}"


def render(doc: Any) -> bool:
    """Renderiza el hero con un documento activo y devuelve True si se clickeó "Continuar".

    Args:
        doc: instancia con atributos `id`, `metadata_modelo.nombre_modelo`,
            `porcentaje_completitud` (0..1), `actualizado_en` (datetime),
            `estado` (str).
    """
    c = SMNYL_COLORS
    nombre = doc.metadata_modelo.nombre_modelo or "Documento sin nombre"
    pct = int(doc.porcentaje_completitud * 100)
    tiempo = formato_relativo(doc.actualizado_en)
    estado = doc.estado

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {c["primary"]}08 0%, {c["accent_soft"]}40 100%);
            border: 1px solid {c["accent_soft"]};
            border-radius: 12px;
            padding: 28px 32px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(10, 60, 83, 0.06);
        ">
            <div style="
                font-size: 0.7rem;
                color: {c["primary_dark"]};
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 600;
                margin-bottom: 8px;
            ">Continúa donde te quedaste</div>
            <div style="
                font-family: var(--font-display);
                font-size: 1.75rem;
                color: {c["text"]};
                font-weight: 600;
                margin-bottom: 6px;
                line-height: 1.2;
            ">{nombre}</div>
            <div style="
                color: {c["text_muted"]};
                font-size: 0.95rem;
                margin-bottom: 4px;
            ">
                <strong style="color: {c["primary_dark"]};">{pct}% completo</strong>
                &nbsp;·&nbsp; Estado: {estado}
            </div>
            <div style="
                color: {c["text_muted"]};
                font-size: 0.85rem;
                font-style: italic;
            ">Última edición {tiempo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cta, _ = st.columns([1, 3])
    with col_cta:
        return bool(
            st.button(
                "Continuar →",
                type="primary",
                use_container_width=True,
                key=f"continue_hero_{doc.id}",
            )
        )
