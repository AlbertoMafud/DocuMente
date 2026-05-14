from __future__ import annotations

import streamlit as st

from src.core.usecases import DetectarModelosProphet, ImportarRegistroProphet
from src.llm import AnthropicClient
from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.theme import SMNYL_COLORS


def _construir_use_cases() -> tuple[DetectarModelosProphet, ImportarRegistroProphet]:
    try:
        llm: AnthropicClient | None = AnthropicClient()
    except Exception:
        llm = None
    repo = DocumentoRepository()
    return DetectarModelosProphet(llm=llm), ImportarRegistroProphet(repo=repo, llm=llm)


def render() -> None:
    header.render(breadcrumbs=["Inicio", "Nueva Ficha Prophet"])

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {SMNYL_COLORS['text']}; margin-bottom: 0.5rem;">
            Nueva Ficha Prophet
        </h1>
        <p style="color: {SMNYL_COLORS['text_muted']}; margin-bottom: 2rem; max-width: 720px;">
            Sube el registro Excel de modelos actuariales. DocuMente detectará los modelos
            disponibles y generará la ficha pre-poblada con los datos del Excel.
        </p>
        """,
        unsafe_allow_html=True,
    )

    archivo = st.file_uploader(
        "Registro de modelos (.xlsx)",
        type=["xlsx", "xlsm"],
        help="El Excel con las hojas Descripcion_General, Detalle Runs, Variables criticas, Conocimiento_Tecnico.",
    )

    if archivo is None:
        st.caption("¿No tienes el formato correcto? Descarga el template desde docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx.")
        if st.button("Cancelar", use_container_width=False):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    xlsx_bytes = archivo.getvalue()

    cache_key = f"prophet_modelos_{archivo.file_id}"
    if cache_key not in st.session_state:
        detector, _ = _construir_use_cases()
        with st.spinner("Detectando modelos en el Excel..."):
            resultado_deteccion = detector.ejecutar(xlsx_bytes)
        st.session_state[cache_key] = resultado_deteccion

    deteccion = st.session_state[cache_key]

    if deteccion.advertencias:
        for adv in deteccion.advertencias:
            st.warning(adv)

    if not deteccion.modelos:
        st.error("No se encontraron modelos en el Excel. Verifica el formato del archivo.")
        if st.button("Cancelar"):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    opciones = {f"{m.nombre} — {m.encargado}": m for m in deteccion.modelos}
    seleccion_key = st.selectbox("Selecciona el modelo a importar", list(opciones.keys()))
    modelo_info = opciones[seleccion_key]

    col_a, col_b, _ = st.columns([1, 1, 2])
    with col_a:
        importar = st.button("Importar ficha", type="primary", use_container_width=True)
    with col_b:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop(cache_key, None)
            st.session_state["pagina"] = "home"
            st.rerun()

    if importar:
        _, uc_importar = _construir_use_cases()
        with st.spinner(f"Importando datos de '{modelo_info.nombre}'..."):
            resultado = uc_importar.ejecutar(
                xlsx_bytes=xlsx_bytes,
                fila_idx=modelo_info.fila_idx,
                nombre_modelo=modelo_info.nombre,
            )

        if resultado.documento is None:
            for adv in resultado.advertencias:
                st.error(adv)
            return

        if resultado.advertencias:
            with st.expander(f"⚠️ {len(resultado.advertencias)} advertencias del import"):
                for adv in resultado.advertencias:
                    st.caption(adv)

        st.success(
            f"Ficha importada: {resultado.secciones_importadas} secciones pre-pobladas, "
            f"{resultado.secciones_vacias} vacías para completar."
        )
        st.session_state.pop(cache_key, None)
        st.session_state["documento_actual_id"] = str(resultado.documento.id)
        st.session_state["pagina"] = "dashboard"
        st.rerun()
