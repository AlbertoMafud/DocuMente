"""DocuMente — entry point de Streamlit.

Router simple basado en `st.session_state["pagina"]`. Cada pantalla vive
en `src/ui/pages/`. La UI consume use cases desde `src/core/usecases/`.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import streamlit as st

from src.core.usecases import ArchivarDocumento, purgar_papelera_expirada
from src.storage.repositories import DocumentoRepository
from src.ui.components import auth_gate, continue_hero, empty_state, header
from src.ui.pages import (
    auditoria,
    brief_inicial,
    crear_nuevo,
    crear_prophet,
    dashboard,
    editar_seccion_mrm,
    editar_seccion_prophet,
    entrevista,
    importar,
    onboarding,
    vista_previa,
)
from src.ui.theme import SMNYL_COLORS, apply_smnyl_theme

ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo-smnyl.jpg"


def _doc_en_progreso_mas_reciente(repo: DocumentoRepository, user_id: str):
    """Devuelve el doc activo más reciente en draft/in_review, o None."""
    activos = repo.listar_por_usuario(user_id)
    en_progreso = [d for d in activos if d.estado in ("draft", "in_review")]
    if not en_progreso:
        return None
    return max(en_progreso, key=lambda d: d.actualizado_en)


def _render_home() -> None:
    """Pantalla de inicio: hero "Continúa…" o 3 CTAs + lista de documentos."""
    header.render(breadcrumbs=None)

    repo = DocumentoRepository()
    user_id = "default"  # TODO Fase A.1.c: leer de header Cognito
    doc_en_progreso = _doc_en_progreso_mas_reciente(repo, user_id)

    # Modo hero (hay actividad reciente): título compacto + hero + CTAs secundarios.
    # Modo bienvenida (sin actividad): título grande + 3 CTAs prominentes.
    if doc_en_progreso is not None:
        st.markdown(
            f"""
            <h1 style="
                font-family: var(--font-display);
                font-size: 2rem;
                font-weight: 600;
                color: {SMNYL_COLORS["text"]};
                margin-bottom: 1.5rem;
                line-height: 1.2;
            ">DocuMente</h1>
            """,
            unsafe_allow_html=True,
        )
        clicked = continue_hero.render(doc_en_progreso)
        if clicked:
            st.session_state["documento_actual_id"] = str(doc_en_progreso.id)
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        # CTAs secundarios pequeños como text-link row
        col_a, col_b, col_c, _ = st.columns([1.1, 1.1, 1.1, 1])
        with col_a:
            if st.button(
                "Crear nuevo",
                use_container_width=True,
                key="cta_secundario_crear",
            ):
                st.session_state["pagina"] = "crear_nuevo"
                st.rerun()
        with col_b:
            if st.button(
                "Importar otro .docx",
                use_container_width=True,
                key="cta_secundario_importar",
            ):
                st.session_state["pagina"] = "importar"
                st.rerun()
        with col_c:
            if st.button(
                "Ficha Prophet",
                use_container_width=True,
                key="cta_secundario_prophet",
            ):
                st.session_state["pagina"] = "crear_prophet"
                st.rerun()
    else:
        st.markdown(
            f"""
            <h1 style="
                font-family: var(--font-display);
                font-size: 3rem;
                font-weight: 600;
                color: {SMNYL_COLORS["text"]};
                margin-bottom: 0.5rem;
                line-height: 1.1;
            ">Documenta modelos sin fricción</h1>
            <p style="
                font-size: 1.25rem;
                color: {SMNYL_COLORS["text_muted"]};
                margin-bottom: 3rem;
                max-width: 720px;
            ">DocuMente entrevista, estructura y genera documentación institucional
            alineada con el marco MRM de SMNYL — desde cero o partiendo de un
            documento existente.</p>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b, col_c, _ = st.columns([1, 1, 1, 1])
        with col_a:
            if st.button(
                "Crear nuevo documento",
                type="primary",
                use_container_width=True,
                help="Empieza con las 28 secciones vacías del template oficial NYL.",
            ):
                st.session_state["pagina"] = "crear_nuevo"
                st.rerun()
        with col_b:
            if st.button("Mejorar documento existente", use_container_width=True):
                st.session_state["pagina"] = "importar"
                st.rerun()
        with col_c:
            if st.button(
                "Iniciar Ficha Prophet",
                use_container_width=True,
                help="Importa el registro Excel de Modelos Actuariales y genera la ficha técnica.",
            ):
                st.session_state["pagina"] = "crear_prophet"
                st.rerun()

    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    tab_activos, tab_archivados, tab_papelera = st.tabs(["Activos", "Archivados", "Papelera"])
    with tab_activos:
        _render_lista_documentos(repo, user_id, modo="activos")
    with tab_archivados:
        _render_lista_documentos(repo, user_id, modo="archivados")
    with tab_papelera:
        _render_lista_documentos(repo, user_id, modo="papelera")


def _render_empty_state_tab(modo: str) -> None:
    """Empty state amigable para tabs sin documentos.

    El tab 'Activos' lleva CTA primario porque su acción esperada es crear
    o importar; los otros dos son informativos (archivar/restaurar no aplica
    sin documentos).
    """
    if modo == "activos":
        clicked = empty_state.render(
            titulo="Aún no tienes documentos activos",
            descripcion=(
                "Crea un documento desde cero con las 28 secciones del template oficial NYL, "
                "importa un .docx existente para mejorarlo, o inicia una Ficha Prophet."
            ),
            icono="📄",
            cta_label="Crear documento",
        )
        if clicked:
            st.session_state["pagina"] = "crear_nuevo"
            st.rerun()
    elif modo == "archivados":
        empty_state.render(
            titulo="Sin documentos archivados",
            descripcion=(
                "Los documentos que archives aparecerán aquí. Archivar no borra: "
                "el documento se preserva fuera de la vista principal y puedes desarchivarlo "
                "cuando lo necesites."
            ),
            icono="📦",
        )
    else:  # papelera
        empty_state.render(
            titulo="Papelera vacía",
            descripcion=(
                "Los documentos enviados a papelera se eliminan automáticamente tras 30 días "
                "si no los restauras. Mientras tanto puedes recuperarlos desde aquí."
            ),
            icono="🗑️",
        )


