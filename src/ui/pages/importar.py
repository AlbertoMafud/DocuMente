"""Pantalla de importar documento .docx existente.

Renderiza:
- Header con breadcrumbs.
- Drop zone para subir un .docx.
- Después de procesarlo: redirige al dashboard de brechas vía session_state.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import streamlit as st

from src.core.usecases import GapAnalyzer, ImportarDocumento
from src.docs.reader import DocxReader
from src.storage.repositories import DocumentoRepository
from src.storage.storage import FilesystemStorage
from src.ui.components import empty_state, header
from src.ui.theme import SMNYL_COLORS

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _construir_use_case() -> ImportarDocumento:
    storage = FilesystemStorage(DATA_DIR)
    return ImportarDocumento(
        storage=storage,
        reader=DocxReader(),
        repo=DocumentoRepository(),
        analyzer=GapAnalyzer(),
    )


def render() -> None:
    header.render(breadcrumbs=["Inicio", "Importar documento"])

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {SMNYL_COLORS["text"]};
            margin-bottom: 0.5rem;">Importar documento existente</h1>
        <p style="color: {SMNYL_COLORS["text_muted"]}; margin-bottom: 2rem;
            max-width: 720px;">
            Sube un archivo <code>.docx</code> con documentación de modelo.
            DocuMente lo analizará contra el Model Development Template oficial
            de NYL e identificará brechas para que las completes con apoyo de Claude.
        </p>
        """,
        unsafe_allow_html=True,
    )

    archivo = st.file_uploader(
        "Arrastra un archivo .docx aquí",
        type=["docx"],
        accept_multiple_files=False,
        help="Solo aceptamos archivos .docx (Word). Tamaño máximo: 25 MB.",
        label_visibility="visible",
    )

    if archivo is None:
        empty_state.render(
            titulo="Aún no has subido un documento",
            descripcion=(
                "Selecciona o arrastra un archivo .docx para empezar. DocuMente lo "
                "parsea, identifica qué secciones del Model Development Template "
                "están presentes y cuáles faltan."
            ),
            icono="📄",
        )
        return

    # Mostrar metadata del archivo subido
    st.markdown(
        "<div style='margin: 1.5rem 0;'></div>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 2rem;">📎</div>
                <div>
                    <div style="font-weight: 600; color: {SMNYL_COLORS["text"]};">
                        {archivo.name}
                    </div>
                    <div style="color: {SMNYL_COLORS["text_muted"]}; font-size: 0.875rem;">
                        {archivo.size / 1024:,.1f} KB
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Analizar documento", type="primary", use_container_width=False):
        with st.spinner("Parseando documento y detectando secciones... esto toma 5-15s."):
            uc = _construir_use_case()
            buffer = BytesIO(archivo.getvalue())
            resultado = uc.ejecutar(buffer, archivo.name)

        # Guardar en session_state para que el dashboard lo lea
        st.session_state["documento_actual_id"] = str(resultado.documento.id)
        st.session_state["pagina"] = "dashboard"
        st.success(
            f"Documento analizado: {sum(1 for s in resultado.documento.secciones if s.contenido)} "
            f"secciones detectadas, {len(resultado.brechas)} brechas."
        )
        st.rerun()
