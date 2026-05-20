"""Pantalla de importar documento .docx existente.

Renderiza:
- Header con breadcrumbs + botón "Volver".
- Drop zone para subir 1 .docx ancla + N fuentes adicionales (PDF/XLSX/TXT/DOCX).
- Después de procesarlo: redirige al dashboard vía session_state.

Las fuentes adicionales se procesan por el reader que les corresponde, se
guardan como FuenteContexto en el Documento, y alimentan SugerenciasMultiFuente
que pre-popula secciones vacías con borradores automáticos.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import streamlit as st

from src.core.usecases import GapAnalyzer, ImportarDocumento
from src.docs.readers.anchor_reader import AnchorReader
from src.llm import AnthropicClient
from src.storage.repositories import DocumentoRepository
from src.storage.storage import FilesystemStorage
from src.ui.components import back_button, empty_state, header
from src.ui.theme import SMNYL_COLORS

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _intentar_construir_llm() -> tuple[AnthropicClient | None, str | None]:
    """Devuelve (cliente, mensaje_error). Solo uno está poblado."""
    try:
        return AnthropicClient(), None
    except Exception as e:
        return None, str(e)


def _construir_use_case(llm: AnthropicClient | None) -> ImportarDocumento:
    storage = FilesystemStorage(DATA_DIR)
    return ImportarDocumento(
        storage=storage,
        reader=AnchorReader(),  # despacha .docx vs .pdf automáticamente
        repo=DocumentoRepository(),
        analyzer=GapAnalyzer(),
        llm=llm,
    )


def render() -> None:
    header.render(breadcrumbs=["Inicio", "Importar documento"])

    back_button.render(destino="home", etiqueta="← Volver al inicio", key="importar_back")

    llm, llm_error = _intentar_construir_llm()
    if llm is None:
        st.warning(
            "El asistente de IA no está disponible "
            f"({llm_error or 'sin configuración de Anthropic API'}). "
            "Podrás importar y trabajar el documento, pero las sugerencias "
            "automáticas a partir de fuentes adicionales se omitirán.",
            icon="⚠️",
        )

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {SMNYL_COLORS["text"]};
            margin-bottom: 0.5rem;">Importar documento existente</h1>
        <p style="color: {SMNYL_COLORS["text_muted"]}; margin-bottom: 2rem;
            max-width: 720px;">
            Sube un archivo <code>.docx</code> o <code>.pdf</code> con documentación
            de modelo. DocuMente lo analizará contra el Model Development Template
            oficial de NYL e identificará brechas para que las completes con apoyo
            de Claude.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 1. Documento ancla (.docx o .pdf)")
    archivo = st.file_uploader(
        "Arrastra el archivo .docx o .pdf principal aquí",
        type=["docx", "pdf"],
        accept_multiple_files=False,
        help=(
            "Este es el documento que da estructura: DocuMente lo parsea contra "
            "el Model Development Template oficial NYL e identifica brechas. "
            "Si subes un PDF, la extracción puede ser menos precisa que con DOCX "
            "(no tiene info de estilos)."
        ),
        label_visibility="visible",
        key="importar_anchor",
    )
    if archivo is not None and archivo.name.lower().endswith(".pdf"):
        st.info(
            "PDF detectado — DocuMente usa heurística para reconocer secciones. "
            "Revisa el resultado en el dashboard; las secciones no detectadas "
            "quedarán vacías y podrás llenarlas con la entrevista o con fuentes "
            "adicionales.",
            icon="ℹ️",
        )

    st.markdown(
        "<div style='margin: 1rem 0;'></div>",
        unsafe_allow_html=True,
    )

    st.markdown("### 2. Fuentes adicionales (opcional)")
    st.markdown(
        f"<p style='color: {SMNYL_COLORS['text_muted']}; font-size: 0.875rem;"
        f" margin-bottom: 0.75rem;'>"
        f"Adjunta material complementario que DocuMente leerá para sugerir "
        f"contenido en las secciones vacías: procedimientos, instructivos, hojas "
        f"de cálculo, notas técnicas. Formatos soportados: PDF, XLSX, TXT, DOCX."
        f"</p>",
        unsafe_allow_html=True,
    )
    fuentes_subidas = st.file_uploader(
        "Arrastra una o más fuentes adicionales aquí",
        type=["pdf", "xlsx", "xlsm", "txt", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="importar_fuentes",
    )

    if archivo is None and not fuentes_subidas:
        empty_state.render(
            titulo="Aún no has subido un documento",
            descripcion=(
                "Selecciona o arrastra el .docx ancla para empezar. Opcionalmente "
                "agrega fuentes adicionales para que DocuMente pueda sugerirte "
                "contenido para las secciones vacías."
            ),
            icono="📄",
        )
        return

    if archivo is None:
        st.warning(
            "Falta el documento .docx ancla. Las fuentes adicionales solas no "
            "alcanzan: necesitamos uno para identificar la estructura.",
            icon="⚠️",
        )
        return

    # Mostrar metadata del archivo principal
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
                        Ancla · {archivo.size / 1024:,.1f} KB
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if fuentes_subidas:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-weight: 600; color: {SMNYL_COLORS['text']};"
                f" margin-bottom: 0.5rem;'>"
                f"📚 {len(fuentes_subidas)} fuente(s) adicional(es)</div>",
                unsafe_allow_html=True,
            )
            for f in fuentes_subidas:
                st.markdown(
                    f"<div style='color: {SMNYL_COLORS['text_muted']}; "
                    f"font-size: 0.875rem;'>"
                    f"&nbsp;&nbsp;• {f.name} ({f.size / 1024:,.1f} KB)</div>",
                    unsafe_allow_html=True,
                )

    if st.button("Analizar documento", type="primary", use_container_width=False):
        n_fuentes = len(fuentes_subidas) if fuentes_subidas else 0
        spinner_msg = (
            f"Parseando documento y procesando {n_fuentes} fuente(s)…"
            if n_fuentes
            else "Parseando documento y detectando secciones... esto toma 5-15s."
        )
        with st.spinner(spinner_msg):
            uc = _construir_use_case(llm)
            buffer = BytesIO(archivo.getvalue())
            fuentes_payload: list[tuple[BytesIO, str]] = []
            if fuentes_subidas:
                for f in fuentes_subidas:
                    fuentes_payload.append((BytesIO(f.getvalue()), f.name))
            resultado = uc.ejecutar(
                buffer,
                archivo.name,
                fuentes_adicionales=fuentes_payload or None,
            )

        # Guardar en session_state para que el dashboard lo lea
        st.session_state["documento_actual_id"] = str(resultado.documento.id)
        # Banner del dashboard con conteos y advertencias
        st.session_state["onboarding_resultado"] = {
            "secciones_prellenadas": resultado.secciones_pre_pobladas,
            "fuentes_extraidas": resultado.fuentes_procesadas,
            "fuentes_descartadas": list(resultado.fuentes_descartadas),
            "advertencias": list(resultado.advertencias),
            "llm_disponible": resultado.llm_disponible,
        }
        st.session_state["pagina"] = "dashboard"
        mensaje = (
            f"Documento analizado: "
            f"{sum(1 for s in resultado.documento.secciones if s.contenido)} "
            f"secciones detectadas, {len(resultado.brechas)} brechas."
        )
        if resultado.fuentes_procesadas:
            mensaje += (
                f" {resultado.fuentes_procesadas} fuente(s) procesada(s); "
                f"{resultado.secciones_pre_pobladas} sección(es) pre-poblada(s) "
                f"con borrador automático."
            )
        st.success(mensaje)
        st.rerun()
