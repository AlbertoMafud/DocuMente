"""Página: editor inline de sección MRM desde vista previa (B.4).

A diferencia de `editar_seccion_prophet.py` (que tiene 3 tipos de editor:
tabla, texto, campos), las secciones del catálogo MRM son todas texto
markdown libre — por lo que el editor es un solo textarea grande con
preview lado a lado.

Flujo de uso:
1. Usuario está en `vista_previa.py` revisando el documento completo.
2. Click "✏️ Editar inline" en una sección → setea
   `st.session_state['mrm_seccion_id']` y navega a `editar_seccion_mrm`.
3. Esta página renderiza textarea + preview vivo + guardar.
4. Al guardar: persiste, registra audit event `seccion_editada`,
   y vuelve a `vista_previa`.

NOTA: el editor de Prophet sigue siendo el camino para secciones tipo
tabla. Este editor es solo para MRM (texto libre).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import streamlit as st

from src.core.models import EventoAuditoria
from src.storage.repositories import DocumentoRepository
from src.ui.components import continue_hero, header
from src.ui.theme import SMNYL_COLORS


def render() -> None:
    """Renderiza el editor de sección MRM con preview en vivo."""
    seccion_id: str = st.session_state.get("mrm_seccion_id", "")
    doc_id: str = st.session_state.get("documento_actual_id", "")

    if not doc_id or not seccion_id:
        st.error("No se encontró el documento o sección. Vuelve a la vista previa.")
        if st.button("← Volver a la vista previa"):
            st.session_state["pagina"] = "vista_previa"
            st.rerun()
        return

    repo = DocumentoRepository()
    try:
        doc = repo.obtener(UUID(doc_id))
    except (ValueError, Exception):
        doc = None

    if doc is None:
        st.error("Documento no encontrado.")
        if st.button("← Volver"):
            st.session_state["pagina"] = "vista_previa"
            st.rerun()
        return

    seccion = doc.seccion_por_id(seccion_id)
    if seccion is None:
        st.error(f"Sección '{seccion_id}' no encontrada.")
        if st.button("← Volver"):
            st.session_state["pagina"] = "vista_previa"
            st.rerun()
        return

    nombre_modelo = doc.metadata_modelo.nombre_modelo or "Documento sin nombre"
    header.render(breadcrumbs=["Inicio", nombre_modelo, "Vista previa", f"Editar {seccion.numero}"])

    text = SMNYL_COLORS["text"]
    muted = SMNYL_COLORS["text_muted"]
    ultimo = doc.ultimo_guardado_seccion(seccion_id)
    indicador_guardado = ""
    if ultimo is not None:
        indicador_guardado = (
            f"<span style='color: {muted}; font-size: 0.8rem; font-style: italic; "
            f"margin-left: 0.75rem;'>· Guardado {continue_hero.formato_relativo(ultimo)}</span>"
        )
    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {text};
            margin-bottom: 0.25rem;">{seccion.numero} {seccion.nombre}{indicador_guardado}</h1>
        <p style="color: {muted}; margin-bottom: 1rem;">
            {
            seccion.intencion
            or "Edita el contenido en markdown. La columna derecha muestra el preview en vivo."
        }
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Layout split: editor (izq) | preview (der)
    col_editor, col_preview = st.columns([1, 1])

    valor_inicial = seccion.contenido or ""
    state_key = f"mrm_editor_{seccion_id}"

    with col_editor:
        st.markdown("**Editor (markdown)**")
        nuevo_contenido = st.text_area(
            "Contenido",
            value=valor_inicial,
            height=520,
            key=state_key,
            label_visibility="collapsed",
            help=(
                "Markdown soportado: **negritas**, *cursivas*, listas con `- `, "
                "tablas con pipes `| col | col |`."
            ),
        )

    with col_preview:
        st.markdown("**Preview en vivo**")
        with st.container(border=True):
            if nuevo_contenido and nuevo_contenido.strip():
                st.markdown(nuevo_contenido)
            else:
                st.caption("_(sin contenido — el preview se actualiza al escribir)_")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    col_guardar, col_cancelar, _ = st.columns([1, 1, 3])
    with col_guardar:
        if st.button("Guardar cambios", type="primary", use_container_width=True):
            contenido_limpio = (nuevo_contenido or "").strip()
            if contenido_limpio == (seccion.contenido or "").strip():
                st.toast("Sin cambios para guardar.", icon="ℹ️")
                st.session_state["pagina"] = "vista_previa"
                st.rerun()
                return

            seccion.contenido = contenido_limpio if contenido_limpio else None
            # Re-evaluar completitud por longitud (mismo criterio que el reader)
            if not contenido_limpio:
                seccion.completitud = "vacia"
            elif len(contenido_limpio) < 200:
                seccion.completitud = "parcial"
            else:
                seccion.completitud = "completa"

            doc.registrar_evento(
                EventoAuditoria(
                    timestamp=datetime.now(UTC),
                    actor=doc.user_id,
                    tipo="seccion_editada",
                    descripcion=(
                        f"Sección '{seccion.numero} {seccion.nombre}' editada inline "
                        f"desde vista previa."
                    ),
                    seccion_id=seccion_id,
                )
            )
            repo.guardar(doc)
            st.toast("Cambios guardados.", icon="✅")
            st.session_state["pagina"] = "vista_previa"
            st.rerun()

    with col_cancelar:
        if st.button("Cancelar", use_container_width=True):
            st.session_state["pagina"] = "vista_previa"
            st.rerun()
