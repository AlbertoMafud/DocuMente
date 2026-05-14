"""Pantalla de onboarding del modelo — captura hechos transversales.

Se muestra una sola vez (al crear documento o al abrir uno cuya `MemoriaModelo`
está vacía). Captura los hechos que aplican a TODO el modelo (no a una sección
específica), para que las entrevistas siguientes no los pregunten.

Es saltable con "Llenar después". Si se salta, los hechos se irán acumulando
orgánicamente vía `KnowledgeExtractor`.
"""

from __future__ import annotations

from uuid import UUID

import streamlit as st

from src.storage.repositories import DocumentoRepository
from src.ui.components import back_button, header
from src.ui.theme import SMNYL_COLORS


def render() -> None:
    documento_id_str = st.session_state.get("documento_actual_id")
    if not documento_id_str:
        header.render(breadcrumbs=["Inicio", "Onboarding"])
        st.warning("No hay documento seleccionado.")
        if st.button("Volver al inicio", type="primary"):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    documento_id = UUID(documento_id_str)
    repo = DocumentoRepository()
    documento = repo.obtener(documento_id)
    if documento is None:
        header.render(breadcrumbs=["Inicio", "Onboarding"])
        st.error("Documento no encontrado.")
        return

    nombre_modelo = documento.metadata_modelo.nombre_modelo or "Documento sin nombre"
    header.render(breadcrumbs=["Inicio", nombre_modelo, "Onboarding"])

    back_button.render(destino="home", etiqueta="← Volver al inicio", key="onboarding_back")

    text_color = SMNYL_COLORS["text"]
    muted = SMNYL_COLORS["text_muted"]

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {text_color};
            margin-bottom: 0.25rem;">Onboarding del modelo</h1>
        <p style="color: {muted}; margin-bottom: 2rem; max-width: 720px;">
            Estos son hechos que aplican a TODO el modelo, no a una sección
            específica. Capturarlos aquí UNA vez evita que Claude los pregunte
            en cada sección. Toma ~2 min y todos los campos son opcionales.
        </p>
        """,
        unsafe_allow_html=True,
    )

    memoria = documento.memoria_modelo

    with st.form("onboarding_modelo"):
        st.markdown("### Identificación del modelo")
        col1, col2 = st.columns(2)
        with col1:
            owner = st.text_input(
                "Model Owner",
                value=memoria.owner_responsable or documento.metadata_modelo.model_owner,
                help="Persona responsable del uso y desempeño del modelo.",
            )
        with col2:
            fae = st.text_input(
                "Functional Area Executive (FAE)",
                value=memoria.fae_responsable or documento.metadata_modelo.fae,
                help="Ejecutivo del área funcional que acepta el riesgo del modelo.",
            )

        st.markdown("### Stack técnico")
        col3, col4 = st.columns(2)
        with col3:
            plataforma = st.text_input(
                "Plataforma",
                value=memoria.plataforma,
                placeholder="Ej. Prophet, GGY Axis, R + AWS",
                help="Dónde corre el modelo en producción.",
            )
        with col4:
            lenguaje = st.text_input(
                "Lenguaje / código",
                value=memoria.lenguaje_codigo,
                placeholder="Ej. R, Python, SQL",
            )

        st.markdown("### Operación")
        col5, col6 = st.columns(2)
        with col5:
            frecuencia = st.text_input(
                "Frecuencia de corridas",
                value=memoria.frecuencia_corridas,
                placeholder="Ej. mensual, trimestral, ad-hoc",
            )
        with col6:
            esg = st.text_input(
                "Generador de Escenarios Económicos (ESG)",
                value=memoria.esg_usado,
                placeholder="Ej. AAA scenario set 2024, ESG corporativo NYL",
            )

        rutas_str = st.text_area(
            "Rutas principales de archivos / carpetas",
            value="\n".join(memoria.rutas_principales),
            placeholder=(
                "Una ruta por línea. Ej.:\n"
                "/data/inputs/MPs/\n"
                "s3://nyl-prophet/outputs/\n"
                "https://sharepoint.smnyl.com/sites/modelos/"
            ),
            height=100,
            help="Donde viven inputs, outputs, código, documentación.",
        )

        st.markdown("### Dependencias")
        col7, col8 = st.columns(2)
        with col7:
            upstream_str = st.text_area(
                "Modelos upstream (uno por línea)",
                value="\n".join(memoria.dependencias_upstream),
                placeholder="Ej.:\nGenerador Económico Corporativo\nMortalidad NIL",
                height=80,
            )
        with col8:
            downstream_str = st.text_area(
                "Modelos downstream (uno por línea)",
                value="\n".join(memoria.dependencias_downstream),
                placeholder="Ej.:\nReporte SOLV II\nBEL Stat",
                height=80,
            )

        st.markdown("### Otros hechos relevantes")
        hechos_libres_str = st.text_area(
            "Cualquier otro hecho transversal del modelo",
            value="\n".join(memoria.hechos_libres),
            placeholder=(
                "Una idea por línea. Ej.:\n"
                "- El modelo es input para attestation MRM semestral.\n"
                "- Tiene tier inherent risk = High.\n"
                "- Última revalidación: 2024 Q4."
            ),
            height=120,
        )

        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        with col_btn1:
            guardar = st.form_submit_button(
                "Guardar y continuar", type="primary", use_container_width=True
            )
        with col_btn2:
            saltar = st.form_submit_button("Saltar (llenar después)", use_container_width=True)

    if guardar or saltar:
        if guardar:
            memoria.owner_responsable = owner.strip()
            memoria.fae_responsable = fae.strip()
            memoria.plataforma = plataforma.strip()
            memoria.lenguaje_codigo = lenguaje.strip()
            memoria.frecuencia_corridas = frecuencia.strip()
            memoria.esg_usado = esg.strip()
            memoria.rutas_principales = [r.strip() for r in rutas_str.splitlines() if r.strip()]
            memoria.dependencias_upstream = [
                r.strip() for r in upstream_str.splitlines() if r.strip()
            ]
            memoria.dependencias_downstream = [
                r.strip() for r in downstream_str.splitlines() if r.strip()
            ]
            memoria.hechos_libres = [h.strip() for h in hechos_libres_str.splitlines() if h.strip()]
            memoria.fuente_ultima_actualizacion = "onboarding"

            # Sincroniza también algunos campos a metadata_modelo si están vacíos
            md = documento.metadata_modelo
            if not md.model_owner and memoria.owner_responsable:
                md.model_owner = memoria.owner_responsable
            if not md.fae and memoria.fae_responsable:
                md.fae = memoria.fae_responsable
            if not md.implementation_platform and memoria.plataforma:
                md.implementation_platform = memoria.plataforma

            repo.guardar(documento)
            st.toast("Memoria del modelo guardada", icon="✅")
        else:
            st.toast("Onboarding saltado — los hechos se acumularán en las entrevistas", icon="ℹ️")

        # Brief inicial solo tiene sentido si el doc viene "desde cero" — todas
        # las secciones vacías. Si viene de importar, las secciones ya tienen
        # contenido y saltamos directo al dashboard.
        doc_es_nuevo = all(s.completitud == "vacia" for s in documento.secciones)
        st.session_state["pagina"] = "brief_inicial" if doc_es_nuevo else "dashboard"
        st.rerun()
