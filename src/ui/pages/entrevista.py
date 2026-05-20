"""Pantalla de entrevista — split layout chat ↔ preview de la sección.

Flujo:
1. Usuario llega aquí desde el dashboard de brechas con `documento_id` y
   `seccion_id` en `st.session_state`.
2. Si no hay estado previo: arranca con `IniciarEntrevista` y muestra la
   primera pregunta de Claude.
3. Cada `chat_input` del usuario dispara `ResponderPregunta`. Auto-guardado
   transparente (cada turno persiste a SQLite).
4. Si Claude marca la sección como completa y el Drafter produce borrador
   suficiente, lo guarda en la sección y muestra una celebración.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import anthropic
import streamlit as st

from src.core.usecases import (
    AdjuntarTablaApendice,
    Drafter,
    IniciarEntrevista,
    InterviewEngine,
    KnowledgeExtractor,
    ResponderPregunta,
    es_seccion_data_heavy,
)
from src.llm import AnthropicClient
from src.storage.repositories import (
    DocumentoRepository,
    EstadoEntrevistaRepository,
)
from src.storage.storage import FilesystemStorage
from src.ui.components import chat_bubble, header, loading_state
from src.ui.theme import SMNYL_COLORS

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _construir_dependencias() -> tuple[IniciarEntrevista, ResponderPregunta, AdjuntarTablaApendice]:
    llm = AnthropicClient()
    engine = InterviewEngine(llm)
    drafter = Drafter(llm)
    extractor = KnowledgeExtractor(llm)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()
    storage = FilesystemStorage(DATA_DIR)
    return (
        IniciarEntrevista(engine, doc_repo, estado_repo),
        ResponderPregunta(engine, drafter, doc_repo, estado_repo, extractor=extractor),
        AdjuntarTablaApendice(storage, doc_repo, estado_repo),
    )


def _render_panel_preview(documento_id: UUID, seccion_id: str) -> None:
    """Panel derecho: preview de la sección que se está construyendo."""
    repo = DocumentoRepository()
    documento = repo.obtener(documento_id)
    if documento is None:
        st.warning("Documento no encontrado.")
        return
    seccion = documento.seccion_por_id(seccion_id)
    if seccion is None:
        st.warning("Sección no encontrada.")
        return

    text_color = SMNYL_COLORS["text"]
    muted = SMNYL_COLORS["text_muted"]

    st.markdown(
        f"<div style='font-size: 0.7rem; color: {muted}; "
        "text-transform: uppercase; letter-spacing: 0.05em;'>SECCIÓN ACTIVA</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-family: var(--font-display); font-size: 1.4rem; "
        f"font-weight: 600; color: {text_color}; margin-bottom: 4px;'>"
        f"{seccion.numero} {seccion.nombre}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='color: {muted}; font-size: 0.875rem; "
        "margin-bottom: 16px;'>"
        f"{seccion.intencion}</div>",
        unsafe_allow_html=True,
    )

    completitud_label = {
        "vacia": ("Vacía", SMNYL_COLORS["danger"]),
        "parcial": ("Parcial", SMNYL_COLORS["warning"]),
        "completa": ("Completa", SMNYL_COLORS["success"]),
        "omitida": ("Omitida", SMNYL_COLORS["text_muted"]),
    }[seccion.completitud]
    st.markdown(
        f"<span style='display: inline-block; padding: 4px 12px; "
        f"border-radius: 999px; background: {completitud_label[1]}1a; "
        f"color: {completitud_label[1]}; font-size: 0.75rem; "
        "font-weight: 600; margin-bottom: 16px;'>"
        f"{completitud_label[0]}</span>",
        unsafe_allow_html=True,
    )

    if seccion.contenido:
        st.markdown("**Borrador actual:**")
        st.markdown(seccion.contenido)
    else:
        st.info(
            "Esta sección aún no tiene contenido. La entrevista llenará "
            "el borrador conforme avancen."
        )

    # Listar apéndices ya vinculados a esta sección
    apendices_seccion = [a for a in documento.apendices if a.seccion_origen_id == seccion_id]
    if apendices_seccion:
        st.markdown("---")
        st.markdown("**Apéndices vinculados:**")
        for ap in apendices_seccion:
            archivo_meta = (
                f"<span style='color: {muted}; font-size: 0.75rem;'>"
                f"({ap.nombre_archivo_original})</span>"
            )
            st.markdown(
                f"- 📎 **{ap.titulo}** {archivo_meta}",
                unsafe_allow_html=True,
            )


def render() -> None:
    documento_id_str = st.session_state.get("documento_actual_id")
    seccion_id = st.session_state.get("seccion_entrevista_id")

    if not documento_id_str or not seccion_id:
        header.render(breadcrumbs=["Inicio", "Entrevista"])
        st.warning(
            "No hay sección seleccionada para entrevistar. Vuelve al dashboard para elegir una."
        )
        if st.button("Volver al dashboard", type="primary"):
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        return

    documento_id = UUID(documento_id_str)
    repo = DocumentoRepository()
    documento = repo.obtener(documento_id)
    if documento is None:
        header.render(breadcrumbs=["Inicio", "Entrevista"])
        st.error("Documento no encontrado.")
        return
    seccion = documento.seccion_por_id(seccion_id)
    if seccion is None:
        header.render(breadcrumbs=["Inicio", "Entrevista"])
        st.error(f"Sección '{seccion_id}' no existe en este documento.")
        return

    nombre_modelo = documento.metadata_modelo.nombre_modelo or "Documento sin nombre"
    header.render(
        breadcrumbs=[
            "Inicio",
            nombre_modelo,
            "Entrevista",
            f"{seccion.numero} {seccion.nombre}",
        ]
    )

    iniciar_uc, responder_uc, adjuntar_uc = _construir_dependencias()

    # Asegurar estado conversacional cargado / iniciado
    estado_repo = EstadoEntrevistaRepository()
    estado = estado_repo.obtener(documento_id_str, seccion_id)

    if estado is None:
        with loading_state.claude_pensando("Iniciando entrevista"):
            try:
                turno = iniciar_uc.ejecutar(documento_id, seccion_id)
            except RuntimeError as e:
                st.error(str(e))
                return
            except anthropic.APIError as e:
                st.error(f"Error al llamar a Claude: {e}")
                return
        estado = turno.estado

    # Layout split: chat (izq.) + preview (der.)
    col_chat, col_preview = st.columns([1.4, 1])

    with col_chat:
        st.markdown(
            "<div style='font-family: var(--font-display); font-size: 1.5rem; "
            "font-weight: 600; margin-bottom: 4px;'>Entrevista</div>",
            unsafe_allow_html=True,
        )
        muted = SMNYL_COLORS["text_muted"]
        st.markdown(
            f"<div style='color: {muted}; font-size: 0.875rem; "
            "margin-bottom: 16px;'>"
            "Auto-guardado activo. Puedes cerrar y retomar después."
            "</div>",
            unsafe_allow_html=True,
        )

        # Drop zone de apéndices — disponible en TODAS las secciones (B.3).
        # Soporta: Excel/CSV (multi-hoja, 1 apéndice por hoja),
        # PDF (cada página se embebe como imagen al exportar),
        # y fórmulas LaTeX (botón aparte abajo).
        es_data_heavy = es_seccion_data_heavy(seccion_id)
        label_expander = (
            "📎 Adjuntar apéndice (sección típicamente data-heavy)"
            if es_data_heavy
            else "📎 Adjuntar apéndice (opcional)"
        )
        with st.expander(label_expander, expanded=False):
            st.caption(
                "**Tabla (Excel/CSV)** — cada hoja se guarda como un apéndice. "
                "**PDF** — cada página se embebe como imagen al exportar; útil para "
                "fórmulas con layout complejo, gráficas o diagramas. "
                "**Fórmula LaTeX** — escribe la fórmula y se renderiza como imagen "
                "(usa el botón al final del expander)."
            )
            titulo_tabla = st.text_input(
                "Título descriptivo (base del apéndice)",
                placeholder="Ej. Tabla de mortalidad SOA 2017 — Producto NIL",
                key=f"titulo_apendice_{seccion_id}",
                help=(
                    "Si el Excel tiene varias hojas, cada apéndice agrega "
                    "el nombre de la hoja al final del título."
                ),
            )
            archivo_tabla = st.file_uploader(
                "Archivo (.xlsx, .xls, .csv, .pdf)",
                type=["xlsx", "xls", "csv", "pdf"],
                key=f"upload_apendice_{seccion_id}",
                label_visibility="collapsed",
            )
            if archivo_tabla is not None:
                if not titulo_tabla.strip():
                    st.warning("Ingresa un título descriptivo antes de procesar el archivo.")
                elif st.button(
                    "Procesar y crear apéndice(s)",
                    type="primary",
                    key=f"btn_apendice_{seccion_id}",
                ):
                    from io import BytesIO

                    es_pdf = archivo_tabla.name.lower().endswith(".pdf")
                    if es_pdf:
                        # PDF como apéndice (C.1): cada página se embebe como imagen.
                        from src.core.usecases import AdjuntarPdfApendice
                        from src.storage.storage import FilesystemStorage

                        pdf_uc = AdjuntarPdfApendice(
                            storage=FilesystemStorage(DATA_DIR),
                            doc_repo=DocumentoRepository(),
                            estado_repo=adjuntar_uc.estado_repo,
                        )
                        with st.spinner("Procesando PDF y creando apéndice…"):
                            try:
                                resultado_pdf = pdf_uc.ejecutar(
                                    documento=documento,
                                    seccion=seccion,
                                    archivo=BytesIO(archivo_tabla.getvalue()),
                                    nombre_original=archivo_tabla.name,
                                    titulo=titulo_tabla.strip(),
                                )
                            except (ValueError, OSError) as e:
                                st.error(f"No se pudo procesar el PDF: {e}")
                                return
                        st.toast(
                            f"Apéndice PDF '{resultado_pdf.apendice.titulo}' creado "
                            f"({resultado_pdf.n_paginas} página(s))",
                            icon="📎",
                        )
                    else:
                        with st.spinner("Leyendo hojas y creando apéndice(s)…"):
                            try:
                                resultados = adjuntar_uc.ejecutar_multihoja(
                                    documento=documento,
                                    seccion=seccion,
                                    archivo=BytesIO(archivo_tabla.getvalue()),
                                    nombre_original=archivo_tabla.name,
                                    titulo_base=titulo_tabla.strip(),
                                )
                            except (ValueError, OSError) as e:
                                st.error(f"No se pudo leer la tabla: {e}")
                                return
                        if len(resultados) == 1:
                            r = resultados[0]
                            st.toast(
                                f"Apéndice '{r.apendice.titulo}' creado "
                                f"({r.tabla.n_filas}×{r.tabla.n_columnas})",
                                icon="📎",
                            )
                        else:
                            st.toast(
                                f"{len(resultados)} apéndices creados desde "
                                f"{len(resultados)} hoja(s) del Excel.",
                                icon="📎",
                            )
                    st.rerun()

            # --- Apéndice fórmula LaTeX (C.1) ---
            st.markdown("---")
            st.markdown("**Insertar fórmula matemática (LaTeX)**")
            st.caption(
                "Escribe la fórmula sin delimitadores `$`. Se renderizará como imagen "
                "nítida en el .docx final. Subset soportado: fracciones, integrales, "
                "sumatorias, símbolos griegos, índices/exponentes."
            )
            titulo_formula = st.text_input(
                "Título de la fórmula",
                placeholder="Ej. Valor presente actuarial",
                key=f"titulo_formula_{seccion_id}",
            )
            latex_source = st.text_area(
                "Source LaTeX (sin `$`)",
                placeholder=r"\bar{A}_x = \int_0^\infty e^{-\delta t} \, _tp_x \, \mu_{x+t} \, dt",
                key=f"latex_source_{seccion_id}",
                height=100,
            )
            if latex_source.strip():
                with st.container(border=True):
                    st.markdown("**Preview** (KaTeX):")
                    try:
                        st.latex(latex_source)
                    except Exception:
                        st.caption("_(preview no disponible — verifica sintaxis)_")
            if st.button(
                "Insertar fórmula como apéndice",
                key=f"btn_formula_{seccion_id}",
                disabled=not (latex_source.strip() and titulo_formula.strip()),
            ):
                from src.core.usecases import AdjuntarFormulaApendice

                formula_uc = AdjuntarFormulaApendice(
                    doc_repo=DocumentoRepository(),
                    estado_repo=adjuntar_uc.estado_repo,
                )
                with st.spinner("Renderizando fórmula…"):
                    try:
                        resultado_formula = formula_uc.ejecutar(
                            documento=documento,
                            seccion=seccion,
                            latex_source=latex_source,
                            titulo=titulo_formula.strip(),
                        )
                    except ValueError as e:
                        st.error(f"No se pudo crear la fórmula: {e}")
                        return
                st.toast(
                    f"Apéndice fórmula '{resultado_formula.apendice.titulo}' creado",
                    icon="📐",
                )
                st.rerun()

        # Renderizar historial — saltamos el primer mensaje "kickoff"
        # porque es interno, el usuario no lo escribió.
        for i, m in enumerate(estado.mensajes):
            if i == 0 and m.rol == "user":
                continue
            chat_bubble.render(m.rol, m.contenido)

        # Si la sección ya está cerrada con borrador, mostrar celebración
        if estado.cerrada and seccion.completitud == "completa":
            st.success(
                f"Sección **{seccion.numero} {seccion.nombre}** completada. "
                "El borrador profesional ya está pegado en el documento "
                "(panel derecho)."
            )
            if st.button("Volver al dashboard", type="primary"):
                st.session_state["pagina"] = "dashboard"
                st.session_state.pop("seccion_entrevista_id", None)
                st.rerun()
        else:
            # Input de chat estándar
            entrada = st.chat_input("Escribe tu respuesta…")
            if entrada:
                with loading_state.claude_pensando("Claude está respondiendo"):
                    try:
                        turno = responder_uc.ejecutar(documento_id, seccion_id, entrada)
                    except anthropic.APIError as e:
                        st.error(f"Error al llamar a Claude: {e}")
                        return
                if turno.seccion_cerrada:
                    st.toast("Sección completa — borrador generado", icon="🎉")
                st.rerun()

        # Botón para pausar y volver
        col_back, _ = st.columns([1, 3])
        with col_back:
            if st.button("Pausar y volver", use_container_width=True):
                st.session_state["pagina"] = "dashboard"
                st.session_state.pop("seccion_entrevista_id", None)
                st.rerun()

    with col_preview, st.container(border=True):
        _render_panel_preview(documento_id, seccion_id)