def _render_lista_documentos(repo: DocumentoRepository, user_id: str, *, modo: str) -> None:
    """Renderiza una lista de documentos con acciones según el modo."""
    if modo == "activos":
        docs = repo.listar_por_usuario(user_id)[:20]
    elif modo == "archivados":
        docs = [d for d in repo.listar_por_usuario(user_id, incluir_archivados=True) if d.archivado]
    else:  # papelera
        docs = repo.listar_por_usuario(user_id, solo_papelera=True)

    if not docs:
        _render_empty_state_tab(modo)
        return

    archivar_uc = ArchivarDocumento(repo)
    muted = SMNYL_COLORS["text_muted"]
    for doc in docs:
        nombre = doc.metadata_modelo.nombre_modelo or "Documento sin nombre"
        pct = int(doc.porcentaje_completitud * 100)
        with st.container(border=True):
            col_info, col_meta, col_btn = st.columns([3, 2, 1.2])
            with col_info:
                meta_html = (
                    f"<span style='color: {muted}; font-size: 0.875rem;'>"
                    f"Estado: {doc.estado} · {pct}% completitud</span>"
                )
                st.markdown(
                    f"**{nombre}**  \n{meta_html}",
                    unsafe_allow_html=True,
                )
            with col_meta:
                st.caption(f"Actualizado: {doc.actualizado_en.strftime('%Y-%m-%d %H:%M')}")
            with col_btn:
                if modo == "activos":
                    if st.button("Abrir", key=f"open_{doc.id}", use_container_width=True):
                        st.session_state["documento_actual_id"] = str(doc.id)
                        st.session_state["pagina"] = "dashboard"
                        st.rerun()
                elif modo == "archivados":
                    if st.button("Desarchivar", key=f"unarch_{doc.id}", use_container_width=True):
                        archivar_uc.desarchivar(doc.id, actor=user_id)
                        st.rerun()
                else:  # papelera
                    if st.button("Restaurar", key=f"restore_{doc.id}", use_container_width=True):
                        archivar_uc.restaurar_de_papelera(doc.id, actor=user_id)
                        st.rerun()

            # Acciones secundarias (en una segunda fila)
            if modo == "activos":
                col_arch, col_pap, _ = st.columns([1, 1, 4])
                with col_arch:
                    if st.button(
                        "📦 Archivar",
                        key=f"arch_{doc.id}",
                        use_container_width=True,
                        help="Oculta este documento de la vista principal sin borrarlo.",
                    ):
                        archivar_uc.archivar(doc.id, actor=user_id)
                        st.rerun()
                with col_pap:
                    if st.button(
                        "🗑️ Papelera",
                        key=f"trash_{doc.id}",
                        use_container_width=True,
                        help="Mueve a papelera. Se purga automáticamente tras 30 días.",
                    ):
                        archivar_uc.enviar_a_papelera(doc.id, actor=user_id)
                        st.rerun()
            elif modo == "papelera":
                # Indicar días restantes hasta auto-purge
                if doc.archivado_en is not None:
                    from datetime import UTC, datetime, timedelta

                    expira = doc.archivado_en + timedelta(days=30)
                    dias = max(0, (expira - datetime.now(UTC)).days)
                    st.caption(f"Se eliminará automáticamente en {dias} día(s).")


def main() -> None:
    st.set_page_config(
        page_title="DocuMente — SMNYL",
        page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_smnyl_theme()

    # Gate de password temporal (mitigación pre-Cognito real, ver Fase A.1.b)
    if not auth_gate.proteger_app():
        return

    # Job idempotente: purgar papelera expirada (>30 días). Se ejecuta una vez
    # por sesión de Streamlit; en EC2 lo ideal es moverlo a un cron del SO.
    if not st.session_state.get("_purge_papelera_executed"):
        with contextlib.suppress(Exception):
            purgar_papelera_expirada(DocumentoRepository())
        st.session_state["_purge_papelera_executed"] = True

    # Inicializar router
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "home"

    pagina = st.session_state["pagina"]

    if pagina == "home":
        _render_home()
    elif pagina == "importar":
        importar.render()
    elif pagina == "crear_nuevo":
        crear_nuevo.render()
    elif pagina == "dashboard":
        dashboard.render()
    elif pagina == "entrevista":
        entrevista.render()
    elif pagina == "onboarding":
        onboarding.render()
    elif pagina == "brief_inicial":
        brief_inicial.render()
    elif pagina == "vista_previa":
        vista_previa.render()
    elif pagina == "auditoria":
        auditoria.render()
    elif pagina == "crear_prophet":
        crear_prophet.render()
    elif pagina == "editar_seccion_prophet":
        editar_seccion_prophet.render()
    elif pagina == "editar_seccion_mrm":
        editar_seccion_mrm.render()
    else:
        st.error(f"Página desconocida: {pagina}")
        st.session_state["pagina"] = "home"


if __name__ == "__main__":
    main()
