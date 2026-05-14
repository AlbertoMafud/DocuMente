"""Pantalla de creación de documento desde cero.

Renderiza:
- Header con breadcrumbs.
- Form con 2 campos: nombre del modelo + model_id.
- Al submit: crea el Documento esqueleto, lo persiste, y redirige a onboarding.
"""

from __future__ import annotations

from io import BytesIO

import streamlit as st

from src.core.usecases import CrearDocumentoEnBlanco
from src.llm import AnthropicClient
from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.theme import SMNYL_COLORS


def _construir_use_case() -> CrearDocumentoEnBlanco:
    try:
        llm: AnthropicClient | None = AnthropicClient()
    except Exception:
        llm = None
    return CrearDocumentoEnBlanco(repo=DocumentoRepository(), llm=llm)


def render() -> None:
    header.render(breadcrumbs=["Inicio", "Crear nuevo documento"])

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {SMNYL_COLORS["text"]};
            margin-bottom: 0.5rem;">Crear nuevo documento</h1>
        <p style="color: {SMNYL_COLORS["text_muted"]}; margin-bottom: 2rem;
            max-width: 720px;">
            Empezarás con la estructura completa del Model Development Template
            oficial de NYL — 28 secciones vacías. DocuMente te guiará para llenarlas
            con apoyo de Claude.
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("crear_documento", clear_on_submit=False):
        st.markdown("### Identificación del modelo")
        nombre = st.text_input(
            "Nombre del modelo *",
            help="Ej. 'ESG Stochastic Generator', 'Lapse Rate Model'.",
        )
        model_id = st.text_input(
            "Model ID *",
            help=(
                "Identificador institucional único. Si tu organización usa "
                "nomenclatura formal (ej. M07.P07.S03.006.D), úsala aquí."
            ),
        )
        st.caption("Ambos campos son obligatorios. Podrás ajustar el resto en el onboarding.")

        st.markdown("### Fuentes adicionales (opcional)")
        st.caption(
            "Si tienes material existente del modelo — procedimientos, hojas de "
            "cálculo, notas técnicas — DocuMente lo leerá y sugerirá contenido "
            "para las secciones vacías. Formatos: PDF, XLSX, TXT, DOCX."
        )
        fuentes_subidas = st.file_uploader(
            "Adjunta fuentes (opcional)",
            type=["pdf", "xlsx", "xlsm", "txt", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="crear_nuevo_fuentes",
        )

        col_a, col_b, _ = st.columns([1, 1, 2])
        with col_a:
            submit = st.form_submit_button(
                "Crear documento", type="primary", use_container_width=True
            )
        with col_b:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state["pagina"] = "home"
        st.rerun()

    if submit:
        if not nombre.strip() or not model_id.strip():
            st.error("Completa nombre del modelo y model ID antes de continuar.")
            return

        fuentes_payload: list[tuple[BytesIO, str]] = []
        if fuentes_subidas:
            for f in fuentes_subidas:
                fuentes_payload.append((BytesIO(f.getvalue()), f.name))

        uc = _construir_use_case()
        try:
            with st.spinner(
                "Creando documento"
                + (f" y procesando {len(fuentes_payload)} fuente(s)…" if fuentes_payload else "…")
            ):
                doc = uc.ejecutar(
                    nombre_modelo=nombre,
                    model_id=model_id,
                    fuentes_adicionales=fuentes_payload or None,
                )
        except ValueError as e:
            st.error(f"No se pudo crear el documento: {e}")
            return

        st.session_state["documento_actual_id"] = str(doc.id)
        st.session_state["pagina"] = "onboarding"
        st.rerun()
