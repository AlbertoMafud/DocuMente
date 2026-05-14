"""Página: editor de sección Prophet.

Permite al usuario editar el contenido de una sección del documento Prophet
(tabla, texto libre o campos estructurados) con persistencia en repositorio.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

import streamlit as st

from src.core.models import EventoAuditoria
from src.core.template_catalog_prophet import SeccionCatalogoProphet, por_id_prophet
from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.theme import SMNYL_COLORS


def render() -> None:
    """Renderiza el editor completo de sección Prophet."""
    seccion_id: str = st.session_state.get("prophet_seccion_id", "")
    doc_id: str = st.session_state.get("documento_actual_id", "")

    repo = DocumentoRepository()
    doc = None
    if doc_id:
        try:
            doc = repo.obtener(UUID(doc_id))
        except (ValueError, Exception):
            doc = None

    if doc is None or not seccion_id:
        st.error("No se encontró el documento o sección. Vuelve al dashboard.")
        if st.button("← Volver"):
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        return

    seccion = doc.seccion_por_id(seccion_id)
    cat = por_id_prophet(seccion_id)

    if seccion is None or cat is None:
        st.error(f"Sección '{seccion_id}' no encontrada.")
        if st.button("← Volver"):
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        return

    header.render(breadcrumbs=["Inicio", doc.metadata_modelo.nombre_modelo, seccion.nombre])

    st.markdown(
        f"""<h1 style="font-family: var(--font-display); color: {SMNYL_COLORS['text']}; margin-bottom: 0.25rem;">
            {seccion.nombre}
        </h1>
        <p style="color: {SMNYL_COLORS['text_muted']}; margin-bottom: 1.5rem;">{cat.intencion}</p>""",
        unsafe_allow_html=True,
    )

    nuevo_contenido: str | None = None

    if cat.tipo_contenido == "tabla":
        nuevo_contenido = _editor_tabla(seccion, cat)
    elif cat.tipo_contenido == "texto":
        nuevo_contenido = _editor_texto(seccion)
    else:
        nuevo_contenido = _editor_campos(seccion, cat)

    col_guardar, col_volver, _ = st.columns([1, 1, 3])
    with col_guardar:
        if st.button("Guardar cambios", type="primary", use_container_width=True) and nuevo_contenido is not None:
            seccion.contenido = nuevo_contenido
            seccion.completitud = "completa"
            doc.registrar_evento(EventoAuditoria(
                timestamp=datetime.now(UTC),
                actor="default",
                tipo="seccion_editada",
                descripcion=f"Sección '{seccion.nombre}' actualizada (Prophet)",
                seccion_id=seccion_id,
            ))
            repo.guardar(doc)
            st.success("Cambios guardados.")
            st.session_state["pagina"] = "dashboard"
            st.rerun()

    with col_volver:
        if st.button("← Volver al dashboard", use_container_width=True):
            st.session_state["pagina"] = "dashboard"
            st.rerun()


def _editor_tabla(seccion, cat: SeccionCatalogoProphet) -> str:
    """Editor de contenido tipo tabla usando st.data_editor."""
    columnas = list(cat.schema_tabla)
    filas_actuales: list[dict] = []
    if seccion.contenido:
        try:
            data = json.loads(seccion.contenido)
            filas_actuales = data.get("filas", []) if isinstance(data, dict) else []
        except json.JSONDecodeError:
            pass

    st.caption(f"{len(filas_actuales)} filas · columnas: {', '.join(columnas)}")

    edited = st.data_editor(
        filas_actuales if filas_actuales else [{col: "" for col in columnas}],
        num_rows="dynamic",
        use_container_width=True,
        key=f"table_editor_{seccion.id}",
    )
    return json.dumps({"filas": edited, "advertencias": []}, ensure_ascii=False)


def _editor_texto(seccion) -> str:
    """Editor de contenido tipo texto libre."""
    valor_actual = ""
    if seccion.contenido:
        try:
            data = json.loads(seccion.contenido)
            valor_actual = data.get("contenido", seccion.contenido)
        except json.JSONDecodeError:
            valor_actual = seccion.contenido

    texto = st.text_area(
        "Contenido",
        value=valor_actual,
        height=300,
        label_visibility="collapsed",
        key=f"text_editor_{seccion.id}",
    )
    return json.dumps({"contenido": texto, "advertencias": []}, ensure_ascii=False)


def _editor_campos(seccion, cat: SeccionCatalogoProphet) -> str:
    """Editor de contenido tipo campos estructurados (formulario)."""
    campos_actuales: dict = {}
    if seccion.contenido:
        try:
            data = json.loads(seccion.contenido)
            raw = data.get("contenido", "{}")
            campos_actuales = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            pass

    cols = cat.schema_tabla if cat.schema_tabla else tuple(campos_actuales.keys())
    resultado: dict = {}
    for col in cols:
        resultado[col] = st.text_input(
            col.replace("_", " ").capitalize(),
            value=campos_actuales.get(col, ""),
            key=f"campo_{seccion.id}_{col}",
        )

    return json.dumps({"contenido": json.dumps(resultado, ensure_ascii=False), "advertencias": []}, ensure_ascii=False)
