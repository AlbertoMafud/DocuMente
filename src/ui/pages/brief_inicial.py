"""Pantalla del Brief Inicial — cuestionario opcional de 10 preguntas.

Se muestra después del onboarding y antes del dashboard, solo para documentos
recién creados (las secciones aún están vacías). Si el doc ya tiene contenido,
se salta automáticamente.

Las respuestas se convierten en borradores `[Borrador — revisar]` para las
secciones mapeadas, reduciendo el trabajo de entrevista posterior.
"""

from __future__ import annotations

from uuid import UUID

import streamlit as st

from src.core.usecases.aplicar_brief import PREGUNTAS_BRIEF, AplicarBrief
from src.llm import AnthropicClient
from src.storage.repositories import DocumentoRepository
from src.ui.components import back_button, header
from src.ui.theme import SMNYL_COLORS


def _doc_tiene_secciones_pobladas(documento_id: UUID, repo: DocumentoRepository) -> bool:
    """True si el documento ya tiene contenido en alguna sección — evitar
    sobreescribir trabajo previo si el flujo de routing se ejecuta de nuevo."""
    documento = repo.obtener(documento_id)
    if documento is None:
        return False
    return any(s.completitud != "vacia" for s in documento.secciones)


def render() -> None:
    documento_id_str = st.session_state.get("documento_actual_id")
    if not documento_id_str:
        header.render(breadcrumbs=["Inicio", "Brief inicial"])
        st.warning("No hay documento seleccionado.")
        if st.button("Volver al inicio", type="primary"):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    documento_id = UUID(documento_id_str)
    repo = DocumentoRepository()
    documento = repo.obtener(documento_id)
    if documento is None:
        header.render(breadcrumbs=["Inicio", "Brief inicial"])
        st.error("Documento no encontrado.")
        return

    nombre_modelo = documento.metadata_modelo.nombre_modelo or "Documento sin nombre"
    header.render(breadcrumbs=["Inicio", nombre_modelo, "Brief inicial"])

    back_button.render(destino="dashboard", etiqueta="← Saltar e ir al dashboard", key="brief_back")

    text = SMNYL_COLORS["text"]
    muted = SMNYL_COLORS["text_muted"]
    primary = SMNYL_COLORS["primary"]

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {text};
            margin-bottom: 0.25rem;">Brief inicial del modelo</h1>
        <p style="color: {muted}; margin-bottom: 0.75rem; max-width: 760px;">
            10 preguntas de alto impacto. Tus respuestas se convierten en borradores
            para las secciones de mayor valor del documento, reduciendo el trabajo
            de entrevista posterior. <strong>Todo es opcional</strong> — puedes
            saltar las preguntas que no apliquen y completarlas más adelante.
        </p>
        <div style="background: {SMNYL_COLORS["bg_soft"]}; border-left: 3px solid {primary};
            padding: 0.75rem 1rem; margin-bottom: 1.5rem; color: {text};
            font-size: 0.875rem; border-radius: 4px;">
            <strong>Tip:</strong> respuestas de 1-3 frases son suficientes. DocuMente las
            convertirá en borradores estructurados; tú los refinarás después.
        </div>
        """,
        unsafe_allow_html=True,
    )

    respuestas: dict[int, str] = {}

    with st.form("brief_inicial_form"):
        for pregunta in PREGUNTAS_BRIEF:
            respuestas[pregunta.numero] = st.text_area(
                f"**{pregunta.numero}. {pregunta.texto}**",
                placeholder=pregunta.placeholder,
                height=80,
                key=f"brief_q_{pregunta.numero}",
            )

        col_a, col_b, _ = st.columns([2, 1, 1])
        with col_a:
            submit = st.form_submit_button(
                "Generar borradores y continuar",
                type="primary",
                use_container_width=True,
            )
        with col_b:
            saltar = st.form_submit_button("Saltar", use_container_width=True)

    if saltar:
        st.session_state["pagina"] = "dashboard"
        st.rerun()

    if submit:
        respuestas_no_vacias = {k: v for k, v in respuestas.items() if v and v.strip()}
        if not respuestas_no_vacias:
            st.info(
                "No llenaste ninguna pregunta. Saltando directo al dashboard…",
                icon="ℹ️",
            )
            st.session_state["pagina"] = "dashboard"
            st.rerun()
            return

        try:
            llm = AnthropicClient()
        except Exception as e:
            st.error(
                f"Falta configuración de Anthropic API ({e}). Saltando al dashboard "
                "sin generar borradores."
            )
            st.session_state["pagina"] = "dashboard"
            st.rerun()
            return

        with st.spinner(
            f"Generando borradores a partir de {len(respuestas_no_vacias)} respuesta(s)…"
        ):
            aplicadas = AplicarBrief(llm).ejecutar(documento, respuestas_no_vacias)
            repo.guardar(documento)

        st.success(
            f"{aplicadas} sección(es) pre-poblada(s) con borrador. Revisa y edita en el dashboard.",
            icon="✅",
        )
        st.session_state["pagina"] = "dashboard"
        st.rerun()
