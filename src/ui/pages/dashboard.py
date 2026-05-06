"""Dashboard de brechas — vista principal después de importar un documento.

Muestra:
- Header con breadcrumbs y nombre del modelo.
- Resumen visual: completitud global, brechas por severidad.
- Grid de SectionCard con todas las secciones del template.
- Lista priorizada de brechas críticas con explicación + sugerencia.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

import streamlit as st

from src.core.models import Brecha, Documento
from src.core.usecases import GapAnalyzer
from src.storage.repositories import DocumentoRepository
from src.ui.components import gap_badge, header, seccion_card
from src.ui.theme import SMNYL_COLORS


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
    completitud_pct = int(documento.porcentaje_completitud * 100)
    n_alta = sum(1 for b in brechas if b.severidad == "alta")
    n_media = sum(1 for b in brechas if b.severidad == "media")
    n_baja = sum(1 for b in brechas if b.severidad == "baja")

    muted = SMNYL_COLORS["text_muted"]
    text = SMNYL_COLORS["text"]
    label_style = (
        f"font-size: 0.75rem; color: {muted}; text-transform: uppercase; letter-spacing: 0.05em;"
    )
    big_style = f"font-size: 2rem; font-weight: 600; color: {text};"

    c1, c2, c3, c4 = st.columns(4)
    with c1.container(border=True):
        st.markdown(f"<div style='{label_style}'>Completitud</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='{big_style}'>{completitud_pct}%</div>",
            unsafe_allow_html=True,
        )
        st.progress(documento.porcentaje_completitud)

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

    _render_resumen(documento, brechas)

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
    # Resumen de costo si hay llamadas LLM
    if documento.metricas_uso.llamadas:
        m = documento.metricas_uso
        cache_pct = int(m.cache_hit_rate * 100)
        with st.container(border=True):
            col_costo, col_cache, col_llamadas = st.columns(3)
            with col_costo:
                st.metric("Costo de generación", f"${m.costo_total_usd:.2f} USD")
            with col_cache:
                emoji = "✅" if cache_pct >= 50 else "⚠️"
                st.metric(f"Cache hit rate {emoji}", f"{cache_pct}%")
            with col_llamadas:
                st.metric("Llamadas LLM", str(len(m.llamadas)))

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

    # Renderizar grid de 3 columnas, cada card con botón "Entrevistar"
    cols = st.columns(3)
    for i, seccion in enumerate(documento.secciones):
        with cols[i % 3]:
            seccion_card.render(
                seccion,
                brechas_count=brechas_por_seccion.get(seccion.id, 0),
            )
            if st.button(
                "Entrevistar",
                key=f"interview_{seccion.id}",
                use_container_width=True,
            ):
                st.session_state["seccion_entrevista_id"] = seccion.id
                st.session_state["pagina"] = "entrevista"
                st.rerun()

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
