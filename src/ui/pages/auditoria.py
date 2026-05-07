"""Pantalla de auditoría — timeline completo + estadísticas del documento.

Materializa el requisito MRM Standard §3.5: la documentación debe registrar
quién hizo qué cuándo. Esta pantalla expone visualmente todo el audit_trail
del documento para revisión, attestation y referencia histórica.
"""

from __future__ import annotations

from collections import Counter
from uuid import UUID

import streamlit as st

from src.core.models.auditoria import TipoEvento
from src.storage.repositories import DocumentoRepository
from src.ui.components import header, timeline
from src.ui.theme import SMNYL_COLORS

_FILTROS_DISPONIBLES: list[tuple[str, TipoEvento | None]] = [
    ("Todos", None),
    ("Cambios de estado", "transicion_estado"),
    ("Sign-offs", "signoff_reviewer"),  # se complementa con signoff_fae abajo
    ("Ediciones", "seccion_editada"),
    ("Omisiones", "seccion_omitida"),
    ("Importación", "documento_importado"),
]


def render() -> None:
    documento_id_str = st.session_state.get("documento_actual_id")
    if not documento_id_str:
        header.render(breadcrumbs=["Inicio", "Auditoría"])
        st.warning("No hay documento seleccionado.")
        if st.button("Volver al inicio", type="primary"):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    documento_id = UUID(documento_id_str)
    repo = DocumentoRepository()
    documento = repo.obtener(documento_id)
    if documento is None:
        header.render(breadcrumbs=["Inicio", "Auditoría"])
        st.error("Documento no encontrado.")
        return

    nombre = documento.metadata_modelo.nombre_modelo or "Documento sin nombre"
    header.render(breadcrumbs=["Inicio", nombre, "Auditoría"])

    text_color = SMNYL_COLORS["text"]
    muted = SMNYL_COLORS["text_muted"]

    st.markdown(
        f"""
        <h1 style='font-family: var(--font-display); color: {text_color};
            margin-bottom: 0.25rem;'>Auditoría del documento</h1>
        <p style='color: {muted}; margin-bottom: 2rem; max-width: 720px;'>
            Registro completo de cambios. Cada evento queda inmutable y
            disponible para attestation semestral.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Resumen estadístico
    eventos = documento.audit_trail
    conteo = Counter(e.tipo for e in eventos)
    secciones_tocadas = {e.seccion_id for e in eventos if e.seccion_id}

    with st.container(border=True):
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Eventos totales", str(len(eventos)))
        with col_b:
            st.metric("Secciones tocadas", str(len(secciones_tocadas)))
        with col_c:
            transiciones = conteo.get("transicion_estado", 0)
            st.metric("Cambios de estado", str(transiciones))
        with col_d:
            signoffs = conteo.get("signoff_reviewer", 0) + conteo.get("signoff_fae", 0)
            st.metric("Sign-offs", str(signoffs))

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Filtro
    col_filtro, col_volver = st.columns([3, 1])
    with col_filtro:
        opcion = st.selectbox(
            "Filtrar por tipo",
            options=[f[0] for f in _FILTROS_DISPONIBLES],
            index=0,
            label_visibility="collapsed",
        )
    with col_volver:
        if st.button("Volver al dashboard", use_container_width=True):
            st.session_state["pagina"] = "dashboard"
            st.rerun()

    eventos_filtrados = _aplicar_filtro(eventos, opcion)
    timeline.render(eventos_filtrados)


def _aplicar_filtro(
    eventos: list,
    opcion: str,
) -> list:
    if opcion == "Todos":
        return list(eventos)
    if opcion == "Sign-offs":
        return [e for e in eventos if e.tipo in ("signoff_reviewer", "signoff_fae")]
    if opcion == "Cambios de estado":
        return [e for e in eventos if e.tipo == "transicion_estado"]
    if opcion == "Ediciones":
        return [e for e in eventos if e.tipo in ("seccion_editada", "seccion_completada")]
    if opcion == "Omisiones":
        return [e for e in eventos if e.tipo == "seccion_omitida"]
    if opcion == "Importación":
        return [e for e in eventos if e.tipo in ("documento_importado", "documento_creado")]
    return list(eventos)
