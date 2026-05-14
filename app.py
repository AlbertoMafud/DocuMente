"""DocuMente — entry point de Streamlit.

Router simple basado en `st.session_state["pagina"]`. Cada pantalla vive
en `src/ui/pages/`. La UI consume use cases desde `src/core/usecases/`.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.pages import (
    auditoria,
    brief_inicial,
    crear_nuevo,
    crear_prophet,
    dashboard,
    editar_seccion_prophet,
    entrevista,
    importar,
    onboarding,
    vista_previa,
)
from src.ui.theme import SMNYL_COLORS, apply_smnyl_theme

ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo-smnyl.jpg"


def _render_home() -> None:
    """Pantalla de inicio: hero + CTAs + lista de documentos recientes."""
    header.render(breadcrumbs=None)

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

    # Documentos recientes
    repo = DocumentoRepository()
    recientes = repo.listar_por_usuario("default")[:5]

    if recientes:
        st.markdown("### Documentos recientes")
        muted = SMNYL_COLORS["text_muted"]
        for doc in recientes:
            nombre = doc.metadata_modelo.nombre_modelo or "Documento sin nombre"
            pct = int(doc.porcentaje_completitud * 100)
            with st.container(border=True):
                col_info, col_meta, col_btn = st.columns([3, 2, 1])
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
                    if st.button("Abrir", key=f"open_{doc.id}", use_container_width=True):
                        st.session_state["documento_actual_id"] = str(doc.id)
                        st.session_state["pagina"] = "dashboard"
                        st.rerun()
    else:
        st.markdown("### Empezar")
        st.caption(
            "Aún no tienes documentos. Importa un .docx existente para "
            "ver tu primer dashboard de brechas."
        )


def main() -> None:
    st.set_page_config(
        page_title="DocuMente — SMNYL",
        page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_smnyl_theme()

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
    else:
        st.error(f"Página desconocida: {pagina}")
        st.session_state["pagina"] = "home"


if __name__ == "__main__":
    main()
