"""Dashboard de brechas — vista principal después de importar un documento.

Muestra:
- Header con breadcrumbs y nombre del modelo.
- Resumen visual: completitud global, brechas por severidad.
- Grid de SectionCard con todas las secciones del template.
- Lista priorizada de brechas críticas con explicación + sugerencia.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path as _Path
from uuid import UUID

import streamlit as st

from src.config import get_settings
from src.core.models import Brecha, Documento
from src.core.models.documento import EstadoDocumento
from src.core.rules import DocumentStateMachine
from src.core.usecases import (
    MOTIVOS_OMISION,
    CambiarEstadoDocumento,
    ExportarDocumento,
    GapAnalyzer,
    OmitirSeccion,
    RegistrarSignoff,
    TransicionRechazada,
)
from src.llm import AnthropicClient
from src.storage.repositories import DocumentoRepository
from src.ui.components import gap_badge, header, seccion_card
from src.ui.theme import SMNYL_COLORS

_TEMPLATE_PATH = (
    _Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "docs"
    / "templates"
    / "model_development_smnyl_final.docx"
)
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

_ETIQUETA_ESTADO: dict[EstadoDocumento, tuple[str, str]] = {
    "draft": ("Borrador", SMNYL_COLORS["text_muted"]),
    "in_review": ("En revisión", SMNYL_COLORS["warning"]),
    "approved": ("Aprobado", SMNYL_COLORS["info"]),
    "published": ("Publicado", SMNYL_COLORS["success"]),
    "retired": ("Retirado", SMNYL_COLORS["danger"]),
}

_BOTON_DESTINO: dict[tuple[EstadoDocumento, EstadoDocumento], str] = {
    ("draft", "in_review"): "Pasar a En Revisión",
    ("in_review", "approved"): "Aprobar",
    ("in_review", "draft"): "Rechazar (volver a Borrador)",
    ("approved", "published"): "Publicar",
    ("approved", "in_review"): "Retractar a En Revisión",
    ("published", "retired"): "Retirar modelo",
}


@st.dialog("Exportar documento")
def _dialog_exportar_docx(documento_id_str: str) -> None:
    """Modal para elegir idioma del .docx y disparar la generación."""
    doc_id = UUID(documento_id_str)
    bytes_key = f"docx_bytes_{documento_id_str}"
    nombre_key = f"docx_nombre_{documento_id_str}"

    st.markdown(
        "Selecciona el idioma del documento exportado. La traducción al inglés "
        "usa Claude para mantener el tono institucional formal y preservar "
        "vocabulario técnico-actuarial."
    )

    idioma_label = st.radio(
        "Idioma",
        options=["Español", "English (US corporate)"],
        key=f"export_idioma_{documento_id_str}",
        horizontal=True,
    )
    idioma = "en" if idioma_label.startswith("English") else "es"

    if idioma == "en":
        st.caption(
            "La traducción dispara llamadas a Claude (~$0.01–0.05 USD según tamaño "
            "del documento). El borrador en español NO se modifica — la traducción "
            "vive solo en el .docx generado."
        )

    col_cancel, col_go = st.columns(2)
    if col_cancel.button(
        "Cancelar", use_container_width=True, key=f"export_cancel_{documento_id_str}"
    ):
        st.rerun()

    if col_go.button(
        "Generar DOCX",
        type="primary",
        use_container_width=True,
        key=f"export_go_{documento_id_str}",
    ):
        if not _TEMPLATE_PATH.exists():
            st.error(f"Plantilla maestra no encontrada en {_TEMPLATE_PATH}.")
            return
        try:
            spinner_msg = (
                "Traduciendo y generando DOCX con marca SMNYL…"
                if idioma == "en"
                else "Generando DOCX con marca SMNYL…"
            )
            with st.spinner(spinner_msg):
                resultado = _build_export_uc(doc_id).ejecutar(
                    doc_id,
                    actor="default",
                    idioma_objetivo=idioma,  # type: ignore[arg-type]
                )
            st.session_state[bytes_key] = resultado.contenido
            st.session_state[nombre_key] = resultado.nombre_archivo
            st.toast("DOCX generado.", icon="📄")
            st.rerun()
        except Exception as e:
            st.error(f"Error al exportar: {e}")


@st.dialog("Editar metadata del modelo")
def _dialog_editar_metadata(documento_id_str: str) -> None:
    """Modal con form para editar los campos clave de la metadata del modelo."""
    repo = DocumentoRepository()
    doc_id = UUID(documento_id_str)
    doc = repo.obtener(doc_id)
    if doc is None:
        st.error("Documento no encontrado.")
        return
    meta = doc.metadata_modelo

    st.caption(
        "Estos campos alimentan la portada y la tabla de Model Profile del DOCX exportado. "
        "Cualquier cambio queda registrado en el audit trail."
    )

    with st.form(key=f"form_meta_{documento_id_str}"):
        nombre = st.text_input(
            "Nombre del modelo *",
            value=meta.nombre_modelo,
            placeholder="Ej. Cálculo de Overrun de Gasto",
        )
        col_a, col_b = st.columns(2)
        with col_a:
            model_id = st.text_input("Model ID", value=meta.model_id)
            fae = st.text_input("FAE (Functional Area Executive)", value=meta.fae)
            current_version = st.text_input("Versión actual", value=meta.current_version)
        with col_b:
            model_class = st.text_input(
                "Model Class",
                value=meta.model_class,
                placeholder="Actuarial, Statistical, …",
            )
            model_owner = st.text_input("Model Owner", value=meta.model_owner)
            implementation_platform = st.text_input(
                "Plataforma",
                value=meta.implementation_platform,
                placeholder="Excel, Prophet, R…",
            )

        tier_opciones = [
            "(no especificado)",
            "low",
            "medium_minus",
            "medium",
            "high",
            "very_high",
            "very_high_plus",
            "critical",
        ]
        tier_actual = meta.inherent_risk_tier or "(no especificado)"
        tier_idx = tier_opciones.index(tier_actual) if tier_actual in tier_opciones else 0
        tier = st.selectbox("Inherent Risk Tier", options=tier_opciones, index=tier_idx)

        col_cancel, col_save = st.columns(2)
        cancelar = col_cancel.form_submit_button("Cancelar", use_container_width=True)
        guardar = col_save.form_submit_button(
            "Guardar cambios", type="primary", use_container_width=True
        )

    if cancelar:
        st.rerun()

    if guardar:
        cambios: list[str] = []
        if nombre.strip() != meta.nombre_modelo:
            cambios.append(f"nombre_modelo: '{meta.nombre_modelo}' → '{nombre.strip()}'")
            meta.nombre_modelo = nombre.strip()
        if model_id.strip() != meta.model_id:
            cambios.append(f"model_id: '{meta.model_id}' → '{model_id.strip()}'")
            meta.model_id = model_id.strip()
        if model_class.strip() != meta.model_class:
            cambios.append(f"model_class: '{meta.model_class}' → '{model_class.strip()}'")
            meta.model_class = model_class.strip()
        if fae.strip() != meta.fae:
            cambios.append(f"fae: '{meta.fae}' → '{fae.strip()}'")
            meta.fae = fae.strip()
        if model_owner.strip() != meta.model_owner:
            cambios.append(f"model_owner: '{meta.model_owner}' → '{model_owner.strip()}'")
            meta.model_owner = model_owner.strip()
        if current_version.strip() != meta.current_version:
            cambios.append(
                f"current_version: '{meta.current_version}' → '{current_version.strip()}'"
            )
            meta.current_version = current_version.strip()
        if implementation_platform.strip() != meta.implementation_platform:
            cambios.append(
                f"implementation_platform: '{meta.implementation_platform}' "
                f"→ '{implementation_platform.strip()}'"
            )
            meta.implementation_platform = implementation_platform.strip()

        nuevo_tier = None if tier == "(no especificado)" else tier
        if nuevo_tier != meta.inherent_risk_tier:
            cambios.append(f"inherent_risk_tier: {meta.inherent_risk_tier} → {nuevo_tier}")
            meta.inherent_risk_tier = nuevo_tier  # type: ignore[assignment]

        if not cambios:
            st.info("Sin cambios que guardar.")
            return

        from src.core.models import EventoAuditoria

        doc.registrar_evento(
            EventoAuditoria(
                actor=doc.user_id,
                tipo="metadata_actualizada",
                descripcion=f"Metadata actualizada: {len(cambios)} campo(s) modificados.",
                metadata={"cambios": "; ".join(cambios)[:480]},
            )
        )
        repo.guardar(doc)
        st.toast("Metadata actualizada.", icon="✏️")
        st.rerun()


@st.dialog("Omitir sección")
def _dialog_omitir_seccion(
    documento_id_str: str,
    seccion_id: str,
    seccion_nombre: str,
    seccion_intencion: str = "",
) -> None:
    """Modal para capturar motivo y confirmar omisión de la sección."""
    st.markdown(
        f"Marcando **{seccion_nombre}** como omitida. "
        "Quedará registrada en el audit trail con tu justificación y el "
        "documento podrá pasar a revisión sin completarla."
    )
    if seccion_intencion:
        st.markdown(
            f"<div style='padding: 10px 14px; background: {SMNYL_COLORS['bg_soft']};"
            f" border-left: 3px solid {SMNYL_COLORS['primary']};"
            f" border-radius: 4px; margin: 8px 0 16px;"
            f" font-size: 0.875rem; color: {SMNYL_COLORS['text']};'>"
            f"<strong style='color: {SMNYL_COLORS['text_muted']};"
            f" font-size: 0.7rem; text-transform: uppercase;"
            f" letter-spacing: 0.05em;'>Qué captura esta sección</strong><br>"
            f"{seccion_intencion}</div>",
            unsafe_allow_html=True,
        )
    motivo_seleccionado = st.selectbox(
        "Motivo",
        options=MOTIVOS_OMISION,
        key=f"motivo_select_{seccion_id}",
    )
    if motivo_seleccionado == "Otro (especificar)":
        motivo_libre = st.text_area(
            "Especifica el motivo",
            key=f"motivo_libre_{seccion_id}",
            placeholder="Describe brevemente por qué se omite esta sección…",
        )
        motivo_final = motivo_libre.strip()
    else:
        comentario = st.text_area(
            "Comentario adicional (opcional)",
            key=f"comentario_{seccion_id}",
            placeholder="Detalles si quieres agregarlos…",
        )
        motivo_final = motivo_seleccionado
        if comentario.strip():
            motivo_final = f"{motivo_seleccionado} — {comentario.strip()}"

    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancelar", use_container_width=True, key=f"cancel_omitir_{seccion_id}"):
            st.rerun()
    with col_confirm:
        if st.button(
            "Confirmar omisión",
            type="primary",
            use_container_width=True,
            disabled=not motivo_final,
            key=f"confirm_omitir_{seccion_id}",
        ):
            OmitirSeccion(DocumentoRepository()).ejecutar(
                UUID(documento_id_str),
                seccion_id=seccion_id,
                motivo=motivo_final,
                actor="default",
            )
            st.rerun()


def _cargar_documento_y_brechas(
    documento_id: UUID,
) -> tuple[Documento, list[Brecha]] | None:
    repo = DocumentoRepository()
    documento = repo.obtener(documento_id)
    if documento is None:
        return None
    brechas = GapAnalyzer().analizar(documento)
    return documento, brechas


def _render_resumen(documento: Documento, brechas: list[Brecha]) -> None:
    resuelto_pct = int(documento.porcentaje_resuelto * 100)
    n_completas = sum(1 for s in documento.secciones_obligatorias if s.completitud == "completa")
    n_omitidas = sum(1 for s in documento.secciones_obligatorias if s.completitud == "omitida")
    n_alta = sum(1 for b in brechas if b.severidad == "alta")
    n_media = sum(1 for b in brechas if b.severidad == "media")
    n_baja = sum(1 for b in brechas if b.severidad == "baja")

    muted = SMNYL_COLORS["text_muted"]
    text = SMNYL_COLORS["text"]
    label_style = (
        f"font-size: 0.75rem; color: {muted}; text-transform: uppercase; letter-spacing: 0.05em;"
    )
    big_style = f"font-size: 2rem; font-weight: 600; color: {text};"

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1.container(border=True):
        st.markdown(f"<div style='{label_style}'>Resolución</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='{big_style}'>{resuelto_pct}%</div>",
            unsafe_allow_html=True,
        )
        st.progress(documento.porcentaje_resuelto)
        st.caption(f"{n_completas} completa(s)")

    for col, n, severidad, label in [
        (c2, n_alta, "alta", "Críticas"),
        (c3, n_media, "media", "Atención"),
        (c4, n_baja, "baja", "Sugerencias"),
    ]:
        with col.container(border=True):
            st.markdown(
                f"<div style='{label_style}'>Brechas {label}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<div style='{big_style}'>{n}</div>", unsafe_allow_html=True)
            gap_badge.render(severidad, label)  # type: ignore[arg-type]

    with c5.container(border=True):
        st.markdown(f"<div style='{label_style}'>Omitidas</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='{big_style}'>{n_omitidas}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<span style='display: inline-block; padding: 2px 10px;"
            f" border-radius: 999px; background: {SMNYL_COLORS['bg_soft']};"
            f" color: {SMNYL_COLORS['text_muted']}; font-size: 0.75rem;"
            f" font-weight: 600; border: 1px solid {SMNYL_COLORS['border']};"
            f" letter-spacing: 0.02em;'>Resueltas con motivo</span>",
            unsafe_allow_html=True,
        )


def _build_export_uc(documento_id: UUID) -> ExportarDocumento:
    settings = get_settings()
    llm = AnthropicClient() if settings.anthropic_api_key else None
    return ExportarDocumento(
        DocumentoRepository(),
        template_path=_TEMPLATE_PATH,
        llm=llm,
    )


def _render_gobernanza(documento: Documento) -> None:
    """Card de Gobernanza: estado actual + transiciones disponibles + sign-offs + link a auditoría."""
    sm = DocumentStateMachine()
    estado_actual = documento.estado
    etiqueta, color_estado = _ETIQUETA_ESTADO[estado_actual]
    n_eventos = len(documento.audit_trail)
    doc_id_str = str(documento.id)

    with st.container(border=True):
        col_titulo, col_export, col_link = st.columns([3, 1, 1])
        with col_titulo:
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 12px;
                    margin-bottom: 4px;'>
                    <span style='font-family: var(--font-display); font-size: 1.1rem;
                        font-weight: 600; color: {SMNYL_COLORS["text"]};'>Gobernanza</span>
                    <span style='display: inline-block; padding: 3px 12px;
                        border-radius: 999px; background: {color_estado}1a;
                        color: {color_estado}; font-size: 0.78rem;
                        font-weight: 600; letter-spacing: 0.04em;
                        text-transform: uppercase;'>{etiqueta}</span>
                </div>
                <div style='color: {SMNYL_COLORS["text_muted"]}; font-size: 0.85rem;'>
                    {n_eventos} evento(s) en el audit trail.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_export:
            bytes_key = f"docx_bytes_{doc_id_str}"
            nombre_key = f"docx_nombre_{doc_id_str}"
            if documento.tipo == "prophet":
                if bytes_key in st.session_state:
                    st.download_button(
                        "Descargar Ficha Prophet",
                        data=st.session_state[bytes_key],
                        file_name=st.session_state[nombre_key],
                        mime=_DOCX_MIME,
                        type="primary",
                        use_container_width=True,
                        key=f"download_prophet_{doc_id_str}",
                        on_click=lambda: (
                            st.session_state.pop(bytes_key, None),
                            st.session_state.pop(nombre_key, None),
                        ),
                    )
                else:
                    if st.button(
                        "Exportar Ficha Prophet",
                        use_container_width=True,
                        key=f"export_prophet_{doc_id_str}",
                        help="Genera la Ficha Prophet en formato .docx.",
                    ):
                        from src.core.usecases import DocxWriterProphet
                        try:
                            with st.spinner("Generando Ficha Prophet..."):
                                docx_bytes = DocxWriterProphet().render(documento)
                            nombre_archivo = f"Ficha_Prophet_{documento.metadata_modelo.nombre_modelo.replace(' ', '_')}.docx"
                            st.session_state[bytes_key] = docx_bytes
                            st.session_state[nombre_key] = nombre_archivo
                            st.rerun()
                        except FileNotFoundError as e:
                            st.warning(str(e))
                        except Exception as e:
                            st.error(f"Error al exportar: {e}")
            elif bytes_key in st.session_state:
                st.download_button(
                    "Descargar DOCX",
                    data=st.session_state[bytes_key],
                    file_name=st.session_state[nombre_key],
                    mime=_DOCX_MIME,
                    type="primary",
                    use_container_width=True,
                    key=f"download_{doc_id_str}",
                    on_click=lambda: (
                        st.session_state.pop(bytes_key, None),
                        st.session_state.pop(nombre_key, None),
                    ),
                )
            else:
                if st.button(
                    "Exportar DOCX",
                    use_container_width=True,
                    key=f"export_{doc_id_str}",
                    help="Elige idioma del documento y genera el .docx.",
                ):
                    _dialog_exportar_docx(doc_id_str)
        with col_link:
            if st.button("Ver auditoría completa", use_container_width=True):
                st.session_state["pagina"] = "auditoria"
                st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Sign-offs si aplican al estado actual
        _render_signoffs(documento)

        # Acciones de transición
        _render_acciones_estado(documento, sm)


def _render_signoffs(documento: Documento) -> None:
    """Sección compacta para registrar sign-off Reviewer (en in_review) o FAE (en approved)."""
    repo = DocumentoRepository()

    if documento.estado == "in_review":
        ya_firmado = any(e.tipo == "signoff_reviewer" for e in documento.audit_trail)
        with st.expander(
            "Sign-off del Reviewer" + (" — registrado ✓" if ya_firmado else " — pendiente"),
            expanded=not ya_firmado,
        ):
            if ya_firmado:
                st.caption("El sign-off del Reviewer ya está registrado en el audit trail.")
            else:
                st.markdown(
                    "Para aprobar el documento, el Reviewer debe afirmar que "
                    "actúa **independiente** del Owner y Developer del modelo."
                )
                confirmado = st.checkbox(
                    "Confirmo que actúo como Reviewer independiente del Owner y Developer.",
                    key="signoff_reviewer_check",
                )
                if st.button(
                    "Registrar sign-off Reviewer",
                    type="primary",
                    disabled=not confirmado,
                    key="btn_signoff_reviewer",
                ):
                    RegistrarSignoff(repo).ejecutar(
                        documento.id, rol="reviewer", actor=documento.user_id
                    )
                    st.toast("Sign-off Reviewer registrado.", icon="🖊️")
                    st.rerun()

    if documento.estado == "approved":
        ya_firmado = any(e.tipo == "signoff_fae" for e in documento.audit_trail)
        with st.expander(
            "Sign-off del FAE" + (" — registrado ✓" if ya_firmado else " — pendiente"),
            expanded=not ya_firmado,
        ):
            if ya_firmado:
                st.caption("El sign-off del FAE ya está registrado.")
            else:
                st.markdown(
                    "Para publicar el documento, el FAE debe afirmar que "
                    "acepta el riesgo del modelo dentro de su área (MRM Standard §3.3)."
                )
                confirmado = st.checkbox(
                    "Confirmo que actúo como FAE y acepto el riesgo del modelo.",
                    key="signoff_fae_check",
                )
                if st.button(
                    "Registrar sign-off FAE",
                    type="primary",
                    disabled=not confirmado,
                    key="btn_signoff_fae",
                ):
                    RegistrarSignoff(repo).ejecutar(
                        documento.id, rol="fae", actor=documento.user_id
                    )
                    st.toast("Sign-off FAE registrado.", icon="🖊️")
                    st.rerun()


def _render_acciones_estado(documento: Documento, sm: DocumentStateMachine) -> None:
    """Botones de transición disponibles desde el estado actual."""
    repo = DocumentoRepository()
    origen = documento.estado
    candidatos: list[EstadoDocumento] = [d for (o, d) in _BOTON_DESTINO if o == origen]
    if not candidatos:
        st.caption(
            "Este documento está en estado terminal."
            if origen == "retired"
            else "Sin acciones disponibles en este estado."
        )
        return

    cols = st.columns(len(candidatos))
    for col, destino in zip(cols, candidatos, strict=True):
        with col:
            etiqueta_btn = _BOTON_DESTINO[(origen, destino)]
            resultado = sm.validar_transicion(documento, destino)
            es_primaria = destino in ("in_review", "approved", "published")
            tooltip = "; ".join(resultado.razones) if not resultado.permitida else None
            clicked = st.button(
                etiqueta_btn,
                type="primary" if (es_primaria and resultado.permitida) else "secondary",
                use_container_width=True,
                disabled=not resultado.permitida,
                help=tooltip,
                key=f"btn_estado_{destino}",
            )
            if clicked:
                try:
                    CambiarEstadoDocumento(repo).ejecutar(
                        documento.id, destino=destino, actor=documento.user_id
                    )
                except TransicionRechazada as e:
                    st.error("No se pudo cambiar el estado: " + "; ".join(e.razones))
                else:
                    st.toast(
                        f"Estado cambiado a '{destino}'.",
                        icon="✅",
                    )
                    st.rerun()


def render() -> None:
    documento_id_str = st.session_state.get("documento_actual_id")
    if not documento_id_str:
        header.render(breadcrumbs=["Inicio", "Dashboard"])
        st.warning("No hay un documento seleccionado. Vuelve a Inicio para importar uno.")
        if st.button("Volver a Inicio", type="primary"):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    cargado = _cargar_documento_y_brechas(UUID(documento_id_str))
    if cargado is None:
        header.render(breadcrumbs=["Inicio", "Dashboard"])
        st.error("No se pudo cargar el documento. Es posible que se haya borrado.")
        return

    documento, brechas = cargado
    nombre = documento.metadata_modelo.nombre_modelo or "Documento sin nombre"

    header.render(breadcrumbs=["Inicio", nombre, "Dashboard"])

    # Título y meta
    col_titulo, col_edit = st.columns([5, 1])
    with col_titulo:
        st.markdown(
            f"""
            <h1 style="font-family: var(--font-display); margin-bottom: 0.25rem;">{nombre}</h1>
            <p style="color: {SMNYL_COLORS["text_muted"]}; margin-bottom: 2rem;">
                Estado: <strong>{documento.estado}</strong> ·
                {len(documento.secciones)} secciones del template ·
                {len(documento.audit_trail)} eventos en audit trail
            </p>
            """,
            unsafe_allow_html=True,
        )
    with col_edit:
        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
        if st.button(
            "Editar metadata",
            use_container_width=True,
            help="Editar nombre, ID, FAE, owner, versión y tier del modelo.",
            key=f"edit_meta_{documento.id}",
        ):
            _dialog_editar_metadata(str(documento.id))

    _render_resumen(documento, brechas)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    _render_gobernanza(documento)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Banner de onboarding si la memoria del modelo está vacía
    if documento.memoria_modelo.esta_vacia:
        with st.container(border=True):
            col_msg, col_btn = st.columns([4, 1])
            with col_msg:
                st.markdown(
                    "**🧠 Onboarding del modelo pendiente**  \n"
                    "Completar 6 campos cortos (~2 min) sobre plataforma, frecuencia y "
                    "rutas evita que Claude pregunte estos hechos básicos en cada sección. "
                    "Recomendado antes de empezar las entrevistas."
                )
            with col_btn:
                if st.button(
                    "Completar onboarding",
                    type="primary",
                    use_container_width=True,
                    key="cta_onboarding",
                ):
                    st.session_state["pagina"] = "onboarding"
                    st.rerun()
    m = documento.metricas_uso
    n_llamadas = len(m.llamadas)
    with st.container(border=True):
        col_costo, col_cache, col_llamadas = st.columns(3)
        with col_costo:
            st.metric("Costo de generación", f"${m.costo_total_usd:.2f} USD")
        with col_cache:
            if n_llamadas == 0:
                st.metric("Cache hit rate", "—", help="Aún no hay llamadas LLM registradas.")
            else:
                cache_pct = int(m.cache_hit_rate * 100)
                emoji = "✅" if cache_pct >= 50 else "⚠️"
                st.metric(f"Cache hit rate {emoji}", f"{cache_pct}%")
        with col_llamadas:
            st.metric("Llamadas LLM", str(n_llamadas))
        if n_llamadas == 0:
            st.caption(
                "Sin llamadas registradas todavía. Continúa una entrevista o "
                "reinicia la app si recientemente actualizaste el código."
            )

    st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)

    # Sección: brechas críticas priorizadas
    st.markdown("### Brechas críticas")
    st.caption("Ordenadas por severidad. Empieza por las marcadas como Críticas.")

    text_color = SMNYL_COLORS["text"]
    muted_color = SMNYL_COLORS["text_muted"]
    if not brechas:
        st.success("¡No hay brechas detectadas! El documento está listo para revisión.")
    else:
        for b in brechas[:10]:
            with st.container(border=True):
                col_badge, col_msg = st.columns([1, 6])
                with col_badge:
                    gap_badge.render(b.severidad)
                with col_msg:
                    msg_style = f"color: {text_color}; font-weight: 500;"
                    sug_style = f"color: {muted_color}; font-size: 0.875rem; margin-top: 4px;"
                    st.markdown(
                        f"<div style='{msg_style}'>{b.mensaje}</div>",
                        unsafe_allow_html=True,
                    )
                    if b.sugerencia:
                        st.markdown(
                            f"<div style='{sug_style}'>💡 {b.sugerencia}</div>",
                            unsafe_allow_html=True,
                        )
        if len(brechas) > 10:
            st.caption(f"… y {len(brechas) - 10} brechas adicionales.")

    st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)

    # Sección: grid de secciones
    st.markdown("### Secciones del Model Development Template")
    st.caption(
        "Estado de cada sección oficial del template. La entrevista (Fase 2) "
        "te ayudará a llenar las que están vacías o parciales."
    )

    # Agrupar brechas por sección para badge counts
    brechas_por_seccion: dict[str, int] = defaultdict(int)
    for b in brechas:
        brechas_por_seccion[b.seccion_id] += 1

    # Renderizar grid de 3 columnas, cada card con botones de acción
    cols = st.columns(3)
    for i, seccion in enumerate(documento.secciones):
        with cols[i % 3]:
            seccion_card.render(
                seccion,
                brechas_count=brechas_por_seccion.get(seccion.id, 0),
            )
            if seccion.completitud == "omitida":
                if st.button(
                    "Reactivar",
                    key=f"reactivar_{seccion.id}",
                    use_container_width=True,
                    help="Vuelve la sección a 'vacía' para retomarla.",
                ):
                    repo_reset = DocumentoRepository()
                    doc_reset = repo_reset.obtener(documento.id)
                    if doc_reset is not None:
                        seccion_reset = doc_reset.seccion_por_id(seccion.id)
                        if seccion_reset is not None:
                            seccion_reset.completitud = "vacia"
                            seccion_reset.motivo_omision = None
                            repo_reset.guardar(doc_reset)
                            st.toast(f"Sección {seccion.numero} reactivada.", icon="↩️")
                            st.rerun()
            else:
                col_int, col_omit = st.columns(2)
                with col_int:
                    if st.button(
                        "Entrevistar",
                        key=f"interview_{seccion.id}",
                        use_container_width=True,
                    ):
                        st.session_state["seccion_entrevista_id"] = seccion.id
                        st.session_state["pagina"] = "entrevista"
                        st.rerun()
                with col_omit:
                    if st.button(
                        "Omitir",
                        key=f"omitir_{seccion.id}",
                        use_container_width=True,
                        help="Marcar como omitida con motivo justificado.",
                    ):
                        _dialog_omitir_seccion(
                            str(documento.id),
                            seccion.id,
                            f"{seccion.numero} {seccion.nombre}",
                            seccion.intencion or "",
                        )

    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    # CTAs
    col_cta_1, col_cta_2, col_cta_3, _ = st.columns([1.4, 1, 1, 1.6])
    with col_cta_1:
        # CTA primario: arrancar con la primera brecha de severidad alta
        primera_alta = next(
            (b for b in brechas if b.severidad == "alta" and b.tipo != "metadata_faltante"),
            None,
        )
        if primera_alta is not None and st.button(
            "Iniciar entrevista por la brecha más crítica",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["seccion_entrevista_id"] = primera_alta.seccion_id
            st.session_state["pagina"] = "entrevista"
            st.rerun()
    with col_cta_2:
        if st.button("Vista previa", use_container_width=True):
            st.session_state["pagina"] = "vista_previa"
            st.rerun()
    with col_cta_3:
        if st.button("Volver a Inicio", use_container_width=True):
            st.session_state["pagina"] = "home"
            st.rerun()
