"""Vista previa HTML del documento completo.

Renderiza todas las secciones concatenadas, secciones vacías como placeholders,
apéndices al final y un panel lateral con metadata + costo + estado.

NO es el DOCX final (eso es Fase 3) — es un preview continuo durante el
proceso para que el usuario tenga visibilidad de cómo va quedando todo.
"""

from __future__ import annotations

from uuid import UUID

import streamlit as st

from src.core.models import Documento
from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.theme import SMNYL_COLORS


def _render_seccion(idx: int, seccion: object) -> None:
    """Renderiza una sección con su contenido o placeholder + botón de edición inline."""
    titulo = f"{seccion.numero} {seccion.nombre}"  # type: ignore[attr-defined]
    text_color = SMNYL_COLORS["text"]
    muted = SMNYL_COLORS["text_muted"]

    col_titulo, col_edit = st.columns([6, 1])
    with col_titulo:
        st.markdown(
            f"<h2 id='sec-{idx}' style='font-family: var(--font-display); "
            f"color: {text_color}; margin-top: 2.5rem; "
            f"border-bottom: 1px solid {SMNYL_COLORS['border']}; "
            f"padding-bottom: 0.5rem;'>{titulo}</h2>",
            unsafe_allow_html=True,
        )
    with col_edit:
        st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)
        # Solo MRM tiene editor inline (tipo de catálogo "model_development").
        # Prophet usa su propio editor especializado desde dashboard.
        if st.button(
            "✏️ Editar",
            key=f"edit_inline_{seccion.id}",  # type: ignore[attr-defined]
            help="Abre el editor inline en una pantalla nueva con preview en vivo.",
            use_container_width=True,
        ):
            st.session_state["mrm_seccion_id"] = seccion.id  # type: ignore[attr-defined]
            st.session_state["pagina"] = "editar_seccion_mrm"
            st.rerun()

    if seccion.contenido:  # type: ignore[attr-defined]
        st.markdown(seccion.contenido)  # type: ignore[attr-defined]
    else:
        bg = "#fdf6e3"  # tono cálido suave
        border = SMNYL_COLORS["warning_dark"]  # acento más sólido y consistente con tokens AA
        oblig = "obligatoria" if seccion.obligatoria else "opcional"  # type: ignore[attr-defined]
        st.markdown(
            f"""
            <div style='background: {bg}; border-left: 4px solid {border};
                padding: 12px 16px; border-radius: 4px; margin: 8px 0;'>
                <div style='color: {muted}; font-size: 0.875rem;'>
                    <em>Sección {oblig} pendiente.</em>
                    Click ✏️ para llenarla manualmente, o usa la entrevista desde el dashboard.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_apendices(documento: Documento) -> None:
    if not documento.apendices:
        return
    text_color = SMNYL_COLORS["text"]
    st.markdown(
        f"<h2 style='font-family: var(--font-display); color: {text_color}; "
        "margin-top: 3rem;'>Apéndices</h2>",
        unsafe_allow_html=True,
    )
    for i, ap in enumerate(documento.apendices, start=1):
        st.markdown(
            f"<h3 id='apendice-{i}' style='font-family: var(--font-display); "
            f"color: {text_color}; margin-top: 1.5rem;'>"
            f"Apéndice {chr(64 + i)}: {ap.titulo}</h3>",
            unsafe_allow_html=True,
        )
        st.caption(
            f"Vinculado a sección **{ap.seccion_origen_id}**. "
            f"Archivo origen: `{ap.nombre_archivo_original}`."
        )
        st.markdown(ap.contenido_md)


def _render_panel_lateral(documento: Documento) -> None:
    md = documento.metadata_modelo
    mem = documento.memoria_modelo
    metricas = documento.metricas_uso

    st.markdown("### Información general")
    st.write(f"**Modelo:** {md.nombre_modelo or '_(sin nombre)_'}")
    st.write(f"**Owner:** {md.model_owner or '_(pendiente)_'}")
    st.write(f"**FAE:** {md.fae or '_(pendiente)_'}")
    st.write(f"**Plataforma:** {mem.plataforma or md.implementation_platform or '_(pendiente)_'}")

    st.markdown("---")
    st.markdown("### Estado")
    pct = int(documento.porcentaje_completitud * 100)
    st.progress(documento.porcentaje_completitud, text=f"{pct}% completitud")
    st.write(f"**Secciones:** {len(documento.secciones)}")
    completas = sum(1 for s in documento.secciones if s.completitud == "completa")
    st.write(f"**Completas:** {completas}")
    st.write(f"**Apéndices:** {len(documento.apendices)}")

    if metricas.llamadas:
        st.markdown("---")
        st.markdown("### Costo y consumo LLM")
        st.metric("Costo total", f"${metricas.costo_total_usd:.4f} USD")
        cache_pct = int(metricas.cache_hit_rate * 100)
        emoji = "✅" if cache_pct >= 50 else "⚠️"
        st.metric(f"Cache hit {emoji}", f"{cache_pct}%")
        st.caption(
            f"{len(metricas.llamadas)} llamadas · "
            f"{metricas.total_input_tokens + metricas.total_cache_read_tokens:,} "
            "tokens de input"
        )


def render() -> None:
    documento_id_str = st.session_state.get("documento_actual_id")
    if not documento_id_str:
        header.render(breadcrumbs=["Inicio", "Vista previa"])
        st.warning("No hay documento seleccionado.")
        if st.button("Volver al inicio", type="primary"):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    documento_id = UUID(documento_id_str)
    documento = DocumentoRepository().obtener(documento_id)
    if documento is None:
        header.render(breadcrumbs=["Inicio", "Vista previa"])
        st.error("Documento no encontrado.")
        return

    nombre_modelo = documento.metadata_modelo.nombre_modelo or "Documento sin nombre"
    header.render(breadcrumbs=["Inicio", nombre_modelo, "Vista previa"])

    text_color = SMNYL_COLORS["text"]
    muted = SMNYL_COLORS["text_muted"]

    # Layout: documento (70%) | panel lateral (30%)
    col_doc, col_lateral = st.columns([2.3, 1])

    with col_doc:
        # Portada
        st.markdown(
            f"""
            <div style='border-bottom: 2px solid {SMNYL_COLORS["primary"]};
                padding-bottom: 1rem; margin-bottom: 1.5rem;'>
                <div style='color: {muted}; font-size: 0.75rem;
                    text-transform: uppercase; letter-spacing: 0.05em;'>
                    Model Development Documentation
                </div>
                <h1 style='font-family: var(--font-display); color: {text_color};
                    font-size: 2.5rem; margin-top: 0.5rem;'>
                    {nombre_modelo}
                </h1>
                <div style='color: {muted}; font-size: 0.875rem;'>
                    Estado: <strong>{documento.estado}</strong> ·
                    Versión: {documento.metadata_modelo.current_version or "1.0"} ·
                    Vista previa generada en tiempo real
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Banner: este es preview, no DOCX final
        st.info(
            "Esta es una vista previa para revisar el avance. La exportación "
            "DOCX con marca SMNYL completa estará disponible en Fase 3."
        )

        # Secciones
        for i, seccion in enumerate(documento.secciones, start=1):
            _render_seccion(i, seccion)

        # Apéndices al final
        _render_apendices(documento)

    with col_lateral:
        with st.container(border=True):
            _render_panel_lateral(documento)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        if st.button("Volver al dashboard", use_container_width=True):
            st.session_state["pagina"] = "dashboard"
            st.rerun()
